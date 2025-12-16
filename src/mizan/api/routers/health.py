"""Health check endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends

from mizan import __version__
from mizan.api.dependencies import Cache, DbSession
from mizan.application.dtos.responses import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    session: DbSession,
    cache: Cache,
) -> HealthResponse:
    """
    Check service health.

    Verifies database and cache connectivity.
    """
    # Check database
    db_healthy = True
    try:
        await session.execute("SELECT 1")
    except Exception:
        db_healthy = False

    # Check cache
    cache_healthy = await cache.health_check()

    status = "healthy" if (db_healthy and cache_healthy) else "degraded"

    return HealthResponse(
        status=status,
        version=__version__,
        database=db_healthy,
        cache=cache_healthy,
        timestamp=datetime.utcnow(),
    )


@router.get("/")
async def root() -> dict[str, str]:
    """API root endpoint."""
    return {
        "name": "Mizan Core Engine",
        "version": __version__,
        "docs": "/docs",
    }
