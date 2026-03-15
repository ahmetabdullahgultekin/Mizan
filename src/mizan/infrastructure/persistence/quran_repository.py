"""
PostgreSQL implementation of IQuranRepository.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mizan.domain.entities import Surah, Verse
from mizan.domain.enums import (
    BasmalahStatus,
    QiraatType,
    RevelationType,
    SajdahType,
    ScriptType,
)
from mizan.domain.exceptions import (
    SurahNotFoundError,
    VerseNotFoundError,
    VerseRangeError,
)
from mizan.domain.repositories import (
    IntegrityReport,
    IQuranRepository,
)
from mizan.domain.value_objects import SurahMetadata, TextChecksum, VerseLocation
from mizan.infrastructure.persistence.models import SurahModel, VerseModel

logger = structlog.get_logger(__name__)


class PostgresQuranRepository(IQuranRepository):
    """
    PostgreSQL implementation of IQuranRepository.

    Provides async access to Quran data stored in PostgreSQL.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _model_to_verse(self, model: VerseModel, surah_model: SurahModel) -> Verse:
        """Convert database model to domain entity."""
        content: dict[ScriptType, str] = {ScriptType.UTHMANI: model.text_uthmani}
        if model.text_uthmani_min:
            content[ScriptType.UTHMANI_MINIMAL] = model.text_uthmani_min
        if model.text_simple:
            content[ScriptType.SIMPLE] = model.text_simple

        surah_metadata = SurahMetadata(
            number=surah_model.id,
            name_arabic=surah_model.name_arabic,
            name_english=surah_model.name_english,
            name_transliteration=surah_model.name_transliteration,
            revelation_type=RevelationType(surah_model.revelation_type),
            revelation_order=surah_model.revelation_order,
            verse_count=surah_model.verse_count,
            basmalah_status=BasmalahStatus(surah_model.basmalah_status),
            ruku_count=surah_model.ruku_count,
            word_count=surah_model.word_count,
            letter_count=surah_model.letter_count,
        )

        qiraat_variants: dict[QiraatType, dict[ScriptType, str]] = {}
        if model.qiraat_variants:
            for qiraat_key, scripts in model.qiraat_variants.items():
                try:
                    qiraat = QiraatType(qiraat_key)
                    qiraat_variants[qiraat] = {
                        ScriptType(k): v for k, v in scripts.items()
                    }
                except ValueError:
                    logger.warning(
                        "unknown_qiraat_variant",
                        key=qiraat_key,
                        surah=model.surah_number,
                        verse=model.verse_number,
                    )

        return Verse(
            id=model.id,
            location=VerseLocation(
                surah_number=model.surah_number,
                verse_number=model.verse_number,
            ),
            content=content,
            qiraat_variants=qiraat_variants,
            surah_metadata=surah_metadata,
            is_sajdah=model.is_sajdah,
            sajdah_type=SajdahType(model.sajdah_type) if model.sajdah_type else None,
            juz_number=model.juz_number,
            hizb_number=model.hizb_number,
            ruku_number=model.ruku_number,
            manzil_number=model.manzil_number,
            page_number=model.page_number,
            checksum=TextChecksum.from_string(model.checksum),
            word_count=model.word_count,
            letter_count=model.letter_count,
            abjad_value_mashriqi=model.abjad_value_mashriqi,
        )

    async def get_verse(self, location: VerseLocation) -> Verse | None:
        stmt = (
            select(VerseModel, SurahModel)
            .join(SurahModel, VerseModel.surah_number == SurahModel.id)
            .where(
                VerseModel.surah_number == location.surah_number,
                VerseModel.verse_number == location.verse_number,
            )
        )
        result = await self._session.execute(stmt)
        row = result.first()
        if row is None:
            return None
        return self._model_to_verse(row[0], row[1])

    async def get_verse_or_raise(self, location: VerseLocation) -> Verse:
        verse = await self.get_verse(location)
        if verse is None:
            raise VerseNotFoundError(location)
        return verse

    async def get_surah(self, surah_number: int) -> Surah:
        surah_stmt = select(SurahModel).where(SurahModel.id == surah_number)
        surah_result = await self._session.execute(surah_stmt)
        surah_model = surah_result.scalar_one_or_none()
        if surah_model is None:
            raise SurahNotFoundError(surah_number)

        verses_stmt = (
            select(VerseModel)
            .where(VerseModel.surah_number == surah_number)
            .order_by(VerseModel.verse_number)
        )
        verses_result = await self._session.execute(verses_stmt)
        verse_models = verses_result.scalars().all()
        verses = tuple(self._model_to_verse(vm, surah_model) for vm in verse_models)

        metadata = SurahMetadata(
            number=surah_model.id,
            name_arabic=surah_model.name_arabic,
            name_english=surah_model.name_english,
            name_transliteration=surah_model.name_transliteration,
            revelation_type=RevelationType(surah_model.revelation_type),
            revelation_order=surah_model.revelation_order,
            verse_count=surah_model.verse_count,
            basmalah_status=BasmalahStatus(surah_model.basmalah_status),
            ruku_count=surah_model.ruku_count,
            word_count=surah_model.word_count,
            letter_count=surah_model.letter_count,
        )
        return Surah(
            metadata=metadata,
            verses=verses,
            checksum=TextChecksum.from_string(surah_model.checksum),
        )

    async def get_verses_in_range(
        self,
        start: VerseLocation,
        end: VerseLocation,
    ) -> list[Verse]:
        if start > end:
            raise VerseRangeError(start, end, "Start must be before or equal to end")

        stmt = (
            select(VerseModel, SurahModel)
            .join(SurahModel, VerseModel.surah_number == SurahModel.id)
            .where(
                (
                    (VerseModel.surah_number > start.surah_number)
                    | (
                        (VerseModel.surah_number == start.surah_number)
                        & (VerseModel.verse_number >= start.verse_number)
                    )
                )
                & (
                    (VerseModel.surah_number < end.surah_number)
                    | (
                        (VerseModel.surah_number == end.surah_number)
                        & (VerseModel.verse_number <= end.verse_number)
                    )
                )
            )
            .order_by(VerseModel.surah_number, VerseModel.verse_number)
        )
        result = await self._session.execute(stmt)
        return [self._model_to_verse(row[0], row[1]) for row in result.all()]

    async def get_all_verses(self) -> list[Verse]:
        stmt = (
            select(VerseModel, SurahModel)
            .join(SurahModel, VerseModel.surah_number == SurahModel.id)
            .order_by(VerseModel.surah_number, VerseModel.verse_number)
        )
        result = await self._session.execute(stmt)
        return [self._model_to_verse(row[0], row[1]) for row in result.all()]

    async def stream_verses(
        self,
        surah_number: int | None = None,
    ) -> AsyncIterator[Verse]:
        stmt = (
            select(VerseModel, SurahModel)
            .join(SurahModel, VerseModel.surah_number == SurahModel.id)
        )
        if surah_number is not None:
            stmt = stmt.where(VerseModel.surah_number == surah_number)
        stmt = stmt.order_by(VerseModel.surah_number, VerseModel.verse_number)

        result = await self._session.stream(stmt)
        async for row in result:
            yield self._model_to_verse(row[0], row[1])

    async def get_verse_count(self, surah_number: int | None = None) -> int:
        stmt = select(func.count(VerseModel.id))
        if surah_number is not None:
            stmt = stmt.where(VerseModel.surah_number == surah_number)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def get_verses_by_criteria(
        self,
        revelation_type: RevelationType | None = None,
        juz_number: int | None = None,
        hizb_number: int | None = None,
        manzil_number: int | None = None,
        has_sajdah: bool | None = None,
    ) -> list[Verse]:
        stmt = (
            select(VerseModel, SurahModel)
            .join(SurahModel, VerseModel.surah_number == SurahModel.id)
        )
        if revelation_type is not None:
            stmt = stmt.where(SurahModel.revelation_type == revelation_type.value)
        if juz_number is not None:
            stmt = stmt.where(VerseModel.juz_number == juz_number)
        if hizb_number is not None:
            stmt = stmt.where(VerseModel.hizb_number == hizb_number)
        if manzil_number is not None:
            stmt = stmt.where(VerseModel.manzil_number == manzil_number)
        if has_sajdah is not None:
            stmt = stmt.where(VerseModel.is_sajdah == has_sajdah)
        stmt = stmt.order_by(VerseModel.surah_number, VerseModel.verse_number)
        result = await self._session.execute(stmt)
        return [self._model_to_verse(row[0], row[1]) for row in result.all()]

    async def search_text(
        self,
        query: str,
        surah_number: int | None = None,
        case_sensitive: bool = False,
    ) -> list[Verse]:
        stmt = (
            select(VerseModel, SurahModel)
            .join(SurahModel, VerseModel.surah_number == SurahModel.id)
        )
        search_field = VerseModel.text_normalized_full
        if case_sensitive:
            stmt = stmt.where(search_field.contains(query))
        else:
            stmt = stmt.where(search_field.ilike(f"%{query}%"))
        if surah_number is not None:
            stmt = stmt.where(VerseModel.surah_number == surah_number)
        stmt = stmt.order_by(VerseModel.surah_number, VerseModel.verse_number)
        result = await self._session.execute(stmt)
        return [self._model_to_verse(row[0], row[1]) for row in result.all()]

    async def verify_integrity(self) -> IntegrityReport:
        failed_verses: list[VerseLocation] = []
        total_verses = 0

        async for verse in self.stream_verses():
            total_verses += 1
            if not verse.verify_integrity():
                failed_verses.append(verse.location)

        all_text_stmt = (
            select(VerseModel.text_uthmani)
            .order_by(VerseModel.surah_number, VerseModel.verse_number)
        )
        result = await self._session.execute(all_text_stmt)
        all_text = "\n".join(row[0] for row in result.all())
        actual_checksum = TextChecksum.compute(all_text)

        return IntegrityReport(
            is_valid=len(failed_verses) == 0,
            checked_at=datetime.utcnow(),
            total_verses=total_verses,
            failed_verses=tuple(failed_verses),
            expected_checksum="",
            actual_checksum=actual_checksum.value,
            details=f"Verified {total_verses} verses, {len(failed_verses)} failures",
        )
