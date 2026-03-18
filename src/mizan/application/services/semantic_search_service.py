"""
Semantic Search Service - searches across Islamic texts by meaning.

Uses cosine similarity between the query embedding and stored chunk/verse
embeddings to find semantically related passages. Also performs BM25-style
keyword search via PostgreSQL tsvector/GIN and fuses results with
Reciprocal Rank Fusion (RRF).
"""

from __future__ import annotations

import asyncio
from uuid import UUID

import structlog

from mizan.domain.entities.library import SemanticSearchResult
from mizan.domain.enums.library_enums import SourceType
from mizan.domain.repositories.library_interfaces import (
    ITextChunkRepository,
    IVerseEmbeddingRepository,
    IVerseTranslationRepository,
)
from mizan.domain.services.embedding_service import IEmbeddingService
from mizan.domain.services.reranking_service import IRerankerService

# Prefix for e5-style models: queries use 'query: ' prefix
QUERY_PREFIX = "query: "

logger = structlog.get_logger(__name__)


class SemanticSearchService:
    """
    Performs hybrid search across library chunks and Quran verse embeddings.

    The search pipeline:
    1. Embed the user's query with 'query: ' prefix (for e5 models)
    2. Execute pgvector cosine similarity search (vector path)
    3. Execute tsvector full-text keyword search (keyword path)
    4. Merge both result lists with Reciprocal Rank Fusion (RRF)
    5. Return ranked results with fused scores
    """

    def __init__(
        self,
        chunk_repo: ITextChunkRepository,
        verse_emb_repo: IVerseEmbeddingRepository,
        embedding_service: IEmbeddingService,
        reranker: IRerankerService | None = None,
        reranker_top_k: int = 30,
        verse_translation_repo: IVerseTranslationRepository | None = None,
    ) -> None:
        self._chunks = chunk_repo
        self._verse_embs = verse_emb_repo
        self._embedder = embedding_service
        self._reranker = reranker
        self._reranker_top_k = reranker_top_k
        self._verse_translations = verse_translation_repo

    async def search(
        self,
        query: str,
        library_space_id: UUID | None = None,
        source_types: list[SourceType] | None = None,
        limit: int = 10,
        min_similarity: float = 0.5,
    ) -> list[SemanticSearchResult]:
        """
        Hybrid search across Islamic texts combining vector + keyword retrieval.

        When source_types includes QURAN (or no filter is specified), this
        searches the pre-computed verse_embeddings table (6,236 Quran verses)
        in addition to any library text_chunks, merging results by RRF score.

        Args:
            query: Natural language query (any language — Arabic, Turkish, English)
            library_space_id: Restrict search to a specific library space
            source_types: Filter by source types (QURAN, TAFSIR, etc.)
            limit: Maximum number of results (default 10, max 100)
            min_similarity: Minimum cosine similarity threshold (0.0-1.0)

        Returns:
            Ranked list of matching passages (highest fused score first)
        """
        limit = min(limit, 100)
        # Fetch more candidates from each path so RRF has enough to merge
        retrieval_limit = min(limit * 3, 100)

        # Determine which sources to search
        search_quran_verses = (
            source_types is None  # No filter -> search everything
            or SourceType.QURAN in source_types
        )
        # Filter out QURAN from library search (verse_embeddings handles it)
        non_quran_types: list[SourceType] | None = (
            [st for st in source_types if st != SourceType.QURAN]
            if source_types is not None
            else None
        )
        search_library = source_types is None or bool(non_quran_types)

        # --- Vector retrieval paths ---
        # NOTE: SQLAlchemy AsyncSession does NOT support concurrent queries
        # on the same session, so we run all DB queries sequentially.
        query_embedding = await self._embedder.embed_text(QUERY_PREFIX + query)

        result_lists: list[list[SemanticSearchResult]] = []

        if search_quran_verses:
            try:
                verse_results = await self._verse_embs.search_by_text(
                    query_embedding=query_embedding,
                    limit=retrieval_limit,
                    min_similarity=min_similarity,
                )
                result_lists.append(verse_results)
            except Exception as e:
                logger.warning("search_path_failed", path="verse_vector", error=str(e))

        if search_library:
            try:
                chunk_results = await self._chunks.semantic_search(
                    query_embedding=query_embedding,
                    library_space_id=library_space_id,
                    source_types=non_quran_types,
                    limit=retrieval_limit,
                    min_similarity=min_similarity,
                )
                result_lists.append(chunk_results)
            except Exception as e:
                logger.warning("search_path_failed", path="chunk_vector", error=str(e))

        # --- Translation embedding retrieval path (cross-lingual) ---
        if search_quran_verses and self._verse_translations is not None:
            try:
                translation_results = await self._verse_translations.search_by_text(
                    query_embedding=query_embedding,
                    limit=retrieval_limit,
                    min_similarity=min_similarity,
                )
                result_lists.append(translation_results)
            except Exception as e:
                logger.warning("search_path_failed", path="translation_vector", error=str(e))

        # --- Keyword retrieval paths (BM25 / tsvector) ---
        if search_quran_verses:
            try:
                keyword_verse_results = await self._verse_embs.keyword_search_verses(
                    query=query,
                    limit=retrieval_limit,
                )
                result_lists.append(keyword_verse_results)
            except Exception as e:
                logger.warning("search_path_failed", path="verse_keyword", error=str(e))

        if search_library:
            try:
                keyword_chunk_results = await self._chunks.keyword_search_chunks(
                    query=query,
                    source_types=non_quran_types,
                    limit=retrieval_limit,
                )
                result_lists.append(keyword_chunk_results)
            except Exception as e:
                logger.warning("search_path_failed", path="chunk_keyword", error=str(e))

        if not result_lists:
            return []

        # Fuse results with RRF
        fused = self._rrf_fuse(*result_lists)

        logger.debug(
            "hybrid_search_complete",
            query=query[:80],
            num_paths=len(result_lists),
            total_candidates=sum(len(r) for r in result_lists),
            fused_count=len(fused),
        )

        # --- Cross-encoder re-ranking (optional) ---
        if self._reranker is not None and fused:
            fused = await self._rerank_results(query, fused, limit)
        else:
            fused = fused[:limit]

        return fused

    async def _rerank_results(
        self,
        query: str,
        candidates: list[SemanticSearchResult],
        limit: int,
    ) -> list[SemanticSearchResult]:
        """
        Re-rank top candidates using the cross-encoder for precise scoring.

        Takes the top reranker_top_k candidates from the fused list,
        scores each (query, document) pair with the cross-encoder, and
        returns the top `limit` results with updated similarity scores.
        """
        assert self._reranker is not None  # noqa: S101

        # Take top candidates for re-ranking (cross-encoder is expensive)
        to_rerank = candidates[: self._reranker_top_k]
        contents = [r.content for r in to_rerank]

        reranked = await self._reranker.rerank(
            query=query,
            documents=contents,
            top_k=limit,
        )

        logger.debug(
            "reranking_complete",
            query=query[:80],
            candidates=len(to_rerank),
            reranked=len(reranked),
            model=self._reranker.model_name,
        )

        # Build reordered results with updated scores
        results: list[SemanticSearchResult] = []
        for orig_idx, score in reranked:
            original = to_rerank[orig_idx]
            results.append(
                SemanticSearchResult(
                    chunk_id=original.chunk_id,
                    text_source_id=original.text_source_id,
                    source_title=original.source_title,
                    source_type=original.source_type,
                    reference=original.reference,
                    content=original.content,
                    similarity_score=round(score, 4),
                    metadata=original.metadata,
                )
            )
        return results

    @staticmethod
    def _rrf_fuse(
        *result_lists: list[SemanticSearchResult],
        k: int = 60,
    ) -> list[SemanticSearchResult]:
        """
        Reciprocal Rank Fusion — merge multiple ranked lists.

        Each result gets a score of 1/(k + rank + 1) from each list it appears in.
        Results appearing in multiple lists get boosted. The parameter k (default 60)
        controls how much weight is given to top-ranked vs lower-ranked items.

        Args:
            *result_lists: Variable number of ranked result lists to fuse.
            k: RRF smoothing constant. Higher = more equal weighting across ranks.

        Returns:
            Merged list sorted by fused RRF score (normalized to 0-1 range).
        """
        scores: dict[str, float] = {}  # key = unique identifier
        results_map: dict[str, SemanticSearchResult] = {}

        for result_list in result_lists:
            for rank, result in enumerate(result_list):
                key = f"{result.source_type.value}:{result.reference}"
                scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
                # Keep the first occurrence (usually has richer metadata)
                if key not in results_map:
                    results_map[key] = result

        # Sort by fused score descending
        sorted_keys = sorted(scores, key=lambda x: scores[x], reverse=True)

        # Normalize RRF score to 0-1 range for display
        # Max possible RRF score = num_lists / (k + 1) (rank 0 in every list)
        num_lists = len(result_lists)
        max_rrf = num_lists / (k + 1) if num_lists > 0 else 1.0

        fused: list[SemanticSearchResult] = []
        for key in sorted_keys:
            result = results_map[key]
            normalized = min(scores[key] / max_rrf, 1.0) if max_rrf > 0 else 0.0
            fused.append(
                SemanticSearchResult(
                    chunk_id=result.chunk_id,
                    text_source_id=result.text_source_id,
                    source_title=result.source_title,
                    source_type=result.source_type,
                    reference=result.reference,
                    content=result.content,
                    similarity_score=round(normalized, 4),
                    metadata=result.metadata,
                )
            )
        return fused

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
