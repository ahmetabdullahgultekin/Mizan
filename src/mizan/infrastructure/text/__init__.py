"""Text processing utilities for Arabic text."""

from mizan.infrastructure.text.normalizer import ArabicNormalizer
from mizan.infrastructure.text.entity_matcher import EntityVariantMatcher

__all__ = [
    "ArabicNormalizer",
    "EntityVariantMatcher",
]
