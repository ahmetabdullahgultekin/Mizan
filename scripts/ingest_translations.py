#!/usr/bin/env python3
"""
Verse Translation Ingestion Script

Downloads English (Sahih International) and Turkish (Diyanet) verse translations
from the quran.com API v4 and stores them in the verse_translations table with
semantic embeddings for cross-lingual search.

Usage:
    # Ingest all translations (English + Turkish)
    python scripts/ingest_translations.py

    # Ingest only English translations
    python scripts/ingest_translations.py --language en

    # Ingest only Turkish translations
    python scripts/ingest_translations.py --language tr

    # Skip verses that already have translations
    python scripts/ingest_translations.py --skip-existing

    # Skip embedding generation (just ingest text)
    python scripts/ingest_translations.py --skip-embed

    # Ingest a single surah (for testing)
    python scripts/ingest_translations.py --surah 1

Environment variables:
    DATABASE_URL  PostgreSQL connection string (default: postgresql+asyncpg://mizan:mizan@localhost:5432/mizan)

Prerequisites:
    1. Run 'alembic upgrade head' to apply all migrations (including 0004_verse_translations)
    2. Ensure the verses table is populated (run ingest_tanzil.py first)
    3. Internet access for quran.com API

Data Source:
    quran.com API v4 — https://api.quran.com/api/v4/quran/translations/{resource_id}?chapter_number={1-114}
    English (Sahih International) = resource ID 20
    Turkish (Diyanet)             = resource ID 77
"""

import argparse
import asyncio
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

QURAN_API_BASE = "https://api.quran.com/api/v4"

# Translation resources on quran.com
TRANSLATION_RESOURCES = {
    "en": {
        "resource_id": 20,
        "source_name": "Sahih International",
    },
    "tr": {
        "resource_id": 77,
        "source_name": "Diyanet",
    },
}

DEFAULT_DB_URL = "postgresql+asyncpg://mizan:mizan@localhost:5432/mizan"

# Passage prefix for e5-style embedding models
PASSAGE_PREFIX = "passage: "


# ---------------------------------------------------------------------------
# API Fetching
# ---------------------------------------------------------------------------


def strip_html(html: str) -> str:
    """Remove HTML tags and decode entities from translation text."""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Remove footnote markers like <sup foot_note=123>1</sup> remnants
    text = re.sub(r"\s+", " ", text).strip()
    # Replace common HTML entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'")
    return text


def fetch_translations_for_chapter(
    surah_number: int,
    resource_id: int,
    retries: int = 3,
) -> dict[int, str]:
    """
    Fetch translations for an entire chapter from quran.com API v4.

    Returns: {verse_number: translation_text} for all verses in the surah.
    """
    url = f"{QURAN_API_BASE}/quran/translations/{resource_id}?chapter_number={surah_number}"
    headers = {"Accept": "application/json", "User-Agent": "Mizan-Ingest/1.0"}

    for attempt in range(retries):
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            translations = data.get("translations", [])
            result: dict[int, str] = {}
            for idx, entry in enumerate(translations):
                text = entry.get("text", "")
                if not text:
                    continue

                # The API may include verse_key or verse_number,
                # or entries may be in sequential order (1-based).
                verse_key = entry.get("verse_key", "")
                if verse_key and ":" in verse_key:
                    verse_num = int(verse_key.split(":")[1])
                elif "verse_number" in entry:
                    verse_num = int(entry["verse_number"])
                else:
                    # Entries are in order, 1-based
                    verse_num = idx + 1

                clean_text = strip_html(text)
                if clean_text:
                    result[verse_num] = clean_text

            return result

        except HTTPError as e:
            if e.code == 429:
                wait = 2 ** (attempt + 1)
                logger.warning("Rate limited (429), waiting %ds...", wait)
                time.sleep(wait)
            elif e.code == 404:
                logger.warning("Surah %d: 404 Not Found for resource %d, skipping", surah_number, resource_id)
                return {}
            else:
                logger.warning(
                    "HTTP %d for surah %d (attempt %d/%d)",
                    e.code, surah_number, attempt + 1, retries,
                )
                time.sleep(1)
        except (URLError, TimeoutError) as e:
            logger.warning(
                "Network error for surah %d (attempt %d/%d): %s",
                surah_number, attempt + 1, retries, e,
            )
            time.sleep(2)

    logger.error("Failed to fetch surah %d after %d retries", surah_number, retries)
    return {}


