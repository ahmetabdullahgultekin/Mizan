"""
Shared rate limiter instance.

Single source of truth for slowapi's Limiter, shared between
main.py (where it is registered on app.state) and any router
that needs to apply @limiter.limit() decorators.

A **default limit** is configured here so the ``SlowAPIMiddleware`` actually
applies a ceiling to *every* route. Previously the limiter had no default and
only the ``/search/semantic`` route carried an explicit ``@limiter.limit``
decorator, so the middleware was effectively inert across the analysis, verses,
library, and morphology routers — any client could hammer them unbounded.

- ``DEFAULT_LIMIT`` (``120/minute`` per IP) is the catch-all applied by the
  middleware to routes without their own decorator.
- Hot/expensive routes still set a tighter explicit limit (e.g. semantic search
  keeps ``30/minute``); an explicit ``@limiter.limit`` overrides the default for
  that route.

Import pattern:
    from mizan.api.limiters import limiter

    # In main.py:
    app.state.limiter = limiter

    # In routers (tighter than the default):
    @limiter.limit("30/minute")
    async def my_endpoint(request: Request, ...): ...
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Catch-all ceiling applied by SlowAPIMiddleware to every route without its own
# explicit @limiter.limit decorator. Keep generous enough for normal browsing
# but low enough to blunt scripted abuse.
DEFAULT_LIMIT = "120/minute"

limiter: Limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[DEFAULT_LIMIT],
)
