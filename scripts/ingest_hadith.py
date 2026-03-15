#!/usr/bin/env python3
"""
Hadith Collection Ingestion Script

Downloads Hadith collections from the fawazahmed0/hadith-api (via jsDelivr CDN)
and inserts them into the Mizan library system (library_spaces → text_sources → text_chunks).

After ingestion, generates semantic embeddings for all chunks so they appear
in the /search/semantic endpoint results.

Usage:
    # Ingest all default collections (Bukhari, Muslim, Abu Dawud, Tirmidhi, Nasai, Ibn Majah)
    python scripts/ingest_hadith.py

    # Ingest only Sahih al-Bukhari
    python scripts/ingest_hadith.py --collection bukhari

    # List available collections
    python scripts/ingest_hadith.py --list

    # Skip embedding generation (just ingest text)
    python scripts/ingest_hadith.py --skip-embed

Environment variables:
    DATABASE_URL  PostgreSQL connection string (default: postgresql+asyncpg://mizan:mizan@localhost:5432/mizan)

Prerequisites:
    1. Run 'alembic upgrade head' to apply all migrations
    2. Internet access for jsDelivr CDN

Data Source:
    fawazahmed0/hadith-api — https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/
    Arabic editions: ara-{collection}.json
"""

import argparse
import asyncio
import json
import logging
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

CDN_BASE = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions"

# Collection metadata: (slug, arabic_title, turkish_title, english_title, author_arabic)
HADITH_COLLECTIONS = {
    "bukhari": (
        "ara-bukhari",
        "صحيح البخاري",
        "Sahih-i Buhari",
        "Sahih al-Bukhari",
        "محمد بن إسماعيل البخاري",
    ),
    "muslim": (
        "ara-muslim",
        "صحيح مسلم",
        "Sahih-i Müslim",
        "Sahih Muslim",
        "مسلم بن الحجاج النيسابوري",
    ),
    "abudawud": (
        "ara-abudawud",
        "سنن أبي داود",
        "Sünen-i Ebu Davud",
        "Sunan Abu Dawud",
        "أبو داود السجستاني",
    ),
    "tirmidhi": (
        "ara-tirmidhi",
        "سنن الترمذي",
        "Sünen-i Tirmizi",
        "Jami' at-Tirmidhi",
        "محمد بن عيسى الترمذي",
    ),
    "nasai": (
        "ara-nasai",
        "سنن النسائي",
        "Sünen-i Nesai",
        "Sunan an-Nasa'i",
        "أحمد بن شعيب النسائي",
    ),
    "ibnmajah": (
        "ara-ibnmajah",
        "سنن ابن ماجه",
        "Sünen-i İbn Mace",
        "Sunan Ibn Majah",
        "محمد بن يزيد ابن ماجه",
    ),
}

# Default: the Kutub al-Sittah (Six Major Collections)
DEFAULT_COLLECTIONS = ["bukhari", "muslim", "abudawud", "tirmidhi", "nasai", "ibnmajah"]

DEFAULT_DB_URL = "postgresql+asyncpg://mizan:mizan@localhost:5432/mizan"
PASSAGE_PREFIX = "passage: "


# ---------------------------------------------------------------------------
# API Fetching
# ---------------------------------------------------------------------------

def fetch_hadith_collection(edition_slug: str, retries: int = 3) -> list[dict]:
    """
    Download a full hadith collection JSON from jsDelivr CDN.

    Returns a list of hadith entries, each with keys like:
        hadithnumber, text, grades, reference, etc.
    """
    url = f"{CDN_BASE}/{edition_slug}.json"
    headers = {"User-Agent": "Mizan-Ingest/1.0", "Accept": "application/json"}

    for attempt in range(retries):
        try:
            logger.info("Downloading %s ...", url)
            req = Request(url, headers=headers)
            with urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            # The API returns {"metadata": {...}, "hadiths": [...]}
            hadiths = data.get("hadiths", [])
            logger.info("  Downloaded %d hadiths", len(hadiths))
            return hadiths

        except HTTPError as e:
            logger.warning("HTTP %d for %s (attempt %d/%d)", e.code, edition_slug, attempt + 1, retries)
            time.sleep(2 ** attempt)
        except (URLError, TimeoutError) as e:
            logger.warning("Network error for %s (attempt %d/%d): %s", edition_slug, attempt + 1, retries, e)
            time.sleep(2)

    logger.error("Failed to fetch %s after %d retries", edition_slug, retries)
    return []


# ---------------------------------------------------------------------------
# Database Ingestion
# ---------------------------------------------------------------------------

