"""Surah metadata value object."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mizan.domain.enums import BasmalahStatus, RevelationType


@dataclass(frozen=True, slots=True)
class SurahMetadata:
    """
    Immutable metadata about a Surah.

    Contains all non-verse-content information about a Surah.
    This is a Value Object - identity is determined by its values.

    Attributes:
        number: Surah number (1-114)
        name_arabic: Arabic name (e.g., الفاتحة)
        name_english: English translation (e.g., The Opening)
        name_transliteration: Romanized name (e.g., Al-Fatihah)
        revelation_type: Meccan or Medinan
        revelation_order: Order of revelation (1-114)
        verse_count: Total number of verses
        basmalah_status: How Basmalah is treated
        ruku_count: Number of Ruku' sections
        word_count: Total word count (pre-computed)
        letter_count: Total letter count (pre-computed)
    """

    number: int
    name_arabic: str
    name_english: str
    name_transliteration: str
    revelation_type: RevelationType
    revelation_order: int
    verse_count: int
    basmalah_status: BasmalahStatus
    ruku_count: int
    word_count: int = 0  # Pre-computed during ingestion
    letter_count: int = 0  # Pre-computed during ingestion

    def __post_init__(self) -> None:
        """Validate surah metadata."""
        if not 1 <= self.number <= 114:
            raise ValueError(f"Invalid surah number: {self.number}")

        if not 1 <= self.revelation_order <= 114:
            raise ValueError(f"Invalid revelation order: {self.revelation_order}")

        if self.verse_count < 1:
            raise ValueError(f"Invalid verse count: {self.verse_count}")

        if self.ruku_count < 1:
            raise ValueError(f"Invalid ruku count: {self.ruku_count}")

        if not self.name_arabic:
            raise ValueError("Arabic name cannot be empty")

    def __str__(self) -> str:
        """Return surah number and Arabic name."""
        return f"{self.number}. {self.name_arabic}"

    def __repr__(self) -> str:
        """Return detailed representation."""
        return (
            f"SurahMetadata(number={self.number}, "
            f"name={self.name_arabic!r}, "
            f"verses={self.verse_count})"
        )

    @property
    def is_meccan(self) -> bool:
        """Check if this is a Meccan surah."""
        from mizan.domain.enums import RevelationType
        return self.revelation_type == RevelationType.MECCAN

    @property
    def is_medinan(self) -> bool:
        """Check if this is a Medinan surah."""
        from mizan.domain.enums import RevelationType
        return self.revelation_type == RevelationType.MEDINAN

    @property
    def has_basmalah(self) -> bool:
        """Check if this surah has a Basmalah."""
        from mizan.domain.enums import BasmalahStatus
        return self.basmalah_status != BasmalahStatus.ABSENT

    @property
    def basmalah_is_verse(self) -> bool:
        """Check if Basmalah counts as a verse in this surah."""
        from mizan.domain.enums import BasmalahStatus
        return self.basmalah_status == BasmalahStatus.NUMBERED_VERSE
