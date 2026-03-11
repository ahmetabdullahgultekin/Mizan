"""
Integration tests — /health endpoint.
"""

from unittest.mock import AsyncMock, patch


def test_health_returns_200(client):
    """Health endpoint returns 200 with required fields."""
    with (
        patch("mizan.api.routers.health.get_async_session") as mock_session_ctx,
        patch("mizan.api.routers.health.get_cache") as mock_cache,
    ):
        # Simulate healthy DB (execute returns something non-null)
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=MagicMock())
        mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_cache_obj = AsyncMock()
        mock_cache_obj.ping = AsyncMock(return_value=True)
        mock_cache.return_value = mock_cache_obj

        response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "database" in data
    assert "cache" in data
    assert "timestamp" in data


# Import MagicMock here too
from unittest.mock import MagicMock  # noqa: E402
