"""Data Transfer Objects for API requests and responses."""

from mizan.application.dtos.requests import (
    AnalysisRequest,
    SearchRequest,
    UnifiedAnalysisRequest,
    VerseRangeRequest,
)
from mizan.application.dtos.responses import (
    AnalysisResponse,
    ErrorResponse,
    HealthResponse,
    SearchResponse,
    SurahResponse,
    UnifiedAnalysisResponse,
    VerseResponse,
)

__all__ = [
    # Requests
    "AnalysisRequest",
    "SearchRequest",
    "UnifiedAnalysisRequest",
    "VerseRangeRequest",
    # Responses
    "AnalysisResponse",
    "ErrorResponse",
    "HealthResponse",
    "SearchResponse",
    "SurahResponse",
    "UnifiedAnalysisResponse",
    "VerseResponse",
]
