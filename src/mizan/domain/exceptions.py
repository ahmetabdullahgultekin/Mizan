"""
Domain exceptions - Business rule violation errors.

All domain exceptions inherit from DomainException for easy catching.
These exceptions are raised when business rules are violated.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mizan.domain.value_objects import TextChecksum, VerseLocation


class DomainException(Exception):
    """
    Base exception for all domain-level errors.

    All domain exceptions should inherit from this class.
    This allows catching all domain errors with a single except clause.
    """

    def __init__(self, message: str, code: str | None = None) -> None:
        """
        Initialize domain exception.

        Args:
            message: Human-readable error message
            code: Machine-readable error code for API responses
        """
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__

    def __str__(self) -> str:
        """Return error message."""
        return self.message

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for API responses."""
        return {
            "error": self.code,
            "message": self.message,
        }


# =============================================================================
# Verse-Related Exceptions
# =============================================================================


class VerseNotFoundError(DomainException):
    """Raised when a requested verse does not exist."""

    def __init__(self, location: VerseLocation) -> None:
        """
        Initialize verse not found error.

        Args:
            location: The verse location that was not found
        """
        self.location = location
        super().__init__(
            message=f"Verse not found: {location}",
            code="VERSE_NOT_FOUND",
        )


class InvalidVerseLocationError(DomainException):
    """Raised when a verse location is invalid."""

    def __init__(self, surah: int, verse: int, reason: str | None = None) -> None:
        """
        Initialize invalid verse location error.

        Args:
            surah: The surah number
            verse: The verse number
            reason: Additional reason for invalidity
        """
        self.surah = surah
        self.verse = verse
        self.reason = reason

        message = f"Invalid verse location: {surah}:{verse}"
        if reason:
            message += f" - {reason}"

        super().__init__(message=message, code="INVALID_VERSE_LOCATION")


class VerseRangeError(DomainException):
    """Raised when a verse range is invalid."""

    def __init__(
        self,
        start: VerseLocation,
        end: VerseLocation,
        reason: str | None = None,
    ) -> None:
        """
        Initialize verse range error.

        Args:
            start: Start of the range
            end: End of the range
            reason: Additional reason for invalidity
        """
        self.start = start
        self.end = end
        self.reason = reason

        message = f"Invalid verse range: {start} to {end}"
        if reason:
            message += f" - {reason}"

        super().__init__(message=message, code="INVALID_VERSE_RANGE")


# =============================================================================
# Surah-Related Exceptions
# =============================================================================


class SurahNotFoundError(DomainException):
    """Raised when a requested surah does not exist."""

    def __init__(self, surah_number: int) -> None:
        """
        Initialize surah not found error.

        Args:
            surah_number: The surah number that was not found
        """
        self.surah_number = surah_number
        super().__init__(
            message=f"Surah not found: {surah_number}",
            code="SURAH_NOT_FOUND",
        )


class InvalidSurahNumberError(DomainException):
    """Raised when a surah number is invalid (not 1-114)."""

    def __init__(self, surah_number: int) -> None:
        """
        Initialize invalid surah number error.

        Args:
            surah_number: The invalid surah number
        """
        self.surah_number = surah_number
        super().__init__(
            message=f"Invalid surah number: {surah_number}. Must be between 1 and 114.",
            code="INVALID_SURAH_NUMBER",
        )


# =============================================================================
# Integrity-Related Exceptions
# =============================================================================


class IntegrityViolationError(DomainException):
    """
    Raised when data integrity check fails.

    This is a critical error indicating potential data corruption.
    The system should halt when this occurs.
    """

    def __init__(
        self,
        expected: TextChecksum,
        actual: TextChecksum,
        context: str | None = None,
    ) -> None:
        """
        Initialize integrity violation error.

        Args:
            expected: Expected checksum
            actual: Actual computed checksum
            context: Additional context (e.g., which verse/surah)
        """
        self.expected = expected
        self.actual = actual
        self.context = context

        message = (
            f"CRITICAL: Data integrity violation detected. "
            f"Expected checksum: {expected.value[:16]}..., "
            f"Actual: {actual.value[:16]}..."
        )
        if context:
            message += f" Context: {context}"

        super().__init__(message=message, code="INTEGRITY_VIOLATION")


