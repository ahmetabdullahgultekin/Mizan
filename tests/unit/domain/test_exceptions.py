"""Unit tests for domain exceptions."""

import pytest
from mizan.domain.exceptions import (
    DomainException,
    VerseNotFoundError,
    InvalidVerseLocationError,
    VerseRangeError,
    SurahNotFoundError,
    InvalidSurahNumberError,
    IntegrityViolationError,
    ChecksumMismatchError,
    AnalysisConfigurationError,
    UnsupportedAnalysisError,
    MorphologyDataNotFoundError,
    InvalidRootError,
    EntityNotFoundError,
    IngestionError,
    DataSourceUnavailableError,
)
from mizan.domain.value_objects import VerseLocation, TextChecksum


class TestDomainException:
    """Tests for base DomainException."""

    def test_create_with_message(self):
        """Test creating exception with message."""
        exc = DomainException("Test error")
        assert str(exc) == "Test error"
        assert exc.message == "Test error"

    def test_create_with_code(self):
        """Test creating exception with custom code."""
        exc = DomainException("Test error", code="CUSTOM_CODE")
        assert exc.code == "CUSTOM_CODE"

    def test_default_code(self):
        """Test default code is class name."""
        exc = DomainException("Test error")
        assert exc.code == "DomainException"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        exc = DomainException("Test error", code="TEST")
        result = exc.to_dict()
        assert result["error"] == "TEST"
        assert result["message"] == "Test error"


class TestVerseNotFoundError:
    """Tests for VerseNotFoundError."""

    def test_create_with_location(self):
        """Test creating with VerseLocation."""
        loc = VerseLocation(surah_number=2, verse_number=286)
        exc = VerseNotFoundError(loc)
        assert exc.location == loc
        assert "2:286" in str(exc)
        assert exc.code == "VERSE_NOT_FOUND"


class TestInvalidVerseLocationError:
    """Tests for InvalidVerseLocationError."""

    def test_create_basic(self):
        """Test creating with basic parameters."""
        exc = InvalidVerseLocationError(surah=0, verse=1)
        assert exc.surah == 0
        assert exc.verse == 1
        assert "0:1" in str(exc)

    def test_create_with_reason(self):
        """Test creating with reason."""
        exc = InvalidVerseLocationError(surah=1, verse=10, reason="Exceeds max verses")
        assert "Exceeds max verses" in str(exc)
        assert exc.code == "INVALID_VERSE_LOCATION"


class TestVerseRangeError:
    """Tests for VerseRangeError."""

    def test_create_with_range(self):
        """Test creating with verse range."""
        start = VerseLocation(surah_number=2, verse_number=100)
        end = VerseLocation(surah_number=1, verse_number=1)  # Invalid: end before start
        exc = VerseRangeError(start, end, reason="End before start")
        assert exc.start == start
        assert exc.end == end
        assert "End before start" in str(exc)


class TestSurahNotFoundError:
    """Tests for SurahNotFoundError."""

    def test_create(self):
        """Test creating with surah number."""
        exc = SurahNotFoundError(surah_number=999)
        assert exc.surah_number == 999
        assert "999" in str(exc)
        assert exc.code == "SURAH_NOT_FOUND"


class TestInvalidSurahNumberError:
    """Tests for InvalidSurahNumberError."""

    def test_create(self):
        """Test creating with invalid surah number."""
        exc = InvalidSurahNumberError(surah_number=0)
        assert exc.surah_number == 0
        assert "between 1 and 114" in str(exc)


class TestIntegrityViolationError:
    """Tests for IntegrityViolationError."""

    def test_create(self):
        """Test creating with checksums."""
        expected = TextChecksum.compute("original")
        actual = TextChecksum.compute("modified")
        exc = IntegrityViolationError(expected, actual, context="Test verse")
        assert exc.expected == expected
        assert exc.actual == actual
        assert "CRITICAL" in str(exc)
        assert "Test verse" in str(exc)


class TestChecksumMismatchError:
    """Tests for ChecksumMismatchError."""

    def test_create(self):
        """Test creating with entity info."""
        exc = ChecksumMismatchError(entity_type="verse", entity_id="2:255")
        assert exc.entity_type == "verse"
        assert exc.entity_id == "2:255"
        assert "verse" in str(exc)


class TestAnalysisConfigurationError:
    """Tests for AnalysisConfigurationError."""

    def test_create(self):
        """Test creating with configuration info."""
        exc = AnalysisConfigurationError(
            parameter="normalization",
            value="invalid",
            reason="Not a valid normalization level"
        )
        assert exc.parameter == "normalization"
        assert exc.value == "invalid"
        assert "normalization=invalid" in str(exc)


class TestUnsupportedAnalysisError:
    """Tests for UnsupportedAnalysisError."""

    def test_create_basic(self):
        """Test creating with analysis type."""
        exc = UnsupportedAnalysisError(analysis_type="unknown_type")
        assert exc.analysis_type == "unknown_type"
        assert "unknown_type" in str(exc)

    def test_create_with_tier(self):
        """Test creating with tier info."""
        exc = UnsupportedAnalysisError(analysis_type="semantic_search", tier=4)
        assert exc.tier == 4
        assert "Tier 4" in str(exc)
        assert "Experimental" in str(exc)


class TestMorphologyDataNotFoundError:
    """Tests for MorphologyDataNotFoundError."""

    def test_create_basic(self):
        """Test creating with word."""
        exc = MorphologyDataNotFoundError(word="كلمة")
        assert exc.word == "كلمة"
        assert "كلمة" in str(exc)

    def test_create_with_location(self):
        """Test creating with location."""
        loc = VerseLocation(surah_number=2, verse_number=1)
        exc = MorphologyDataNotFoundError(word="كلمة", location=loc)
        assert exc.location == loc
        assert "2:1" in str(exc)


class TestInvalidRootError:
    """Tests for InvalidRootError."""

    def test_create(self):
        """Test creating with invalid root."""
        exc = InvalidRootError(root="ك")  # Too short
        assert exc.root == "ك"
        assert "3 (trilateral) or 4 (quadrilateral)" in str(exc)


class TestEntityNotFoundError:
    """Tests for EntityNotFoundError."""

    def test_create(self):
        """Test creating with entity info."""
        exc = EntityNotFoundError(entity_type="divine_name", entity_name="Unknown")
        assert exc.entity_type == "divine_name"
        assert exc.entity_name == "Unknown"
        assert "divine_name" in str(exc)


class TestIngestionError:
    """Tests for IngestionError."""

    def test_create(self):
        """Test creating with source and reason."""
        exc = IngestionError(source="tanzil", reason="Invalid XML format")
        assert exc.source == "tanzil"
        assert exc.reason == "Invalid XML format"
        assert "tanzil" in str(exc)


class TestDataSourceUnavailableError:
    """Tests for DataSourceUnavailableError."""

    def test_create_basic(self):
        """Test creating with source name."""
        exc = DataSourceUnavailableError(source="masaq")
        assert exc.source == "masaq"
        assert "masaq" in str(exc)

    def test_create_with_path(self):
        """Test creating with file path."""
        exc = DataSourceUnavailableError(source="masaq", path="/data/masaq.tsv")
        assert exc.path == "/data/masaq.tsv"
        assert "/data/masaq.tsv" in str(exc)
