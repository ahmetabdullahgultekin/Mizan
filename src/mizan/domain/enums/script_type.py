"""Quranic script type definitions."""

from enum import StrEnum


class ScriptType(StrEnum):
    """
    Quranic script variations from Tanzil.net (Version 1.1, February 2021).

    The Quran can be written in different orthographic styles.
    Each script has different Unicode character usage.
    """

    UTHMANI = "uthmani"
    """
    الرسم العثماني - Original Uthmani orthography.

    Features:
    - Uses Alif Wasla (ٱ U+0671) for definite article
    - Preserves Huruf Muqatta'at with maddah (الٓمٓ)
    - Includes small high letters (ۦ ۧ ۨ)
    - Precise tanween placement
    - Silent markers present (حَوْلَهُۥ)
    """

    UTHMANI_MINIMAL = "uthmani_min"
    """
    Uthmani script with simplified diacritics.

    - Alif Wasla simplified to regular Alif
    - Reduced small letters
    - Simplified diacritical marks
    """

    SIMPLE = "simple"
    """
    الرسم الإملائي - Modern standard Arabic spelling.

    Features:
    - Uses regular Alif (ا U+0627) throughout
    - No small high letters
    - Standard diacritical placement
    - Easier for modern readers
    """
