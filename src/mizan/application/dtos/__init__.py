"""Data Transfer Objects for API requests and responses."""

from mizan.application.dtos.requests import (
    AnalysisRequest,
    SearchRequest,
    VerseRangeRequest,
)
from mizan.application.dtos.responses import (
    AnalysisResponse,
    ErrorResponse,
    HealthResponse,
    SearchResponse,
    SurahResponse,
    VerseResponse,
)

__all__ = [
    # Requests
    "AnalysisRequest",
    "SearchRequest",
    "VerseRangeRequest",
    # Responses
    "AnalysisResponse",
    "ErrorResponse",
    "HealthResponse",
    "SearchResponse",
    "SurahResponse",
    "VerseResponse",
]
