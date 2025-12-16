"""
FastAPI dependencies for dependency injection.

Provides repository and service instances to endpoints.
"""

from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from mizan.application.services.analyzer_service import AnalyzerService
from mizan.infrastructure.cache.redis_cache import RedisCache, get_cache
from mizan.infrastructure.persistence.database import get_async_session
from mizan.infrastructure.persistence.repositories import (
    PostgresMorphologyRepository,
    PostgresQuranRepository,
    PostgresSurahMetadataRepository,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async for session in get_async_session():
        yield session


async def get_quran_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PostgresQuranRepository:
    """Get Quran repository dependency."""
    return PostgresQuranRepository(session)


async def get_surah_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PostgresSurahMetadataRepository:
    """Get Surah metadata repository dependency."""
    return PostgresSurahMetadataRepository(session)


async def get_morphology_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PostgresMorphologyRepository:
    """Get Morphology repository dependency."""
    return PostgresMorphologyRepository(session)


async def get_redis_cache() -> RedisCache:
    """Get Redis cache dependency."""
    return await get_cache()


async def get_analyzer_service(
    quran_repo: Annotated[PostgresQuranRepository, Depends(get_quran_repository)],
    cache: Annotated[RedisCache, Depends(get_redis_cache)],
) -> AnalyzerService:
    """Get analyzer service dependency."""
    return AnalyzerService(quran_repo, cache)


# Type aliases for cleaner endpoint signatures
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
QuranRepo = Annotated[PostgresQuranRepository, Depends(get_quran_repository)]
SurahRepo = Annotated[PostgresSurahMetadataRepository, Depends(get_surah_repository)]
MorphologyRepo = Annotated[PostgresMorphologyRepository, Depends(get_morphology_repository)]
Cache = Annotated[RedisCache, Depends(get_redis_cache)]
Analyzer = Annotated[AnalyzerService, Depends(get_analyzer_service)]
