"""
Pydantic response models for the Library and Semantic Search API.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from mizan.domain.enums.library_enums import IndexingStatus, SourceType


class LibrarySpaceResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TextSourceResponse(BaseModel):
    id: UUID
    library_space_id: UUID
    source_type: SourceType
    title_arabic: str
    title_turkish: str | None
    title_english: str | None
    author: str | None
    status: IndexingStatus
    total_chunks: int
    indexed_chunks: int
    indexing_progress: float
    embedding_model: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SemanticSearchResultResponse(BaseModel):
    chunk_id: UUID
    text_source_id: UUID
    source_title: str
    source_type: SourceType
    reference: str
    content: str
    similarity_score: float
    metadata: dict

    model_config = {"from_attributes": True}


class SemanticSearchResponse(BaseModel):
    query: str
    results: list[SemanticSearchResultResponse]
    total_results: int
    embedding_model: str


class SimilarVerseResponse(BaseModel):
    surah_number: int
    verse_number: int
    similarity_score: float


class VerseEmbeddingStatsResponse(BaseModel):
    total_embeddings: int
    model_name: str | None
