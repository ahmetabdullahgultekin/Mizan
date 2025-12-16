"""Revelation type definitions for Quranic surahs."""

from enum import StrEnum


class RevelationType(StrEnum):
    """
    Place of revelation for Quranic surahs.

    Surahs are classified based on where they were primarily revealed.
    """

    MECCAN = "meccan"
    """
    مكية - Revealed in Makkah.
    Generally shorter surahs with themes of monotheism,
    resurrection, and moral principles.
    """

    MEDINAN = "medinan"
    """
    مدنية - Revealed in Madinah.
    Generally longer surahs with themes of legislation,
    social organization, and community building.
    """
