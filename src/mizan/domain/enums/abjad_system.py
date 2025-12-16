"""Abjad numeral system definitions."""

from enum import StrEnum


class AbjadSystem(StrEnum):
    """
    Abjad numeral systems used in Islamic tradition.

    The Abjad numerals assign numerical values to Arabic letters.
    Two main systems exist with different orderings for some letters.
    """

    MASHRIQI = "mashriqi"
    """
    Eastern (Mashriqi) system - Used in Levant, Iraq, Gulf regions.

    Standard mapping (أبجد هوز حطي كلمن سعفص قرشت ثخذ ضظغ):
    - أ=1, ب=2, ج=3, د=4, ه=5, و=6, ز=7, ح=8, ط=9
    - ي=10, ك=20, ل=30, م=40, ن=50, س=60, ع=70, ف=80, ص=90
    - ق=100, ر=200, ش=300, ت=400, ث=500, خ=600, ذ=700, ض=800, ظ=900, غ=1000
    """

    MAGHRIBI = "maghribi"
    """
    Western (Maghribi) system - Used in North Africa, Al-Andalus.

    Different ordering for letters س, ش, ص, ض:
    - ص=60, ض=90, س=300, ش=800
    """
