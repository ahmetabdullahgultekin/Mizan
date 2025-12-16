"""Analysis endpoints for counting, Abjad, and frequency operations."""

from fastapi import APIRouter, HTTPException, Path, Query

from mizan.api.dependencies import Analyzer
from mizan.application.dtos.requests import AbjadRequest, SearchRequest
from mizan.application.dtos.responses import (
    AbjadResponse,
    CountResponse,
    FrequencyResponse,
    SearchResponse,
)
from mizan.domain.enums import AbjadSystem, NormalizationLevel, ScriptType
from mizan.domain.exceptions import DomainException

router = APIRouter()


@router.get("/analysis/letters/count", response_model=CountResponse)
async def count_letters(
    analyzer: Analyzer,
    surah: int | None = Query(None, ge=1, le=114, description="Surah number"),
    verse: int | None = Query(None, ge=1, description="Verse number"),
    script: ScriptType = Query(ScriptType.UTHMANI, description="Script type"),
    count_alif_wasla: bool = Query(True, description="Count Alif Wasla"),
    count_alif_khanjariyya: bool = Query(True, description="Count Alif Khanjariyya"),
) -> CountResponse:
    """
    Count Arabic letters in specified scope.

    Scope can be:
    - Entire Quran (no parameters)
    - Single surah (surah only)
    - Single verse (surah and verse)
    """
    try:
        result = await analyzer.count_letters(
            surah_number=surah,
            verse_number=verse,
            script_type=script,
            count_alif_wasla=count_alif_wasla,
            count_alif_khanjariyya=count_alif_khanjariyya,
        )
        return CountResponse(
            count_type="letters",
            count=result["count"],
            scope=result["scope"],
            methodology=result["methodology"],
        )
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analysis/words/count", response_model=CountResponse)
async def count_words(
    analyzer: Analyzer,
    surah: int | None = Query(None, ge=1, le=114),
    verse: int | None = Query(None, ge=1),
    script: ScriptType = Query(ScriptType.UTHMANI),
) -> CountResponse:
    """
    Count words in specified scope.

    Returns count with full methodology documentation.
    """
    try:
        result = await analyzer.count_words(
            surah_number=surah,
            verse_number=verse,
            script_type=script,
        )
        return CountResponse(
            count_type="words",
            count=result["count"],
            scope=result["scope"],
            methodology=result["methodology"],
        )
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analysis/abjad", response_model=AbjadResponse)
async def calculate_abjad(
    analyzer: Analyzer,
    text: str | None = Query(None, description="Text to calculate"),
    surah: int | None = Query(None, ge=1, le=114),
    verse: int | None = Query(None, ge=1),
    system: str = Query("mashriqi", pattern="^(mashriqi|maghribi)$"),
    include_breakdown: bool = Query(False),
) -> AbjadResponse:
    """
    Calculate Abjad (gematria) value.

    Supports both Mashriqi (Eastern) and Maghribi (Western) systems.
    """
    try:
        abjad_system = AbjadSystem(system)
        result = await analyzer.calculate_abjad(
            text=text,
            surah_number=surah,
            verse_number=verse,
            system=abjad_system,
            include_breakdown=include_breakdown,
        )
        return AbjadResponse(
            value=result["value"],
            system=system,
            text_analyzed=text or f"Surah {surah}" + (f":{verse}" if verse else ""),
            breakdown=result.get("breakdown"),
            is_prime=result["is_prime"],
            digital_root=result["digital_root"],
        )
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analysis/letters/frequency", response_model=FrequencyResponse)
async def get_letter_frequency(
    analyzer: Analyzer,
    surah: int | None = Query(None, ge=1, le=114),
    verse: int | None = Query(None, ge=1),
    script: ScriptType = Query(ScriptType.UTHMANI),
    normalize_variants: bool = Query(True, description="Group letter variants"),
) -> FrequencyResponse:
    """
    Get letter frequency distribution.

    Returns count for each Arabic letter.
    """
    try:
        result = await analyzer.get_letter_frequency(
            surah_number=surah,
            verse_number=verse,
            script_type=script,
            normalize_variants=normalize_variants,
        )
        return FrequencyResponse(
            frequency_type="letters",
            total_items=result["total_letters"],
            unique_items=result["unique_letters"],
            distribution=result["frequency"],
            top_items=result["top_10"],
        )
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search")
async def search_quran(
    analyzer: Analyzer,
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    surah: int | None = Query(None, ge=1, le=114),
    normalization: NormalizationLevel = Query(NormalizationLevel.FULL),
    limit: int = Query(100, ge=1, le=1000),
) -> dict:
    """
    Search for text in the Quran.

    Supports various normalization levels for flexible matching.
    """
    try:
        result = await analyzer.search_text(
            query=q,
            surah_number=surah,
            normalization=normalization,
            limit=limit,
        )
        return result
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analysis/verse/{surah}/{verse}")
async def analyze_verse(
    analyzer: Analyzer,
    surah: int = Path(..., ge=1, le=114),
    verse: int = Path(..., ge=1),
) -> dict:
    """
    Get complete analysis for a single verse.

    Returns letter count, word count, Abjad value, and frequency.
    """
    try:
        # Get all analyses in parallel
        letter_result = await analyzer.count_letters(surah, verse)
        word_result = await analyzer.count_words(surah, verse)
        abjad_result = await analyzer.calculate_abjad(
            surah_number=surah,
            verse_number=verse,
            include_breakdown=True,
        )
        frequency_result = await analyzer.get_letter_frequency(surah, verse)

        return {
            "location": f"{surah}:{verse}",
            "letters": letter_result,
            "words": word_result,
            "abjad": abjad_result,
            "letter_frequency": frequency_result,
        }
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
