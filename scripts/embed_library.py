#!/usr/bin/env python3
"""
Batch embedding generator for all text_chunks without embeddings.

Processes all sources sequentially, commits every COMMIT_INTERVAL chunks
so progress is visible and recoverable. Uses all CPU cores via torch threading.

Usage:
    python scripts/embed_library.py                  # Embed all un-embedded chunks
    python scripts/embed_library.py --source-id X    # Embed specific source only
    python scripts/embed_library.py --dry-run         # Show what would be embedded
"""
import argparse
import asyncio
import logging
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Maximize CPU utilization
BATCH_SIZE = 64          # Larger batches = better throughput
COMMIT_INTERVAL = 256    # Commit every N chunks (visible progress)


async def embed_all(source_id: str | None = None, dry_run: bool = False):
    # Set torch threads to use all cores BEFORE importing model
    try:
        import torch
        cores = os.cpu_count() or 4
        torch.set_num_threads(cores)
        torch.set_num_interop_threads(max(1, cores // 2))
        log.info(f"PyTorch using {cores} threads")
    except ImportError:
        pass

    from mizan.infrastructure.persistence.database import init_db, close_db
    from mizan.infrastructure.persistence.models import TextChunkModel, TextSourceModel
    from mizan.infrastructure.embeddings.sentence_transformer_service import SentenceTransformerEmbeddingService
    from sqlalchemy import select, update, func, text
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from datetime import datetime

    await init_db()

    # Create a separate engine for embedding work with autocommit-friendly sessions
    db_url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://mizan:mizan@postgres:5432/mizan")
    engine = create_async_engine(db_url, pool_size=2)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    # Load model once
    log.info("Loading embedding model...")
    t0 = time.time()
    svc = SentenceTransformerEmbeddingService(model_name="intfloat/multilingual-e5-base")
    # Force model load
    await svc.embed_text("passage: warmup")
    log.info(f"Model loaded in {time.time() - t0:.1f}s")

    # Get sources to process
    async with Session() as session:
        q = select(TextSourceModel).order_by(TextSourceModel.created_at)
        if source_id:
            q = q.where(TextSourceModel.id == source_id)
        result = await session.execute(q)
        sources = list(result.scalars().all())

    total_embedded = 0
    total_start = time.time()

    for src in sources:
        # Count un-embedded chunks for this source
        async with Session() as session:
            count_q = select(func.count(TextChunkModel.id)).where(
                TextChunkModel.text_source_id == src.id,
                TextChunkModel.embedding.is_(None),
            )
            result = await session.execute(count_q)
            remaining = result.scalar_one()

        if remaining == 0:
            log.info(f"✓ {src.title_english} — already fully embedded, skipping")
            continue

        log.info(f"{'[DRY RUN] ' if dry_run else ''}Embedding {src.title_english}: {remaining} chunks")
        if dry_run:
            continue

        src_start = time.time()
        src_embedded = 0
        offset = 0

        while True:
            async with Session() as session:
                # Fetch next batch of un-embedded chunks
                result = await session.execute(
                    select(TextChunkModel.id, TextChunkModel.content)
                    .where(
                        TextChunkModel.text_source_id == src.id,
                        TextChunkModel.embedding.is_(None),
                    )
                    .order_by(TextChunkModel.chunk_index)
                    .limit(COMMIT_INTERVAL)
                )
                chunk_rows = list(result.fetchall())

                if not chunk_rows:
                    break

                # Process in sub-batches for model efficiency
                for i in range(0, len(chunk_rows), BATCH_SIZE):
                    sub = chunk_rows[i : i + BATCH_SIZE]
                    texts = ["passage: " + row.content for row in sub]

                    embeddings = await svc.embed_batch(texts)

                    for row, emb in zip(sub, embeddings):
                        await session.execute(
                            update(TextChunkModel)
                            .where(TextChunkModel.id == row.id)
                            .values(embedding=emb)
                        )

                    src_embedded += len(sub)
                    total_embedded += len(sub)

                # COMMIT after each COMMIT_INTERVAL block
                await session.commit()

                elapsed = time.time() - src_start
                rate = src_embedded / elapsed if elapsed > 0 else 0
                eta = (remaining - src_embedded) / rate if rate > 0 else 0
                log.info(
                    f"  {src_embedded}/{remaining} ({src_embedded * 100 // remaining}%) "
                    f"— {rate:.0f} chunks/s — ETA {eta:.0f}s"
                )

        # Update source metadata
        async with Session() as session:
            await session.execute(
                update(TextSourceModel)
                .where(TextSourceModel.id == src.id)
                .values(
                    indexed_chunks=src.total_chunks,
                    embedding_model="intfloat/multilingual-e5-base",
                    updated_at=datetime.utcnow(),
                )
            )
            await session.commit()

        elapsed = time.time() - src_start
        log.info(f"✓ {src.title_english} — {src_embedded} chunks in {elapsed:.0f}s ({src_embedded / elapsed:.0f}/s)")

    total_elapsed = time.time() - total_start
    log.info(f"\n{'='*60}")
    log.info(f"Done! {total_embedded} chunks embedded in {total_elapsed:.0f}s")
    log.info(f"Average: {total_embedded / total_elapsed:.0f} chunks/s")

    await engine.dispose()
    await close_db()


def main():
    parser = argparse.ArgumentParser(description="Embed all un-embedded text_chunks")
    parser.add_argument("--source-id", help="Only embed this source UUID")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    args = parser.parse_args()
    asyncio.run(embed_all(source_id=args.source_id, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
