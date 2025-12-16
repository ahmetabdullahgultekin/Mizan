"""
Arabic text normalizer - Progressive normalization levels.

Implements the normalization strategy from Appendix H of the PSD.
"""

from typing import Final

from mizan.domain.enums import NormalizationLevel


class ArabicNormalizer:
    """
    Arabic text normalizer with progressive normalization levels.

    Each level includes all transformations from previous levels.
    This allows precise control over text processing for different use cases.
    """

    # Tashkeel (diacritical marks) - vowels and other marks
    TASHKEEL: Final[frozenset[str]] = frozenset([
        "\u064B",  # Fathatan ً
        "\u064C",  # Dammatan ٌ
        "\u064D",  # Kasratan ٍ
        "\u064E",  # Fatha َ
        "\u064F",  # Damma ُ
        "\u0650",  # Kasra ِ
        "\u0651",  # Shadda ّ
        "\u0652",  # Sukun ْ
        "\u0653",  # Maddah above ٓ
        "\u0654",  # Hamza above ٔ
        "\u0655",  # Hamza below ٕ
        "\u0656",  # Subscript Alef ٖ
        "\u0657",  # Inverted Damma ٗ
        "\u0658",  # Mark Noon Ghunna ٘
        "\u065C",  # Vowel Sign Dot Below
        "\u065D",  # Reversed Damma
        "\u065E",  # Fatha with Two Dots
        "\u0670",  # Superscript Alef (Alif Khanjariyya) ـٰ
    ])

    # Hamza variants mapped to base Hamza
    HAMZA_MAP: Final[dict[str, str]] = {
        "\u0623": "\u0621",  # أ → ء (Alif with Hamza above)
        "\u0625": "\u0621",  # إ → ء (Alif with Hamza below)
        "\u0624": "\u0621",  # ؤ → ء (Waw with Hamza)
        "\u0626": "\u0621",  # ئ → ء (Ya with Hamza)
        "\u0622": "\u0621",  # آ → ء (Alif with Maddah)
    }

    # Alif variants mapped to plain Alif
    ALIF_MAP: Final[dict[str, str]] = {
        "\u0622": "\u0627",  # آ → ا (Alif with Maddah)
        "\u0623": "\u0627",  # أ → ا (Alif with Hamza above)
        "\u0625": "\u0627",  # إ → ا (Alif with Hamza below)
        "\u0671": "\u0627",  # ٱ → ا (Alif Wasla)
        "\u0670": "\u0627",  # ـٰ → ا (Alif Khanjariyya/Superscript)
    }

    # Ya variants mapped to plain Ya
    YA_MAP: Final[dict[str, str]] = {
        "\u0649": "\u064A",  # ى → ي (Alif Maqsura)
        "\u0626": "\u064A",  # ئ → ي (Ya with Hamza)
    }

    # Tatweel (kashida) - stretching character
    TATWEEL: Final[str] = "\u0640"

    # Small letters and special marks (Uthmani)
    SMALL_LETTERS: Final[frozenset[str]] = frozenset([
        "\u06E1",  # Small High Dotless Head of Khah
        "\u06E2",  # Small High Meem Isolated Form
        "\u06E3",  # Small Low Seen
        "\u06E4",  # Small High Madda
        "\u06E5",  # Small Waw
        "\u06E6",  # Small Ya
        "\u06E7",  # Small High Yeh
        "\u06E8",  # Small High Noon
        "\u06E9",  # Place of Sajdah
        "\u06EA",  # Empty Centre Low Stop
        "\u06EB",  # Empty Centre High Stop
        "\u06EC",  # Rounded High Stop
        "\u06ED",  # Small Low Meem
    ])

    # Waqf (pause) signs
    WAQF_SIGNS: Final[frozenset[str]] = frozenset([
        "\u06D6",  # Small High Ligature Sad with Lam with Alef Maksura
        "\u06D7",  # Small High Ligature Qaf with Lam with Alef Maksura
        "\u06D8",  # Small High Meem Initial Form
        "\u06D9",  # Small High Lam Alef
        "\u06DA",  # Small High Jeem
        "\u06DB",  # Small High Three Dots
        "\u06DC",  # Small High Seen
        "\u06DD",  # End of Ayah ۝
        "\u06DE",  # Start of Rub El Hizb ۞
    ])

    def normalize(
        self,
        text: str,
        level: NormalizationLevel = NormalizationLevel.FULL,
    ) -> str:
        """
        Normalize Arabic text to the specified level.

        Args:
            text: Arabic text to normalize
            level: Normalization level (progressive)

        Returns:
            Normalized text
        """
        if level == NormalizationLevel.NONE:
            return text

        # Level 1: Remove tashkeel
        if level.value >= NormalizationLevel.TASHKEEL_REMOVED.value:
            text = self._remove_tashkeel(text)

        # Level 2: Unify Hamza
        if level.value >= NormalizationLevel.HAMZA_UNIFIED.value:
            text = self._unify_hamza(text)

        # Level 3: Unify Alif
        if level.value >= NormalizationLevel.ALIF_UNIFIED.value:
            text = self._unify_alif(text)

        # Level 4: Unify Ya
        if level.value >= NormalizationLevel.YA_UNIFIED.value:
            text = self._unify_ya(text)

        # Level 5 (FULL): Additional cleanup
        if level == NormalizationLevel.FULL:
            text = self._full_normalize(text)

        return text

    def _remove_tashkeel(self, text: str) -> str:
        """Remove all diacritical marks."""
        return "".join(c for c in text if c not in self.TASHKEEL)

    def _unify_hamza(self, text: str) -> str:
        """Unify Hamza variants to bare Hamza."""
        for variant, replacement in self.HAMZA_MAP.items():
            text = text.replace(variant, replacement)
        return text

    def _unify_alif(self, text: str) -> str:
        """Unify Alif variants to plain Alif."""
        for variant, replacement in self.ALIF_MAP.items():
            text = text.replace(variant, replacement)
        return text

    def _unify_ya(self, text: str) -> str:
        """Unify Ya variants to plain Ya."""
        for variant, replacement in self.YA_MAP.items():
            text = text.replace(variant, replacement)
        return text

    def _full_normalize(self, text: str) -> str:
        """Apply full normalization (all transformations)."""
        # Remove tatweel
        text = text.replace(self.TATWEEL, "")

        # Remove small letters
        text = "".join(c for c in text if c not in self.SMALL_LETTERS)

        # Remove waqf signs
        text = "".join(c for c in text if c not in self.WAQF_SIGNS)

        return text

    def remove_tashkeel_only(self, text: str) -> str:
        """Remove only tashkeel (convenience method)."""
        return self._remove_tashkeel(text)

    def strip_non_letters(self, text: str) -> str:
        """Remove everything except Arabic letters."""
        ARABIC_LETTERS = frozenset(
            "ابتثجحخدذرزسشصضطظعغفقكلمنهويءآأؤإئى"
            "\u0671"  # Alif Wasla
        )
        return "".join(c for c in text if c in ARABIC_LETTERS)

    def normalize_for_search(self, text: str) -> str:
        """
        Normalize text for search matching.

        Applies full normalization and additional cleanup
        for fuzzy matching.
        """
        text = self.normalize(text, NormalizationLevel.FULL)
        # Also remove spaces for continuous matching
        text = text.replace(" ", "")
        return text

    def compare_normalized(
        self,
        text1: str,
        text2: str,
        level: NormalizationLevel = NormalizationLevel.FULL,
    ) -> bool:
        """
        Compare two texts after normalization.

        Useful for checking if two texts are equivalent
        despite different spellings/diacritics.
        """
        return (
            self.normalize(text1, level) == self.normalize(text2, level)
        )
