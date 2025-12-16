"""
Entity variant matcher - Prefix-aware word matching.

Implements the entity variant matching algorithm from Appendix G.
"""

from typing import Final


class EntityVariantMatcher:
    """
    Matches Arabic words with their prefix-attached variants.

    Arabic words often have prefixes (prepositions, conjunctions) attached.
    This class generates all possible forms for matching.

    Example:
        الله matches: الله, بالله, والله, فالله, لله, كالله
    """

    # Single-letter matchable prefixes
    MATCHABLE_PREFIXES: Final[frozenset[str]] = frozenset([
        "بِ", "بـ", "ب",  # Preposition "bi" (by/with)
        "وَ", "وـ", "و",  # Conjunction "wa" (and)
        "فَ", "فـ", "ف",  # Conjunction "fa" (so/then)
        "لِ", "لـ", "ل",  # Preposition "li" (to/for)
        "كَ", "كـ", "ك",  # Preposition "ka" (like/as)
        "أَ", "أ",        # Interrogative/vocative
        "يَا", "يا",      # Vocative particle
    ])

    # Combined prefixes (multiple prefixes together)
    COMBINED_PREFIXES: Final[frozenset[str]] = frozenset([
        "وَبِ", "وب",    # wa + bi
        "فَبِ", "فب",    # fa + bi
        "وَلِ", "ول",    # wa + li
        "فَلِ", "فل",    # fa + li
        "وَكَ", "وك",    # wa + ka
        "فَكَ", "فك",    # fa + ka
        "أَبِ", "أب",    # a + bi
        "أَفَ", "أف",    # a + fa
        "أَوَ", "أو",    # a + wa
    ])

    # All prefixes combined
    ALL_PREFIXES: Final[frozenset[str]] = MATCHABLE_PREFIXES | COMBINED_PREFIXES

    def __init__(self, base_word: str) -> None:
        """
        Initialize matcher with a base word.

        Args:
            base_word: The canonical form of the word to match
        """
        self._base_word = base_word
        self._all_forms = self._generate_all_forms()

    def _generate_all_forms(self) -> frozenset[str]:
        """Generate all possible prefixed forms of the base word."""
        forms: set[str] = {self._base_word}

        # Add single prefix forms
        for prefix in self.MATCHABLE_PREFIXES:
            # Strip tashkeel from prefix for matching
            clean_prefix = self._strip_tashkeel(prefix)
            forms.add(clean_prefix + self._base_word)
            forms.add(prefix + self._base_word)

        # Add combined prefix forms
        for prefix in self.COMBINED_PREFIXES:
            clean_prefix = self._strip_tashkeel(prefix)
            forms.add(clean_prefix + self._base_word)
            forms.add(prefix + self._base_word)

        # Handle special case: word starting with ال (definite article)
        if self._base_word.startswith("ال") or self._base_word.startswith("ٱل"):
            # Words with ال can also have prefixes attached differently
            base_without_al = self._base_word[2:]  # Remove ال
            for prefix in ["لِل", "لل", "بِال", "بال", "وَال", "وال", "فَال", "فال", "كَال", "كال"]:
                clean = self._strip_tashkeel(prefix)
                forms.add(clean + base_without_al)
                forms.add(prefix + base_without_al)

        return frozenset(forms)

    def _strip_tashkeel(self, text: str) -> str:
        """Remove diacritical marks from text."""
        TASHKEEL = frozenset([
            "\u064B", "\u064C", "\u064D", "\u064E", "\u064F",
            "\u0650", "\u0651", "\u0652", "\u0653", "\u0654",
            "\u0655", "\u0670",
        ])
        return "".join(c for c in text if c not in TASHKEEL)

    def matches(self, word: str) -> bool:
        """
        Check if a word matches any form of the base word.

        Args:
            word: Word to check

        Returns:
            True if word matches any known form
        """
        # Direct match
        if word in self._all_forms:
            return True

        # Try without tashkeel
        clean_word = self._strip_tashkeel(word)
        clean_forms = {self._strip_tashkeel(f) for f in self._all_forms}
        return clean_word in clean_forms

    def get_all_forms(self) -> frozenset[str]:
        """Get all known forms of this word."""
        return self._all_forms

    @property
    def base_word(self) -> str:
        """Get the base (canonical) word."""
        return self._base_word

    def extract_prefix(self, word: str) -> tuple[str, str] | None:
        """
        Extract prefix from a word if it matches.

        Args:
            word: Word to analyze

        Returns:
            Tuple of (prefix, base) or None if no match
        """
        if not self.matches(word):
            return None

        # Check each prefix
        for prefix in sorted(self.ALL_PREFIXES, key=len, reverse=True):
            clean_prefix = self._strip_tashkeel(prefix)
            if word.startswith(prefix) or word.startswith(clean_prefix):
                actual_prefix = prefix if word.startswith(prefix) else clean_prefix
                remainder = word[len(actual_prefix):]
                if self._strip_tashkeel(remainder) == self._strip_tashkeel(self._base_word):
                    return (actual_prefix, remainder)

        # No prefix - exact match
        if self.matches(word):
            return ("", word)

        return None


class EntityMatcher:
    """
    Matcher for multiple entity forms (e.g., Divine Names, Prophet names).

    Maintains a collection of EntityVariantMatchers for efficient lookup.
    """

    def __init__(self, entities: dict[str, list[str]]) -> None:
        """
        Initialize with entity definitions.

        Args:
            entities: Dictionary mapping entity names to list of variant forms
                     e.g., {"Allah": ["الله", "اللَّه"], "Rahman": ["الرحمن"]}
        """
        self._matchers: dict[str, list[EntityVariantMatcher]] = {}
        for name, variants in entities.items():
            self._matchers[name] = [EntityVariantMatcher(v) for v in variants]

    def find_entity(self, word: str) -> str | None:
        """
        Find which entity a word matches, if any.

        Args:
            word: Word to check

        Returns:
            Entity name if found, None otherwise
        """
        for entity_name, matchers in self._matchers.items():
            for matcher in matchers:
                if matcher.matches(word):
                    return entity_name
        return None

    def get_entity_forms(self, entity_name: str) -> set[str]:
        """
        Get all known forms for an entity.

        Args:
            entity_name: Name of the entity

        Returns:
            Set of all word forms
        """
        if entity_name not in self._matchers:
            return set()

        forms: set[str] = set()
        for matcher in self._matchers[entity_name]:
            forms.update(matcher.get_all_forms())
        return forms

    @property
    def entity_names(self) -> list[str]:
        """Get list of all entity names."""
        return list(self._matchers.keys())
