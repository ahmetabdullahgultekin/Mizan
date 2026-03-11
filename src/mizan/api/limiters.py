"""
Shared rate limiter instance.

Single source of truth for slowapi's Limiter, shared between
main.py (where it is registered on app.state) and any router
that needs to apply @limiter.limit() decorators.

Import pattern:
    from mizan.api.limiters import limiter

    # In main.py:
    app.state.limiter = limiter

    # In routers:
    @limiter.limit("30/minute")
    async def my_endpoint(request: Request, ...): ...
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter: Limiter = Limiter(key_func=get_remote_address)
