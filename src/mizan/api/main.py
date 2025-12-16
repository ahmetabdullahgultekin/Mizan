"""
FastAPI application entry point.

Configures the API with routers, middleware, and lifecycle events.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mizan import __version__
from mizan.api.routers import analysis, health, verses
from mizan.infrastructure.cache.redis_cache import close_cache, get_cache
from mizan.infrastructure.config import get_settings
from mizan.infrastructure.persistence.database import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan management.

    Handles startup and shutdown events.
    """
    # Startup
    settings = get_settings()

    # Initialize database
    await init_db()

    # Initialize cache
    await get_cache()

    yield

    # Shutdown
    await close_cache()
    await close_db()


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
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(verses.router, prefix="/api/v1", tags=["Verses"])
    app.include_router(analysis.router, prefix="/api/v1", tags=["Analysis"])

    return app


# Application instance
app = create_app()
