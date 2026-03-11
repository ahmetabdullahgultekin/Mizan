"""Analysis endpoints for counting, Abjad, and frequency operations."""

import asyncio

import structlog
from fastapi import APIRouter, HTTPException, Path, Query

from mizan.api.dependencies import Analyzer
from mizan.application.dtos.requests import AbjadRequest, SearchRequest
from mizan.application.dtos.responses import (
    AbjadBreakdownItem,
    AbjadResponse,
    CountResponse,
    FrequencyItemResponse,
    FrequencyResponse,
    SearchResponse,
    VerseAbjadResponse,
    VerseAnalysisResponse,
    VerseFrequencyResponse,
    VerseLettersResponse,
    VerseWordsResponse,
)
from mizan.domain.enums import AbjadSystem, NormalizationLevel, ScriptType
from mizan.domain.exceptions import DomainException

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/analysis/letters/count", response_model=CountResponse)
async def count_letters(
    analyzer: Analyzer,
    surah: int | None = Query(None, ge=1, le=114, description="Surah number"),
    verse: int | None = Query(None, ge=1, description="Verse number"),
    script: ScriptType = Query(ScriptType.UTHMANI, description="Script type"),
    count_alif_wasla: bool = Query(True, description="Count Alif Wasla"),
    count_alif_khanjariyya: bool = Query(True, description="Count Alif Khanjariyya"),
    text: str | None = Query(None, max_length=10000, description="Arbitrary text to count"),
) -> CountResponse:
    """
    Count Arabic letters in specified scope.

    Scope can be:
    - Arbitrary text (text parameter)
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
            text=text,
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
    text: str | None = Query(None, max_length=10000, description="Arbitrary text to count"),
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
            text=text,
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
            text_analyzed=result.get("text_analyzed", text or f"Surah {surah}" + (f":{verse}" if verse else "")),
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
        top_items = [FrequencyItemResponse(**item) for item in result["top_items"]]
        return FrequencyResponse(
            frequency_type="letters",
            total_items=result["total_items"],
            unique_items=result["unique_items"],
            distribution=result["distribution"],
            top_items=top_items,
        )
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search", response_model=SearchResponse)
async def search_quran(
    analyzer: Analyzer,
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    surah: int | None = Query(None, ge=1, le=114),
    normalization: NormalizationLevel = Query(NormalizationLevel.FULL),
    limit: int = Query(100, ge=1, le=1000),
) -> SearchResponse:
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
        return SearchResponse(
            query=result["query"],
            total_results=result["total_results"],
            results=result["results"],
            methodology=result["methodology"],
        )
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analysis/verse/{surah}/{verse}", response_model=VerseAnalysisResponse)
async def analyze_verse(
    analyzer: Analyzer,
    surah: int = Path(..., ge=1, le=114),
    verse: int = Path(..., ge=1),
) -> VerseAnalysisResponse:
    """
    Get complete analysis for a single verse.

    Returns letter count, word count, Abjad value, and frequency.
    All sub-analyses run in parallel for optimal performance.
    """
    try:
        letter_result, word_result, abjad_result, frequency_result = await asyncio.gather(
            analyzer.count_letters(surah_number=surah, verse_number=verse),
            analyzer.count_words(surah_number=surah, verse_number=verse),
            analyzer.calculate_abjad(
                surah_number=surah,
                verse_number=verse,
                include_breakdown=True,
            ),
            analyzer.get_letter_frequency(surah_number=surah, verse_number=verse),
        )

        abjad_breakdown = None
        if abjad_result.get("breakdown"):
            abjad_breakdown = [
                AbjadBreakdownItem(
                    letter=item["letter"],
                    abjad_value=item["abjad_value"],
                )
                for item in abjad_result["breakdown"]
            ]

        top_items = [FrequencyItemResponse(**item) for item in frequency_result["top_items"]]

        return VerseAnalysisResponse(
            location=f"{surah}:{verse}",
            letters=VerseLettersResponse(
                count=letter_result["count"],
                scope=letter_result["scope"],
                methodology=letter_result["methodology"],
            ),
            words=VerseWordsResponse(
                count=word_result["count"],
                scope=word_result["scope"],
                methodology=word_result["methodology"],
            ),
            abjad=VerseAbjadResponse(
                value=abjad_result["value"],
                system=abjad_result["system"],
                text_analyzed=abjad_result.get("text_analyzed", f"{surah}:{verse}"),
                is_prime=abjad_result["is_prime"],
                digital_root=abjad_result["digital_root"],
                breakdown=abjad_breakdown,
            ),
            letter_frequency=VerseFrequencyResponse(
                total_items=frequency_result["total_items"],
                unique_items=frequency_result["unique_items"],
                distribution=frequency_result["distribution"],
                top_items=top_items,
            ),
        )
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
