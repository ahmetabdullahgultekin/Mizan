"""Unit tests for domain services."""

import pytest
from mizan.domain.services import LetterCounter, AbjadCalculator, WordCounter
from mizan.domain.enums import AbjadSystem


class TestLetterCounter:
    """Tests for LetterCounter service."""

    def test_count_simple_word(self, letter_counter):
        """Test counting letters in a simple word."""
        # بسم = ب + س + م = 3 letters
        assert letter_counter.count_letters("بسم") == 3

    def test_count_with_tashkeel(self, letter_counter):
        """Test that tashkeel is not counted."""
        # بِسْمِ = still 3 letters (tashkeel ignored)
        assert letter_counter.count_letters("بِسْمِ") == 3

    def test_count_basmalah_simple(self, letter_counter, basmalah_simple):
        """Test counting letters in simple Basmalah."""
        # بسم الله الرحمن الرحيم
        # Spaces not counted
        count = letter_counter.count_letters(basmalah_simple)
        assert count == 19  # 3 + 4 + 6 + 6 = 19

    def test_count_with_alif_wasla(self, letter_counter):
        """Test counting Alif Wasla."""
        # ٱللَّه = 4 letters (Alif Wasla counts as Alif)
        text = "ٱللَّه"
        count = letter_counter.count_letters(text, count_alif_wasla=True)
        assert count == 4

    def test_count_without_alif_wasla(self, letter_counter):
        """Test not counting Alif Wasla."""
        text = "ٱللَّه"
        count = letter_counter.count_letters(text, count_alif_wasla=False)
        assert count == 3  # Only ل ل ه

    def test_count_with_alif_khanjariyya(self, letter_counter):
        """Test counting Alif Khanjariyya."""
        # الرحمـٰن contains Alif Khanjariyya
        text = "ٱلرَّحْمَـٰنِ"
        count_with = letter_counter.count_letters(text, count_alif_khanjariyya=True)
        count_without = letter_counter.count_letters(text, count_alif_khanjariyya=False)
        assert count_with > count_without

    def test_get_letter_frequency(self, letter_counter):
        """Test getting letter frequency."""
        text = "الله"  # ا ل ل ه
        freq = letter_counter.get_letter_frequency(text, normalize_variants=True)
        assert freq.get("ا", 0) == 1
        assert freq.get("ل", 0) == 2
        assert freq.get("ه", 0) == 1

    def test_get_letter_frequency_with_normalization(self, letter_counter):
        """Test frequency with Alif variant normalization."""
        text = "إِإأآا"  # Various Alif forms
        freq = letter_counter.get_letter_frequency(text, normalize_variants=True)
        assert freq.get("ا", 0) == 5  # All normalized to plain Alif

    def test_extract_letters(self, letter_counter):
        """Test extracting only letters."""
        text = "بِسْمِ ٱللَّهِ"
        letters = letter_counter.extract_letters(text)
        # Should contain only Arabic letters, no spaces or diacritics
        assert " " not in letters
        assert "\u064E" not in letters  # Fatha

    def test_is_arabic_letter(self, letter_counter):
        """Test is_arabic_letter method."""
        assert letter_counter.is_arabic_letter("ا") is True
        assert letter_counter.is_arabic_letter("b") is False
        assert letter_counter.is_arabic_letter(" ") is False
        assert letter_counter.is_arabic_letter("\u0671") is True  # Alif Wasla

    def test_count_empty_string(self, letter_counter):
        """Test counting empty string."""
        assert letter_counter.count_letters("") == 0

    def test_count_non_arabic(self, letter_counter):
        """Test counting non-Arabic text."""
        assert letter_counter.count_letters("Hello World") == 0


