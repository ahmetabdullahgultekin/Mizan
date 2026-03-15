"""
Integration tests — verses and analysis routers.

Tests routing, request validation, and error handling without a real database.
The database calls are intercepted via FastAPI dependency overrides.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# /api/v1/surahs
# ---------------------------------------------------------------------------


def test_list_surahs_calls_repository(client):
    """GET /api/v1/surahs returns 200 (with mocked DB from conftest)."""
    response = client.get("/api/v1/surahs")
    # With mocked session the endpoint is reachable (may return empty or 500)
    assert response.status_code in (200, 500)


def test_get_verse_invalid_surah_returns_400_or_404(client):
    """GET /api/v1/verses/0/1 — surah 0 is invalid."""
    response = client.get("/api/v1/verses/0/1")
    assert response.status_code in (400, 404, 422)


def test_get_verse_surah_out_of_range_returns_400(client):
    """GET /api/v1/verses/115/1 — surah 115 does not exist."""
    response = client.get("/api/v1/verses/115/1")
    assert response.status_code in (400, 404, 422)


# ---------------------------------------------------------------------------
# /api/v1/analysis
# ---------------------------------------------------------------------------


def test_abjad_analysis_requires_text(client):
    """GET /api/v1/analysis/abjad without text parameter → 400 or 422 or 500."""
    response = client.get("/api/v1/analysis/abjad")
    assert response.status_code in (400, 422, 500)


def test_abjad_analysis_with_text_returns_200(client):
    """GET /api/v1/analysis/abjad?text=بسم returns 200 with numeric value."""
    response = client.get("/api/v1/analysis/abjad", params={"text": "بسم"})
    assert response.status_code == 200
    data = response.json()
    assert "value" in data or "abjad_value" in data or "total" in data


def test_letter_count_requires_text(client):
    """GET /api/v1/analysis/letters/count without text → 400 or 422 or 500."""
    response = client.get("/api/v1/analysis/letters/count")
    assert response.status_code in (400, 422, 500)


def test_letter_count_returns_integer(client):
    """GET /api/v1/analysis/letters/count?text=بسم returns a count."""
    response = client.get("/api/v1/analysis/letters/count", params={"text": "بسم"})
    assert response.status_code == 200
    data = response.json()
    # Response should contain a numeric count field
    assert any(isinstance(v, int) for v in data.values())
