"""
Surah entity - Aggregate for a complete Quranic chapter.

A Surah contains all verses and metadata for one of the 114 chapters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from mizan.domain.entities.verse import Verse
    from mizan.domain.value_objects import SurahMetadata, TextChecksum, VerseLocation


@dataclass(frozen=True)
class Surah:
    """
    Aggregate for a complete Surah (chapter).

    Immutable after creation. Contains all verses and metadata.

    Attributes:
        metadata: Surah metadata (name, revelation type, etc.)
        verses: Immutable tuple of all verses in order
        checksum: Hash of complete surah text for integrity
    """

    metadata: SurahMetadata
    verses: tuple[Verse, ...]
    checksum: TextChecksum

    def __post_init__(self) -> None:
        """Validate surah upon creation."""
        if len(self.verses) != self.metadata.verse_count:
            raise ValueError(
                f"Verse count mismatch for Surah {self.metadata.number}: "
                f"expected {self.metadata.verse_count}, got {len(self.verses)}"
            )

        # Verify verses are in order
        for i, verse in enumerate(self.verses, start=1):
            if verse.verse_number != i:
                raise ValueError(
                    f"Verse order mismatch in Surah {self.metadata.number}: "
                    f"expected verse {i}, got {verse.verse_number}"
                )

            if verse.surah_number != self.metadata.number:
                raise ValueError(
                    f"Verse {verse.location} does not belong to Surah {self.metadata.number}"
                )

    @property
    def number(self) -> int:
        """Get surah number."""
        return self.metadata.number

    @property
    def name_arabic(self) -> str:
        """Get Arabic name."""
        return self.metadata.name_arabic

    @property
    def name_english(self) -> str:
        """Get English name."""
        return self.metadata.name_english

    @property
    def verse_count(self) -> int:
        """Get total verse count."""
        return self.metadata.verse_count

    @property
    def total_words(self) -> int:
        """Get total word count across all verses."""
        return sum(v.word_count for v in self.verses)

    @property
    def total_letters(self) -> int:
        """Get total letter count across all verses."""
        return sum(v.letter_count for v in self.verses)

    @property
    def total_abjad(self) -> int:
        """Get total Abjad value across all verses (Mashriqi)."""
        return sum(v.abjad_value_mashriqi for v in self.verses)

    def get_verse(self, verse_number: int) -> Verse:
        """
        Get a specific verse by number.

        Args:
            verse_number: Verse number (1-indexed)

        Returns:
            The requested Verse

        Raises:
            IndexError: If verse number is out of range
        """
        if not 1 <= verse_number <= len(self.verses):
            raise IndexError(
                f"Verse {verse_number} does not exist in Surah {self.number}. "
                f"Valid range: 1-{len(self.verses)}"
            )
        return self.verses[verse_number - 1]

    def get_verse_by_location(self, location: VerseLocation) -> Verse:
        """
        Get a verse by its VerseLocation.

        Args:
            location: The verse location

        Returns:
            The requested Verse

        Raises:
            ValueError: If location doesn't match this surah
            IndexError: If verse number is out of range
        """
        if location.surah_number != self.number:
            raise ValueError(
                f"Location {location} does not belong to Surah {self.number}"
            )
        return self.get_verse(location.verse_number)

    def get_verses_in_range(self, start: int, end: int) -> tuple[Verse, ...]:
        """
        Get verses in a range (inclusive).

        Args:
            start: Starting verse number (1-indexed)
            end: Ending verse number (1-indexed, inclusive)

        Returns:
            Tuple of verses in the range

        Raises:
            ValueError: If range is invalid
        """
        if start < 1:
            raise ValueError(f"Start verse must be >= 1, got {start}")
        if end > len(self.verses):
            raise ValueError(
                f"End verse {end} exceeds surah length {len(self.verses)}"
            )
        if start > end:
            raise ValueError(f"Start ({start}) cannot be greater than end ({end})")

        return self.verses[start - 1 : end]

    def get_sajdah_verses(self) -> tuple[Verse, ...]:
        """Get all verses marked for prostration."""
        return tuple(v for v in self.verses if v.is_sajdah)

    def iter_verses(self) -> Iterator[Verse]:
        """Iterate over all verses in order."""
        return iter(self.verses)

    def get_full_text(self, script: ScriptType | None = None) -> str:
        """
        Get the complete surah text.

        Args:
            script: Script type (defaults to UTHMANI)

        Returns:
            Complete surah text with verses separated by newlines
        """
        from mizan.domain.enums import ScriptType
        script = script or ScriptType.UTHMANI
        return "\n".join(v.get_text(script) for v in self.verses)

    def verify_integrity(self) -> bool:
        """
        Verify integrity of all verses and overall surah checksum.

        Returns:
            True if all checksums match, False if any corruption detected
        """
        # Verify each verse
        for verse in self.verses:
            if not verse.verify_integrity():
                return False

        # Verify overall surah checksum
        from mizan.domain.enums import ScriptType
        full_text = self.get_full_text(ScriptType.UTHMANI)
        return self.checksum.verify(full_text)

    def __str__(self) -> str:
        """Return surah number and name."""
        return f"{self.number}. {self.name_arabic} ({self.name_english})"

    def __repr__(self) -> str:
        """Return detailed representation."""
        return (
            f"Surah(number={self.number}, "
            f"name={self.name_arabic!r}, "
            f"verses={len(self.verses)})"
        )

    def __len__(self) -> int:
        """Return verse count."""
        return len(self.verses)

    def __iter__(self) -> Iterator[Verse]:
        """Iterate over verses."""
        return iter(self.verses)

    def __getitem__(self, index: int) -> Verse:
        """Get verse by 0-based index."""
        return self.verses[index]

    def __hash__(self) -> int:
        """Hash based on surah number."""
        return hash(self.number)

    def __eq__(self, other: object) -> bool:
        """Equality based on surah number and checksum."""
        if not isinstance(other, Surah):
            return NotImplemented
        return self.number == other.number and self.checksum == other.checksum


# Import for type checking only
if TYPE_CHECKING:
    from mizan.domain.enums import ScriptType
