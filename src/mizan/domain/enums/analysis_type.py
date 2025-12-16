"""Analysis type definitions for all supported operations."""

from enum import StrEnum


class AnalysisType(StrEnum):
    """
    Types of analysis operations supported by the engine.

    Organized by category and implementation tier.
    """

    # =========================================================================
    # Basic Counting (Tier 1)
    # =========================================================================
    LETTER_COUNT = "letter_count"
    """Count total Arabic letters in text."""

    WORD_COUNT = "word_count"
    """Count total words in text."""

    VERSE_COUNT = "verse_count"
    """Count total verses in scope."""

    # =========================================================================
    # Frequency Analysis (Tier 1)
    # =========================================================================
    LETTER_FREQUENCY = "letter_frequency"
    """Frequency distribution of each Arabic letter."""

    WORD_FREQUENCY = "word_frequency"
    """Frequency distribution of words."""

    ROOT_FREQUENCY = "root_frequency"
    """Frequency distribution of word roots (Tier 3)."""

    # =========================================================================
    # Numerical Analysis (Tier 1)
    # =========================================================================
    ABJAD_VALUE = "abjad_value"
    """Calculate Abjad/Gematria numerical value."""

    PRIME_CHECK = "prime_check"
    """Check if a count or Abjad value is prime."""

    MODULAR_ARITHMETIC = "modular_arithmetic"
    """Perform modular arithmetic on counts/values."""

    NUMBER_WORD_COUNT = "number_word_count"
    """Count occurrences of number words (أحد، اثنان، etc.)."""

    # =========================================================================
    # Morphological Analysis (Tier 3)
    # =========================================================================
    ROOT_EXTRACTION = "root_extraction"
    """Extract trilateral/quadrilateral root."""

    PATTERN_EXTRACTION = "pattern_extraction"
    """Extract morphological pattern (وزن - verb/noun patterns)."""

    WORD_TYPE_ANALYSIS = "word_type_analysis"
    """Determine word type (اسم/فعل/حرف - noun/verb/particle)."""

    VERB_TENSE_ANALYSIS = "verb_tense_analysis"
    """Determine verb tense (ماضي/مضارع/أمر - past/present/imperative)."""

    # =========================================================================
    # Search & Pattern (Tier 1-2)
    # =========================================================================
    PATTERN_SEARCH = "pattern_search"
    """Search for regex patterns in text."""

    SPECIFIC_WORD_SEARCH = "specific_word_search"
    """Search for specific word occurrences."""

    ROOT_SEARCH = "root_search"
    """Search for all words from a root (Tier 3)."""

    PHRASE_SEARCH = "phrase_search"
    """Search for phrase occurrences."""

    # =========================================================================
    # Entity Analysis (Tier 2)
    # =========================================================================
    DIVINE_NAME_ANALYSIS = "divine_name_analysis"
    """Analyze occurrences of أسماء الله الحسنى (99 names)."""

    PROPHET_NAME_ANALYSIS = "prophet_name_analysis"
    """Analyze occurrences of prophet names (25 prophets)."""

    PROPER_NOUN_EXTRACTION = "proper_noun_extraction"
    """Extract proper nouns (places, peoples, etc.)."""

    # =========================================================================
    # Structural Analysis (Tier 5 - Research Tools)
    # =========================================================================
    VERSE_ENDING_PATTERN = "verse_ending_pattern"
    """Analyze verse ending patterns (فواصل)."""

    RING_STRUCTURE = "ring_structure"
    """Detect ring/chiastic structure (بنية دائرية)."""

    PARALLEL_PASSAGE = "parallel_passage"
    """Find parallel passages across surahs."""

    # =========================================================================
    # Thematic Analysis (Tier 4 - Experimental)
    # =========================================================================
    TOPIC_EXTRACTION = "topic_extraction"
    """Extract topics using LDA modeling."""

    CROSS_REFERENCE = "cross_reference"
    """Find thematically related verses."""

    SEMANTIC_FIELD = "semantic_field"
    """Analyze semantic fields of concepts."""

    # =========================================================================
    # Comparative Analysis (Tier 1-2)
    # =========================================================================
    WORD_PAIR_COMPARISON = "word_pair_comparison"
    """Compare occurrences of word pairs (الدنيا vs الآخرة)."""

    SURAH_COMPARISON = "surah_comparison"
    """Compare statistics across surahs."""

    MECCAN_MEDINAN_COMPARISON = "meccan_medinan_comparison"
    """Compare Meccan vs Medinan characteristics."""

    # =========================================================================
    # Graph/Relationship Analysis (Tier 4 - Experimental)
    # =========================================================================
    CO_OCCURRENCE_NETWORK = "co_occurrence_network"
    """Build word co-occurrence networks."""

    CONCEPT_MAP = "concept_map"
    """Generate concept relationship maps."""