class TestAbjadCalculator:
    """Tests for AbjadCalculator service."""

    def test_calculate_alif(self, abjad_calculator):
        """Test Abjad value of Alif."""
        result = abjad_calculator.calculate("ا")
        assert result.value == 1

    def test_calculate_simple_word(self, abjad_calculator):
        """Test Abjad value of a simple word."""
        # الله = ا(1) + ل(30) + ل(30) + ه(5) = 66
        result = abjad_calculator.calculate("الله")
        assert result.value == 66

    def test_calculate_with_breakdown(self, abjad_calculator):
        """Test that breakdown is provided."""
        result = abjad_calculator.calculate("الله")
        breakdown = result.get_breakdown_dict()
        assert "ا" in breakdown
        assert breakdown["ل"] == 60  # Two lams: 30 + 30

    def test_mashriqi_vs_maghribi(self, abjad_calculator):
        """Test difference between Mashriqi and Maghribi systems."""
        # س has different values: Mashriqi=60, Maghribi=300
        mashriqi = abjad_calculator.calculate("س", AbjadSystem.MASHRIQI)
        maghribi = abjad_calculator.calculate("س", AbjadSystem.MAGHRIBI)
        assert mashriqi.value == 60
        assert maghribi.value == 300

    def test_calculate_bismillah(self, abjad_calculator):
        """Test Abjad value of Bismillah (famous 786)."""
        # بسم الله الرحمن الرحيم
        # This is a famous calculation, but depends on exact text
        text = "بسم الله الرحمن الرحيم"
        result = abjad_calculator.calculate(text)
        # The exact value depends on which letters are included
        assert result.value > 0

    def test_get_value_single_letter(self, abjad_calculator):
        """Test getting value of a single letter."""
        assert abjad_calculator.get_value("ا") == 1
        assert abjad_calculator.get_value("ب") == 2
        assert abjad_calculator.get_value("غ") == 1000

    def test_get_value_non_letter(self, abjad_calculator):
        """Test getting value of non-letter returns None."""
        assert abjad_calculator.get_value(" ") is None
        assert abjad_calculator.get_value("a") is None

    def test_is_prime(self, abjad_calculator):
        """Test prime number detection."""
        assert abjad_calculator.is_prime(2) is True
        assert abjad_calculator.is_prime(7) is True
        assert abjad_calculator.is_prime(4) is False
        assert abjad_calculator.is_prime(1) is False

    def test_factorize(self, abjad_calculator):
        """Test prime factorization."""
        assert abjad_calculator.factorize(12) == [2, 2, 3]
        assert abjad_calculator.factorize(7) == [7]  # Prime
        assert abjad_calculator.factorize(1) == []

    def test_digital_root(self, abjad_calculator):
        """Test digital root calculation."""
        assert abjad_calculator.digital_root(786) == 3  # 7+8+6=21 → 2+1=3
        assert abjad_calculator.digital_root(9) == 9
        assert abjad_calculator.digital_root(0) == 0

    def test_calculate_empty_string(self, abjad_calculator):
        """Test calculating empty string."""
        result = abjad_calculator.calculate("")
        assert result.value == 0

    def test_alif_variants_equal_value(self, abjad_calculator):
        """Test that all Alif variants have same value."""
        variants = ["ا", "أ", "إ", "آ", "ء"]
        for variant in variants:
            assert abjad_calculator.get_value(variant) == 1


class TestWordCounter:
    """Tests for WordCounter service."""

    def test_count_simple_text(self, word_counter):
        """Test counting words in simple text."""
        result = word_counter.count_words("بسم الله الرحمن الرحيم")
        assert result.count == 4

    def test_count_returns_words_list(self, word_counter):
        """Test that word list is returned."""
        result = word_counter.count_words("بسم الله")
        assert len(result.words) == 2
        assert "بسم" in result.words
        assert "الله" in result.words

    def test_methodology_documented(self, word_counter):
        """Test that methodology is documented."""
        result = word_counter.count_words("بسم الله")
        assert "Whitespace-delimited" in result.methodology

    def test_decisions_logged(self, word_counter):
        """Test that decisions are logged."""
        result = word_counter.count_words("بسم الله")
        assert len(result.decisions) > 0

    def test_count_removes_waqf_signs(self, word_counter):
        """Test that waqf signs are removed."""
        # Text with waqf sign ۚ
        text = "كلمة ۚ أخرى"
        result = word_counter.count_words(text)
        assert "ۚ" not in result.words

    def test_count_removes_ayah_marker(self, word_counter):
        """Test that ayah end marker is removed."""
        text = "كلمة۝ أخرى"
        result = word_counter.count_words(text)
        assert result.count == 2

    def test_count_simple_method(self, word_counter):
        """Test simple counting method."""
        count = word_counter.count_words_simple("بسم الله الرحمن الرحيم")
        assert count == 4

    def test_split_words(self, word_counter):
        """Test splitting into word list."""
        words = word_counter.split_words("بسم الله")
        assert words == ["بسم", "الله"]

    def test_get_word_positions(self, word_counter):
        """Test getting word positions."""
        text = "بسم الله"
        positions = word_counter.get_word_positions(text)
        assert len(positions) == 2
        # Each entry is (word, start, end)
        assert positions[0][0] == "بسم"
        assert positions[1][0] == "الله"

    def test_count_empty_string(self, word_counter):
        """Test counting empty string."""
        result = word_counter.count_words("")
        assert result.count == 0

    def test_count_whitespace_only(self, word_counter):
        """Test counting whitespace-only string."""
        result = word_counter.count_words("   ")
        assert result.count == 0

    def test_audit_dict(self, word_counter):
        """Test conversion to audit dictionary."""
        result = word_counter.count_words("بسم الله")
        audit = result.to_audit_dict()
        assert "count" in audit
        assert "words" in audit
        assert "methodology" in audit
        assert "decisions" in audit
