#!/usr/bin/env python3
"""
Tafsir Ibn Kathir Ingestion Script

Downloads Tafsir Ibn Kathir (Arabic) from the quran.com API v4 and inserts
it into the Mizan library system (library_spaces → text_sources → text_chunks).

After ingestion, generates semantic embeddings for all chunks so they appear
in the /search/semantic endpoint results.

Usage:
    # Ingest all 114 surahs (default)
    python scripts/ingest_tafsir.py

    # Ingest a single surah (for testing)
    python scripts/ingest_tafsir.py --surah 1

    # Skip embedding generation (just ingest text)
    python scripts/ingest_tafsir.py --skip-embed

    # Use a specific library space name
    python scripts/ingest_tafsir.py --space "My Research Library"

Environment variables:
    DATABASE_URL  PostgreSQL connection string (default: postgresql+asyncpg://mizan:mizan@localhost:5432/mizan)

Prerequisites:
    1. Run 'alembic upgrade head' to apply all migrations
    2. Ensure the verses table is populated (run ingest_tanzil.py first)
    3. Internet access for quran.com API

Data Source:
    quran.com API v4 — https://api.quran.com/api/v4/tafsirs/{tafsir_id}/by_chapter/{chapter}
    Tafsir Ibn Kathir (Arabic) = resource ID 14 (ar-tafsir-ibn-kathir)
"""

import argparse
import asyncio
import json
import logging
import re
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from uuid import uuid4
from datetime import datetime

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

# quran.com API v4 — Tafsir Ibn Kathir (Arabic)
# Resource ID 14 = ar-tafsir-ibn-kathir (verified via /resources/tafsirs)
QURAN_API_BASE = "https://api.quran.com/api/v4"
TAFSIR_ID = 14  # Arabic Ibn Kathir

# Surah verse counts (from Tanzil data — same as ingest_tanzil.py)
SURAH_VERSE_COUNTS = {
    1: 7, 2: 286, 3: 200, 4: 176, 5: 120, 6: 165, 7: 206, 8: 75,
    9: 129, 10: 109, 11: 123, 12: 111, 13: 43, 14: 52, 15: 99,
    16: 128, 17: 111, 18: 110, 19: 98, 20: 135, 21: 112, 22: 78,
    23: 118, 24: 64, 25: 77, 26: 227, 27: 93, 28: 88, 29: 69,
    30: 60, 31: 34, 32: 30, 33: 73, 34: 54, 35: 45, 36: 83,
    37: 182, 38: 88, 39: 75, 40: 85, 41: 54, 42: 53, 43: 89,
    44: 59, 45: 37, 46: 35, 47: 38, 48: 29, 49: 18, 50: 45,
    51: 60, 52: 49, 53: 62, 54: 55, 55: 78, 56: 96, 57: 29,
    58: 22, 59: 24, 60: 13, 61: 14, 62: 11, 63: 11, 64: 18,
    65: 12, 66: 12, 67: 30, 68: 52, 69: 52, 70: 44, 71: 28,
    72: 28, 73: 20, 74: 56, 75: 40, 76: 31, 77: 50, 78: 40,
    79: 46, 80: 42, 81: 29, 82: 19, 83: 36, 84: 25, 85: 22,
    86: 17, 87: 19, 88: 26, 89: 30, 90: 20, 91: 15, 92: 21,
    93: 11, 94: 8, 95: 8, 96: 19, 97: 5, 98: 8, 99: 8,
    100: 11, 101: 11, 102: 8, 103: 3, 104: 9, 105: 5, 106: 4,
    107: 7, 108: 3, 109: 6, 110: 3, 111: 5, 112: 4, 113: 5, 114: 6,
}

DEFAULT_DB_URL = "postgresql+asyncpg://mizan:mizan@localhost:5432/mizan"

# Passage prefix for e5-style embedding models
PASSAGE_PREFIX = "passage: "


# ---------------------------------------------------------------------------
# API Fetching
# ---------------------------------------------------------------------------

def strip_html(html: str) -> str:
    """Remove HTML tags and decode entities from tafsir text."""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Replace common HTML entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'")
    return text


def fetch_tafsir_for_chapter(surah_number: int, retries: int = 3) -> dict[int, str]:
    """
    Fetch tafsir for an entire chapter from quran.com API.

    Returns: {verse_number: tafsir_text} for all verses in the surah.
    """
    url = f"{QURAN_API_BASE}/tafsirs/{TAFSIR_ID}/by_chapter/{surah_number}"
    headers = {"Accept": "application/json", "User-Agent": "Mizan-Ingest/1.0"}

    for attempt in range(retries):
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            tafsirs = data.get("tafsirs", [])
            result: dict[int, str] = {}
            for entry in tafsirs:
                verse_key = entry.get("verse_key", "")
                text = entry.get("text", "")
                if not verse_key or not text:
                    continue

                # verse_key is "surah:verse" e.g. "1:1"
                parts = verse_key.split(":")
                if len(parts) == 2:
                    verse_num = int(parts[1])
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
                logger.warning("Surah %d: 404 Not Found, skipping", surah_number)
                return {}
            else:
                logger.warning("HTTP %d for surah %d (attempt %d/%d)", e.code, surah_number, attempt + 1, retries)
                time.sleep(1)
        except (URLError, TimeoutError) as e:
            logger.warning("Network error for surah %d (attempt %d/%d): %s", surah_number, attempt + 1, retries, e)
            time.sleep(2)

    logger.error("Failed to fetch surah %d after %d retries", surah_number, retries)
    return {}


