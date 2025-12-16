"""Response DTOs for API endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    database: bool = Field(..., description="Database connectivity")
    cache: bool = Field(..., description="Cache connectivity")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response format."""

    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(None, description="Additional details")


class VerseResponse(BaseModel):
    """Single verse response."""

    surah_number: int
    verse_number: int
    text_uthmani: str
    text_simple: str | None = None

    # Metadata
    juz_number: int
    hizb_number: int
    manzil_number: int
    page_number: int
    ruku_number: int

    # Sajdah info
    is_sajdah: bool
    sajdah_type: str | None = None

    # Pre-computed values
    word_count: int
    letter_count: int
    abjad_value: int

    # Surah info
    surah_name_arabic: str
    surah_name_english: str


class SurahResponse(BaseModel):
    """Surah metadata response."""

    number: int
    name_arabic: str
    name_english: str
    name_transliteration: str
    revelation_type: str
    revelation_order: int
    verse_count: int
    word_count: int
    letter_count: int
    ruku_count: int


class SurahDetailResponse(SurahResponse):
    """Surah with verses response."""

    verses: list[VerseResponse]


class SearchResultItem(BaseModel):
    """Single search result."""

    surah_number: int
    verse_number: int
    text: str
    match_positions: list[tuple[int, int]] = Field(
        default_factory=list,
        description="Start/end positions of matches",
    )
    context_before: str = ""
    context_after: str = ""


class SearchResponse(BaseModel):
    """Search results response."""

    query: str
    total_results: int
    results: list[SearchResultItem]
    methodology: str = Field(
        ...,
        description="Search methodology used",
    )


class AnalysisResponse(BaseModel):
    """Analysis result response."""

    analysis_type: str
    scope: dict[str, Any]
    result: dict[str, Any]
    methodology: str
    computed_at: datetime = Field(default_factory=datetime.utcnow)


class CountResponse(BaseModel):
    """Count result response."""

    count_type: str  # "letters", "words", "verses"
    count: int
    scope: dict[str, Any]
    methodology: str
    breakdown: dict[str, int] | None = None


class AbjadResponse(BaseModel):
    """Abjad calculation response."""

    value: int
    system: str
    text_analyzed: str
    breakdown: list[dict[str, Any]] | None = None
    is_prime: bool
    digital_root: int


class FrequencyResponse(BaseModel):
    """Frequency distribution response."""

    frequency_type: str  # "letters", "words", "roots"
    total_items: int
    unique_items: int
    distribution: dict[str, int]
    top_items: list[tuple[str, int]]


class IntegrityResponse(BaseModel):
    """Integrity verification response."""

    is_valid: bool
    checked_at: datetime
    total_verses: int
    failed_count: int
    details: str
