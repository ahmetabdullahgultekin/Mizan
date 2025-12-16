"""Text normalization level definitions."""

from enum import StrEnum


class NormalizationLevel(StrEnum):
    """
    Progressive levels of Arabic text normalization.

    Each level includes all transformations from previous levels.
    This allows precise control over text processing.
    """

    NONE = "none"
    """No normalization - preserve original text exactly."""

    TASHKEEL_REMOVED = "tashkeel_removed"
    """
    Remove diacritical marks (tashkeel/harakat).
    Includes: fatha, damma, kasra, sukun, shadda, tanween.
    """

    HAMZA_UNIFIED = "hamza_unified"
    """
    Unify Hamza variants to bare Hamza (ء).
    Affects: أ إ ؤ ئ آ → ء (on their carriers)
    """

    ALIF_UNIFIED = "alif_unified"
    """
    Unify all Alif variants to plain Alif (ا).
    Affects: آ أ إ ٱ (Alif Wasla) ـٰ (Alif Khanjariyya) → ا
    """

    YA_UNIFIED = "ya_unified"
    """
    Unify Ya variants.
    Affects: ى (Alif Maqsura) ئ → ي
    """

    FULL = "full"
    """
    Maximum normalization - all above transformations applied.
    Use for fuzzy matching and search operations.
    """
