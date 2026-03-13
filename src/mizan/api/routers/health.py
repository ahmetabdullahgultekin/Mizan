"""Health check endpoints."""

from datetime import datetime

import structlog
from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from mizan import __version__
from mizan.api.dependencies import Cache, DbSession
from mizan.application.dtos.responses import HealthResponse
from mizan.infrastructure.config import get_settings

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/api/v1/health", response_model=HealthResponse, include_in_schema=False)
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
    except SQLAlchemyError:
        db_healthy = False

    # Check cache
    cache_healthy = await cache.health_check()

    # Check embedding service (only if semantic analysis is enabled)
    embedding_ok: bool | None = None
    settings = get_settings()
    if settings.enable_semantic_analysis:
        embedding_ok = True
        try:
            from mizan.infrastructure.embeddings.factory import get_embedding_service

            svc = get_embedding_service()
            await svc.embed_batch(["health check"])
        except Exception:
            embedding_ok = False
            logger.warning("embedding_service_health_check_failed")

    embedding_healthy = embedding_ok is None or embedding_ok
    overall_status = "healthy" if (db_healthy and cache_healthy and embedding_healthy) else "degraded"

    return HealthResponse(
        status=overall_status,
        version=__version__,
        database=db_healthy,
        cache=cache_healthy,
        embedding=embedding_ok,
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
