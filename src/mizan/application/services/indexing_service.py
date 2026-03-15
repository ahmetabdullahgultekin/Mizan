"""
Indexing Service - chunks text sources and generates embeddings.

For the multilingual-e5 family of models, the recommended prefix pattern is:
- Passages (documents): 'passage: <text>'
- Queries (search input): 'query: <text>'

This improves retrieval quality significantly for Arabic and multilingual text.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

import structlog

from mizan.domain.entities.library import TextChunk, VerseEmbedding
from mizan.domain.enums.library_enums import IndexingStatus, SourceType
from mizan.domain.repositories.interfaces import IQuranRepository
from mizan.domain.repositories.library_interfaces import (
    ITextChunkRepository,
    ITextSourceRepository,
    IVerseEmbeddingRepository,
)
from mizan.domain.services.embedding_service import IEmbeddingService
from mizan.infrastructure.chunking.chunking_strategies import (
    ParagraphChunker,
    RawChunk,
    SlidingWindowChunker,
)

logger = structlog.get_logger(__name__)

# Prefix for e5-style models (improves retrieval quality)
PASSAGE_PREFIX = "passage: "


class IndexingService:
    """
    Orchestrates the chunking and embedding pipeline for Islamic text sources.

    Workflow:
    1. Receive raw text content for a TextSource
    2. Apply appropriate chunking strategy based on source type
    3. Persist chunks to database
    4. Generate embeddings in batches
    5. Update embeddings in database
    6. Update source status to INDEXED
    """

    def __init__(
        self,
        source_repo: ITextSourceRepository,
        chunk_repo: ITextChunkRepository,
        embedding_service: IEmbeddingService,
        batch_size: int = 32,
    ) -> None:
        self._sources = source_repo
        self._chunks = chunk_repo
        self._embedder = embedding_service
        self._batch_size = batch_size

    async def index_text_source(
        self,
        source_id: UUID,
        content: str,
        source_type: SourceType,
    ) -> int:
        """
        Index a text source: chunk it, embed all chunks, store results.

        Args:
            source_id: The TextSource to index
            content: Raw text content
            source_type: Determines which chunking strategy to use

        Returns:
            Number of chunks indexed
        """
        # Idempotency guard — prevent concurrent duplicate indexing runs
        existing = await self._sources.get_by_id(source_id)
        if existing is not None and existing.status == IndexingStatus.INDEXING:
            logger.warning(
                "indexing_already_in_progress",
                source_id=str(source_id),
            )
            return 0

        # Mark as indexing
        await self._sources.update_status(
            source_id,
            status=IndexingStatus.INDEXING,
            embedding_model=self._embedder.model_name,
        )

        try:
            # 1. Chunk the text
            raw_chunks = self._chunk_text(content, source_type)

            # 2. Persist chunks (without embeddings)
            domain_chunks = [
                TextChunk.create(
                    text_source_id=source_id,
                    chunk_index=rc.chunk_index,
                    content=rc.content,
                    reference=rc.reference,
                    metadata=rc.metadata,
                )
                for rc in raw_chunks
            ]
            await self._chunks.create_batch(domain_chunks)

            # Update total_chunks count
            await self._sources.update_status(
                source_id,
                status=IndexingStatus.INDEXING,
                total_chunks=len(domain_chunks),
                indexed_chunks=0,
            )

            # 3. Generate and store embeddings in batches
            indexed = 0
            for i in range(0, len(domain_chunks), self._batch_size):
                batch = domain_chunks[i : i + self._batch_size]
                texts = [PASSAGE_PREFIX + c.content for c in batch]
                embeddings = await self._embedder.embed_batch(texts)

                updates = [
                    (chunk.id, emb)
                    for chunk, emb in zip(batch, embeddings, strict=True)
                ]
                await self._chunks.update_embeddings_batch(updates)

                indexed += len(batch)
                await self._sources.update_status(
                    source_id,
                    status=IndexingStatus.INDEXING,
                    indexed_chunks=indexed,
                )
                logger.info(
                    "indexed_chunks",
                    indexed=indexed,
                    total=len(domain_chunks),
                    source_id=str(source_id),
                )

            # 4. Mark as fully indexed
            await self._sources.update_status(
                source_id,
                status=IndexingStatus.INDEXED,
                indexed_chunks=indexed,
                total_chunks=len(domain_chunks),
                embedding_model=self._embedder.model_name,
            )

            return indexed

        except Exception:
            logger.exception("indexing_failed", source_id=str(source_id))
            await self._sources.update_status(
                source_id, status=IndexingStatus.FAILED
            )
            raise

    def _chunk_text(self, content: str, source_type: SourceType) -> list[RawChunk]:
        """Select and apply the appropriate chunking strategy."""
        if source_type == SourceType.TAFSIR:
            return ParagraphChunker(max_words=300).chunk(content)
        elif source_type == SourceType.HADITH:
            return ParagraphChunker(max_words=200).chunk(content)
        else:
            return SlidingWindowChunker(window_size=200, overlap=50).chunk(content)


class QuranEmbeddingIndexer:
    """
    Specialized indexer for embedding the existing Quran verses.

    Uses the VerseChunker (1 verse = 1 chunk) and stores results
    in the verse_embeddings table for verse similarity search.
    """

    def __init__(
        self,
        quran_repo: IQuranRepository,
        verse_emb_repo: IVerseEmbeddingRepository,
        embedding_service: IEmbeddingService,
        batch_size: int = 32,
    ) -> None:
        self._quran = quran_repo
        self._verse_embs = verse_emb_repo
        self._embedder = embedding_service
        self._batch_size = batch_size

    async def embed_all_verses(
        self,
        surah_number: int | None = None,
        skip_existing: bool = False,
    ) -> int:
        """
        Generate and store embeddings for all Quran verses (or one surah).

        Args:
            surah_number: If provided, only embed verses of this surah
            skip_existing: If True, skip verses that already have embeddings
                           (enables checkpoint/resume for interrupted runs)

        Returns:
            Number of verses newly embedded
        """
        # Stream verses for memory efficiency (6236 verses total)
        verses = []
        async for verse in self._quran.stream_verses(surah_number=surah_number):
            verses.append(verse)

        # Checkpoint/resume: filter out already-embedded verses
        if skip_existing:
            from mizan.infrastructure.persistence.library_repositories import (
                PostgresVerseEmbeddingRepository,
            )
            if isinstance(self._verse_embs, PostgresVerseEmbeddingRepository):
                existing_keys = await self._verse_embs.get_embedded_verse_keys(
                    model_name=self._embedder.model_name
                )
                before_count = len(verses)
                verses = [
                    v for v in verses
                    if (v.location.surah_number, v.location.verse_number) not in existing_keys
                ]
                skipped = before_count - len(verses)
                if skipped:
                    logger.info("skipping_embedded_verses", skipped=skipped)

        logger.info("embedding_verses_start", verse_count=len(verses))

        embedded = 0
        for i in range(0, len(verses), self._batch_size):
            batch = verses[i : i + self._batch_size]
            texts = [PASSAGE_PREFIX + v.text_uthmani for v in batch]
            embeddings = await self._embedder.embed_batch(texts)

            verse_embeddings = [
                VerseEmbedding(
                    id=uuid4(),
                    verse_id=v.id,
                    surah_number=v.location.surah_number,
                    verse_number=v.location.verse_number,
                    embedding=emb,
                    model_name=self._embedder.model_name,
                    created_at=datetime.utcnow(),
                )
                for v, emb in zip(batch, embeddings, strict=True)
            ]

            await self._verse_embs.upsert_batch(verse_embeddings)
            embedded += len(batch)
            logger.info("embedded_verses_progress", embedded=embedded, total=len(verses))

        return embedded
