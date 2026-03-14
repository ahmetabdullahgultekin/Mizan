#!/usr/bin/env python3
"""
Batch library source ingestion script.

Adds text files (translations, Tafsir, Hadith, etc.) to the Islamic Knowledge
Library and triggers indexing (chunking + embedding generation) for semantic search.

Usage:
    # Add a single text file to a library space
    python scripts/ingest_library_source.py \\
        --space "Tafsir Collection" \\
        --type tafsir \\
        --title "Tafsir Ibn Kathir - Al-Fatiha" \\
        --author "Ibn Kathir" \\
        --file data/tafsir_ibn_kathir_fatiha.txt

    # Add all .txt files from a directory
    python scripts/ingest_library_source.py \\
        --space "Hadith Collection" \\
        --type hadith \\
        --dir data/hadith/

    # Use Gemini embeddings instead of local model
    python scripts/ingest_library_source.py \\
        --space "My Library" \\
        --type other \\
        --file data/notes.txt \\
        --provider gemini \\
        --api-key YOUR_KEY

Prerequisites:
    1. Run 'alembic upgrade head' to apply all migrations
    2. For local embeddings: pip install sentence-transformers
    3. For Gemini embeddings: pip install google-generativeai
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
    space_name: str,
    source_type_str: str,
    files: list[Path],
    title: str | None,
    author: str | None,
    provider: str,
    embedding_model: str,
    api_key: str,
    batch_size: int,
) -> None:
    from mizan.domain.enums.library_enums import SourceType
    from mizan.infrastructure.persistence.database import (
        close_db,
        get_session_context,
        init_db,
    )
    from mizan.infrastructure.persistence.library_repositories import (
        PostgresLibrarySpaceRepository,
        PostgresTextChunkRepository,
        PostgresTextSourceRepository,
    )
    from mizan.application.services.library_service import LibraryService
    from mizan.application.services.indexing_service import IndexingService

    # Map source type string to enum
    source_type_map = {
        "quran": SourceType.QURAN,
        "tafsir": SourceType.TAFSIR,
        "hadith": SourceType.HADITH,
        "other": SourceType.OTHER,
    }
    source_type = source_type_map[source_type_str]

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
            space_repo = PostgresLibrarySpaceRepository(session)
            source_repo = PostgresTextSourceRepository(session)
            chunk_repo = PostgresTextChunkRepository(session)

            library_svc = LibraryService(space_repo=space_repo, source_repo=source_repo)
            indexing_svc = IndexingService(
                source_repo=source_repo,
                chunk_repo=chunk_repo,
                embedding_service=embedding_service,
                batch_size=batch_size,
            )

            # Find or create the library space
            existing_spaces = await library_svc.list_spaces()
            space = next((s for s in existing_spaces if s.name == space_name), None)
            if space is None:
                space = await library_svc.create_space(name=space_name)
                logger.info("Created library space: %s (%s)", space.name, space.id)
            else:
                logger.info("Using existing space: %s (%s)", space.name, space.id)

            # Process each file
            total_chunks = 0
            for file_path in files:
                file_title = title or file_path.stem.replace("_", " ").title()

                logger.info("Processing: %s", file_path.name)

                # Read file content
                content = file_path.read_text(encoding="utf-8").strip()
                if not content:
                    logger.warning("Skipping empty file: %s", file_path)
                    continue

                word_count = len(content.split())
                logger.info("  Content: %d words", word_count)

                # Create text source
                source = await library_svc.add_source(
                    library_space_id=space.id,
                    source_type=source_type,
                    title_arabic=file_title,
                    author=author,
                )
                logger.info("  Created source: %s (%s)", source.title_arabic, source.id)

                # Index (chunk + embed)
                chunks_indexed = await indexing_svc.index_text_source(
                    source_id=source.id,
                    content=content,
                    source_type=source_type,
                )
                total_chunks += chunks_indexed
                logger.info("  Indexed: %d chunks", chunks_indexed)

            # Summary
            logger.info("=" * 60)
            logger.info("Ingestion complete!")
            logger.info("  Space: %s", space_name)
            logger.info("  Files processed: %d", len(files))
            logger.info("  Total chunks indexed: %d", total_chunks)
            logger.info("=" * 60)

    finally:
        await close_db()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest text files into the Islamic Knowledge Library"
    )
    parser.add_argument(
        "--space",
        required=True,
        help="Library space name (created if it doesn't exist)",
    )
    parser.add_argument(
        "--type",
        choices=["quran", "tafsir", "hadith", "other"],
        required=True,
        dest="source_type",
        help="Source type (determines chunking strategy)",
    )

    # File input (one of --file or --dir required)
    file_group = parser.add_mutually_exclusive_group(required=True)
    file_group.add_argument(
        "--file",
        type=Path,
        help="Path to a single text file to ingest",
    )
    file_group.add_argument(
        "--dir",
        type=Path,
        dest="directory",
        help="Directory of .txt files to ingest",
    )

    parser.add_argument(
        "--title",
        default=None,
        help="Title for the source (default: filename)",
    )
    parser.add_argument(
        "--author",
        default=None,
        help="Author name",
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

    # Validate inputs
    if args.provider == "gemini" and not args.api_key:
        logger.error("--api-key is required when using --provider=gemini")
        sys.exit(1)

    # Collect files
    if args.file:
        if not args.file.exists():
            logger.error("File not found: %s", args.file)
            sys.exit(1)
        files = [args.file]
    else:
        if not args.directory.is_dir():
            logger.error("Directory not found: %s", args.directory)
            sys.exit(1)
        files = sorted(args.directory.glob("*.txt"))
        if not files:
            logger.error("No .txt files found in %s", args.directory)
            sys.exit(1)
        logger.info("Found %d .txt files in %s", len(files), args.directory)

    asyncio.run(
        run(
            space_name=args.space,
            source_type_str=args.source_type,
            files=files,
            title=args.title,
            author=args.author,
            provider=args.provider,
            embedding_model=args.model,
            api_key=args.api_key,
            batch_size=args.batch_size,
        )
    )


if __name__ == "__main__":
    main()
