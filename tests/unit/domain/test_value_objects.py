"""Unit tests for domain value objects."""

import pytest
from mizan.domain.value_objects import VerseLocation, TextChecksum, AbjadValue, SurahMetadata
from mizan.domain.enums import AbjadSystem, BasmalahStatus, RevelationType


class TestVerseLocation:
    """Tests for VerseLocation value object."""

    def test_create_valid_location(self):
        """Test creating a valid verse location."""
        loc = VerseLocation(surah_number=1, verse_number=1)
        assert loc.surah_number == 1
        assert loc.verse_number == 1

    def test_create_location_last_surah(self):
        """Test creating location for last surah."""
        loc = VerseLocation(surah_number=114, verse_number=6)
        assert loc.surah_number == 114
        assert loc.verse_number == 6

    def test_create_location_ayat_kursi(self):
        """Test creating location for Ayat al-Kursi."""
        loc = VerseLocation(surah_number=2, verse_number=255)
        assert str(loc) == "2:255"

    def test_invalid_surah_zero(self):
        """Test that surah 0 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid surah number"):
            VerseLocation(surah_number=0, verse_number=1)

    def test_invalid_surah_too_high(self):
        """Test that surah > 114 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid surah number"):
            VerseLocation(surah_number=115, verse_number=1)

    def test_invalid_verse_zero(self):
        """Test that verse 0 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid verse number"):
            VerseLocation(surah_number=1, verse_number=0)

    def test_invalid_verse_negative(self):
        """Test that negative verse raises ValueError."""
        with pytest.raises(ValueError, match="Invalid verse number"):
            VerseLocation(surah_number=1, verse_number=-1)

    def test_invalid_verse_exceeds_surah_length(self):
        """Test that verse exceeding surah length raises ValueError."""
        # Al-Fatiha has only 7 verses
        with pytest.raises(ValueError, match="Maximum is 7"):
            VerseLocation(surah_number=1, verse_number=8)

    def test_str_representation(self):
        """Test string representation."""
        loc = VerseLocation(surah_number=2, verse_number=255)
        assert str(loc) == "2:255"

    def test_from_string_valid(self):
        """Test creating from valid string."""
        loc = VerseLocation.from_string("2:255")
        assert loc.surah_number == 2
        assert loc.verse_number == 255

    def test_from_string_with_spaces(self):
        """Test creating from string with spaces."""
        loc = VerseLocation.from_string("  2:255  ")
        assert loc.surah_number == 2
        assert loc.verse_number == 255

    def test_from_string_invalid_format(self):
        """Test invalid string format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid location format"):
            VerseLocation.from_string("2-255")

    def test_from_string_non_integer(self):
        """Test non-integer values raise ValueError."""
        with pytest.raises(ValueError, match="must be integers"):
            VerseLocation.from_string("two:255")

    def test_immutability(self):
        """Test that VerseLocation is immutable."""
        loc = VerseLocation(surah_number=1, verse_number=1)
        with pytest.raises(AttributeError):
            loc.surah_number = 2  # type: ignore

    def test_equality(self):
        """Test equality comparison."""
        loc1 = VerseLocation(surah_number=2, verse_number=255)
        loc2 = VerseLocation(surah_number=2, verse_number=255)
        assert loc1 == loc2

    def test_ordering(self):
        """Test ordering comparison."""
        loc1 = VerseLocation(surah_number=1, verse_number=7)
        loc2 = VerseLocation(surah_number=2, verse_number=1)
        assert loc1 < loc2

    def test_ordering_same_surah(self):
        """Test ordering within same surah."""
        loc1 = VerseLocation(surah_number=2, verse_number=100)
        loc2 = VerseLocation(surah_number=2, verse_number=255)
        assert loc1 < loc2

    def test_is_first_verse(self):
        """Test is_first_verse method."""
        loc1 = VerseLocation(surah_number=2, verse_number=1)
        loc2 = VerseLocation(surah_number=2, verse_number=2)
        assert loc1.is_first_verse()
        assert not loc2.is_first_verse()

    def test_is_last_verse(self):
        """Test is_last_verse method."""
        loc1 = VerseLocation(surah_number=1, verse_number=7)  # Fatiha has 7 verses
        loc2 = VerseLocation(surah_number=1, verse_number=1)
        assert loc1.is_last_verse()
        assert not loc2.is_last_verse()

    def test_next_verse(self):
        """Test next_verse method."""
        loc = VerseLocation(surah_number=1, verse_number=1)
        next_loc = loc.next_verse()
        assert next_loc is not None
        assert next_loc.verse_number == 2

    def test_next_verse_at_end(self):
        """Test next_verse at end of surah returns None."""
        loc = VerseLocation(surah_number=1, verse_number=7)
        assert loc.next_verse() is None

    def test_previous_verse(self):
        """Test previous_verse method."""
        loc = VerseLocation(surah_number=1, verse_number=2)
        prev_loc = loc.previous_verse()
        assert prev_loc is not None
        assert prev_loc.verse_number == 1

    def test_previous_verse_at_start(self):
        """Test previous_verse at start of surah returns None."""
        loc = VerseLocation(surah_number=1, verse_number=1)
        assert loc.previous_verse() is None


