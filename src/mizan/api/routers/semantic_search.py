"""
Semantic Search API Endpoints.

Search across Islamic texts by meaning, not just keywords.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException, Request

from mizan.api.dependencies import DbSession
from mizan.api.limiters import limiter
from mizan.application.dtos.library_requests import SemanticSearchRequest
from mizan.application.dtos.library_responses import (
    SemanticSearchResponse,
    SemanticSearchResultResponse,
    SimilarVerseResponse,
    VerseEmbeddingStatsResponse,
)
from mizan.application.services.semantic_search_service import SemanticSearchService
from mizan.infrastructure.config import get_settings
from mizan.infrastructure.embeddings.factory import get_embedding_service
from mizan.infrastructure.persistence.library_repositories import (
    PostgresTextChunkRepository,
    PostgresVerseEmbeddingRepository,
    PostgresVerseTranslationRepository,
)
from mizan.infrastructure.reranking import get_reranker_service

router = APIRouter(prefix="/search")
logger = structlog.get_logger(__name__)


def _get_search_service(session: DbSession) -> SemanticSearchService:
    settings = get_settings()
    return SemanticSearchService(
        chunk_repo=PostgresTextChunkRepository(session),
        verse_emb_repo=PostgresVerseEmbeddingRepository(session),
        embedding_service=get_embedding_service(),
        verse_translation_repo=PostgresVerseTranslationRepository(session),
        reranker=get_reranker_service(),
        reranker_top_k=settings.reranker_top_k,
    )


@router.post(
    "/semantic",
    response_model=SemanticSearchResponse,
    summary="Semantic search across Islamic texts",
)
@limiter.limit("30/minute")
async def semantic_search(
    request: Request,
    body: SemanticSearchRequest,
    session: DbSession,
) -> SemanticSearchResponse:
    """
    Search for Islamic text passages by meaning (semantic search).

    Unlike keyword search, this finds content that is conceptually related
    even if the exact words are different.

    **Examples:**
    - Query: "evrenin kusursuz düzeni" → finds verses about cosmic order
    - Query: "صبر في الشدائد" → finds Arabic passages on patience in hardship
    - Query: "mercy and forgiveness of God" → finds across all languages/sources

    The search uses cosine similarity between your query's embedding and
    pre-computed embeddings of all indexed text chunks.

    **Note:** Results are only returned for sources that have been fully
    indexed (status=INDEXED). Use POST /api/v1/library/spaces/{id}/sources
    to add and index new sources.
    """
    svc = _get_search_service(session)
    results = await svc.search(
        query=body.query,
        library_space_id=body.library_space_id,
        source_types=body.source_types,
        limit=body.limit,
        min_similarity=body.min_similarity,
    )
    embedder = get_embedding_service()
    return SemanticSearchResponse(
        query=body.query,
        results=[
            SemanticSearchResultResponse(
                chunk_id=r.chunk_id,
                text_source_id=r.text_source_id,
                source_title=r.source_title,
                source_type=r.source_type,
                reference=r.reference,
                content=r.content,
                similarity_score=round(r.similarity_score, 4),
                metadata=r.metadata,
            )
            for r in results
        ],
        total_results=len(results),
        embedding_model=embedder.model_name,
    )


@router.get(
    "/verses/{surah_number}/{verse_number}/similar",
    response_model=list[SimilarVerseResponse],
    summary="Find Quran verses similar to a given verse",
)
async def find_similar_verses(
    surah_number: int,
    verse_number: int,
    session: DbSession,
    limit: int = 10,
) -> list[SimilarVerseResponse]:
    """
    Find Quran verses semantically similar to the given verse.

    Requires verse embeddings to be pre-computed.
    Run `scripts/embed_quran.py` to generate all verse embeddings.

    **Example:** GET /api/v1/search/verses/2/255/similar
    Returns verses most similar to Ayat al-Kursi.
    """
    if not (1 <= surah_number <= 114):
        raise HTTPException(status_code=400, detail="surah_number must be 1-114")
    if verse_number < 1:
        raise HTTPException(status_code=400, detail="verse_number must be >= 1")
    limit = min(limit, 50)

    svc = _get_search_service(session)
    try:
        similar = await svc.find_similar_verses(
            surah_number=surah_number,
            verse_number=verse_number,
            limit=limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    return [
        SimilarVerseResponse(
            surah_number=s,
            verse_number=v,
            similarity_score=round(score, 4),
        )
        for s, v, score in similar
    ]


@router.get(
    "/verses/embeddings/stats",
    response_model=VerseEmbeddingStatsResponse,
    summary="Get verse embedding statistics",
)
async def verse_embedding_stats(
    session: DbSession,
    model_name: str | None = None,
) -> VerseEmbeddingStatsResponse:
    """Get statistics about how many verse embeddings have been computed."""
    from mizan.infrastructure.persistence.library_repositories import (
        PostgresVerseEmbeddingRepository,
    )

    repo = PostgresVerseEmbeddingRepository(session)
    count = await repo.get_total_count(model_name=model_name)
    return VerseEmbeddingStatsResponse(
        total_embeddings=count,
        model_name=model_name or get_embedding_service().model_name,
    )
