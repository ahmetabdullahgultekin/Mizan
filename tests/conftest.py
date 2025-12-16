"""
Pytest configuration and shared fixtures.

This file is automatically loaded by pytest and provides:
- Shared fixtures for all tests
- Configuration for async tests
- Sample data for testing
"""

import pytest
from uuid import uuid4

from mizan.domain.enums import (
    AbjadSystem,
    BasmalahStatus,
    QiraatType,
    RevelationType,
    SajdahType,
    ScriptType,
)
from mizan.domain.value_objects import (
    SurahMetadata,
    TextChecksum,
    VerseLocation,
)


# =============================================================================
# Sample Arabic Text Fixtures
# =============================================================================


@pytest.fixture
def basmalah_uthmani() -> str:
    """Basmalah in Uthmani script with Alif Wasla."""
    return "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ"


@pytest.fixture
def basmalah_simple() -> str:
    """Basmalah in simple script."""
    return "بسم الله الرحمن الرحيم"


@pytest.fixture
def fatiha_verse_1() -> str:
    """Al-Fatiha verse 1 (same as Basmalah)."""
    return "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ"


@pytest.fixture
def fatiha_verse_2() -> str:
    """Al-Fatiha verse 2."""
    return "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَـٰلَمِينَ"


@pytest.fixture
def ayat_al_kursi() -> str:
    """Ayat al-Kursi (2:255) - longest verse commonly referenced."""
    return (
        "ٱللَّهُ لَآ إِلَـٰهَ إِلَّا هُوَ ٱلْحَىُّ ٱلْقَيُّومُ ۚ لَا تَأْخُذُهُۥ سِنَةٌۭ وَلَا نَوْمٌۭ ۚ "
        "لَّهُۥ مَا فِى ٱلسَّمَـٰوَٰتِ وَمَا فِى ٱلْأَرْضِ ۗ مَن ذَا ٱلَّذِى يَشْفَعُ عِندَهُۥٓ إِلَّا بِإِذْنِهِۦ ۚ "
        "يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ ۖ وَلَا يُحِيطُونَ بِشَىْءٍۢ مِّنْ عِلْمِهِۦٓ إِلَّا بِمَا شَآءَ ۚ "
        "وَسِعَ كُرْسِيُّهُ ٱلسَّمَـٰوَٰتِ وَٱلْأَرْضَ ۖ وَلَا يَـُٔودُهُۥ حِفْظُهُمَا ۚ وَهُوَ ٱلْعَلِىُّ ٱلْعَظِيمُ"
    )


@pytest.fixture
def surah_ikhlas() -> list[str]:
    """Complete Surah Al-Ikhlas (112) - 4 verses."""
    return [
        "قُلْ هُوَ ٱللَّهُ أَحَدٌ",
        "ٱللَّهُ ٱلصَّمَدُ",
        "لَمْ يَلِدْ وَلَمْ يُولَدْ",
        "وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌۢ",
    ]


# =============================================================================
# Value Object Fixtures
# =============================================================================


@pytest.fixture
def verse_location_fatiha_1() -> VerseLocation:
    """VerseLocation for Al-Fatiha verse 1."""
    return VerseLocation(surah_number=1, verse_number=1)


@pytest.fixture
def verse_location_baqarah_255() -> VerseLocation:
    """VerseLocation for Ayat al-Kursi."""
    return VerseLocation(surah_number=2, verse_number=255)


@pytest.fixture
def verse_location_ikhlas_1() -> VerseLocation:
    """VerseLocation for Al-Ikhlas verse 1."""
    return VerseLocation(surah_number=112, verse_number=1)


@pytest.fixture
def sample_checksum() -> TextChecksum:
    """Sample checksum for testing."""
    return TextChecksum.compute("بسم الله الرحمن الرحيم")


# =============================================================================
# Surah Metadata Fixtures
# =============================================================================


@pytest.fixture
def fatiha_metadata() -> SurahMetadata:
    """Metadata for Al-Fatiha."""
    return SurahMetadata(
        number=1,
        name_arabic="الفاتحة",
        name_english="The Opening",
        name_transliteration="Al-Fatihah",
        revelation_type=RevelationType.MECCAN,
        revelation_order=5,
        verse_count=7,
        basmalah_status=BasmalahStatus.NUMBERED_VERSE,
        ruku_count=1,
        word_count=29,
        letter_count=139,
    )


@pytest.fixture
def ikhlas_metadata() -> SurahMetadata:
    """Metadata for Al-Ikhlas."""
    return SurahMetadata(
        number=112,
        name_arabic="الإخلاص",
        name_english="Sincerity",
        name_transliteration="Al-Ikhlas",
        revelation_type=RevelationType.MECCAN,
        revelation_order=22,
        verse_count=4,
        basmalah_status=BasmalahStatus.OPENING_UNNUMBERED,
        ruku_count=1,
        word_count=15,
        letter_count=47,
    )


@pytest.fixture
def tawbah_metadata() -> SurahMetadata:
    """Metadata for At-Tawbah (no Basmalah)."""
    return SurahMetadata(
        number=9,
        name_arabic="التوبة",
        name_english="The Repentance",
        name_transliteration="At-Tawbah",
        revelation_type=RevelationType.MEDINAN,
        revelation_order=113,
        verse_count=129,
        basmalah_status=BasmalahStatus.ABSENT,
        ruku_count=16,
        word_count=2506,
        letter_count=11116,
    )


# =============================================================================
# Service Instance Fixtures
# =============================================================================


@pytest.fixture
def letter_counter():
    """LetterCounter service instance."""
    from mizan.domain.services import LetterCounter
    return LetterCounter()


@pytest.fixture
def abjad_calculator():
    """AbjadCalculator service instance."""
    from mizan.domain.services import AbjadCalculator
    return AbjadCalculator()


@pytest.fixture
def word_counter():
    """WordCounter service instance."""
    from mizan.domain.services import WordCounter
    return WordCounter()
