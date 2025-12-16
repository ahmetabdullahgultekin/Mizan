"""Verse location value object - immutable identifier for verse position."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# Quran structural constants
MIN_SURAH: Final[int] = 1
MAX_SURAH: Final[int] = 114
MIN_VERSE: Final[int] = 1

# Maximum verses per surah (for validation)
MAX_VERSES_PER_SURAH: Final[dict[int, int]] = {
    1: 7, 2: 286, 3: 200, 4: 176, 5: 120, 6: 165, 7: 206, 8: 75, 9: 129, 10: 109,
    11: 123, 12: 111, 13: 43, 14: 52, 15: 99, 16: 128, 17: 111, 18: 110, 19: 98, 20: 135,
    21: 112, 22: 78, 23: 118, 24: 64, 25: 77, 26: 227, 27: 93, 28: 88, 29: 69, 30: 60,
    31: 34, 32: 30, 33: 73, 34: 54, 35: 45, 36: 83, 37: 182, 38: 88, 39: 75, 40: 85,
    41: 54, 42: 53, 43: 89, 44: 59, 45: 37, 46: 35, 47: 38, 48: 29, 49: 18, 50: 45,
    51: 60, 52: 49, 53: 62, 54: 55, 55: 78, 56: 96, 57: 29, 58: 22, 59: 24, 60: 13,
    61: 14, 62: 11, 63: 11, 64: 18, 65: 12, 66: 12, 67: 30, 68: 52, 69: 52, 70: 44,
    71: 28, 72: 28, 73: 20, 74: 56, 75: 40, 76: 31, 77: 50, 78: 40, 79: 46, 80: 42,
    81: 29, 82: 19, 83: 36, 84: 25, 85: 22, 86: 17, 87: 19, 88: 26, 89: 30, 90: 20,
    91: 15, 92: 21, 93: 11, 94: 8, 95: 8, 96: 19, 97: 5, 98: 8, 99: 8, 100: 11,
    101: 11, 102: 8, 103: 3, 104: 9, 105: 5, 106: 4, 107: 7, 108: 3, 109: 6, 110: 3,
    111: 5, 112: 4, 113: 5, 114: 6,
}


@dataclass(frozen=True, slots=True)
class VerseLocation:
    """
    Immutable identifier for a verse's position in the Mushaf.

    This is a Value Object in DDD terms - identity is determined by its values,
    not by a unique identifier.

    Attributes:
        surah_number: Surah number (1-114)
        verse_number: Verse number within the surah (1-N, varies by surah)
    """

    surah_number: int
    verse_number: int

    def __post_init__(self) -> None:
        """Validate the verse location upon creation."""
        if not MIN_SURAH <= self.surah_number <= MAX_SURAH:
            raise ValueError(
                f"Invalid surah number: {self.surah_number}. "
                f"Must be between {MIN_SURAH} and {MAX_SURAH}."
            )

        if self.verse_number < MIN_VERSE:
            raise ValueError(
                f"Invalid verse number: {self.verse_number}. "
                f"Must be at least {MIN_VERSE}."
            )

        # Validate against known verse counts
        max_verses = MAX_VERSES_PER_SURAH.get(self.surah_number)
        if max_verses is not None and self.verse_number > max_verses:
            raise ValueError(
                f"Invalid verse number: {self.verse_number} for surah {self.surah_number}. "
                f"Maximum is {max_verses}."
            )

    def __str__(self) -> str:
        """Return standard surah:verse notation."""
        return f"{self.surah_number}:{self.verse_number}"

    def __repr__(self) -> str:
        """Return detailed representation."""
        return f"VerseLocation(surah={self.surah_number}, verse={self.verse_number})"

    @classmethod
    def from_string(cls, location_str: str) -> VerseLocation:
        """
        Create a VerseLocation from string notation.

        Args:
            location_str: String in "surah:verse" format (e.g., "2:255")

        Returns:
            VerseLocation instance

        Raises:
            ValueError: If string format is invalid
        """
        parts = location_str.strip().split(":")
        if len(parts) != 2:
            raise ValueError(
                f"Invalid location format: '{location_str}'. "
                "Expected 'surah:verse' format (e.g., '2:255')."
            )

        try:
            surah = int(parts[0])
            verse = int(parts[1])
        except ValueError as e:
            raise ValueError(
                f"Invalid location format: '{location_str}'. "
                "Surah and verse must be integers."
            ) from e

        return cls(surah_number=surah, verse_number=verse)

    def next_verse(self) -> VerseLocation | None:
        """
        Get the next verse location, or None if at end of surah.

        Returns:
            Next VerseLocation or None if at surah end
        """
        max_verses = MAX_VERSES_PER_SURAH.get(self.surah_number, 0)
        if self.verse_number >= max_verses:
            return None
        return VerseLocation(self.surah_number, self.verse_number + 1)

    def previous_verse(self) -> VerseLocation | None:
        """
        Get the previous verse location, or None if at start of surah.

        Returns:
            Previous VerseLocation or None if at surah start
        """
        if self.verse_number <= MIN_VERSE:
            return None
        return VerseLocation(self.surah_number, self.verse_number - 1)

    def is_first_verse(self) -> bool:
        """Check if this is the first verse of a surah."""
        return self.verse_number == MIN_VERSE

    def is_last_verse(self) -> bool:
        """Check if this is the last verse of a surah."""
        max_verses = MAX_VERSES_PER_SURAH.get(self.surah_number, 0)
        return self.verse_number == max_verses

    def __lt__(self, other: object) -> bool:
        """Enable sorting by surah then verse."""
        if not isinstance(other, VerseLocation):
            return NotImplemented
        if self.surah_number != other.surah_number:
            return self.surah_number < other.surah_number
        return self.verse_number < other.verse_number

    def __le__(self, other: object) -> bool:
        """Enable sorting by surah then verse."""
        if not isinstance(other, VerseLocation):
            return NotImplemented
        return self < other or self == other
