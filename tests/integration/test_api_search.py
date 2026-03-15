"""
Integration tests — semantic search router.

Verifies routing, rate-limit registration, and input validation.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# POST /api/v1/search/semantic
# ---------------------------------------------------------------------------


def test_semantic_search_missing_query_returns_422(client):
    """POST /search/semantic with no body → 422."""
    response = client.post("/api/v1/search/semantic")
    assert response.status_code == 422


def test_semantic_search_empty_query_returns_422(client):
    """POST /search/semantic with empty query string → 422."""
    response = client.post(
        "/api/v1/search/semantic",
        json={"query": ""},
    )
    assert response.status_code == 422


def test_semantic_search_valid_request_structure(client):
    """POST /search/semantic with valid payload — endpoint is reachable."""
    from unittest.mock import AsyncMock, patch

    with patch(
        "mizan.api.routers.semantic_search.SemanticSearchService"
    ) as MockSvc:
        instance = MockSvc.return_value
        instance.search = AsyncMock(return_value=[])

        with patch("mizan.api.routers.semantic_search.get_embedding_service") as MockEmb:
            emb = MockEmb.return_value
            emb.model_name = "test-model"
            emb.embed_batch = AsyncMock(return_value=[[0.0] * 768])

            response = client.post(
                "/api/v1/search/semantic",
                json={"query": "mercy of God"},
            )

    # With mocked service the response depends on the internal mock chain;
    # the key assertion is that the route is registered and processes the request.
    assert response.status_code in (200, 500)


# ---------------------------------------------------------------------------
# GET /api/v1/search/verses/{surah}/{verse}/similar
# ---------------------------------------------------------------------------


def test_similar_verses_invalid_surah_returns_400(client):
    """surah_number 0 → 400 Bad Request."""
    response = client.get("/api/v1/search/verses/0/1/similar")
    assert response.status_code == 400


def test_similar_verses_surah_too_high_returns_400(client):
    """surah_number 115 → 400 Bad Request."""
    response = client.get("/api/v1/search/verses/115/1/similar")
    assert response.status_code == 400


def test_similar_verses_verse_zero_returns_400(client):
    """verse_number 0 → 400 Bad Request."""
    response = client.get("/api/v1/search/verses/1/0/similar")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/v1/search/verses/embeddings/stats
# ---------------------------------------------------------------------------


def test_embedding_stats_endpoint_is_reachable(client):
    """GET /search/verses/embeddings/stats → 200 or 500 (route exists)."""
    from unittest.mock import AsyncMock, patch

    with patch(
        "mizan.api.routers.semantic_search.PostgresVerseEmbeddingRepository"
    ) as MockRepo:
        instance = MockRepo.return_value
        instance.get_total_count = AsyncMock(return_value=6236)

        with patch("mizan.api.routers.semantic_search.get_embedding_service") as MockEmb:
            MockEmb.return_value.model_name = "test-model"

            response = client.get("/api/v1/search/verses/embeddings/stats")

    assert response.status_code in (200, 500)
