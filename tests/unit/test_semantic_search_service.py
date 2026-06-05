"""
Unit tests for SemanticSearchService — RRF fusion, min_similarity scaling,
and reranker integration.

All repositories, the embedder, and the reranker are replaced with mocks so
these tests run with no database, Redis, or ML model download.

Regression focus
----------------
The post-fusion `min_similarity` filter used to be applied to RRF-fused /
sigmoid-reranked scores using a 0.5 *cosine* threshold. Those fused scores are
on a completely different scale (a rank-reciprocal sum normalised to 0-1, or a
sigmoid cross-encoder score), so the filter silently dropped valid hits. The
cosine threshold is already enforced upstream on each vector retrieval path.
These tests pin that behaviour.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from mizan.application.services.semantic_search_service import SemanticSearchService
from mizan.domain.entities.library import SemanticSearchResult
from mizan.domain.enums.library_enums import SourceType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _result(ref: str, score: float, source_type: SourceType = SourceType.QURAN,
            metadata: dict | None = None) -> SemanticSearchResult:
    """Build a SemanticSearchResult with a per-path cosine score."""
    return SemanticSearchResult(
        chunk_id=uuid4(),
        text_source_id=uuid4(),
        source_title="Quran",
        source_type=source_type,
        reference=ref,
        content=f"content for {ref}",
        similarity_score=score,
        metadata=metadata or {},
    )


def _make_service(
    verse_results: list[SemanticSearchResult] | None = None,
    chunk_results: list[SemanticSearchResult] | None = None,
    translation_results: list[SemanticSearchResult] | None = None,
    keyword_verse_results: list[SemanticSearchResult] | None = None,
    keyword_chunk_results: list[SemanticSearchResult] | None = None,
    reranker: MagicMock | None = None,
) -> SemanticSearchService:
    """Wire a SemanticSearchService with fully-mocked dependencies."""
    embedder = MagicMock()
    embedder.embed_text = AsyncMock(return_value=[0.1] * 768)

    verse_repo = MagicMock()
    verse_repo.search_by_text = AsyncMock(return_value=verse_results or [])
    verse_repo.keyword_search_verses = AsyncMock(return_value=keyword_verse_results or [])

    chunk_repo = MagicMock()
    chunk_repo.semantic_search = AsyncMock(return_value=chunk_results or [])
    chunk_repo.keyword_search_chunks = AsyncMock(return_value=keyword_chunk_results or [])

    translation_repo = MagicMock()
    translation_repo.search_by_text = AsyncMock(return_value=translation_results or [])

    return SemanticSearchService(
        chunk_repo=chunk_repo,
        verse_emb_repo=verse_repo,
        embedding_service=embedder,
        reranker=reranker,
        reranker_top_k=30,
        verse_translation_repo=translation_repo,
    )


# ---------------------------------------------------------------------------
# Regression: post-fusion min_similarity must NOT drop valid fused hits
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_min_similarity_not_reapplied_to_fused_scores():
    """
    A broad query produces several valid vector hits across multiple paths.

    Each hit passes the cosine gate upstream (score >= 0.5 there), but after RRF
    fusion the normalised scores fall well below the 0.5 cosine threshold. The
    old code re-applied that threshold to the fused score and returned far fewer
    results than retrieved. With the fix, every distinct fused hit survives.
    """
    # Three verses found by the Arabic vector path (each a strong cosine match
    # >= 0.5 upstream), and two DIFFERENT verses found only by the cross-lingual
    # translation path. Because each verse appears in just one path, its RRF
    # contribution is a single 1/(k+rank) term, which normalises well below 0.5.
    verse_hits = [
        _result("39:53", 0.88),
        _result("7:156", 0.81),
        _result("21:107", 0.77),
    ]
    translation_hits = [
        _result("6:54", 0.73, metadata={"translation_text": "your Lord has decreed mercy"}),
        _result("12:64", 0.68, metadata={"translation_text": "the most merciful of the merciful"}),
    ]

    svc = _make_service(
        verse_results=verse_hits,
        translation_results=translation_hits,
    )

    results = await svc.search(
        query="mercy",
        source_types=[SourceType.QURAN],
        limit=10,
        min_similarity=0.5,  # the default that triggered the bug
    )

    # All five distinct verses must come back — none dropped by a mis-scaled filter.
    refs = {r.reference for r in results}
    assert refs == {"39:53", "7:156", "21:107", "6:54", "12:64"}
    assert len(results) == 5

    # Sanity: the fused scores are genuinely below the old 0.5 cosine threshold,
    # proving the old post-filter WOULD have dropped these valid hits.
    assert all(r.similarity_score < 0.5 for r in results), (
        "Expected RRF-normalised scores below 0.5; if these were >= 0.5 the test "
        "would not exercise the regression."
    )


@pytest.mark.asyncio
async def test_single_path_top_hit_survives_default_threshold():
    """
    With a single retrieval path, the top RRF hit normalises to ~1.0, but lower
    ranks decay quickly. Every retrieved hit must still be returned regardless of
    where its normalised score lands relative to 0.5.
    """
    hits = [_result(f"2:{i}", 0.9 - i * 0.01) for i in range(1, 9)]
    svc = _make_service(verse_results=hits)

    results = await svc.search(
        query="guidance",
        source_types=[SourceType.QURAN],
        limit=10,
        min_similarity=0.5,
    )

    assert len(results) == 8
    assert {r.reference for r in results} == {h.reference for h in hits}


@pytest.mark.asyncio
async def test_min_similarity_still_gates_each_vector_path():
    """
    `min_similarity` must still be forwarded to each vector retrieval path so the
    cosine gate is enforced where the scores ARE cosine similarities.
    """
    svc = _make_service(verse_results=[_result("1:1", 0.95)])

    await svc.search(
        query="x",
        source_types=[SourceType.QURAN],
        limit=5,
        min_similarity=0.42,
    )

    svc._verse_embs.search_by_text.assert_awaited_once()
    _, kwargs = svc._verse_embs.search_by_text.call_args
    assert kwargs["min_similarity"] == 0.42


@pytest.mark.asyncio
async def test_empty_when_no_paths_return_anything():
    """No hits on any path → empty list (not an error)."""
    svc = _make_service()
    results = await svc.search(query="nothing matches", limit=10, min_similarity=0.5)
    assert results == []


@pytest.mark.asyncio
async def test_reranked_results_not_filtered_by_cosine_threshold():
    """
    When a reranker is present, results carry sigmoid scores. Those must not be
    filtered against the 0.5 cosine threshold either.
    """
    verse_hits = [
        _result("39:53", 0.88, metadata={"translation_text": "mercy encompasses all"}),
        _result("7:156", 0.81, metadata={"translation_text": "mercy encompasses all things"}),
    ]

    reranker = MagicMock()
    reranker.model_name = "stub-cross-encoder"
    # Sigmoid scores both below 0.5 — would be wiped by the old post-filter.
    reranker.rerank = AsyncMock(return_value=[(0, 0.40), (1, 0.35)])

    svc = _make_service(verse_results=verse_hits, reranker=reranker)

    results = await svc.search(
        query="mercy",
        source_types=[SourceType.QURAN],
        limit=10,
        min_similarity=0.5,
    )

    reranker.rerank.assert_awaited_once()
    assert {r.reference for r in results} == {"39:53", "7:156"}
    assert len(results) == 2
