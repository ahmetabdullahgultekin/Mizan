"""Mushaf edition definitions."""

from enum import StrEnum


class MushafEdition(StrEnum):
    """
    Authorized Mushaf editions with scholarly recognition.

    Each edition has specific characteristics and is recognized
    by Islamic scholarly institutions.
    """

    MADINAH_HAFS = "madinah_hafs"
    """
    King Fahd Complex, Madinah - Hafs recitation.
    مجمع الملك فهد لطباعة المصحف الشريف
    Most widely distributed and authenticated Mushaf globally.
    """

    MADINAH_WARSH = "madinah_warsh"
    """
    King Fahd Complex, Madinah - Warsh recitation.
    Used primarily in North and West Africa.
    """

    EGYPTIAN_STANDARD = "egyptian_standard"
    """
    Al-Azhar 1924 Edition.
    Historic standardization effort by Egyptian scholars.
    """

    INDO_PAK = "indo_pak"
    """
    Indo-Pakistani script.
    Uses different calligraphic style common in South Asia.
    """

    TANZIL_UTHMANI = "tanzil_uthmani"
    """
    Tanzil.net Uthmani text.
    Digital version maintaining Uthmani orthography.
    """

    TANZIL_SIMPLE = "tanzil_simple"
    """
    Tanzil.net Simple text.
    Digital version with simplified/modern orthography.
    """
