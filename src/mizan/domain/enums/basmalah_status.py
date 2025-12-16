"""Basmalah status definitions for Quranic surahs."""

from enum import StrEnum


class BasmalahStatus(StrEnum):
    """
    Classification of Basmalah status per Surah.

    The Basmalah (بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ) requires careful handling
    as its status varies across surahs.
    """

    NUMBERED_VERSE = "numbered_verse"
    """
    Basmalah is counted as verse 1.
    Only applies to Al-Fatiha (Surah 1).
    """

    OPENING_UNNUMBERED = "opening_unnumbered"
    """
    Basmalah is present but not counted as a verse.
    Applies to 111 surahs (2-8, 10-114 except 27 which has both).
    """

    ABSENT = "absent"
    """
    Basmalah is not present.
    Only applies to At-Tawbah (Surah 9) by scholarly consensus (Ijma').
    """

    WITHIN_VERSE = "within_verse"
    """
    Basmalah appears within verse text (not as opening).
    An-Naml 27:30 contains the Basmalah within the verse.
    """
