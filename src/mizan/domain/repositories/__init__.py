"""Repository Interfaces (Ports) - Abstractions for data access."""

from mizan.domain.repositories.interfaces import (
    IntegrityReport,
    IMorphologyRepository,
    IQuranRepository,
    ISurahMetadataRepository,
    MorphologyData,
)

__all__ = [
    "IntegrityReport",
    "IMorphologyRepository",
    "IQuranRepository",
    "ISurahMetadataRepository",
    "MorphologyData",
]
