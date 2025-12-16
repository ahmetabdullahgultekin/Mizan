"""Word form inclusion definitions for search operations."""

from enum import StrEnum


class WordFormInclusion(StrEnum):
    """
    Controls which word forms to include in search/counting operations.

    Arabic words often have prefixes (prepositions, conjunctions) and
    suffixes (pronouns) attached. This enum controls matching behavior.
    """

    EXACT_ONLY = "exact_only"
    """
    Match the exact word form only.
    Example: الله matches only الله, not بالله or والله
    """

    WITH_PREFIXES = "with_prefixes"
    """
    Match word with any attached prefixes.
    Includes: بِ، وَ، فَ، لِ، كَ، أَ، يَا and combinations.
    Example: الله matches الله, بالله, والله, فالله, كالله
    """

    WITH_SUFFIXES = "with_suffixes"
    """
    Match word with any attached suffixes.
    Includes: هُ، هَا، هُمْ، كَ، كُمْ، نَا، etc.
    Example: كتاب matches كتاب, كتابه, كتابهم, كتابك
    """

    WITH_BOTH = "with_both"
    """
    Match word with both prefixes and suffixes.
    Example: كتاب matches بكتابهم, وكتابك, etc.
    """

    LEMMA_BASED = "lemma_based"
    """
    Match based on dictionary lemma form.
    Uses morphological analysis to find lemma.
    Example: كتاب matches كتب, كاتب, مكتوب (same lemma family)
    """

    ROOT_BASED = "root_based"
    """
    Match based on trilateral/quadrilateral root.
    Example: root ك-ت-ب matches كتاب, كتب, كاتب, مكتبة, استكتب
    """

    ALL_DERIVATIVES = "all_derivatives"
    """
    Match all morphological derivatives from the root.
    Most inclusive option - use with caution for counting.
    """
