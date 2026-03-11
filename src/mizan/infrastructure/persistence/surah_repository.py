"""
PostgreSQL implementation of ISurahMetadataRepository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mizan.domain.enums import BasmalahStatus, RevelationType
from mizan.domain.exceptions import SurahNotFoundError
from mizan.domain.repositories import ISurahMetadataRepository
from mizan.domain.value_objects import SurahMetadata
from mizan.infrastructure.persistence.models import SurahModel


class PostgresSurahMetadataRepository(ISurahMetadataRepository):
    """PostgreSQL implementation of ISurahMetadataRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _model_to_metadata(self, model: SurahModel) -> SurahMetadata:
        return SurahMetadata(
            number=model.id,
            name_arabic=model.name_arabic,
            name_english=model.name_english,
            name_transliteration=model.name_transliteration,
            revelation_type=RevelationType(model.revelation_type),
            revelation_order=model.revelation_order,
            verse_count=model.verse_count,
            basmalah_status=BasmalahStatus(model.basmalah_status),
            ruku_count=model.ruku_count,
            word_count=model.word_count,
            letter_count=model.letter_count,
        )

    async def get_metadata(self, surah_number: int) -> SurahMetadata:
        stmt = select(SurahModel).where(SurahModel.id == surah_number)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise SurahNotFoundError(surah_number)
        return self._model_to_metadata(model)

    async def get_all_metadata(self) -> list[SurahMetadata]:
        stmt = select(SurahModel).order_by(SurahModel.id)
        result = await self._session.execute(stmt)
        return [self._model_to_metadata(m) for m in result.scalars().all()]

    async def get_meccan_surahs(self) -> list[SurahMetadata]:
        stmt = (
            select(SurahModel)
            .where(SurahModel.revelation_type == RevelationType.MECCAN.value)
            .order_by(SurahModel.id)
        )
        result = await self._session.execute(stmt)
        return [self._model_to_metadata(m) for m in result.scalars().all()]

    async def get_medinan_surahs(self) -> list[SurahMetadata]:
        stmt = (
            select(SurahModel)
            .where(SurahModel.revelation_type == RevelationType.MEDINAN.value)
            .order_by(SurahModel.id)
        )
        result = await self._session.execute(stmt)
        return [self._model_to_metadata(m) for m in result.scalars().all()]