# ---------------------------------------------------------------------------
# Database Ingestion
# ---------------------------------------------------------------------------


async def ingest_translations(
    language: str | None,
    surah_number: int | None,
    skip_existing: bool,
    skip_embed: bool,
    batch_size: int,
) -> None:
    from sqlalchemy import select

    from mizan.infrastructure.persistence.database import close_db, get_session_context, init_db
    from mizan.infrastructure.persistence.models import VerseModel, VerseTranslationModel

    await init_db()

    try:
        languages = [language] if language else list(TRANSLATION_RESOURCES.keys())

        for lang in languages:
            config = TRANSLATION_RESOURCES[lang]
            resource_id = config["resource_id"]
            source_name = config["source_name"]

            logger.info(
                "Starting translation ingestion: %s (%s, resource_id=%d)",
                source_name, lang, resource_id,
            )

            async with get_session_context() as session:
                # Build a lookup of (surah_number, verse_number) -> verse_id
                result = await session.execute(
                    select(VerseModel.id, VerseModel.surah_number, VerseModel.verse_number)
                )
                verse_lookup: dict[tuple[int, int], object] = {
                    (row.surah_number, row.verse_number): row.id
                    for row in result.fetchall()
                }
                logger.info("Loaded %d verse IDs from database", len(verse_lookup))

                # If skip_existing, find which verses already have translations
                existing_keys: set[tuple[int, int]] = set()
                if skip_existing:
                    result = await session.execute(
                        select(
                            VerseTranslationModel.surah_number,
                            VerseTranslationModel.verse_number,
                        ).where(
                            VerseTranslationModel.language == lang,
                            VerseTranslationModel.resource_id == resource_id,
                        )
                    )
                    existing_keys = {
                        (row.surah_number, row.verse_number)
                        for row in result.fetchall()
                    }
                    if existing_keys:
                        logger.info(
                            "Skipping %d existing %s translations",
                            len(existing_keys), lang,
                        )

                # Fetch and store translations surah by surah
                surahs_to_process = [surah_number] if surah_number else list(range(1, 115))
                total_stored = 0

                for s_num in surahs_to_process:
                    logger.info(
                        "Fetching %s translations for Surah %d/%d...",
                        lang.upper(), s_num, surahs_to_process[-1],
                    )
                    trans_data = fetch_translations_for_chapter(s_num, resource_id)

                    if not trans_data:
                        logger.warning("No translation data for Surah %d (%s)", s_num, lang)
                        continue

                    batch_models = []
                    for v_num, text in trans_data.items():
                        key = (s_num, v_num)
                        if skip_existing and key in existing_keys:
                            continue
                        verse_id = verse_lookup.get(key)
                        if verse_id is None:
                            logger.warning("No verse_id for %d:%d, skipping", s_num, v_num)
                            continue

                        model = VerseTranslationModel(
                            id=uuid4(),
                            verse_id=verse_id,
                            surah_number=s_num,
                            verse_number=v_num,
                            language=lang,
                            translation_text=text,
                            source_name=source_name,
                            resource_id=resource_id,
                            embedding=None,
                            model_name=None,
                            created_at=datetime.utcnow(),
                        )
                        batch_models.append(model)

                    if batch_models:
                        # Use upsert to handle re-runs gracefully
                        from sqlalchemy.dialects.postgresql import insert as pg_insert

                        for m in batch_models:
                            stmt = pg_insert(VerseTranslationModel).values(
                                id=m.id,
                                verse_id=m.verse_id,
                                surah_number=m.surah_number,
                                verse_number=m.verse_number,
                                language=m.language,
                                translation_text=m.translation_text,
                                source_name=m.source_name,
                                resource_id=m.resource_id,
                                embedding=None,
                                model_name=None,
                                created_at=m.created_at,
                            )
                            stmt = stmt.on_conflict_do_update(
                                constraint="uq_verse_translation",
                                set_={
                                    "translation_text": stmt.excluded.translation_text,
                                    "source_name": stmt.excluded.source_name,
                                    "created_at": stmt.excluded.created_at,
                                },
                            )
                            await session.execute(stmt)

                        total_stored += len(batch_models)

                    # Flush every 10 surahs
                    if s_num % 10 == 0:
                        await session.flush()
                        logger.info("  Flushed: %d translations stored so far", total_stored)

                    # Rate limiting — be respectful to quran.com API
                    time.sleep(1)

                await session.flush()
                logger.info(
                    "Stored %d %s translations (%s)",
                    total_stored, lang.upper(), source_name,
                )

                # Generate embeddings
                if not skip_embed and total_stored > 0:
                    await _embed_translations(session, lang, batch_size)

            logger.info("Done with %s translations!", lang.upper())

    finally:
        await close_db()


