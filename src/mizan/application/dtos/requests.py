"""Request DTOs for API endpoints."""

from pydantic import BaseModel, Field, field_validator

from mizan.domain.enums import (
    AnalysisType,
    NormalizationLevel,
    ScriptType,
    WordFormInclusion,
)


class VerseRangeRequest(BaseModel):
    """Request for a range of verses."""

    start_surah: int = Field(..., ge=1, le=114, description="Starting surah number")
    start_verse: int = Field(..., ge=1, description="Starting verse number")
    end_surah: int = Field(..., ge=1, le=114, description="Ending surah number")
    end_verse: int = Field(..., ge=1, description="Ending verse number")

    @field_validator("end_surah")
    @classmethod
    def validate_range(cls, v: int, info) -> int:
        """Ensure end is not before start."""
        start_surah = info.data.get("start_surah")
        if start_surah and v < start_surah:
            raise ValueError("End surah cannot be before start surah")
        return v


class SearchRequest(BaseModel):
    """Request for text search."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    surah_number: int | None = Field(None, ge=1, le=114, description="Filter by surah")
    normalization: NormalizationLevel = Field(
        default=NormalizationLevel.FULL,
        description="Normalization level for matching",
    )
    word_form: WordFormInclusion = Field(
        default=WordFormInclusion.EXACT_ONLY,
        description="Word form matching mode",
    )
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Results offset")


class AnalysisRequest(BaseModel):
    """Request for text analysis."""

    # Scope
    surah_number: int | None = Field(None, ge=1, le=114)
    verse_number: int | None = Field(None, ge=1)
    start_surah: int | None = Field(None, ge=1, le=114)
    start_verse: int | None = Field(None, ge=1)
    end_surah: int | None = Field(None, ge=1, le=114)
    end_verse: int | None = Field(None, ge=1)

    # Analysis configuration
    analysis_type: AnalysisType = Field(..., description="Type of analysis")
    script_type: ScriptType = Field(
        default=ScriptType.UTHMANI,
        description="Script type to analyze",
    )
    normalization: NormalizationLevel = Field(
        default=NormalizationLevel.NONE,
        description="Normalization before analysis",
    )

    # Optional parameters
    include_basmalah: bool = Field(
        default=True,
        description="Include Basmalah in counts",
    )
    count_alif_wasla: bool = Field(
        default=True,
        description="Count Alif Wasla as letter",
    )
    count_alif_khanjariyya: bool = Field(
        default=True,
        description="Count Alif Khanjariyya as letter",
    )

    @field_validator("verse_number")
    @classmethod
    def validate_verse_requires_surah(cls, v: int | None, info) -> int | None:
        """Ensure verse_number requires surah_number."""
        if v is not None and info.data.get("surah_number") is None:
            raise ValueError("verse_number requires surah_number")
        return v

    model_config = {"use_enum_values": True}


class CountRequest(BaseModel):
    """Simple count request for a scope."""

    surah_number: int | None = Field(None, ge=1, le=114)
    verse_number: int | None = Field(None, ge=1)
    script_type: ScriptType = Field(default=ScriptType.UTHMANI)
    count_alif_wasla: bool = Field(default=True)
    count_alif_khanjariyya: bool = Field(default=True)


class AbjadRequest(BaseModel):
    """Request for Abjad calculation."""

    text: str | None = Field(None, description="Text to calculate (or use scope)")
    surah_number: int | None = Field(None, ge=1, le=114)
    verse_number: int | None = Field(None, ge=1)
    system: str = Field(default="mashriqi", pattern="^(mashriqi|maghribi)$")
    include_breakdown: bool = Field(default=False)
