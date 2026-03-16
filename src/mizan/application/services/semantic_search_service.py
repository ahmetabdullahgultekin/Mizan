"""
Semantic Search Service - searches across Islamic texts by meaning.

Uses cosine similarity between the query embedding and stored chunk/verse
embeddings to find semantically related passages.
"""

from __future__ import annotations

from uuid import UUID

from mizan.domain.entities.library import SemanticSearchResult
from mizan.domain.enums.library_enums import SourceType
from mizan.domain.repositories.library_interfaces import (
    ITextChunkRepository,
    IVerseEmbeddingRepository,
)
from mizan.domain.services.embedding_service import IEmbeddingService

# Prefix for e5-style models: queries use 'query: ' prefix
QUERY_PREFIX = "query: "


class SemanticSearchService:
    """
    Performs semantic search across library chunks and Quran verse embeddings.

    The search pipeline:
    1. Embed the user's query with 'query: ' prefix (for e5 models)
    2. Execute pgvector cosine similarity search against stored embeddings
    3. Return ranked results with similarity scores
    """

    def __init__(
        self,
        chunk_repo: ITextChunkRepository,
        verse_emb_repo: IVerseEmbeddingRepository,
        embedding_service: IEmbeddingService,
    ) -> None:
        self._chunks = chunk_repo
        self._verse_embs = verse_emb_repo
        self._embedder = embedding_service

    async def search(
        self,
        query: str,
        library_space_id: UUID | None = None,
        source_types: list[SourceType] | None = None,
        limit: int = 10,
        min_similarity: float = 0.5,
    ) -> list[SemanticSearchResult]:
        """
        Search across Islamic texts by semantic similarity.

        When source_types includes QURAN (or no filter is specified), this
        searches the pre-computed verse_embeddings table (6,236 Quran verses)
        in addition to any library text_chunks, merging results by similarity.

        Args:
            query: Natural language query (any language — Arabic, Turkish, English)
            library_space_id: Restrict search to a specific library space
            source_types: Filter by source types (QURAN, TAFSIR, etc.)
            limit: Maximum number of results (default 10, max 100)
            min_similarity: Minimum cosine similarity threshold (0.0–1.0)

        Returns:
            Ranked list of matching passages (highest similarity first)
        """
        limit = min(limit, 100)

        # Embed the query
        query_embedding = await self._embedder.embed_text(QUERY_PREFIX + query)

        # Determine which sources to search
        search_quran_verses = (
            source_types is None  # No filter → search everything
            or SourceType.QURAN in source_types
        )
        # Filter out QURAN from library search (verse_embeddings handles it)
        non_quran_types: list[SourceType] | None = (
            [st for st in source_types if st != SourceType.QURAN]
            if source_types is not None
            else None
        )
        search_library = source_types is None or bool(non_quran_types)

        all_results: list[SemanticSearchResult] = []

        # 1. Search verse_embeddings for Quran verses
        if search_quran_verses:
            verse_results = await self._verse_embs.search_by_text(
                query_embedding=query_embedding,
                limit=limit,
                min_similarity=min_similarity,
            )
            all_results.extend(verse_results)

        # 2. Search library text_chunks (for non-Quran sources, or all if no filter)
        if search_library:
            chunk_results = await self._chunks.semantic_search(
                query_embedding=query_embedding,
                library_space_id=library_space_id,
                source_types=non_quran_types,
                limit=limit,
                min_similarity=min_similarity,
            )
            all_results.extend(chunk_results)

        # Sort combined results by similarity (highest first) and trim to limit
        all_results.sort(key=lambda r: r.similarity_score, reverse=True)
        return all_results[:limit]

    async def find_similar_verses(
        self,
        surah_number: int,
        verse_number: int,
        limit: int = 10,
    ) -> list[tuple[int, int, float]]:
        """
        Find Quran verses most similar to a given verse.

        Requires that verse embeddings have been pre-computed
        (run scripts/embed_quran.py first).

        Args:
            surah_number: Reference verse's surah number
            verse_number: Reference verse's verse number
            limit: Maximum number of similar verses to return

        Returns:
            List of (surah_number, verse_number, similarity_score) tuples,
            sorted by similarity descending.

        Raises:
            ValueError: If the reference verse has no embedding yet.
        """
        # Look up the reference verse's embedding
        verse_emb = await self._verse_embs.get_by_verse(
            surah_number=surah_number,
            verse_number=verse_number,
        )
        if verse_emb is None:
            raise ValueError(
                f"No embedding found for verse {surah_number}:{verse_number}. "
                "Run scripts/embed_quran.py to generate verse embeddings."
            )

        return await self._verse_embs.find_similar_verses(
            query_embedding=verse_emb.embedding,
            limit=limit,
            exclude_surah=surah_number,
            exclude_verse=verse_number,
        )

    async def search_similar_to_verse(
        self,
        surah_number: int,
        verse_number: int,
        library_space_id: UUID | None = None,
        source_types: list[SourceType] | None = None,
        limit: int = 10,
    ) -> list[SemanticSearchResult]:
        """
        Search the library for content semantically similar to a verse.

        Useful for finding tafsir or hadith passages that discuss the
        same topic as a given Quranic verse.

        Args:
            surah_number: Reference verse surah
            verse_number: Reference verse number
            library_space_id: Optional library filter
            source_types: Optional source type filter
            limit: Maximum results

        Returns:
            Ranked list of matching library chunks
        """
        verse_emb = await self._verse_embs.get_by_verse(
            surah_number=surah_number,
            verse_number=verse_number,
        )
        if verse_emb is None:
            raise ValueError(f"No embedding found for verse {surah_number}:{verse_number}.")

        return await self._chunks.semantic_search(
            query_embedding=verse_emb.embedding,
            library_space_id=library_space_id,
            source_types=source_types,
            limit=limit,
        )
