"""Abjad value object for gematria calculations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mizan.domain.enums import AbjadSystem


@dataclass(frozen=True, slots=True)
class AbjadValue:
    """
    Gematria/Abjad numerical value of text.

    The Abjad system assigns numerical values to Arabic letters.
    This Value Object stores both the total value and the breakdown
    for complete auditability.

    Attributes:
        system: The Abjad system used (Mashriqi or Maghribi)
        value: Total numerical value
        letter_breakdown: Immutable tuple of (letter, value) pairs
    """

    system: AbjadSystem
    value: int
    letter_breakdown: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        """Validate the Abjad value."""
        if self.value < 0:
            raise ValueError(f"Abjad value cannot be negative: {self.value}")

        # Verify breakdown sums to total
        computed_sum = sum(v for _, v in self.letter_breakdown)
        if computed_sum != self.value:
            raise ValueError(
                f"Letter breakdown sum ({computed_sum}) does not match value ({self.value})"
            )

    def __str__(self) -> str:
        """Return the numerical value as string."""
        return str(self.value)

    def __repr__(self) -> str:
        """Return detailed representation."""
        return f"AbjadValue(system={self.system.value!r}, value={self.value})"

    def __int__(self) -> int:
        """Allow conversion to int."""
        return self.value

    def __add__(self, other: object) -> int:
        """Allow addition with integers or other AbjadValues."""
        if isinstance(other, AbjadValue):
            return self.value + other.value
        if isinstance(other, int):
            return self.value + other
        return NotImplemented

    def __radd__(self, other: object) -> int:
        """Support reverse addition."""
        return self.__add__(other)

    def get_breakdown_dict(self) -> dict[str, int]:
        """
        Get letter breakdown as a dictionary.

        Note: If a letter appears multiple times, values are summed.

        Returns:
            Dictionary mapping letters to their total contribution
        """
        result: dict[str, int] = {}
        for letter, val in self.letter_breakdown:
            result[letter] = result.get(letter, 0) + val
        return result

    def get_letter_count(self) -> int:
        """Get total number of letters contributing to the value."""
        return len(self.letter_breakdown)

    def is_prime(self) -> bool:
        """Check if the Abjad value is a prime number."""
        if self.value < 2:
            return False
        if self.value == 2:
            return True
        if self.value % 2 == 0:
            return False
        for i in range(3, int(self.value**0.5) + 1, 2):
            if self.value % i == 0:
                return False
        return True

    def modulo(self, divisor: int) -> int:
        """
        Get remainder when divided by divisor.

        Args:
            divisor: The number to divide by

        Returns:
            Remainder (self.value % divisor)

        Raises:
            ValueError: If divisor is zero
        """
        if divisor == 0:
            raise ValueError("Cannot compute modulo with divisor of 0")
        return self.value % divisor

    def digital_root(self) -> int:
        """
        Calculate the digital root (repeated digit sum until single digit).

        The digital root is computed by repeatedly summing digits
        until a single digit remains. Also known as the "digital sum".

        Returns:
            Single digit (1-9) or 0 if value is 0
        """
        if self.value == 0:
            return 0
        return 1 + (self.value - 1) % 9
