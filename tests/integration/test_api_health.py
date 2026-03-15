"""
Integration tests — /health endpoint.

Uses dependency overrides from conftest.py (mocked DB session and cache).
"""


def test_health_returns_200(client):
    """Health endpoint returns 200 with required fields."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "database" in data
    assert "cache" in data
    assert "timestamp" in data
