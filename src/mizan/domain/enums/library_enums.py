"""
Enumerations for the Islamic Knowledge Library system.
"""

from enum import Enum


class SourceType(str, Enum):
    """Type of Islamic text source."""

    QURAN = "QURAN"
    TAFSIR = "TAFSIR"
    HADITH = "HADITH"
    OTHER = "OTHER"


class IndexingStatus(str, Enum):
    """Status of the indexing/embedding process for a text source."""

    PENDING = "PENDING"
    INDEXING = "INDEXING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class EmbeddingProvider(str, Enum):
    """Supported embedding providers."""

    LOCAL = "local"
    GEMINI = "gemini"
