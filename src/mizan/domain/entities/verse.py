"""
Verse entity - Aggregate root for a single Quranic verse (Ayah).

This is the core entity in the domain model. A Verse is immutable after creation
to preserve textual integrity - the Quranic text must never be modified.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from mizan.domain.enums import QiraatType, SajdahType, ScriptType
    from mizan.domain.value_objects import SurahMetadata, TextChecksum, VerseLocation


@dataclass(frozen=True)
class Verse:
    """
    Aggregate root for a single verse (Ayah).

    Immutable after creation to preserve textual integrity.
    The Quranic text is sacred and must never be modified during runtime.

    Attributes:
        id: Unique identifier for this verse instance
        location: Position in the Mushaf (surah:verse)
        content: Text content mapped by script type
        qiraat_variants: Qira'at-specific text variants
        surah_metadata: Reference to parent surah metadata
        is_sajdah: Whether this verse has a prostration mark
        sajdah_type: Type of prostration (Wajib or Mustahabb)
        juz_number: Part number (1-30)
        hizb_number: Half-part number (1-60)
        ruku_number: Section number within surah
        manzil_number: Manzil number (1-7)
        page_number: Page in Madinah Mushaf
        checksum: Integrity verification hash
        word_count: Pre-computed word count
        letter_count: Pre-computed letter count
        abjad_value_mashriqi: Pre-computed Abjad value (Mashriqi system)
    """

    id: UUID
    location: VerseLocation
    content: dict[ScriptType, str]
    qiraat_variants: dict[QiraatType, dict[ScriptType, str]]
    surah_metadata: SurahMetadata
    is_sajdah: bool
    sajdah_type: SajdahType | None
    juz_number: int
    hizb_number: int
    ruku_number: int
    manzil_number: int
    page_number: int
    checksum: TextChecksum
    word_count: int
    letter_count: int
    abjad_value_mashriqi: int

    def __post_init__(self) -> None:
        """Validate verse upon creation."""
        # Validate juz number
        if not 1 <= self.juz_number <= 30:
            raise ValueError(f"Invalid juz number: {self.juz_number}")

        # Validate hizb number
        if not 1 <= self.hizb_number <= 60:
            raise ValueError(f"Invalid hizb number: {self.hizb_number}")

        # Validate manzil number
        if not 1 <= self.manzil_number <= 7:
            raise ValueError(f"Invalid manzil number: {self.manzil_number}")

        # Validate ruku number
        if self.ruku_number < 1:
            raise ValueError(f"Invalid ruku number: {self.ruku_number}")

        # Validate page number
        if self.page_number < 1:
            raise ValueError(f"Invalid page number: {self.page_number}")

        # Validate sajdah consistency
        if self.is_sajdah and self.sajdah_type is None:
            raise ValueError("Sajdah verse must have a sajdah_type")
        if not self.is_sajdah and self.sajdah_type is not None:
            raise ValueError("Non-sajdah verse cannot have a sajdah_type")

        # Validate content exists
        if not self.content:
            raise ValueError("Verse must have content in at least one script type")

    def get_text(
        self,
        script: ScriptType | None = None,
        qiraat: QiraatType | None = None,
    ) -> str:
        """
        Get verse text for specific script and Qira'at.

        Args:
            script: Script type (defaults to UTHMANI)
            qiraat: Qira'at type (defaults to HAFS_AN_ASIM)

        Returns:
            The verse text in the specified format

        Raises:
            KeyError: If the requested script/qiraat combination is not available
        """
        from mizan.domain.enums import QiraatType, ScriptType

        script = script or ScriptType.UTHMANI
        qiraat = qiraat or QiraatType.HAFS_AN_ASIM

        # Check if there's a Qira'at-specific variant
        if qiraat in self.qiraat_variants:
            variants = self.qiraat_variants[qiraat]
            if script in variants:
                return variants[script]

        # Fall back to default content
        if script not in self.content:
            available = ", ".join(s.value for s in self.content.keys())
            raise KeyError(
                f"Script type '{script.value}' not available for verse {self.location}. "
                f"Available scripts: {available}"
            )
        return self.content[script]

    @property
    def text_uthmani(self) -> str:
        """Get Uthmani script text (convenience property)."""
        from mizan.domain.enums import ScriptType
        return self.get_text(ScriptType.UTHMANI)

    @property
    def text_simple(self) -> str:
        """Get Simple script text (convenience property)."""
        from mizan.domain.enums import ScriptType
        return self.get_text(ScriptType.SIMPLE)

    @property
    def surah_number(self) -> int:
        """Get surah number (convenience property)."""
        return self.location.surah_number

    @property
    def verse_number(self) -> int:
        """Get verse number (convenience property)."""
        return self.location.verse_number

    def verify_integrity(self) -> bool:
        """
        Verify the integrity of this verse's content.

        Returns:
            True if checksum matches, False if corruption detected
        """
        from mizan.domain.enums import ScriptType

        # Verify against primary Uthmani text
        uthmani_text = self.content.get(ScriptType.UTHMANI, "")
        return self.checksum.verify(uthmani_text)

    def has_qiraat_variant(self, qiraat: QiraatType) -> bool:
        """Check if this verse has a variant for the given Qira'at."""
        return qiraat in self.qiraat_variants

    def __str__(self) -> str:
        """Return verse location as string."""
        return str(self.location)

    def __repr__(self) -> str:
        """Return detailed representation."""
        return (
            f"Verse(location={self.location}, "
            f"words={self.word_count}, "
            f"letters={self.letter_count})"
        )

    def __hash__(self) -> int:
        """Hash based on ID for set/dict usage."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Equality based on ID."""
        if not isinstance(other, Verse):
            return NotImplemented
        return self.id == other.id
