"""Text processing utilities for Arabic text."""

from mizan.infrastructure.text.entity_matcher import EntityVariantMatcher
from mizan.infrastructure.text.normalizer import ArabicNormalizer

__all__ = [
    "ArabicNormalizer",
    "EntityVariantMatcher",
]