class TestTextChecksum:
    """Tests for TextChecksum value object."""

    def test_compute_sha256(self):
        """Test computing SHA256 checksum."""
        checksum = TextChecksum.compute("test", algorithm="sha256")
        assert checksum.algorithm == "sha256"
        assert len(checksum.value) == 64  # SHA256 produces 64 hex chars

    def test_compute_sha512(self):
        """Test computing SHA512 checksum."""
        checksum = TextChecksum.compute("test", algorithm="sha512")
        assert checksum.algorithm == "sha512"
        assert len(checksum.value) == 128  # SHA512 produces 128 hex chars

    def test_compute_arabic_text(self, basmalah_simple):
        """Test checksum of Arabic text."""
        checksum = TextChecksum.compute(basmalah_simple)
        assert checksum.algorithm == "sha256"
        assert len(checksum.value) == 64

    def test_verify_correct(self):
        """Test verification with correct text."""
        text = "بسم الله الرحمن الرحيم"
        checksum = TextChecksum.compute(text)
        assert checksum.verify(text) is True

    def test_verify_incorrect(self):
        """Test verification with incorrect text."""
        checksum = TextChecksum.compute("original")
        assert checksum.verify("modified") is False

    def test_verify_arabic_diacritics_matter(self):
        """Test that diacritics affect checksum."""
        text1 = "بسم"
        text2 = "بِسْمِ"
        checksum1 = TextChecksum.compute(text1)
        checksum2 = TextChecksum.compute(text2)
        assert checksum1.value != checksum2.value

    def test_unsupported_algorithm(self):
        """Test unsupported algorithm raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported algorithm"):
            TextChecksum.compute("test", algorithm="md5")

    def test_from_string(self):
        """Test creating from string representation."""
        checksum = TextChecksum.compute("test")
        string_rep = str(checksum)
        restored = TextChecksum.from_string(string_rep)
        assert restored.algorithm == checksum.algorithm
        assert restored.value == checksum.value

    def test_matches(self):
        """Test matches method."""
        checksum1 = TextChecksum.compute("test")
        checksum2 = TextChecksum.compute("test")
        assert checksum1.matches(checksum2)

    def test_immutability(self):
        """Test that TextChecksum is immutable."""
        checksum = TextChecksum.compute("test")
        with pytest.raises(AttributeError):
            checksum.value = "modified"  # type: ignore


class TestAbjadValue:
    """Tests for AbjadValue value object."""

    def test_create_valid(self):
        """Test creating valid AbjadValue."""
        # ب=2, س=60, م=40 → total=102
        value = AbjadValue(
            system=AbjadSystem.MASHRIQI,
            value=102,
            letter_breakdown=(("ب", 2), ("س", 60), ("م", 40)),
        )
        assert value.value == 102
        assert value.system == AbjadSystem.MASHRIQI

    def test_breakdown_sum_validation(self):
        """Test that breakdown must sum to value."""
        with pytest.raises(ValueError, match="does not match"):
            AbjadValue(
                system=AbjadSystem.MASHRIQI,
                value=100,  # Wrong total
                letter_breakdown=(("ب", 2), ("س", 60), ("م", 40)),  # Sums to 102
            )

    def test_negative_value_rejected(self):
        """Test that negative values are rejected."""
        with pytest.raises(ValueError, match="cannot be negative"):
            AbjadValue(
                system=AbjadSystem.MASHRIQI,
                value=-1,
                letter_breakdown=(),
            )

    def test_is_prime_true(self):
        """Test is_prime for prime number."""
        value = AbjadValue(
            system=AbjadSystem.MASHRIQI,
            value=7,
            letter_breakdown=(("ز", 7),),
        )
        assert value.is_prime() is True

    def test_is_prime_false(self):
        """Test is_prime for non-prime number."""
        value = AbjadValue(
            system=AbjadSystem.MASHRIQI,
            value=4,
            letter_breakdown=(("د", 4),),
        )
        assert value.is_prime() is False

    def test_digital_root(self):
        """Test digital root calculation."""
        # Test digital root of 10: 1+0 = 1
        value1 = AbjadValue(
            system=AbjadSystem.MASHRIQI,
            value=10,
            letter_breakdown=(("ي", 10),),
        )
        assert value1.digital_root() == 1

        # Test digital root of 21: 2+1 = 3
        value2 = AbjadValue(
            system=AbjadSystem.MASHRIQI,
            value=21,
            letter_breakdown=(("ك", 20), ("ا", 1)),
        )
        assert value2.digital_root() == 3

        # Test digital root of 786: 7+8+6 = 21 → 2+1 = 3
        # ش=300, ف=80, ق=100, ر=200, و=6, ق=100 → total=786
        value3 = AbjadValue(
            system=AbjadSystem.MASHRIQI,
            value=786,
            letter_breakdown=(("ش", 300), ("ف", 80), ("ق", 100), ("ر", 200), ("و", 6), ("ق", 100)),
        )
        assert value3.digital_root() == 3

    def test_modulo(self):
        """Test modulo operation."""
        value = AbjadValue(
            system=AbjadSystem.MASHRIQI,
            value=100,
            letter_breakdown=(("ق", 100),),
        )
        assert value.modulo(19) == 5  # 100 % 19 = 5

    def test_modulo_division_by_zero(self):
        """Test modulo by zero raises ValueError."""
        value = AbjadValue(
            system=AbjadSystem.MASHRIQI,
            value=100,
            letter_breakdown=(("ق", 100),),
        )
        with pytest.raises(ValueError, match="divisor of 0"):
            value.modulo(0)

    def test_int_conversion(self):
        """Test conversion to int."""
        value = AbjadValue(
            system=AbjadSystem.MASHRIQI,
            value=100,
            letter_breakdown=(("ق", 100),),
        )
        assert int(value) == 100

    def test_addition(self):
        """Test addition with integer."""
        value = AbjadValue(
            system=AbjadSystem.MASHRIQI,
            value=100,
            letter_breakdown=(("ق", 100),),
        )
        assert value + 50 == 150
        assert 50 + value == 150


class TestSurahMetadata:
    """Tests for SurahMetadata value object."""

    def test_create_valid(self, fatiha_metadata):
        """Test creating valid SurahMetadata."""
        assert fatiha_metadata.number == 1
        assert fatiha_metadata.name_arabic == "الفاتحة"
        assert fatiha_metadata.verse_count == 7

    def test_invalid_surah_number(self):
        """Test invalid surah number raises ValueError."""
        with pytest.raises(ValueError, match="Invalid surah number"):
            SurahMetadata(
                number=0,
                name_arabic="Test",
                name_english="Test",
                name_transliteration="Test",
                revelation_type=RevelationType.MECCAN,
                revelation_order=1,
                verse_count=1,
                basmalah_status=BasmalahStatus.OPENING_UNNUMBERED,
                ruku_count=1,
            )

    def test_is_meccan(self, fatiha_metadata, tawbah_metadata):
        """Test is_meccan property."""
        assert fatiha_metadata.is_meccan is True
        assert tawbah_metadata.is_meccan is False

    def test_is_medinan(self, fatiha_metadata, tawbah_metadata):
        """Test is_medinan property."""
        assert fatiha_metadata.is_medinan is False
        assert tawbah_metadata.is_medinan is True

    def test_has_basmalah(self, fatiha_metadata, tawbah_metadata):
        """Test has_basmalah property."""
        assert fatiha_metadata.has_basmalah is True
        assert tawbah_metadata.has_basmalah is False

    def test_basmalah_is_verse(self, fatiha_metadata, ikhlas_metadata):
        """Test basmalah_is_verse property."""
        assert fatiha_metadata.basmalah_is_verse is True
        assert ikhlas_metadata.basmalah_is_verse is False

    def test_immutability(self, fatiha_metadata):
        """Test that SurahMetadata is immutable."""
        with pytest.raises(AttributeError):
            fatiha_metadata.number = 2  # type: ignore
