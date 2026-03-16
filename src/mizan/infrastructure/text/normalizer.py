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

    # Explicit normalization progression order.
    # Comparing enum string values lexicographically is incorrect for this use case.
    LEVEL_ORDER: Final[dict[NormalizationLevel, int]] = {
        NormalizationLevel.NONE: 0,
        NormalizationLevel.TASHKEEL_REMOVED: 1,
        NormalizationLevel.HAMZA_UNIFIED: 2,
        NormalizationLevel.ALIF_UNIFIED: 3,
        NormalizationLevel.YA_UNIFIED: 4,
        NormalizationLevel.FULL: 5,
    }

    # Tashkeel (diacritical marks) - vowels and other marks
    TASHKEEL: Final[frozenset[str]] = frozenset(
        [
            "\u064b",  # Fathatan ً
            "\u064c",  # Dammatan ٌ
            "\u064d",  # Kasratan ٍ
            "\u064e",  # Fatha َ
            "\u064f",  # Damma ُ
            "\u0650",  # Kasra ِ
            "\u0651",  # Shadda ّ
            "\u0652",  # Sukun ْ
            "\u0653",  # Maddah above ٓ
            "\u0654",  # Hamza above ٔ
            "\u0655",  # Hamza below ٕ
            "\u0656",  # Subscript Alef ٖ
            "\u0657",  # Inverted Damma ٗ
            "\u0658",  # Mark Noon Ghunna ٘
            "\u065c",  # Vowel Sign Dot Below
            "\u065d",  # Reversed Damma
            "\u065e",  # Fatha with Two Dots
            "\u0670",  # Superscript Alef (Alif Khanjariyya) ـٰ
        ]
    )

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
        "\u0649": "\u064a",  # ى → ي (Alif Maqsura)
        "\u0626": "\u064a",  # ئ → ي (Ya with Hamza)
    }

    # Tatweel (kashida) - stretching character
    TATWEEL: Final[str] = "\u0640"

    # Small letters and special marks (Uthmani)
    SMALL_LETTERS: Final[frozenset[str]] = frozenset(
        [
            "\u06e1",  # Small High Dotless Head of Khah
            "\u06e2",  # Small High Meem Isolated Form
            "\u06e3",  # Small Low Seen
            "\u06e4",  # Small High Madda
            "\u06e5",  # Small Waw
            "\u06e6",  # Small Ya
            "\u06e7",  # Small High Yeh
            "\u06e8",  # Small High Noon
            "\u06e9",  # Place of Sajdah
            "\u06ea",  # Empty Centre Low Stop
            "\u06eb",  # Empty Centre High Stop
            "\u06ec",  # Rounded High Stop
            "\u06ed",  # Small Low Meem
        ]
    )

    # Waqf (pause) signs
    WAQF_SIGNS: Final[frozenset[str]] = frozenset(
        [
            "\u06d6",  # Small High Ligature Sad with Lam with Alef Maksura
            "\u06d7",  # Small High Ligature Qaf with Lam with Alef Maksura
            "\u06d8",  # Small High Meem Initial Form
            "\u06d9",  # Small High Lam Alef
            "\u06da",  # Small High Jeem
            "\u06db",  # Small High Three Dots
            "\u06dc",  # Small High Seen
            "\u06dd",  # End of Ayah ۝
            "\u06de",  # Start of Rub El Hizb ۞
        ]
    )

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
        if self._is_at_least(level, NormalizationLevel.TASHKEEL_REMOVED):
            text = self._remove_tashkeel(text)

        # Level 2: Unify Hamza
        if self._is_at_least(level, NormalizationLevel.HAMZA_UNIFIED):
            text = self._unify_hamza(text)

        # Level 3: Unify Alif
        if self._is_at_least(level, NormalizationLevel.ALIF_UNIFIED):
            text = self._unify_alif(text)

        # Level 4: Unify Ya
        if self._is_at_least(level, NormalizationLevel.YA_UNIFIED):
            text = self._unify_ya(text)

        # Level 5 (FULL): Additional cleanup
        if level == NormalizationLevel.FULL:
            text = self._full_normalize(text)

        return text

    def _is_at_least(
        self,
        current: NormalizationLevel,
        threshold: NormalizationLevel,
    ) -> bool:
        """Check whether the current level includes the threshold level."""
        return self.LEVEL_ORDER[current] >= self.LEVEL_ORDER[threshold]

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
            "ابتثجحخدذرزسشصضطظعغفقكلمنهويءآأؤإئى\u0671"  # Alif Wasla
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
        return self.normalize(text1, level) == self.normalize(text2, level)