async def ingest_hadith(
    collections: list[str],
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

            # 2. Process each collection
            for collection_key in collections:
                if collection_key not in HADITH_COLLECTIONS:
                    logger.error("Unknown collection: %s (use --list to see options)", collection_key)
                    continue

                edition_slug, title_ar, title_tr, title_en, author = HADITH_COLLECTIONS[collection_key]

                logger.info("=" * 60)
                logger.info("Processing: %s (%s)", title_en, collection_key)
                logger.info("=" * 60)

                # Find or create text source
                result = await session.execute(
                    select(TextSourceModel).where(
                        TextSourceModel.library_space_id == space.id,
                        TextSourceModel.title_arabic == title_ar,
                    )
                )
                source = result.scalar_one_or_none()

                if source is None:
                    source = TextSourceModel(
                        id=uuid4(),
                        library_space_id=space.id,
                        source_type=SourceType.HADITH.value,
                        title_arabic=title_ar,
                        title_turkish=title_tr,
                        title_english=title_en,
                        author=author,
                        status=IndexingStatus.PENDING.value,
                        total_chunks=0,
                        indexed_chunks=0,
                        embedding_model=None,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    session.add(source)
                    await session.flush()
                    logger.info("Created text source: %s (%s)", title_en, source.id)
                else:
                    logger.info("Text source exists: %s (%s)", title_en, source.id)
                    # Check existing chunks
                    chunk_count_result = await session.execute(
                        select(func.count()).select_from(TextChunkModel).where(
                            TextChunkModel.text_source_id == source.id
                        )
                    )
                    existing_chunks = chunk_count_result.scalar_one()
                    if existing_chunks > 0:
                        logger.info("  Already has %d chunks. Skipping text ingestion.", existing_chunks)
                        if not skip_embed:
                            await _embed_chunks(session, source.id, batch_size)
                        continue

                # Mark as indexing
                source.status = IndexingStatus.INDEXING.value
                source.updated_at = datetime.utcnow()
                await session.flush()

                # Fetch from CDN
                hadiths = fetch_hadith_collection(edition_slug)
                if not hadiths:
                    source.status = IndexingStatus.FAILED.value
                    source.updated_at = datetime.utcnow()
                    await session.flush()
                    continue

                # Insert chunks — one hadith = one chunk (hadiths are natural units)
                chunk_index = 0
                skipped = 0

                for hadith in hadiths:
                    text = hadith.get("text", "").strip()
                    hadith_num = hadith.get("hadithnumber", chunk_index + 1)

                    # Skip empty or very short entries
                    if not text or len(text) < 20:
                        skipped += 1
                        continue

                    # Build reference string
                    reference = f"{title_en} #{hadith_num}"

                    # Build metadata
                    metadata = {
                        "hadith_number": hadith_num,
                        "collection": collection_key,
                        "word_count": len(text.split()),
                    }

                    # Include grades if present
                    grades = hadith.get("grades", [])
                    if grades:
                        # Take the first grade as primary
                        metadata["grade"] = grades[0].get("grade", "") if isinstance(grades[0], dict) else str(grades[0])

                    # For very long hadiths (>350 words), split into segments
                    words = text.split()
                    if len(words) <= 350:
                        chunk = TextChunkModel(
                            id=uuid4(),
                            text_source_id=source.id,
                            chunk_index=chunk_index,
                            content=text,
                            reference=reference,
                            embedding=None,
                            metadata_=metadata,
                            created_at=datetime.utcnow(),
                        )
                        session.add(chunk)
                        chunk_index += 1
                    else:
                        # Split long hadiths into ~250 word segments
                        for seg_start in range(0, len(words), 230):
                            seg_words = words[seg_start:seg_start + 250]
                            seg_text = " ".join(seg_words)
                            part_num = seg_start // 230 + 1

                            chunk_meta = {**metadata, "part": part_num}
                            chunk = TextChunkModel(
                                id=uuid4(),
                                text_source_id=source.id,
                                chunk_index=chunk_index,
                                content=seg_text,
                                reference=f"{reference} pt.{part_num}",
                                embedding=None,
                                metadata_=chunk_meta,
                                created_at=datetime.utcnow(),
                            )
                            session.add(chunk)
                            chunk_index += 1

                    # Flush every 500 hadiths to control memory
                    if chunk_index % 500 == 0 and chunk_index > 0:
                        await session.flush()
                        logger.info("  Flushed: %d chunks", chunk_index)

                await session.flush()
                total_chunks = chunk_index
                logger.info(
                    "Ingested %d chunks from %s (%d skipped)",
                    total_chunks, title_en, skipped,
                )

                # Update source metadata
                source.total_chunks = total_chunks
                source.updated_at = datetime.utcnow()

                if skip_embed:
                    source.status = IndexingStatus.INDEXED.value
                    await session.flush()
                else:
                    # Generate embeddings
                    await session.flush()
                    await _embed_chunks(session, source.id, batch_size)
                    source.status = IndexingStatus.INDEXED.value
                    source.indexed_chunks = total_chunks
                    source.embedding_model = "intfloat/multilingual-e5-base"
                    source.updated_at = datetime.utcnow()
                    await session.flush()

                logger.info("✓ %s fully ingested and indexed.", title_en)

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

        if embedded % 200 == 0 or embedded == len(chunks):
            logger.info("  Embedded %d/%d chunks", embedded, len(chunks))

    logger.info("Embedding complete: %d chunks embedded.", embedded)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest Hadith collections into Mizan library system"
    )
    parser.add_argument(
        "--collection", type=str, default=None,
        help="Single collection to ingest (e.g., 'bukhari'). Default: all 6 major collections."
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List available hadith collections and exit"
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

    if args.list:
        print("\nAvailable Hadith collections:\n")
        print(f"  {'Key':<12} {'English Title':<25} {'Arabic Title'}")
        print(f"  {'-'*12} {'-'*25} {'-'*30}")
        for key, (_, title_ar, _, title_en, _) in HADITH_COLLECTIONS.items():
            print(f"  {key:<12} {title_en:<25} {title_ar}")
        print(f"\nDefault (all 6): {', '.join(DEFAULT_COLLECTIONS)}")
        return

    import os
    db_url = args.db_url or os.environ.get("DATABASE_URL", DEFAULT_DB_URL)
    if "asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    collections = [args.collection] if args.collection else DEFAULT_COLLECTIONS

    asyncio.run(
        ingest_hadith(
            collections=collections,
            space_name=args.space,
            skip_embed=args.skip_embed,
            db_url=db_url,
            batch_size=args.batch_size,
        )
    )


if __name__ == "__main__":
    main()
