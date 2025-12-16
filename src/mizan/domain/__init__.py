"""
Domain Layer - Pure business logic with zero external dependencies.

This layer contains:
- Entities: Core domain objects (Verse, Surah)
- Value Objects: Immutable domain primitives (VerseLocation, AbjadValue)
- Enumerations: Domain-specific type definitions
- Services: Domain operations (LetterCounter, AbjadCalculator)
- Repository Interfaces: Ports for data access
- Exceptions: Domain-specific error types
"""

from mizan.domain.entities import Surah, Verse
from mizan.domain.enums import (
    AbjadSystem,
    AnalysisType,
    BasmalahStatus,
    MushafEdition,
    NormalizationLevel,
    QiraatType,
    RevelationType,
    SajdahType,
    ScriptType,
    WordFormInclusion,
)
from mizan.domain.exceptions import (
    DomainException,
    IntegrityViolationError,
    InvalidVerseLocationError,
    VerseNotFoundError,
)
from mizan.domain.repositories import (
    IMorphologyRepository,
    IQuranRepository,
    ISurahMetadataRepository,
    IntegrityReport,
)
from mizan.domain.services import (
    AbjadCalculator,
    LetterCounter,
    WordCounter,
)
from mizan.domain.value_objects import (
    AbjadValue,
    SurahMetadata,
    TextChecksum,
    VerseLocation,
)

__all__ = [
    # Entities
    "Surah",
    "Verse",
    # Enumerations
    "AbjadSystem",
    "AnalysisType",
    "BasmalahStatus",
    "MushafEdition",
    "NormalizationLevel",
    "QiraatType",
    "RevelationType",
    "SajdahType",
    "ScriptType",
    "WordFormInclusion",
    # Value Objects
    "AbjadValue",
    "SurahMetadata",
    "TextChecksum",
    "VerseLocation",
    # Repository Interfaces
    "IMorphologyRepository",
    "IQuranRepository",
    "ISurahMetadataRepository",
    "IntegrityReport",
    # Services
    "AbjadCalculator",
    "LetterCounter",
    "WordCounter",
    # Exceptions
    "DomainException",
    "IntegrityViolationError",
    "InvalidVerseLocationError",
    "VerseNotFoundError",
]
