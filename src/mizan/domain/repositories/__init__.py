"""Repository Interfaces (Ports) - Abstractions for data access."""

from mizan.domain.repositories.interfaces import (
    IntegrityReport,
    IMorphologyRepository,
    IQuranRepository,
    ISurahMetadataRepository,
    MorphologyData,
)
from mizan.domain.repositories.library_interfaces import (
    ILibrarySpaceRepository,
    ITextChunkRepository,
    ITextSourceRepository,
    IVerseEmbeddingRepository,
)

__all__ = [
    "IntegrityReport",
    "IMorphologyRepository",
    "IQuranRepository",
    "ISurahMetadataRepository",
    "MorphologyData",
    "ILibrarySpaceRepository",
    "ITextChunkRepository",
    "ITextSourceRepository",
    "IVerseEmbeddingRepository",
]
