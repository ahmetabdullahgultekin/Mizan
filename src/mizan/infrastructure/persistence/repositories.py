"""
Repository implementations - Adapters for domain ports.

These repositories implement the domain repository interfaces
using SQLAlchemy for PostgreSQL persistence.
"""

from datetime import datetime
from typing import AsyncIterator
from uuid import UUID

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
    IMorphologyRepository,
    IQuranRepository,
    ISurahMetadataRepository,
    IntegrityReport,
    MorphologyData,
)
from mizan.domain.value_objects import SurahMetadata, TextChecksum, VerseLocation
from mizan.infrastructure.persistence.models import (
    MorphologyModel,
    SurahModel,
    VerseModel,
)


class PostgresQuranRepository(IQuranRepository):
    """
    PostgreSQL implementation of IQuranRepository.

    Provides async access to Quran data stored in PostgreSQL.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with async session."""
        self._session = session

    def _model_to_verse(self, model: VerseModel, surah_model: SurahModel) -> Verse:
        """Convert database model to domain entity."""
        # Build content dictionary
        content: dict[ScriptType, str] = {ScriptType.UTHMANI: model.text_uthmani}
        if model.text_uthmani_min:
            content[ScriptType.UTHMANI_MINIMAL] = model.text_uthmani_min
        if model.text_simple:
            content[ScriptType.SIMPLE] = model.text_simple

        # Build surah metadata
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

        # Parse qiraat variants
        qiraat_variants: dict[QiraatType, dict[ScriptType, str]] = {}
        if model.qiraat_variants:
            for qiraat_key, scripts in model.qiraat_variants.items():
                try:
                    qiraat = QiraatType(qiraat_key)
                    qiraat_variants[qiraat] = {
                        ScriptType(k): v for k, v in scripts.items()
                    }
                except ValueError:
                    pass  # Skip unknown qiraat types

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
        """Retrieve a single verse by location."""
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
        """Retrieve a single verse, raise if not found."""
        verse = await self.get_verse(location)
        if verse is None:
            raise VerseNotFoundError(location)
        return verse

    async def get_surah(self, surah_number: int) -> Surah:
        """Retrieve a complete Surah with all verses."""
        # Get surah metadata
        surah_stmt = select(SurahModel).where(SurahModel.id == surah_number)
        surah_result = await self._session.execute(surah_stmt)
        surah_model = surah_result.scalar_one_or_none()

        if surah_model is None:
            raise SurahNotFoundError(surah_number)

        # Get all verses
        verses_stmt = (
            select(VerseModel)
            .where(VerseModel.surah_number == surah_number)
            .order_by(VerseModel.verse_number)
        )
        verses_result = await self._session.execute(verses_stmt)
        verse_models = verses_result.scalars().all()

        # Convert to domain entities
        verses = tuple(
            self._model_to_verse(vm, surah_model) for vm in verse_models
        )

        # Build surah metadata
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
        """Retrieve verses within a range (inclusive)."""
        if start > end:
            raise VerseRangeError(start, end, "Start must be before or equal to end")

        # Build query for range
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
        """Retrieve all verses in the Quran."""
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
        """Stream verses for memory-efficient processing."""
        stmt = (
            select(VerseModel, SurahModel)
            .join(SurahModel, VerseModel.surah_number == SurahModel.id)
        )

        if surah_number is not None:
            stmt = stmt.where(VerseModel.surah_number == surah_number)

        stmt = stmt.order_by(VerseModel.surah_number, VerseModel.verse_number)

        # Use server-side cursor for streaming
        result = await self._session.stream(stmt)
        async for row in result:
            yield self._model_to_verse(row[0], row[1])

    async def get_verse_count(self, surah_number: int | None = None) -> int:
        """Get total verse count."""
        stmt = select(func.count(VerseModel.id))
        if surah_number is not None:
            stmt = stmt.where(VerseModel.surah_number == surah_number)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_verses_by_criteria(
        self,
        revelation_type: RevelationType | None = None,
        juz_number: int | None = None,
        hizb_number: int | None = None,
        manzil_number: int | None = None,
        has_sajdah: bool | None = None,
    ) -> list[Verse]:
        """Query verses by various criteria."""
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
        """Search for text within verses."""
        stmt = (
            select(VerseModel, SurahModel)
            .join(SurahModel, VerseModel.surah_number == SurahModel.id)
        )

        # Search in normalized text for better matching
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
        """Verify checksums of all stored data."""
        failed_verses: list[VerseLocation] = []
        total_verses = 0

        # Stream all verses and verify checksums
        async for verse in self.stream_verses():
            total_verses += 1
            if not verse.verify_integrity():
                failed_verses.append(verse.location)

        # Calculate overall checksum
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
            expected_checksum="",  # Would be set from config
            actual_checksum=actual_checksum.value,
            details=f"Verified {total_verses} verses, {len(failed_verses)} failures",
        )


