"""
Integration test fixtures.

Uses FastAPI's dependency override mechanism with in-memory mocks
to test routers without a real database or Redis instance.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mizan.api.dependencies import get_db_session, get_redis_cache
from mizan.api.main import create_app
from mizan.infrastructure.cache.redis_cache import RedisCache

# ---------------------------------------------------------------------------
# Mock session factory
# ---------------------------------------------------------------------------


def _mock_session() -> AsyncSession:
    """Return a MagicMock shaped like AsyncSession."""
    session = MagicMock(spec=AsyncSession)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    return session


async def _mock_session_dep():
    """Async generator dependency override for database session."""
    yield _mock_session()


def _mock_cache() -> RedisCache:
    cache = MagicMock(spec=RedisCache)
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    return cache


async def _mock_cache_dep() -> RedisCache:
    return _mock_cache()


# ---------------------------------------------------------------------------
# App fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def app():
    """FastAPI app with dependency overrides for testing."""
    application = create_app()
    application.dependency_overrides[get_db_session] = _mock_session_dep
    application.dependency_overrides[get_redis_cache] = _mock_cache_dep
    yield application
    application.dependency_overrides.clear()


@pytest.fixture(scope="module")
def client(app):
    """Synchronous test client."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest_asyncio.fixture(scope="module")
async def async_client(app):
    """Async HTTPX test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
