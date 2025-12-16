"""Quranic recitation (Qira'at) type definitions."""

from enum import StrEnum


class QiraatType(StrEnum):
    """
    The ten canonical Qira'at and their primary Rawis.

    The Quran has been transmitted through multiple authentic chains
    of recitation (Qira'at). These affect letter counts and must be
    handled distinctly.
    """

    # Most common recitations
    HAFS_AN_ASIM = "hafs_an_asim"
    """
    حفص عن عاصم - Most widespread globally.
    Used in majority of Muslim world (Middle East, South Asia).
    """

    WARSH_AN_NAFI = "warsh_an_nafi"
    """
    ورش عن نافع - Used in North/West Africa.
    Notable differences in letter counts (e.g., مَالِكِ vs مَلِكِ in 1:4).
    """

    QALUN_AN_NAFI = "qalun_an_nafi"
    """قالون عن نافع - Used in Libya, Tunisia."""

    # Other authenticated Qira'at
    AL_DURI_AN_ABU_AMR = "duri_abu_amr"
    """الدوري عن أبي عمرو - Transmitted through Abu Amr."""

    AL_SUSI_AN_ABU_AMR = "susi_abu_amr"
    """السوسي عن أبي عمرو - Alternative riwayah of Abu Amr."""

    IBN_KATHIR = "ibn_kathir"
    """ابن كثير - Meccan recitation tradition."""

    IBN_AMIR = "ibn_amir"
    """ابن عامر - Damascene recitation tradition."""

    ASIM = "asim"
    """عاصم - Kufan recitation (Hafs is the primary rawi)."""

    HAMZA = "hamza"
    """حمزة - Kufan recitation with distinct hamza handling."""

    AL_KISAI = "kisai"
    """الكسائي - Kufan recitation."""

    KHALAF = "khalaf"
    """خلف العاشر - The tenth canonical qira'at."""
