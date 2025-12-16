"""Sajdah (prostration) type definitions."""

from enum import StrEnum


class SajdahType(StrEnum):
    """
    Types of prostration verses in the Quran.

    Certain verses in the Quran are marked for prostration (سجدة التلاوة).
    """

    WAJIB = "wajib"
    """
    واجب - Obligatory prostration.
    According to Hanafi school, prostration is mandatory upon recitation.
    4 verses: 32:15, 41:37, 53:62, 96:19
    """

    MUSTAHABB = "mustahabb"
    """
    مستحب - Recommended prostration.
    Prostration is encouraged but not obligatory.
    11 verses: 7:206, 13:15, 16:50, 17:109, 19:58, 22:18, 22:77, 25:60, 27:26, 38:24, 84:21
    """