# ---------------------------------------------------------------------------
# Database Ingestion
# ---------------------------------------------------------------------------

async def ingest_tafsir(
    surah_number: int | None,
    space_name: str,
    skip_embed: bool,
    db_url: str,
    batch_size: int,
) -> None:
    from mizan.infrastructure.persistence.database import init_db, close_db, get_session_context
    from mizan.infrastructure.persistence.models import (
        LibrarySpaceModel,
        TextSourceModel,
        TextChunkModel,
    )
    from mizan.domain.enums.library_enums import IndexingStatus, SourceType
    from sqlalchemy import select, func

    await init_db()

    try:
        async with get_session_context() as session:
            # 1. Find or create library space
            result = await session.execute(
                select(LibrarySpaceModel).where(LibrarySpaceModel.name == space_name)
            )
            space = result.scalar_one_or_none()
            if space is None:
                space = LibrarySpaceModel(
                    id=uuid4(),
                    name=space_name,
                    description="Mizan default library for Tafsir and Hadith texts",
                    created_at=datetime.utcnow(),
                )
                session.add(space)
                await session.flush()
                logger.info("Created library space: %s (%s)", space.name, space.id)
            else:
                logger.info("Using existing library space: %s (%s)", space.name, space.id)

            # 2. Find or create text source for Ibn Kathir
            source_title_ar = "تفسير ابن كثير"
            result = await session.execute(
                select(TextSourceModel).where(
                    TextSourceModel.library_space_id == space.id,
                    TextSourceModel.title_arabic == source_title_ar,
                )
            )
            source = result.scalar_one_or_none()

            if source is None:
                source = TextSourceModel(
                    id=uuid4(),
                    library_space_id=space.id,
                    source_type=SourceType.TAFSIR.value,
                    title_arabic=source_title_ar,
                    title_turkish="İbn Kesir Tefsiri",
                    title_english="Tafsir Ibn Kathir",
                    author="ابن كثير (إسماعيل بن عمر)",
                    status=IndexingStatus.PENDING.value,
                    total_chunks=0,
                    indexed_chunks=0,
                    embedding_model=None,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(source)
                await session.flush()
                logger.info("Created text source: %s (%s)", source.title_english, source.id)
            else:
                logger.info("Using existing text source: %s (%s)", source.title_english, source.id)
                # Check if already has chunks
                chunk_count_result = await session.execute(
                    select(func.count()).select_from(TextChunkModel).where(
                        TextChunkModel.text_source_id == source.id
                    )
                )
                existing_chunks = chunk_count_result.scalar_one()
                if existing_chunks > 0:
                    logger.info("Source already has %d chunks. Skipping ingestion (use --force to re-ingest).", existing_chunks)
                    if not skip_embed:
                        await _embed_chunks(session, source.id, batch_size)
                    return

            # 3. Mark as indexing
            source.status = IndexingStatus.INDEXING.value
            source.updated_at = datetime.utcnow()
            await session.flush()

            # 4. Fetch and chunk tafsir data
            surahs_to_process = [surah_number] if surah_number else list(range(1, 115))
            total_chunks = 0
            chunk_index = 0

            for s_num in surahs_to_process:
                logger.info("Fetching Tafsir for Surah %d/%d...", s_num, surahs_to_process[-1])
                tafsir_data = fetch_tafsir_for_chapter(s_num)

                if not tafsir_data:
                    logger.warning("No tafsir data for Surah %d", s_num)
                    continue

                verse_count = SURAH_VERSE_COUNTS.get(s_num, 0)

                for v_num in range(1, verse_count + 1):
                    text = tafsir_data.get(v_num)
                    if not text or len(text.strip()) < 10:
                        continue

                    # For long tafsir entries, split into ~300 word chunks
                    words = text.split()
                    if len(words) <= 350:
                        # Single chunk for this verse's tafsir
                        chunk = TextChunkModel(
                            id=uuid4(),
                            text_source_id=source.id,
                            chunk_index=chunk_index,
                            content=text,
                            reference=f"Ibn Kathir {s_num}:{v_num}",
                            embedding=None,
                            metadata_={
                                "surah_number": s_num,
                                "verse_number": v_num,
                                "source": "ibn_kathir",
                                "word_count": len(words),
                            },
                            created_at=datetime.utcnow(),
                        )
                        session.add(chunk)
                        chunk_index += 1
                    else:
                        # Split long entries into ~300 word segments
                        for seg_start in range(0, len(words), 280):
                            seg_words = words[seg_start:seg_start + 300]
                            seg_text = " ".join(seg_words)
                            part_num = seg_start // 280 + 1

                            chunk = TextChunkModel(
                                id=uuid4(),
                                text_source_id=source.id,
                                chunk_index=chunk_index,
                                content=seg_text,
                                reference=f"Ibn Kathir {s_num}:{v_num} pt.{part_num}",
                                embedding=None,
                                metadata_={
                                    "surah_number": s_num,
                                    "verse_number": v_num,
                                    "part": part_num,
                                    "source": "ibn_kathir",
                                    "word_count": len(seg_words),
                                },
                                created_at=datetime.utcnow(),
                            )
                            session.add(chunk)
                            chunk_index += 1

                total_chunks = chunk_index

                # Flush every 10 surahs to avoid huge memory usage
                if s_num % 10 == 0:
                    await session.flush()
                    logger.info("  Flushed: %d chunks so far", total_chunks)

                # Rate limiting — be respectful to quran.com API
                time.sleep(0.5)

            await session.flush()

            # 5. Update source metadata
            source.total_chunks = total_chunks
            source.status = IndexingStatus.INDEXED.value if skip_embed else IndexingStatus.INDEXING.value
            source.updated_at = datetime.utcnow()
            await session.flush()

            logger.info("Ingested %d tafsir chunks for %d surahs", total_chunks, len(surahs_to_process))

            # 6. Generate embeddings
            if not skip_embed and total_chunks > 0:
                await _embed_chunks(session, source.id, batch_size)

                source.status = IndexingStatus.INDEXED.value
                source.indexed_chunks = total_chunks
                source.embedding_model = "intfloat/multilingual-e5-base"
                source.updated_at = datetime.utcnow()
                await session.flush()

            logger.info("Done! Tafsir Ibn Kathir fully ingested and indexed.")

    finally:
        await close_db()


async def _embed_chunks(session, source_id, batch_size: int) -> None:
    """Generate embeddings for all un-embedded chunks of a source."""
    from mizan.infrastructure.persistence.models import TextChunkModel
    from mizan.infrastructure.embeddings.sentence_transformer_service import (
        SentenceTransformerEmbeddingService,
    )
    from sqlalchemy import select, update

    logger.info("Generating embeddings (this may take a while on CPU)...")

    embedding_service = SentenceTransformerEmbeddingService(
        model_name="intfloat/multilingual-e5-base"
    )

    # Fetch all chunks without embeddings
    result = await session.execute(
        select(TextChunkModel)
        .where(
            TextChunkModel.text_source_id == source_id,
            TextChunkModel.embedding.is_(None),
        )
        .order_by(TextChunkModel.chunk_index)
    )
    chunks = list(result.scalars().all())

    if not chunks:
        logger.info("All chunks already have embeddings.")
        return

    logger.info("Embedding %d chunks in batches of %d...", len(chunks), batch_size)

    embedded = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [PASSAGE_PREFIX + c.content for c in batch]
        embeddings = await embedding_service.embed_batch(texts)

        for chunk, emb in zip(batch, embeddings):
            await session.execute(
                update(TextChunkModel)
                .where(TextChunkModel.id == chunk.id)
                .values(embedding=emb)
            )

        embedded += len(batch)
        await session.flush()
        logger.info("  Embedded %d/%d chunks", embedded, len(chunks))

    logger.info("Embedding complete: %d chunks embedded.", embedded)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest Tafsir Ibn Kathir into Mizan library system"
    )
    parser.add_argument(
        "--surah", type=int, default=None,
        help="Surah number to ingest (default: all 114 surahs)"
    )
    parser.add_argument(
        "--space", default="Mizan Kütüphanesi",
        help="Library space name (default: 'Mizan Kütüphanesi')"
    )
    parser.add_argument(
        "--skip-embed", action="store_true",
        help="Skip embedding generation (just ingest text)"
    )
    parser.add_argument(
        "--batch-size", type=int, default=32,
        help="Embedding batch size (default: 32)"
    )
    parser.add_argument(
        "--db-url", default=None,
        help="PostgreSQL async URL (default: $DATABASE_URL or local)"
    )
    args = parser.parse_args()

    import os
    db_url = args.db_url or os.environ.get("DATABASE_URL", DEFAULT_DB_URL)
    # Ensure async driver
    if "asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    asyncio.run(
        ingest_tafsir(
            surah_number=args.surah,
            space_name=args.space,
            skip_embed=args.skip_embed,
            db_url=db_url,
            batch_size=args.batch_size,
        )
    )


if __name__ == "__main__":
    main()
