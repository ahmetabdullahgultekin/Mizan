"""
Integration tests — rate limiting actually applies across routes.

These prove the fix for the inert rate limiter: previously the shared
``Limiter`` had no ``default_limits`` and only ``/search/semantic`` carried an
explicit ``@limiter.limit`` decorator, so ``SlowAPIMiddleware`` enforced nothing
on the analysis / verses / library / morphology routers. Adding
``default_limits`` makes the middleware apply a catch-all ceiling to every route.

The tests build a *fresh* app with a *fresh* low-limit ``Limiter`` and clear its
in-memory storage so they are deterministic and isolated from the session-scoped
``client`` fixture (whose limiter state would otherwise leak between tests).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from slowapi import Limiter
from slowapi.util import get_remote_address

import mizan.api.limiters as limiters_module
from mizan.api.dependencies import get_db_session, get_redis_cache
from mizan.api.main import create_app
from mizan.infrastructure.config import get_settings


@pytest.fixture
def rate_limited_client(monkeypatch):
    """A client whose shared limiter has a tiny default limit (3/minute).

    Patches the module-level ``limiter`` so both ``main.create_app`` (which reads
    ``app.state.limiter``/the middleware) and the router decorators bind to it,
    then resets its storage so each test starts from a clean counter.
    """
    test_limiter = Limiter(key_func=get_remote_address, default_limits=["3/minute"])
    monkeypatch.setattr(limiters_module, "limiter", test_limiter)
    # The semantic_search router imported `limiter` by reference at module load;
    # patch that binding too so its decorator shares the test limiter's storage.
    import mizan.api.routers.semantic_search as ss_module

    monkeypatch.setattr(ss_module, "limiter", test_limiter, raising=False)

    settings = get_settings()
    settings.init_db_on_startup = False  # keep it hermetic

    app = create_app()
    # create_app() pinned app.state.limiter to the (already patched) module value.
    app.state.limiter = test_limiter
    app.dependency_overrides[get_db_session] = _passthrough_session
    app.dependency_overrides[get_redis_cache] = _passthrough_cache

    # Reset the in-memory storage so the counter starts at zero.
    test_limiter.reset()

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


async def _passthrough_session():  # pragma: no cover - trivial stub
    from unittest.mock import AsyncMock, MagicMock

    from sqlalchemy.ext.asyncio import AsyncSession

    session = MagicMock(spec=AsyncSession)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    yield session


async def _passthrough_cache():  # pragma: no cover - trivial stub
    from unittest.mock import AsyncMock, MagicMock

    from mizan.infrastructure.cache.redis_cache import RedisCache

    cache = MagicMock(spec=RedisCache)
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    return cache


def test_default_limit_applies_to_undecorated_route(rate_limited_client):
    """The analysis/abjad route has no @limiter.limit but is still bounded.

    With a 3/minute default, the 4th call must be throttled to 429 — proving the
    catch-all default limit (the fix) reaches routes that carry no decorator.
    """
    url = "/api/v1/analysis/abjad"
    params = {"text": "بسم الله"}

    statuses = [rate_limited_client.get(url, params=params).status_code for _ in range(4)]

    # First three succeed under the 3/minute default; the fourth is rate-limited.
    assert statuses[:3] == [200, 200, 200], statuses
    assert statuses[3] == 429, statuses


def test_rate_limit_429_reports_the_limit(rate_limited_client):
    """A throttled response is a proper 429 whose body names the exceeded limit."""
    url = "/api/v1/analysis/abjad"
    params = {"text": "بسم الله"}

    last = None
    for _ in range(5):
        last = rate_limited_client.get(url, params=params)

    assert last is not None
    assert last.status_code == 429
    # slowapi's default 429 body echoes the breached rate, e.g. "3 per 1 minute".
    assert "minute" in last.text.lower()


def test_limiter_has_default_limits_configured():
    """The production shared limiter ships with a non-empty default limit.

    Regression guard: if someone removes default_limits, the middleware silently
    goes inert again for every undecorated route.
    """
    from mizan.api.limiters import limiter

    assert limiter._default_limits, "shared limiter must configure default_limits"
