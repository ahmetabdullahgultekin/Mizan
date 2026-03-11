#!/usr/bin/env python3
"""
Bulk Quran verse embedding script.

Generates semantic embeddings for all 6,236 Quran verses and stores them
in the verse_embeddings table for use with the /search/verses/{s}/{v}/similar
endpoint.

Usage:
    # Embed all verses (recommended first run)
    python scripts/embed_quran.py

    # Embed only a specific surah (for testing)
    python scripts/embed_quran.py --surah 1

    # Use Gemini API instead of local model
    python scripts/embed_quran.py --provider gemini --api-key YOUR_KEY

    # Override batch size (default: 32)
    python scripts/embed_quran.py --batch-size 64

Prerequisites:
    1. Run 'alembic upgrade head' to apply migrations
    2. Ensure the verses table is populated (run ingest scripts first)
    3. For local model: pip install sentence-transformers
       (downloads ~280MB model on first run)
    4. For Gemini: pip install google-generativeai
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


async def run(
    surah_number: int | None,
    provider: str,
    embedding_model: str,
    api_key: str,
    batch_size: int,
) -> None:
    from mizan.application.services.indexing_service import QuranEmbeddingIndexer
    from mizan.infrastructure.config import get_settings
    from mizan.infrastructure.persistence.database import (
        close_db,
        get_session_context,
        init_db,
    )
    from mizan.infrastructure.persistence.library_repositories import (
        PostgresVerseEmbeddingRepository,
    )
    from mizan.infrastructure.persistence.repositories import PostgresQuranRepository

    # Select embedding service
    if provider == "gemini":
        from mizan.infrastructure.embeddings.gemini_embedding_service import (
            GeminiEmbeddingService,
        )
        embedding_service = GeminiEmbeddingService(api_key=api_key, model_name=embedding_model)
        logger.info("Using Gemini API: %s", embedding_model)
    else:
        from mizan.infrastructure.embeddings.sentence_transformer_service import (
            SentenceTransformerEmbeddingService,
        )
        embedding_service = SentenceTransformerEmbeddingService(model_name=embedding_model)
        logger.info("Using local model: %s (will download if not cached)", embedding_model)

    # Initialize DB
    await init_db()

    try:
        async with get_session_context() as session:
            indexer = QuranEmbeddingIndexer(
                quran_repo=PostgresQuranRepository(session),
                verse_emb_repo=PostgresVerseEmbeddingRepository(session),
                embedding_service=embedding_service,
                batch_size=batch_size,
            )

            if surah_number:
                logger.info("Embedding Surah %d...", surah_number)
            else:
                logger.info(
                    "Embedding all 6,236 Quran verses. "
                    "This takes ~5 min on CPU, ~30 sec on GPU."
                )

            count = await indexer.embed_all_verses(surah_number=surah_number)
            logger.info("Done! Embedded %d verses.", count)

    finally:
        await close_db()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate semantic embeddings for Quran verses"
    )
    parser.add_argument(
        "--surah",
        type=int,
        default=None,
        help="Surah number to embed (default: all surahs)",
    )
    parser.add_argument(
        "--provider",
        choices=["local", "gemini"],
        default="local",
        help="Embedding provider (default: local)",
    )
    parser.add_argument(
        "--model",
        default="intfloat/multilingual-e5-base",
        help="Model name (default: intfloat/multilingual-e5-base)",
    )
    parser.add_argument(
        "--api-key",
        default="",
        help="Gemini API key (required when --provider=gemini)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Embedding batch size (default: 32)",
    )

    args = parser.parse_args()

    if args.provider == "gemini" and not args.api_key:
        logger.error("--api-key is required when using --provider=gemini")
        sys.exit(1)

    asyncio.run(
        run(
            surah_number=args.surah,
            provider=args.provider,
            embedding_model=args.model,
            api_key=args.api_key,
            batch_size=args.batch_size,
        )
    )


if __name__ == "__main__":
    main()
