"""Letter counting method definitions."""

from enum import StrEnum


class LetterCountMethod(StrEnum):
    """
    Method for counting Arabic letters in Quranic text.

    Different scholarly traditions count letters differently,
    particularly regarding Alif variants. This enum provides
    standardized options based on verified scholarly practices.

    VERIFIED AGAINST SCHOLARLY DATA:
    - Al-Fatiha = 139 letters (traditional scholarly consensus)
    - Basmalah = 19 letters (famous traditional count)
    """

    TRADITIONAL = "traditional"
    """
    التعداد التقليدي - Traditional scholarly counting method.

    This is the DEFAULT and RECOMMENDED method.

    Rules:
    - Count base Arabic letters (28 letters)
    - INCLUDE Alif Wasla (ٱ) as Alif - it represents Alif in speech
    - EXCLUDE Alif Khanjariyya (ـٰ) - it's a diacritical mark
    - EXCLUDE all tashkeel (diacritical marks)

    VERIFIED RESULTS:
    - Al-Fatiha = 139 letters (matches scholarly consensus)
    - Basmalah = 19 letters (matches traditional count)

    Used by: Traditional Islamic scholarship, classical tafasir
    """

    UTHMANI_FULL = "uthmani_full"
    """
    التعداد العثماني الكامل - Full Uthmani script counting.

    Rules:
    - Count base Arabic letters (28 letters)
    - INCLUDE Alif Wasla (ٱ) as Alif
    - INCLUDE Alif Khanjariyya (ـٰ) as Alif
    - EXCLUDE all tashkeel (diacritical marks)

    Results for Al-Fatiha: 145 letters

    Used by: Some modern digital Quran analysis tools
    """

    NO_WASLA = "no_wasla"
    """
    بدون ألف الوصل - Base letters only.

    Rules:
    - Count base Arabic letters (28 letters) only
    - EXCLUDE Alif Wasla (ٱ)
    - EXCLUDE Alif Khanjariyya (ـٰ)
    - EXCLUDE all tashkeel (diacritical marks)

    Results for Al-Fatiha: 125 letters (Uthmani), 143 letters (Simple)

    Used by: Low-level text analysis, comparing scripts
    """
