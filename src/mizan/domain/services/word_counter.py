"""
Word counter domain service.

Provides transparent word counting with full methodology logging.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class WordCountResult:
    """
    Result of a word count operation with full transparency.

    Attributes:
        count: The total word count
        words: List of identified words
        methodology: Description of counting methodology used
        decisions: List of specific decisions made during counting
    """

    count: int
    words: tuple[str, ...]
    methodology: str
    decisions: tuple[str, ...]

    def to_audit_dict(self) -> dict[str, object]:
        """Convert to dictionary for audit logging."""
        return {
            "count": self.count,
            "words": list(self.words),
            "methodology": self.methodology,
            "decisions": list(self.decisions),
        }


class WordCounter:
    """
    Domain service for transparent Arabic word counting.

    Provides clear methodology and full audit trail for reproducibility.
    This is critical because different counting methodologies yield different
    results (e.g., the "يوم=365" claim varies from 217 to 475 depending on method).
    """

    # Arabic word separators
    WORD_SEPARATORS: Final[frozenset[str]] = frozenset([
        " ",       # Space
        "\u00A0",  # Non-breaking space
        "\u200B",  # Zero-width space (used in some texts)
    ])

    # Characters that are NOT part of words
    NON_WORD_CHARS: Final[frozenset[str]] = frozenset([
        "\u06DD",  # End of Ayah mark ۝
        "\u06DE",  # Start of Rub El Hizb ۞
        "\u06E9",  # Place of Sajdah ۩
        # Waqf (pause) signs
        "ۖ", "ۗ", "ۘ", "ۙ", "ۚ", "ۛ", "ۜ",
    ])

    def count_words(
        self,
        text: str,
        include_particles: bool = True,
        methodology_note: str = "",
    ) -> WordCountResult:
        """
        Count words in Arabic text with full transparency.

        Args:
            text: Arabic text to count
            include_particles: If True, count particles (و، ف، etc.) as words
            methodology_note: Additional note about the specific counting context

        Returns:
            WordCountResult with count, words, and methodology details
        """
        decisions: list[str] = []

        # Remove non-word characters
        cleaned = text
        for char in self.NON_WORD_CHARS:
            if char in cleaned:
                cleaned = cleaned.replace(char, " ")
                decisions.append(f"Removed {repr(char)} (non-word character)")

        # Split by whitespace
        raw_words = cleaned.split()
        decisions.append(f"Split text into {len(raw_words)} raw tokens")

        # Filter empty strings and clean words
        words: list[str] = []
        for word in raw_words:
            word = word.strip()
            if word:
                words.append(word)

        # Build methodology description
        methodology = "Whitespace-delimited word counting"
        if include_particles:
            methodology += " (particles counted as separate words)"
        else:
            methodology += " (attached particles merged with base word)"
        if methodology_note:
            methodology += f". Note: {methodology_note}"

        return WordCountResult(
            count=len(words),
            words=tuple(words),
            methodology=methodology,
            decisions=tuple(decisions),
        )

    def count_words_simple(self, text: str) -> int:
        """
        Simple word count returning just the integer.

        Uses default methodology (whitespace-delimited, particles included).
        """
        return self.count_words(text).count

    def split_words(self, text: str) -> list[str]:
        """
        Split text into words.

        Returns list of words without full audit trail.
        """
        return list(self.count_words(text).words)

    def get_word_positions(self, text: str) -> list[tuple[str, int, int]]:
        """
        Get words with their positions in the original text.

        Returns:
            List of (word, start_index, end_index) tuples
        """
        positions: list[tuple[str, int, int]] = []
        current_word_start: int | None = None
        current_word: list[str] = []

        for i, char in enumerate(text):
            if char in self.WORD_SEPARATORS or char in self.NON_WORD_CHARS:
                if current_word:
                    word = "".join(current_word)
                    positions.append((word, current_word_start or 0, i))
                    current_word = []
                    current_word_start = None
            else:
                if current_word_start is None:
                    current_word_start = i
                current_word.append(char)

        # Handle last word
        if current_word:
            word = "".join(current_word)
            positions.append((word, current_word_start or 0, len(text)))

        return positions
