"""
Mizan Core Engine - Global Standards Documentation

This module documents the scholarly standards that the Mizan Core Engine
follows for Quranic text analysis. All defaults are based on globally
accepted standards from authoritative sources.

VERIFIED AGAINST:
- Tanzil.net (Medina Mushaf, verified text)
- Quran.com API (Quranic Arabic Corpus, University of Leeds)
- IslamWeb Fatwa database
- Ibn Kathir Tafsir (classical reference)
- Wikipedia (Abjad numerals standard)
"""

# =============================================================================
# AUTHORITATIVE SOURCES
# =============================================================================

SOURCES = {
    "tanzil": {
        "name": "Tanzil.net",
        "url": "https://tanzil.net",
        "description": "Primary Quran text source, verified against Medina Mushaf",
        "statistics": {
            "total_surahs": 114,
            "total_verses": 6236,
            "total_words": 77430,
            "total_letters": 325666,  # Uthmani text
        },
    },
    "quran_corpus": {
        "name": "Quranic Arabic Corpus",
        "url": "https://corpus.quran.com",
        "description": "University of Leeds, morphological analysis",
        "statistics": {
            "total_verses": 6236,
            "total_words": 77429,  # 1 word difference at QS 37:130
        },
    },
    "islamweb": {
        "name": "IslamWeb Fatwa",
        "url": "https://www.islamweb.net",
        "description": "Classical scholarly statistics",
        "statistics": {
            "total_letters": 320015,  # Mujahid via Ibn Kathir
            "total_words": 77449,
        },
    },
}


# =============================================================================
# LETTER COUNTING STANDARDS
# =============================================================================

LETTER_COUNTING = {
    "standard_followed": "Modern Computational (Tanzil/Quran.com)",
    "methodology": """
    We follow the MODERN COMPUTATIONAL method:
    - Count all written Arabic letters
    - Include Alif Wasla (ٱ) as Alif
    - Exclude Alif Khanjariyya (ـٰ) as diacritical mark
    - Exclude all tashkeel (diacritical marks)
    - Shaddah counts as one letter (the written form)
    """,
    "verified_counts": {
        "al_fatiha_with_basmalah": 139,  # Uthmani, TRADITIONAL method
        "al_fatiha_without_basmalah": 120,  # verses 2-7 only
        "basmalah": 19,  # Famous traditional count
    },
    "alternative_methods": {
        "IBN_KATHIR_PHONETIC": """
        Classical method (not yet implemented):
        - Count only PRONOUNCED letters
        - Count shaddah as TWO letters (geminated consonant)
        - Exclude silent letters (like "lam" in definite article)
        - Al-Fatiha = 113 letters (without Basmalah)
        """,
    },
}


# =============================================================================
# ABJAD NUMERAL STANDARDS
# =============================================================================

ABJAD_STANDARDS = {
    "standard_followed": "Mashriqi (Eastern) System",
    "description": """
    The Abjad numeral system assigns numerical values to Arabic letters.
    We use the Mashriqi (Eastern) system as the default, which is the
    standard used throughout the Middle East and most Islamic scholarship.
    """,
    "mashriqi_values": {
        "ا": 1, "ب": 2, "ج": 3, "د": 4, "ه": 5, "و": 6, "ز": 7, "ح": 8, "ط": 9,
        "ي": 10, "ك": 20, "ل": 30, "م": 40, "ن": 50, "س": 60, "ع": 70, "ف": 80, "ص": 90,
        "ق": 100, "ر": 200, "ش": 300, "ت": 400, "ث": 500, "خ": 600, "ذ": 700, "ض": 800, "ظ": 900,
        "غ": 1000,
    },
    "verified_values": {
        "الله": 66,  # Allah - universally accepted
        "محمد": 92,  # Muhammad - universally accepted
        "بسم الله الرحمن الرحيم": 786,  # Basmalah - famous value
        "الرحمن": 329,  # Ar-Rahman
        "الرحيم": 289,  # Ar-Rahim
    },
    "alternative_system": "Maghribi (Western) - differs for letters 60-1000",
}


# =============================================================================
# WORD COUNTING STANDARDS
# =============================================================================

WORD_COUNTING = {
    "standard_followed": "Whitespace-delimited (Tanzil standard)",
    "methodology": """
    Words are counted by whitespace separation, which matches:
    - Tanzil.net methodology
    - Quran.com API word count
    - Academic Quran corpus standards
    """,
    "verified_counts": {
        "al_fatiha": 29,  # Including Basmalah
        "al_ikhlas": 15,
        "total_quran": 77430,  # Tanzil standard
    },
}


# =============================================================================
# DEFAULT CONFIGURATION
# =============================================================================

DEFAULTS = {
    "letter_counting_method": "TRADITIONAL",
    "abjad_system": "MASHRIQI",
    "text_source": "Tanzil.net Uthmani",
    "verse_count_standard": 6236,
}


# =============================================================================
# WHY THESE STANDARDS?
# =============================================================================

RATIONALE = """
We chose the Modern Computational standard (Tanzil/Quran.com) as our default
because:

1. REPRODUCIBILITY: Results can be independently verified using the same
   Unicode text and counting rules.

2. GLOBAL ADOPTION: Tanzil.net and Quran.com are used by millions of users
   worldwide and are the de facto standards for digital Quran applications.

3. ACADEMIC ACCEPTANCE: The Quranic Arabic Corpus (University of Leeds) uses
   compatible methodologies for linguistic analysis.

4. TRANSPARENCY: The counting rules are explicit and documented, unlike
   classical methods which may have implicit rules.

5. FLEXIBILITY: We provide multiple methods (TRADITIONAL, UTHMANI_FULL,
   NO_WASLA) to accommodate different scholarly needs.

Classical methods like Ibn Kathir's phonetic counting are valid for their
intended purposes (recitation analysis), but the modern computational method
is more suitable for text analysis applications.
"""
