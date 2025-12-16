"""
Abjad calculator domain service.

Computes Abjad/Gematria numerical values for Arabic text.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from mizan.domain.enums import AbjadSystem
    from mizan.domain.value_objects import AbjadValue


class AbjadCalculator:
    """
    Domain service for Abjad/Gematria calculations.

    The Abjad system assigns numerical values to Arabic letters.
    Two main systems exist: Mashriqi (Eastern) and Maghribi (Western).
    """

    # Mashriqi (Eastern) Abjad values - أبجد هوز حطي كلمن سعفص قرشت ثخذ ضظغ
    MASHRIQI_VALUES: Final[dict[str, int]] = {
        # Units (1-9)
        "ا": 1, "أ": 1, "إ": 1, "آ": 1, "ء": 1, "\u0671": 1,  # Alif variants + Alif Wasla
        "ب": 2,
        "ج": 3,
        "د": 4,
        "ه": 5,
        "و": 6,
        "ز": 7,
        "ح": 8,
        "ط": 9,
        # Tens (10-90)
        "ي": 10, "ى": 10, "ئ": 10,  # Ya variants
        "ك": 20,
        "ل": 30,
        "م": 40,
        "ن": 50,
        "س": 60,
        "ع": 70,
        "ف": 80,
        "ص": 90,
        # Hundreds (100-900)
        "ق": 100,
        "ر": 200,
        "ش": 300,
        "ت": 400,
        "ث": 500,
        "خ": 600,
        "ذ": 700,
        "ض": 800,
        "ظ": 900,
        # Thousands
        "غ": 1000,
    }

    # Maghribi (Western) Abjad values - different ordering for س ش ص ض
    MAGHRIBI_VALUES: Final[dict[str, int]] = {
        # Units (1-9) - same as Mashriqi
        "ا": 1, "أ": 1, "إ": 1, "آ": 1, "ء": 1, "\u0671": 1,
        "ب": 2,
        "ج": 3,
        "د": 4,
        "ه": 5,
        "و": 6,
        "ز": 7,
        "ح": 8,
        "ط": 9,
        # Tens (10-90) - same as Mashriqi
        "ي": 10, "ى": 10, "ئ": 10,
        "ك": 20,
        "ل": 30,
        "م": 40,
        "ن": 50,
        "ص": 60,  # Different from Mashriqi (س=60)
        "ع": 70,
        "ف": 80,
        "ض": 90,  # Different from Mashriqi (ص=90)
        # Hundreds (100-900)
        "ق": 100,
        "ر": 200,
        "س": 300,  # Different from Mashriqi (ش=300)
        "ت": 400,
        "ث": 500,
        "خ": 600,
        "ذ": 700,
        "ش": 800,  # Different from Mashriqi (ض=800)
        "ظ": 900,
        # Thousands
        "غ": 1000,
    }

    # Alif Khanjariyya - superscript Alif (counts as Alif)
    ALIF_KHANJARIYYA: Final[str] = "\u0670"

    def calculate(
        self,
        text: str,
        system: AbjadSystem | None = None,
        include_alif_khanjariyya: bool = True,
    ) -> AbjadValue:
        """
        Calculate the Abjad value of text.

        Args:
            text: Arabic text to calculate
            system: Abjad system to use (default: MASHRIQI)
            include_alif_khanjariyya: Whether to count superscript Alif

        Returns:
            AbjadValue with total and breakdown
        """
        from mizan.domain.enums import AbjadSystem
        from mizan.domain.value_objects import AbjadValue

        system = system or AbjadSystem.MASHRIQI
        values = (
            self.MASHRIQI_VALUES
            if system == AbjadSystem.MASHRIQI
            else self.MAGHRIBI_VALUES
        )

        breakdown: list[tuple[str, int]] = []
        total = 0

        for char in text:
            # Check for Alif Khanjariyya
            if char == self.ALIF_KHANJARIYYA and include_alif_khanjariyya:
                val = 1  # Same as Alif
                breakdown.append((char, val))
                total += val
            elif char in values:
                val = values[char]
                breakdown.append((char, val))
                total += val

        return AbjadValue(
            system=system,
            value=total,
            letter_breakdown=tuple(breakdown),
        )

    def calculate_simple(
        self,
        text: str,
        system: AbjadSystem | None = None,
    ) -> int:
        """
        Calculate Abjad value and return just the integer.

        Convenience method when full breakdown is not needed.
        """
        return self.calculate(text, system).value

    def get_value(
        self,
        letter: str,
        system: AbjadSystem | None = None,
    ) -> int | None:
        """
        Get Abjad value of a single letter.

        Args:
            letter: Single Arabic letter
            system: Abjad system to use

        Returns:
            Integer value or None if not a valued letter
        """
        from mizan.domain.enums import AbjadSystem

        system = system or AbjadSystem.MASHRIQI
        values = (
            self.MASHRIQI_VALUES
            if system == AbjadSystem.MASHRIQI
            else self.MAGHRIBI_VALUES
        )

        if letter == self.ALIF_KHANJARIYYA:
            return 1
        return values.get(letter)

    def is_prime(self, value: int) -> bool:
        """Check if an Abjad value is a prime number."""
        if value < 2:
            return False
        if value == 2:
            return True
        if value % 2 == 0:
            return False
        for i in range(3, int(value**0.5) + 1, 2):
            if value % i == 0:
                return False
        return True

    def factorize(self, value: int) -> list[int]:
        """
        Get prime factorization of an Abjad value.

        Args:
            value: The value to factorize

        Returns:
            List of prime factors in ascending order
        """
        if value < 2:
            return []

        factors = []
        d = 2
        while d * d <= value:
            while value % d == 0:
                factors.append(d)
                value //= d
            d += 1
        if value > 1:
            factors.append(value)
        return factors

    def digital_root(self, value: int) -> int:
        """
        Calculate digital root (repeated digit sum until single digit).

        Args:
            value: The value to reduce

        Returns:
            Single digit (1-9) or 0 if value is 0
        """
        if value == 0:
            return 0
        return 1 + (value - 1) % 9
