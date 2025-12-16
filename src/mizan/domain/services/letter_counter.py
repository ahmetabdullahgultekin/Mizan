"""
Letter counter domain service.

Provides accurate Arabic letter counting with configurable rules.
"""

from __future__ import annotations

from typing import Final

from mizan.domain.enums import LetterCountMethod


class LetterCounter:
    """
    Domain service for accurate Arabic letter counting.

    Handles the complexities of Arabic script including:
    - Base letters
    - Alif variants (Wasla, Khanjariyya)
    - Hamza forms
    - Diacritical marks (excluded from count)
    """

    # Base Arabic letters (28 letters of the Arabic alphabet)
    ARABIC_LETTERS: Final[frozenset[str]] = frozenset(
        "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
        "ءآأؤإئى"  # Hamza variants and Alif Maqsura
    )

    # Alif Wasla - used in Uthmani script for definite article
    ALIF_WASLA: Final[str] = "\u0671"  # ٱ

    # Alif Khanjariyya - superscript Alif (counts as Alif per scholarly consensus)
    ALIF_KHANJARIYYA: Final[str] = "\u0670"  # ـٰ

    # Combined countable special characters
    COUNTABLE_SPECIAL: Final[frozenset[str]] = frozenset([ALIF_WASLA, ALIF_KHANJARIYYA])

    # Tashkeel (diacritical marks) - NOT counted as letters
    TASHKEEL: Final[frozenset[str]] = frozenset([
        "\u064B",  # Fathatan ً
        "\u064C",  # Dammatan ٌ
        "\u064D",  # Kasratan ٍ
        "\u064E",  # Fatha َ
        "\u064F",  # Damma ُ
        "\u0650",  # Kasra ِ
        "\u0651",  # Shadda ّ
        "\u0652",  # Sukun ْ
        "\u0653",  # Maddah ٓ
        "\u0654",  # Hamza above ٔ
        "\u0655",  # Hamza below ٕ
        "\u0656",  # Subscript Alef ٖ
        "\u0657",  # Inverted Damma ٗ
        "\u0658",  # Noon Ghunna ٘
    ])

    # Tatweel (kashida) - stretching character, NOT a letter
    TATWEEL: Final[str] = "\u0640"  # ـ

    def count_letters(
        self,
        text: str,
        method: LetterCountMethod = LetterCountMethod.TRADITIONAL,
        *,
        count_alif_wasla: bool | None = None,
        count_alif_khanjariyya: bool | None = None,
    ) -> int:
        """
        Count Arabic letters in text.

        Args:
            text: Arabic text to count
            method: Counting method (default: TRADITIONAL - matches scholarly consensus)
            count_alif_wasla: Override for Alif Wasla counting (None = use method default)
            count_alif_khanjariyya: Override for Alif Khanjariyya counting (None = use method default)

        Returns:
            Total letter count

        Note:
            - Diacritical marks (tashkeel) are never counted
            - Shadda does NOT count double (scholarly majority opinion)
            - Spaces and punctuation are not counted
            - TRADITIONAL method gives: Basmalah=19, Al-Fatiha=139 (scholarly consensus)
        """
        # Determine counting rules based on method or explicit overrides
        include_wasla, include_khanjariyya = self._get_counting_rules(
            method, count_alif_wasla, count_alif_khanjariyya
        )

        count = 0
        for char in text:
            if char in self.ARABIC_LETTERS:
                count += 1
            elif include_wasla and char == self.ALIF_WASLA:
                count += 1
            elif include_khanjariyya and char == self.ALIF_KHANJARIYYA:
                count += 1
        return count

    def _get_counting_rules(
        self,
        method: LetterCountMethod,
        wasla_override: bool | None,
        khanjariyya_override: bool | None,
    ) -> tuple[bool, bool]:
        """Get counting rules based on method and any explicit overrides.

        Based on verification against scholarly data:
        - Al-Fatiha scholarly count = 139 letters
        - This equals Uthmani base (125) + Alif Wasla (14) = 139
        - Alif Khanjariyya (6) is NOT counted in traditional scholarship
        """
        # Default rules per method (wasla, khanjariyya)
        method_rules = {
            # TRADITIONAL: Include Wasla (as Alif), exclude Khanjariyya
            # Verified: Al-Fatiha = 139 letters (scholarly consensus)
            LetterCountMethod.TRADITIONAL: (True, False),

            # UTHMANI_FULL: Include all Alif variants
            # Al-Fatiha = 145 letters with this method
            LetterCountMethod.UTHMANI_FULL: (True, True),

            # NO_WASLA: Base letters only (for simple text analysis)
            # Use this when working with simple/imlai text
            LetterCountMethod.NO_WASLA: (False, False),
        }
        include_wasla, include_khanjariyya = method_rules.get(
            method, (True, False)  # Default to TRADITIONAL
        )

        # Apply explicit overrides if provided
        if wasla_override is not None:
            include_wasla = wasla_override
        if khanjariyya_override is not None:
            include_khanjariyya = khanjariyya_override

        return include_wasla, include_khanjariyya

    def count_letters_detailed(
        self,
        text: str,
        method: LetterCountMethod = LetterCountMethod.TRADITIONAL,
        *,
        count_alif_wasla: bool | None = None,
        count_alif_khanjariyya: bool | None = None,
    ) -> dict[str, int | str]:
        """
        Count letters with detailed breakdown.

        Args:
            text: Arabic text to count
            method: Counting method (default: TRADITIONAL)
            count_alif_wasla: Override for Alif Wasla counting
            count_alif_khanjariyya: Override for Alif Khanjariyya counting

        Returns a dictionary with:
        - "total": Total letter count
        - "base_letters": Count of standard Arabic letters
        - "alif_wasla": Count of Alif Wasla characters (always shown)
        - "alif_khanjariyya": Count of Alif Khanjariyya characters (always shown)
        - "method": The counting method used
        """
        include_wasla, include_khanjariyya = self._get_counting_rules(
            method, count_alif_wasla, count_alif_khanjariyya
        )

        base = 0
        wasla = 0
        khanjariyya = 0

        for char in text:
            if char in self.ARABIC_LETTERS:
                base += 1
            elif char == self.ALIF_WASLA:
                wasla += 1
            elif char == self.ALIF_KHANJARIYYA:
                khanjariyya += 1

        total = base
        if include_wasla:
            total += wasla
        if include_khanjariyya:
            total += khanjariyya

        return {
            "total": total,
            "base_letters": base,
            "alif_wasla": wasla,
            "alif_khanjariyya": khanjariyya,
            "method": str(method),
            "wasla_included": include_wasla,
            "khanjariyya_included": include_khanjariyya,
        }

    def get_letter_frequency(
        self,
        text: str,
        normalize_variants: bool = True,
    ) -> dict[str, int]:
        """
        Get frequency distribution of each Arabic letter.

        Args:
            text: Arabic text to analyze
            normalize_variants: If True, group variants (e.g., all Alifs together)

        Returns:
            Dictionary mapping letters to their counts
        """
        freq: dict[str, int] = {}
        for char in text:
            if char in self.ARABIC_LETTERS or char in self.COUNTABLE_SPECIAL:
                letter = self._normalize_letter(char) if normalize_variants else char
                freq[letter] = freq.get(letter, 0) + 1
        return freq

    def _normalize_letter(self, char: str) -> str:
        """
        Normalize letter variants to base form.

        - All Alif variants → ا
        - All Ya variants → ي
        - Hamza stays as ء
        """
        # Alif variants
        ALIF_VARIANTS = frozenset(["آ", "أ", "إ", "ا", self.ALIF_WASLA, self.ALIF_KHANJARIYYA])
        if char in ALIF_VARIANTS:
            return "ا"

        # Ya variants
        YA_VARIANTS = frozenset(["ي", "ى", "ئ"])
        if char in YA_VARIANTS:
            return "ي"

        return char

    def is_arabic_letter(self, char: str) -> bool:
        """Check if a character is an Arabic letter."""
        return char in self.ARABIC_LETTERS or char in self.COUNTABLE_SPECIAL

    def extract_letters(self, text: str) -> str:
        """
        Extract only Arabic letters from text.

        Removes diacritics, spaces, punctuation - returns only letters.
        """
        return "".join(
            char for char in text
            if char in self.ARABIC_LETTERS or char in self.COUNTABLE_SPECIAL
        )
