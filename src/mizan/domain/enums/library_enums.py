"""
Enumerations for the Islamic Knowledge Library system.
"""

from enum import StrEnum


class SourceType(StrEnum):
    """Type of Islamic text source."""

    QURAN = "QURAN"
    TAFSIR = "TAFSIR"
    HADITH = "HADITH"
    OTHER = "OTHER"


class IndexingStatus(StrEnum):
    """Status of the indexing/embedding process for a text source."""

    PENDING = "PENDING"
    INDEXING = "INDEXING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class EmbeddingProvider(StrEnum):
    """Supported embedding providers."""

    LOCAL = "local"
    GEMINI = "gemini"