async def _embed_translations(
    session: object,
    language: str,
    batch_size: int,
) -> None:
    """Generate embeddings for all un-embedded translations of a given language."""
    from sqlalchemy import select, update

    from mizan.infrastructure.embeddings.sentence_transformer_service import (
        SentenceTransformerEmbeddingService,
    )
    from mizan.infrastructure.persistence.models import VerseTranslationModel

    logger.info("Generating embeddings for %s translations...", language.upper())

    embedding_service = SentenceTransformerEmbeddingService(
        model_name="intfloat/multilingual-e5-base"
    )
    model_name = embedding_service.model_name

    # Fetch all translations without embeddings for this language
    result = await session.execute(  # type: ignore[union-attr]
        select(VerseTranslationModel)
        .where(
            VerseTranslationModel.language == language,
            VerseTranslationModel.embedding.is_(None),
        )
        .order_by(
            VerseTranslationModel.surah_number,
            VerseTranslationModel.verse_number,
        )
    )
    translations = list(result.scalars().all())

    if not translations:
        logger.info("All %s translations already have embeddings.", language.upper())
        return

    logger.info(
        "Embedding %d %s translations in batches of %d...",
        len(translations), language.upper(), batch_size,
    )

    embedded = 0
    for i in range(0, len(translations), batch_size):
        batch = translations[i : i + batch_size]
        texts = [PASSAGE_PREFIX + t.translation_text for t in batch]
        embeddings = await embedding_service.embed_batch(texts)

        for trans, emb in zip(batch, embeddings):
            await session.execute(  # type: ignore[union-attr]
                update(VerseTranslationModel)
                .where(VerseTranslationModel.id == trans.id)
                .values(embedding=emb, model_name=model_name)
            )

        embedded += len(batch)
        await session.flush()  # type: ignore[union-attr]
        logger.info("  Embedded %d/%d translations", embedded, len(translations))

    logger.info("Embedding complete: %d %s translations embedded.", embedded, language.upper())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest verse translations from quran.com into Mizan"
    )
    parser.add_argument(
        "--language",
        choices=["en", "tr", "all"],
        default="all",
        help="Language to ingest: 'en' (Sahih International), 'tr' (Diyanet), or 'all' (default: all)",
    )
    parser.add_argument(
        "--surah",
        type=int,
        default=None,
        help="Surah number to ingest (default: all 114 surahs)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip verses that already have translations stored",
    )
    parser.add_argument(
        "--skip-embed",
        action="store_true",
        help="Skip embedding generation (just ingest text)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Embedding batch size (default: 32)",
    )
    parser.add_argument(
        "--db-url",
        default=None,
        help="PostgreSQL async URL (default: $DATABASE_URL or local)",
    )
    args = parser.parse_args()

    import os

    db_url = args.db_url or os.environ.get("DATABASE_URL", DEFAULT_DB_URL)
    # Ensure async driver
    if "asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    lang = None if args.language == "all" else args.language

    asyncio.run(
        ingest_translations(
            language=lang,
            surah_number=args.surah,
            skip_existing=args.skip_existing,
            skip_embed=args.skip_embed,
            batch_size=args.batch_size,
        )
    )


if __name__ == "__main__":
    main()
