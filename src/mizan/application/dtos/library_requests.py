"""
Pydantic request models for the Library and Semantic Search API.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from mizan.domain.enums.library_enums import SourceType


class CreateLibrarySpaceRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Library name")
    description: str | None = Field(None, description="Optional description")


class AddTextSourceRequest(BaseModel):
    source_type: SourceType = Field(..., description="Type of Islamic text")
    title_arabic: str = Field(..., min_length=1, max_length=500)
    title_turkish: str | None = Field(None, max_length=500)
    title_english: str | None = Field(None, max_length=500)
    author: str | None = Field(None, max_length=300)
    content: str = Field(
        ...,
        min_length=1,
        description="Full text content to index",
    )


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="Search query")
    library_space_id: UUID | None = Field(
        None, description="Restrict search to a specific library (optional)"
    )
    source_types: list[SourceType] | None = Field(
        None, description="Filter by source type(s) (optional)"
    )
    limit: int = Field(default=10, ge=1, le=100, description="Max results")
    min_similarity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity threshold",
    )
