"""Health check endpoints."""

from datetime import datetime

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import text

from mizan import __version__
from mizan.api.dependencies import Cache, DbSession
from mizan.application.dtos.responses import HealthResponse
from mizan.infrastructure.config import get_settings

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health_check(
    session: DbSession,
    cache: Cache,
) -> HealthResponse:
    """
    Check service health.

    Verifies database, cache, and embedding service connectivity.
    """
    # Check database
    db_healthy = True
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_healthy = False

    # Check cache
    cache_healthy = await cache.health_check()

    # Check embedding service (only if semantic analysis is enabled)
    embedding_ok = True
    settings = get_settings()
    if settings.enable_semantic_analysis:
        try:
            from mizan.infrastructure.embeddings.factory import get_embedding_service

            svc = get_embedding_service()
            # A zero-length test to verify the service is reachable
            await svc.embed_batch(["health check"])
        except Exception:
            embedding_ok = False
            logger.warning("embedding_service_health_check_failed")

    overall_status = "healthy" if (db_healthy and cache_healthy and embedding_ok) else "degraded"

    return HealthResponse(
        status=overall_status,
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