class PostgresSurahMetadataRepository(ISurahMetadataRepository):
    """PostgreSQL implementation of ISurahMetadataRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _model_to_metadata(self, model: SurahModel) -> SurahMetadata:
        """Convert database model to domain value object."""
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
        """Get metadata for a specific surah."""
        stmt = select(SurahModel).where(SurahModel.id == surah_number)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise SurahNotFoundError(surah_number)
        return self._model_to_metadata(model)

    async def get_all_metadata(self) -> list[SurahMetadata]:
        """Get metadata for all 114 surahs."""
        stmt = select(SurahModel).order_by(SurahModel.id)
        result = await self._session.execute(stmt)
        return [self._model_to_metadata(m) for m in result.scalars().all()]

    async def get_meccan_surahs(self) -> list[SurahMetadata]:
        """Get metadata for all Meccan surahs."""
        stmt = (
            select(SurahModel)
            .where(SurahModel.revelation_type == RevelationType.MECCAN.value)
            .order_by(SurahModel.id)
        )
        result = await self._session.execute(stmt)
        return [self._model_to_metadata(m) for m in result.scalars().all()]

    async def get_medinan_surahs(self) -> list[SurahMetadata]:
        """Get metadata for all Medinan surahs."""
        stmt = (
            select(SurahModel)
            .where(SurahModel.revelation_type == RevelationType.MEDINAN.value)
            .order_by(SurahModel.id)
        )
        result = await self._session.execute(stmt)
        return [self._model_to_metadata(m) for m in result.scalars().all()]


class PostgresMorphologyRepository(IMorphologyRepository):
    """PostgreSQL implementation of IMorphologyRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _model_to_data(self, model: MorphologyModel) -> MorphologyData:
        """Convert database model to domain data object."""
        return MorphologyData(
            word_uthmani=model.word_uthmani,
            word_imlaei=model.word_imlaei,
            root=model.root,
            lemma=model.lemma,
            pattern=model.pattern,
            pos_tag=model.pos_tag,
            morpheme_type=model.morpheme_type,
            person=model.person,
            gender=model.gender,
            number=model.number,
            case_state=model.case_state,
            mood_voice=model.mood_voice,
            syntactic_role=model.syntactic_role,
            irab_description=model.irab_description,
        )

    async def get_word_morphology(
        self,
        location: VerseLocation,
        word_number: int,
    ) -> list[MorphologyData]:
        """Get morphological analysis for a word."""
        stmt = (
            select(MorphologyModel)
            .where(
                MorphologyModel.surah_number == location.surah_number,
                MorphologyModel.verse_number == location.verse_number,
                MorphologyModel.word_number == word_number,
            )
            .order_by(MorphologyModel.segment_number)
        )
        result = await self._session.execute(stmt)
        return [self._model_to_data(m) for m in result.scalars().all()]

    async def get_verse_morphology(
        self,
        location: VerseLocation,
    ) -> list[list[MorphologyData]]:
        """Get morphological analysis for all words in a verse."""
        stmt = (
            select(MorphologyModel)
            .where(
                MorphologyModel.surah_number == location.surah_number,
                MorphologyModel.verse_number == location.verse_number,
            )
            .order_by(MorphologyModel.word_number, MorphologyModel.segment_number)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        # Group by word number
        words: dict[int, list[MorphologyData]] = {}
        for model in models:
            word_num = model.word_number
            if word_num not in words:
                words[word_num] = []
            words[word_num].append(self._model_to_data(model))

        return [words[k] for k in sorted(words.keys())]

    async def search_by_root(self, root: str) -> list[tuple[VerseLocation, int]]:
        """Find all occurrences of a root in the Quran."""
        # Normalize root (remove dashes if present)
        normalized_root = root.replace("-", "").replace("ـ", "")

        stmt = (
            select(
                MorphologyModel.surah_number,
                MorphologyModel.verse_number,
                MorphologyModel.word_number,
            )
            .where(MorphologyModel.root == normalized_root)
            .distinct()
            .order_by(
                MorphologyModel.surah_number,
                MorphologyModel.verse_number,
                MorphologyModel.word_number,
            )
        )
        result = await self._session.execute(stmt)
        return [
            (VerseLocation(row[0], row[1]), row[2])
            for row in result.all()
        ]

    async def search_by_lemma(self, lemma: str) -> list[tuple[VerseLocation, int]]:
        """Find all occurrences of a lemma."""
        stmt = (
            select(
                MorphologyModel.surah_number,
                MorphologyModel.verse_number,
                MorphologyModel.word_number,
            )
            .where(MorphologyModel.lemma == lemma)
            .distinct()
            .order_by(
                MorphologyModel.surah_number,
                MorphologyModel.verse_number,
                MorphologyModel.word_number,
            )
        )
        result = await self._session.execute(stmt)
        return [
            (VerseLocation(row[0], row[1]), row[2])
            for row in result.all()
        ]

    async def get_root_frequency(self) -> dict[str, int]:
        """Get frequency distribution of all roots."""
        stmt = (
            select(
                MorphologyModel.root,
                func.count(MorphologyModel.id).label("count"),
            )
            .where(MorphologyModel.root.isnot(None))
            .group_by(MorphologyModel.root)
            .order_by(func.count(MorphologyModel.id).desc())
        )
        result = await self._session.execute(stmt)
        return {row[0]: row[1] for row in result.all() if row[0]}

    async def get_unique_roots(self) -> set[str]:
        """Get all unique roots in the Quran."""
        stmt = (
            select(MorphologyModel.root)
            .where(MorphologyModel.root.isnot(None))
            .distinct()
        )
        result = await self._session.execute(stmt)
        return {row[0] for row in result.all() if row[0]}
