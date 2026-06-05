"""
Unit tests for the morphology `data_status` / `preview` flag.

Morphology endpoints return null root/lemma/pattern until the Quranic Arabic
Corpus (QAC/MASAQ) dataset is ingested. Every response must self-describe as
"preview" in that state so empty linguistic fields are not mistaken for verified
"this word has no root" output, and must flip to "complete" once roots exist.

The router functions are exercised directly with a mocked repository so these
tests need no FastAPI app, database, or data files.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from mizan.api.routers import morphology
from mizan.domain.repositories.interfaces import MorphologyData


def _seg(root: str | None = None, lemma: str | None = None) -> MorphologyData:
    return MorphologyData(
        word_uthmani="ٱللَّهُ",
        word_imlaei="الله",
        root=root,
        lemma=lemma,
        pattern=None,
        pos_tag="N",
        morpheme_type="STEM",
        person=None,
        gender=None,
        number=None,
        case_state=None,
        mood_voice=None,
        syntactic_role=None,
        irab_description=None,
    )


@pytest.mark.asyncio
async def test_verse_morphology_flags_preview_when_no_roots():
    repo = MagicMock()
    # Two words, segments present but no root/lemma → preview.
    repo.get_verse_morphology = AsyncMock(return_value=[[_seg()], [_seg()]])

    resp = await morphology.get_verse_morphology(repo, surah=2, verse=255)

    assert resp["data_status"] == "preview"
    assert resp["preview"] is True
    assert "note" in resp
    assert resp["word_count"] == 2


@pytest.mark.asyncio
async def test_verse_morphology_flags_complete_when_roots_present():
    repo = MagicMock()
    repo.get_verse_morphology = AsyncMock(return_value=[[_seg(root="ولد")]])

    resp = await morphology.get_verse_morphology(repo, surah=19, verse=1)

    assert resp["data_status"] == "complete"
    assert resp["preview"] is False
    assert "note" not in resp


@pytest.mark.asyncio
async def test_word_morphology_flags_preview_when_no_roots():
    repo = MagicMock()
    repo.get_word_morphology = AsyncMock(return_value=[_seg()])

    resp = await morphology.get_word_morphology(repo, surah=2, verse=255, word=1)

    assert resp["data_status"] == "preview"
    assert resp["preview"] is True


@pytest.mark.asyncio
async def test_root_search_flags_preview_when_empty():
    repo = MagicMock()
    repo.search_by_root = AsyncMock(return_value=[])

    resp = await morphology.search_by_root(repo, root="كتب", limit=100)

    assert resp["data_status"] == "preview"
    assert resp["total_occurrences"] == 0


@pytest.mark.asyncio
async def test_root_frequency_flags_preview_when_empty():
    repo = MagicMock()
    repo.get_root_frequency = AsyncMock(return_value={})

    resp = await morphology.get_root_frequency(repo, limit=50)

    assert resp["data_status"] == "preview"
    assert resp["total_unique_roots"] == 0


@pytest.mark.asyncio
async def test_root_frequency_flags_complete_when_data_present():
    repo = MagicMock()
    repo.get_root_frequency = AsyncMock(return_value={"ولد": 3, "صبر": 2})

    resp = await morphology.get_root_frequency(repo, limit=50)

    assert resp["data_status"] == "complete"
    assert resp["preview"] is False
    assert resp["total_unique_roots"] == 2