class ChecksumMismatchError(DomainException):
    """Raised when a checksum verification fails."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        """
        Initialize checksum mismatch error.

        Args:
            entity_type: Type of entity (e.g., "verse", "surah")
            entity_id: Identifier of the entity
        """
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(
            message=f"Checksum mismatch for {entity_type}: {entity_id}",
            code="CHECKSUM_MISMATCH",
        )


# =============================================================================
# Analysis-Related Exceptions
# =============================================================================


class AnalysisConfigurationError(DomainException):
    """Raised when analysis is configured incorrectly."""

    def __init__(self, parameter: str, value: str, reason: str) -> None:
        """
        Initialize analysis configuration error.

        Args:
            parameter: The misconfigured parameter name
            value: The invalid value
            reason: Why the value is invalid
        """
        self.parameter = parameter
        self.value = value
        self.reason = reason
        super().__init__(
            message=f"Invalid analysis configuration: {parameter}={value}. {reason}",
            code="ANALYSIS_CONFIG_ERROR",
        )


class UnsupportedAnalysisError(DomainException):
    """Raised when an unsupported analysis type is requested."""

    def __init__(self, analysis_type: str, tier: int | None = None) -> None:
        """
        Initialize unsupported analysis error.

        Args:
            analysis_type: The requested analysis type
            tier: The tier this analysis belongs to (if experimental)
        """
        self.analysis_type = analysis_type
        self.tier = tier

        message = f"Unsupported analysis type: {analysis_type}"
        if tier and tier >= 4:
            message += f" (Tier {tier} - Experimental, not enabled)"

        super().__init__(message=message, code="UNSUPPORTED_ANALYSIS")


# =============================================================================
# Morphology-Related Exceptions
# =============================================================================


class MorphologyDataNotFoundError(DomainException):
    """Raised when morphological data is not available for a word."""

    def __init__(self, word: str, location: VerseLocation | None = None) -> None:
        """
        Initialize morphology data not found error.

        Args:
            word: The word for which morphology was not found
            location: Optional verse location for context
        """
        self.word = word
        self.location = location

        message = f"Morphological data not found for word: {word}"
        if location:
            message += f" at {location}"

        super().__init__(message=message, code="MORPHOLOGY_NOT_FOUND")


class InvalidRootError(DomainException):
    """Raised when a root is invalid (not 3-4 letters)."""

    def __init__(self, root: str) -> None:
        """
        Initialize invalid root error.

        Args:
            root: The invalid root
        """
        self.root = root
        super().__init__(
            message=(
                f"Invalid Arabic root: {root}. "
                "Roots must be 3 (trilateral) or 4 (quadrilateral) letters."
            ),
            code="INVALID_ROOT",
        )


# =============================================================================
# Entity-Related Exceptions
# =============================================================================


class EntityNotFoundError(DomainException):
    """Raised when a named entity is not found in the reference data."""

    def __init__(self, entity_type: str, entity_name: str) -> None:
        """
        Initialize entity not found error.

        Args:
            entity_type: Type of entity (e.g., "divine_name", "prophet")
            entity_name: Name of the entity
        """
        self.entity_type = entity_type
        self.entity_name = entity_name
        super().__init__(
            message=f"{entity_type} not found: {entity_name}",
            code="ENTITY_NOT_FOUND",
        )


# =============================================================================
# Ingestion-Related Exceptions
# =============================================================================


class IngestionError(DomainException):
    """Raised when data ingestion fails."""

    def __init__(self, source: str, reason: str) -> None:
        """
        Initialize ingestion error.

        Args:
            source: Data source that failed (e.g., "tanzil", "masaq")
            reason: Why ingestion failed
        """
        self.source = source
        self.reason = reason
        super().__init__(
            message=f"Failed to ingest data from {source}: {reason}",
            code="INGESTION_ERROR",
        )


class DataSourceUnavailableError(DomainException):
    """Raised when a required data source is not available."""

    def __init__(self, source: str, path: str | None = None) -> None:
        """
        Initialize data source unavailable error.

        Args:
            source: Name of the data source
            path: Optional file path that was not found
        """
        self.source = source
        self.path = path

        message = f"Data source not available: {source}"
        if path:
            message += f" (path: {path})"

        super().__init__(message=message, code="DATA_SOURCE_UNAVAILABLE")
