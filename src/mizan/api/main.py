"""
FastAPI application entry point.

Configures the API with routers, middleware, and lifecycle events.
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from mizan import __version__
from mizan.api.limiters import limiter
from mizan.api.routers import analysis, health, verses
from mizan.api.routers.library import router as library_router
from mizan.api.routers.semantic_search import router as semantic_search_router
from mizan.domain.exceptions import DomainException
from mizan.infrastructure.cache.redis_cache import close_cache, get_cache
from mizan.infrastructure.config import get_settings
from mizan.infrastructure.persistence.database import close_db, init_db


def _init_sentry() -> None:
    """Initialise Sentry error tracking if SENTRY_DSN is configured."""
    settings = get_settings()
    if not settings.sentry_dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.asgi import SentryAsgiMiddleware  # noqa: F401 — checked below

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.sentry_environment,
            release=__version__,
            traces_sample_rate=0.1,
            send_default_pii=False,
        )
        logger.info("sentry_initialised", environment=settings.sentry_environment)
    except ImportError:
        logger.warning(
            "sentry_sdk_not_installed",
            detail="Install sentry-sdk to enable error tracking: pip install sentry-sdk",
        )

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan management: startup and shutdown."""
    settings = get_settings()

    _init_sentry()
    await init_db()
    await get_cache()

    logger.info("Mizan API started", version=__version__, env=settings.log_level)

    yield

    await close_cache()
    await close_db()
    logger.info("Mizan API stopped")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Mizan Core Engine",
        description=(
            "High-precision Quranic text analysis API. "
            "Provides accurate counting, Abjad calculations, "
            "and morphological analysis."
        ),
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Rate limiter state
    app.state.limiter = limiter

    # Rate limit exceeded → 429
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    # Sentry ASGI middleware — only added when sentry_sdk is installed and DSN is set
    if settings.sentry_dsn:
        try:
            from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
            app.add_middleware(SentryAsgiMiddleware)  # type: ignore[arg-type]
        except ImportError:
            pass  # sentry_sdk not installed; warning already emitted at startup

    # CORS middleware — origins controlled via ALLOWED_ORIGINS env var
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # SlowAPI rate limiting middleware
    app.add_middleware(SlowAPIMiddleware)

    # ---------------------------------------------------------------------------
    # Security headers middleware
    # ---------------------------------------------------------------------------

    @app.middleware("http")
    async def security_headers(request: Request, call_next: object) -> Response:
        response: Response = await call_next(request)  # type: ignore[operator]
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    # ---------------------------------------------------------------------------
    # Request / response logging middleware
    # ---------------------------------------------------------------------------

    @app.middleware("http")
    async def request_logging(request: Request, call_next: object) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        log = logger.bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        response: Response = await call_next(request)  # type: ignore[operator]

        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        log.info(
            "request",
            status=response.status_code,
            duration_ms=elapsed_ms,
        )

        response.headers["X-Request-ID"] = request_id
        return response

    # ---------------------------------------------------------------------------
    # Centralized domain exception handler
    # ---------------------------------------------------------------------------

    @app.exception_handler(DomainException)
    async def domain_exception_handler(
        request: Request, exc: DomainException
    ) -> JSONResponse:
        """Map domain exceptions to HTTP responses without repeating try/except in every router."""
        from mizan.domain.exceptions import (
            EntityNotFoundError,
            InvalidSurahNumberError,
            InvalidVerseLocationError,
            MorphologyDataNotFoundError,
            SurahNotFoundError,
            VerseNotFoundError,
        )

        not_found_types = (
            VerseNotFoundError,
            SurahNotFoundError,
            EntityNotFoundError,
            MorphologyDataNotFoundError,
        )
        bad_request_types = (
            InvalidVerseLocationError,
            InvalidSurahNumberError,
        )

        if isinstance(exc, not_found_types):
            status_code = 404
        elif isinstance(exc, bad_request_types):
            status_code = 400
        else:
            status_code = 400

        logger.warning("domain_exception", code=exc.code, detail=exc.message)
        return JSONResponse(status_code=status_code, content=exc.to_dict())

    # ---------------------------------------------------------------------------
    # Routers
    # ---------------------------------------------------------------------------

    app.include_router(health.router, tags=["Health"])
    app.include_router(verses.router, prefix="/api/v1", tags=["Verses"])
    app.include_router(analysis.router, prefix="/api/v1", tags=["Analysis"])

    if settings.enable_semantic_analysis:
        app.include_router(library_router, prefix="/api/v1", tags=["Library"])
        app.include_router(
            semantic_search_router, prefix="/api/v1", tags=["Semantic Search"]
        )

    return app


# Application instance
app = create_app()
