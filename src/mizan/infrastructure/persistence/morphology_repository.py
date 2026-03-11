"""
PostgreSQL implementation of IMorphologyRepository.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mizan.domain.repositories import IMorphologyRepository, MorphologyData
from mizan.domain.value_objects import VerseLocation
from mizan.infrastructure.persistence.models import MorphologyModel


class PostgresMorphologyRepository(IMorphologyRepository):
    """PostgreSQL implementation of IMorphologyRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _model_to_data(self, model: MorphologyModel) -> MorphologyData:
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

        words: dict[int, list[MorphologyData]] = {}
        for model in models:
            word_num = model.word_number
            if word_num not in words:
                words[word_num] = []
            words[word_num].append(self._model_to_data(model))
        return [words[k] for k in sorted(words.keys())]

    async def search_by_root(self, root: str) -> list[tuple[VerseLocation, int]]:
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
        return [(VerseLocation(row[0], row[1]), row[2]) for row in result.all()]

    async def search_by_lemma(self, lemma: str) -> list[tuple[VerseLocation, int]]:
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
        return [(VerseLocation(row[0], row[1]), row[2]) for row in result.all()]

    async def get_root_frequency(self) -> dict[str, int]:
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
        stmt = (
            select(MorphologyModel.root)
            .where(MorphologyModel.root.isnot(None))
            .distinct()
        )
        result = await self._session.execute(stmt)
        return {row[0] for row in result.all() if row[0]}
