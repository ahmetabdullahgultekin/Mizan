"""Verse and Surah endpoints."""

from fastapi import APIRouter, HTTPException, Path, Query

from mizan.api.dependencies import Analyzer, QuranRepo, SurahRepo
from mizan.application.dtos.responses import (
    SurahDetailResponse,
    SurahResponse,
    VerseResponse,
)
from mizan.domain.enums import RevelationType, ScriptType
from mizan.domain.exceptions import SurahNotFoundError, VerseNotFoundError
from mizan.domain.value_objects import VerseLocation

router = APIRouter()


@router.get("/verses/{surah}/{verse}", response_model=VerseResponse)
async def get_verse(
    analyzer: Analyzer,
    surah: int = Path(..., ge=1, le=114, description="Surah number"),
    verse: int = Path(..., ge=1, description="Verse number"),
) -> VerseResponse:
    """
    Get a single verse with all metadata.

    Returns verse text, structural information, and pre-computed values.
    """
    try:
        result = await analyzer.get_verse(surah, verse)
        return VerseResponse(**result)
    except VerseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/surahs", response_model=list[SurahResponse])
async def list_surahs(
    surah_repo: SurahRepo,
    revelation_type: RevelationType | None = Query(None, description="Filter by revelation type"),
) -> list[SurahResponse]:
    """
    List all surahs with metadata.

    Optionally filter by revelation type (Meccan/Medinan).
    """
    if revelation_type == RevelationType.MECCAN:
        metadata_list = await surah_repo.get_meccan_surahs()
    elif revelation_type == RevelationType.MEDINAN:
        metadata_list = await surah_repo.get_medinan_surahs()
    else:
        metadata_list = await surah_repo.get_all_metadata()

    return [
        SurahResponse(
            number=m.number,
            name_arabic=m.name_arabic,
            name_english=m.name_english,
            name_transliteration=m.name_transliteration,
            revelation_type=m.revelation_type.value,
            revelation_order=m.revelation_order,
            verse_count=m.verse_count,
            word_count=m.word_count,
            letter_count=m.letter_count,
            ruku_count=m.ruku_count,
        )
        for m in metadata_list
    ]


@router.get("/surahs/{surah_number}", response_model=SurahResponse)
async def get_surah(
    surah_repo: SurahRepo,
    surah_number: int = Path(..., ge=1, le=114),
) -> SurahResponse:
    """Get metadata for a specific surah."""
    try:
        m = await surah_repo.get_metadata(surah_number)
        return SurahResponse(
            number=m.number,
            name_arabic=m.name_arabic,
            name_english=m.name_english,
            name_transliteration=m.name_transliteration,
            revelation_type=m.revelation_type.value,
            revelation_order=m.revelation_order,
            verse_count=m.verse_count,
            word_count=m.word_count,
            letter_count=m.letter_count,
            ruku_count=m.ruku_count,
        )
    except SurahNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/surahs/{surah_number}/verses")
async def get_surah_verses(
    quran_repo: QuranRepo,
    surah_number: int = Path(..., ge=1, le=114),
    script: ScriptType = Query(ScriptType.UTHMANI, description="Script type"),
) -> dict:
    """
    Get all verses for a surah.

    Returns basic verse data for the entire surah.
    """
    try:
        surah = await quran_repo.get_surah(surah_number)
        return {
            "surah_number": surah.number,
            "surah_name": surah.name_arabic,
            "verse_count": surah.verse_count,
            "verses": [
                {
                    "number": v.verse_number,
                    "text": v.get_text(script),
                    "word_count": v.word_count,
                    "letter_count": v.letter_count,
                }
                for v in surah.verses
            ],
        }
    except SurahNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/juz/{juz_number}/verses")
async def get_juz_verses(
    quran_repo: QuranRepo,
    juz_number: int = Path(..., ge=1, le=30, description="Juz number"),
) -> dict:
    """
    Get all verses in a Juz (part).

    Returns verses grouped by the specified Juz.
    """
    verses = await quran_repo.get_verses_by_criteria(juz_number=juz_number)

    return {
        "juz_number": juz_number,
        "verse_count": len(verses),
        "verses": [
            {
                "surah": v.surah_number,
                "verse": v.verse_number,
                "text": v.text_uthmani,
            }
            for v in verses
        ],
    }


@router.get("/sajdah/verses")
async def get_sajdah_verses(
    quran_repo: QuranRepo,
) -> dict:
    """
    Get all verses with prostration marks.

    Returns the 15 Sajdah verses in the Quran.
    """
    verses = await quran_repo.get_verses_by_criteria(has_sajdah=True)

    return {
        "total": len(verses),
        "verses": [
            {
                "surah": v.surah_number,
                "verse": v.verse_number,
                "text": v.text_uthmani,
                "sajdah_type": v.sajdah_type.value if v.sajdah_type else None,
                "surah_name": v.surah_metadata.name_arabic,
            }
            for v in verses
        ],
    }
