"""
Repository Interfaces (Ports) - Abstract definitions for data access.

These interfaces define the contract between the domain layer and infrastructure.
Implementations are provided by the infrastructure layer (adapters).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, AsyncIterator

if TYPE_CHECKING:
    from mizan.domain.entities import Surah, Verse
    from mizan.domain.enums import RevelationType
    from mizan.domain.value_objects import SurahMetadata, VerseLocation


@dataclass(frozen=True)
class IntegrityReport:
    """
    Result of integrity verification.

    Contains details about the verification process and any failures.

    Attributes:
        is_valid: Overall validation result
        checked_at: When verification was performed
        total_verses: Total number of verses checked
        failed_verses: Locations of verses that failed verification
        expected_checksum: Expected overall checksum
        actual_checksum: Actual computed checksum
        details: Human-readable summary
    """

    is_valid: bool
    checked_at: datetime
    total_verses: int
    failed_verses: tuple[VerseLocation, ...]
    expected_checksum: str
    actual_checksum: str
    details: str

    @property
    def failure_count(self) -> int:
        """Get number of failed verifications."""
        return len(self.failed_verses)

    @property
    def success_rate(self) -> float:
        """Get verification success rate as percentage."""
        if self.total_verses == 0:
            return 0.0
        return ((self.total_verses - self.failure_count) / self.total_verses) * 100


class IQuranRepository(ABC):
    """
    Port for Quran data access.

    This interface defines all operations for retrieving Quranic text.
    Implementations are in the Infrastructure layer.
    """

    @abstractmethod
    async def get_verse(self, location: VerseLocation) -> Verse | None:
        """
        Retrieve a single verse by location.

        Args:
            location: The verse location (surah:verse)

        Returns:
            The Verse if found, None otherwise
        """
        ...

    @abstractmethod
    async def get_verse_or_raise(self, location: VerseLocation) -> Verse:
        """
        Retrieve a single verse, raise if not found.

        Args:
            location: The verse location (surah:verse)

        Returns:
            The Verse

        Raises:
            VerseNotFoundError: If verse does not exist
        """
        ...

    @abstractmethod
    async def get_surah(self, surah_number: int) -> Surah:
        """
        Retrieve a complete Surah with all verses.

        Args:
            surah_number: Surah number (1-114)

        Returns:
            The complete Surah

        Raises:
            SurahNotFoundError: If surah does not exist
        """
        ...

    @abstractmethod
    async def get_verses_in_range(
        self,
        start: VerseLocation,
        end: VerseLocation,
    ) -> list[Verse]:
        """
        Retrieve verses within a range (inclusive).

        Args:
            start: Starting verse location
            end: Ending verse location (inclusive)

        Returns:
            List of verses in the range

        Raises:
            VerseRangeError: If range is invalid
        """
        ...

    @abstractmethod
    async def get_all_verses(self) -> list[Verse]:
        """
        Retrieve all verses in the Quran.

        Returns:
            List of all 6236 verses in order
        """
        ...

    @abstractmethod
    async def stream_verses(
        self,
        surah_number: int | None = None,
    ) -> AsyncIterator[Verse]:
        """
        Stream verses for memory-efficient processing.

        Args:
            surah_number: Optional filter by surah (None = all verses)

        Yields:
            Verses one at a time
        """
        ...

    @abstractmethod
    async def get_verse_count(self, surah_number: int | None = None) -> int:
        """
        Get total verse count.

        Args:
            surah_number: Optional filter by surah (None = entire Quran)

        Returns:
            Total number of verses
        """
        ...

    @abstractmethod
    async def get_verses_by_criteria(
        self,
        revelation_type: RevelationType | None = None,
        juz_number: int | None = None,
        hizb_number: int | None = None,
        manzil_number: int | None = None,
        has_sajdah: bool | None = None,
    ) -> list[Verse]:
        """
        Query verses by various criteria.

        Args:
            revelation_type: Filter by Meccan/Medinan
            juz_number: Filter by Juz (1-30)
            hizb_number: Filter by Hizb (1-60)
            manzil_number: Filter by Manzil (1-7)
            has_sajdah: Filter for sajdah verses

        Returns:
            List of matching verses
        """
        ...

    @abstractmethod
    async def search_text(
        self,
        query: str,
        surah_number: int | None = None,
        case_sensitive: bool = False,
    ) -> list[Verse]:
        """
        Search for text within verses.

        Args:
            query: Text to search for
            surah_number: Optional filter by surah
            case_sensitive: Whether search is case-sensitive

        Returns:
            List of verses containing the query
        """
        ...

    @abstractmethod
    async def verify_integrity(self) -> IntegrityReport:
        """
        Verify checksums of all stored data.

        Returns:
            IntegrityReport with verification results
        """
        ...


class ISurahMetadataRepository(ABC):
    """
    Port for Surah metadata access.

    Provides access to surah-level information without loading verses.
    """

    @abstractmethod
    async def get_metadata(self, surah_number: int) -> SurahMetadata:
        """
        Get metadata for a specific surah.

        Args:
            surah_number: Surah number (1-114)

        Returns:
            SurahMetadata for the requested surah

        Raises:
            SurahNotFoundError: If surah does not exist
        """
        ...

    @abstractmethod
    async def get_all_metadata(self) -> list[SurahMetadata]:
        """
        Get metadata for all 114 surahs.

        Returns:
            List of all SurahMetadata in order
        """
        ...

    @abstractmethod
    async def get_meccan_surahs(self) -> list[SurahMetadata]:
        """Get metadata for all Meccan surahs."""
        ...

    @abstractmethod
    async def get_medinan_surahs(self) -> list[SurahMetadata]:
        """Get metadata for all Medinan surahs."""
        ...


@dataclass(frozen=True)
class MorphologyData:
    """
    Morphological analysis data for a word.

    From MASAQ dataset.

    Attributes:
        word_uthmani: Word in Uthmani script
        word_imlaei: Word in Imla'i script
        root: Trilateral/quadrilateral root
        lemma: Dictionary form
        pattern: Morphological pattern (وزن)
        pos_tag: Part of speech tag
        morpheme_type: STEM, PREFIX, or SUFFIX
        person: 1, 2, 3 or None
        gender: M, F, or None
        number: S (singular), D (dual), P (plural)
        case_state: Grammatical case
        mood_voice: Verb mood and voice
        syntactic_role: Syntactic function
        irab_description: Traditional Arabic grammar description
    """

    word_uthmani: str
    word_imlaei: str
    root: str | None
    lemma: str | None
    pattern: str | None
    pos_tag: str
    morpheme_type: str
    person: str | None
    gender: str | None
    number: str | None
    case_state: str | None
    mood_voice: str | None
    syntactic_role: str | None
    irab_description: str | None


class IMorphologyRepository(ABC):
    """
    Port for morphological data access.

    Provides access to word-level morphological analysis from MASAQ dataset.
    """

    @abstractmethod
    async def get_word_morphology(
        self,
        location: VerseLocation,
        word_number: int,
    ) -> list[MorphologyData]:
        """
        Get morphological analysis for a word.

        A word may have multiple morphemes (prefix, stem, suffix).

        Args:
            location: Verse location
            word_number: Word position in verse (1-indexed)

        Returns:
            List of MorphologyData for all morphemes
        """
        ...

    @abstractmethod
    async def get_verse_morphology(
        self,
        location: VerseLocation,
    ) -> list[list[MorphologyData]]:
        """
        Get morphological analysis for all words in a verse.

        Args:
            location: Verse location

        Returns:
            List of lists - outer list is words, inner list is morphemes
        """
        ...

    @abstractmethod
    async def search_by_root(self, root: str) -> list[tuple[VerseLocation, int]]:
        """
        Find all occurrences of a root in the Quran.

        Args:
            root: Arabic root (e.g., ك-ت-ب or كتب)

        Returns:
            List of (location, word_number) tuples
        """
        ...

    @abstractmethod
    async def search_by_lemma(self, lemma: str) -> list[tuple[VerseLocation, int]]:
        """
        Find all occurrences of a lemma.

        Args:
            lemma: Dictionary form of word

        Returns:
            List of (location, word_number) tuples
        """
        ...

    @abstractmethod
    async def get_root_frequency(self) -> dict[str, int]:
        """
        Get frequency distribution of all roots.

        Returns:
            Dictionary mapping roots to occurrence counts
        """
        ...

    @abstractmethod
    async def get_unique_roots(self) -> set[str]:
        """
        Get all unique roots in the Quran.

        Returns:
            Set of all roots
        """
        ...
