"""Unit tests for domain enumerations."""

import pytest
from mizan.domain.enums import (
    AbjadSystem,
    AnalysisType,
    BasmalahStatus,
    MushafEdition,
    NormalizationLevel,
    QiraatType,
    RevelationType,
    SajdahType,
    ScriptType,
    WordFormInclusion,
)


class TestAbjadSystem:
    """Tests for AbjadSystem enum."""

    def test_mashriqi_value(self):
        """Test Mashriqi enum value."""
        assert AbjadSystem.MASHRIQI.value == "mashriqi"

    def test_maghribi_value(self):
        """Test Maghribi enum value."""
        assert AbjadSystem.MAGHRIBI.value == "maghribi"

    def test_all_values_are_strings(self):
        """Test that all enum values are strings."""
        for member in AbjadSystem:
            assert isinstance(member.value, str)


class TestScriptType:
    """Tests for ScriptType enum."""

    def test_uthmani_value(self):
        """Test Uthmani enum value."""
        assert ScriptType.UTHMANI.value == "uthmani"

    def test_simple_value(self):
        """Test Simple enum value."""
        assert ScriptType.SIMPLE.value == "simple"

    def test_uthmani_minimal_value(self):
        """Test Uthmani Minimal enum value."""
        assert ScriptType.UTHMANI_MINIMAL.value == "uthmani_min"


class TestQiraatType:
    """Tests for QiraatType enum."""

    def test_hafs_value(self):
        """Test Hafs enum value."""
        assert QiraatType.HAFS_AN_ASIM.value == "hafs_an_asim"

    def test_warsh_value(self):
        """Test Warsh enum value."""
        assert QiraatType.WARSH_AN_NAFI.value == "warsh_an_nafi"

    def test_all_qiraat_defined(self):
        """Test that major Qira'at are defined."""
        qiraat_names = [q.value for q in QiraatType]
        assert "hafs_an_asim" in qiraat_names
        assert "warsh_an_nafi" in qiraat_names
        assert "qalun_an_nafi" in qiraat_names


class TestBasmalahStatus:
    """Tests for BasmalahStatus enum."""

    def test_numbered_verse(self):
        """Test numbered verse status."""
        assert BasmalahStatus.NUMBERED_VERSE.value == "numbered_verse"

    def test_opening_unnumbered(self):
        """Test opening unnumbered status."""
        assert BasmalahStatus.OPENING_UNNUMBERED.value == "opening_unnumbered"

    def test_absent(self):
        """Test absent status."""
        assert BasmalahStatus.ABSENT.value == "absent"

    def test_within_verse(self):
        """Test within verse status."""
        assert BasmalahStatus.WITHIN_VERSE.value == "within_verse"


class TestRevelationType:
    """Tests for RevelationType enum."""

    def test_meccan_value(self):
        """Test Meccan enum value."""
        assert RevelationType.MECCAN.value == "meccan"

    def test_medinan_value(self):
        """Test Medinan enum value."""
        assert RevelationType.MEDINAN.value == "medinan"


class TestSajdahType:
    """Tests for SajdahType enum."""

    def test_wajib_value(self):
        """Test Wajib (obligatory) enum value."""
        assert SajdahType.WAJIB.value == "wajib"

    def test_mustahabb_value(self):
        """Test Mustahabb (recommended) enum value."""
        assert SajdahType.MUSTAHABB.value == "mustahabb"


class TestMushafEdition:
    """Tests for MushafEdition enum."""

    def test_madinah_hafs(self):
        """Test Madinah Hafs edition."""
        assert MushafEdition.MADINAH_HAFS.value == "madinah_hafs"

    def test_tanzil_editions(self):
        """Test Tanzil editions exist."""
        assert MushafEdition.TANZIL_UTHMANI.value == "tanzil_uthmani"
        assert MushafEdition.TANZIL_SIMPLE.value == "tanzil_simple"


class TestNormalizationLevel:
    """Tests for NormalizationLevel enum."""

    def test_none_value(self):
        """Test NONE level."""
        assert NormalizationLevel.NONE.value == "none"

    def test_full_value(self):
        """Test FULL level."""
        assert NormalizationLevel.FULL.value == "full"

    def test_progressive_levels(self):
        """Test that all progressive levels are defined."""
        levels = [level.value for level in NormalizationLevel]
        expected = ["none", "tashkeel_removed", "hamza_unified", "alif_unified", "ya_unified", "full"]
        for exp in expected:
            assert exp in levels


class TestWordFormInclusion:
    """Tests for WordFormInclusion enum."""

    def test_exact_only(self):
        """Test EXACT_ONLY value."""
        assert WordFormInclusion.EXACT_ONLY.value == "exact_only"

    def test_with_prefixes(self):
        """Test WITH_PREFIXES value."""
        assert WordFormInclusion.WITH_PREFIXES.value == "with_prefixes"

    def test_root_based(self):
        """Test ROOT_BASED value."""
        assert WordFormInclusion.ROOT_BASED.value == "root_based"


class TestAnalysisType:
    """Tests for AnalysisType enum."""

    def test_basic_counting_types(self):
        """Test basic counting analysis types."""
        assert AnalysisType.LETTER_COUNT.value == "letter_count"
        assert AnalysisType.WORD_COUNT.value == "word_count"
        assert AnalysisType.VERSE_COUNT.value == "verse_count"

    def test_frequency_types(self):
        """Test frequency analysis types."""
        assert AnalysisType.LETTER_FREQUENCY.value == "letter_frequency"
        assert AnalysisType.WORD_FREQUENCY.value == "word_frequency"

    def test_numerical_types(self):
        """Test numerical analysis types."""
        assert AnalysisType.ABJAD_VALUE.value == "abjad_value"
        assert AnalysisType.PRIME_CHECK.value == "prime_check"

    def test_morphological_types(self):
        """Test morphological analysis types."""
        assert AnalysisType.ROOT_EXTRACTION.value == "root_extraction"
        assert AnalysisType.PATTERN_EXTRACTION.value == "pattern_extraction"

    def test_entity_types(self):
        """Test entity analysis types."""
        assert AnalysisType.DIVINE_NAME_ANALYSIS.value == "divine_name_analysis"
        assert AnalysisType.PROPHET_NAME_ANALYSIS.value == "prophet_name_analysis"
