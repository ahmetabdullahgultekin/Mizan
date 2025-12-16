"""Text checksum value object for integrity verification."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import Final

# Supported hash algorithms
SUPPORTED_ALGORITHMS: Final[frozenset[str]] = frozenset({
    "sha256",
    "sha384",
    "sha512",
    "sha3_256",
    "sha3_512",
})

DEFAULT_ALGORITHM: Final[str] = "sha256"


@dataclass(frozen=True, slots=True)
class TextChecksum:
    """
    Cryptographic hash of text content for integrity verification.

    This Value Object ensures that Quranic text has not been altered
    or corrupted. Any change to the text will result in a different checksum.

    Attributes:
        algorithm: Hash algorithm used (e.g., "sha256")
        value: Hex-encoded hash value
    """

    algorithm: str
    value: str

    def __post_init__(self) -> None:
        """Validate checksum upon creation."""
        if self.algorithm not in SUPPORTED_ALGORITHMS:
            raise ValueError(
                f"Unsupported algorithm: {self.algorithm}. "
                f"Supported: {', '.join(sorted(SUPPORTED_ALGORITHMS))}"
            )

        if not self.value:
            raise ValueError("Checksum value cannot be empty.")

        # Validate hex format
        try:
            int(self.value, 16)
        except ValueError as e:
            raise ValueError(
                f"Invalid checksum value: must be hex-encoded. Got: {self.value[:20]}..."
            ) from e

    def __str__(self) -> str:
        """Return algorithm:hash format."""
        return f"{self.algorithm}:{self.value}"

    def __repr__(self) -> str:
        """Return detailed representation with truncated hash."""
        truncated = f"{self.value[:16]}...{self.value[-8:]}" if len(self.value) > 32 else self.value
        return f"TextChecksum(algorithm={self.algorithm!r}, value={truncated!r})"

    @classmethod
    def compute(cls, text: str, algorithm: str = DEFAULT_ALGORITHM) -> TextChecksum:
        """
        Compute checksum for given text.

        Args:
            text: Text to hash
            algorithm: Hash algorithm to use (default: sha256)

        Returns:
            TextChecksum instance with computed hash
        """
        if algorithm not in SUPPORTED_ALGORITHMS:
            raise ValueError(
                f"Unsupported algorithm: {algorithm}. "
                f"Supported: {', '.join(sorted(SUPPORTED_ALGORITHMS))}"
            )

        hasher = hashlib.new(algorithm)
        hasher.update(text.encode("utf-8"))
        return cls(algorithm=algorithm, value=hasher.hexdigest())

    @classmethod
    def from_string(cls, checksum_str: str) -> TextChecksum:
        """
        Create TextChecksum from string representation.

        Args:
            checksum_str: String in "algorithm:hash" format

        Returns:
            TextChecksum instance

        Raises:
            ValueError: If format is invalid
        """
        parts = checksum_str.split(":", 1)
        if len(parts) != 2:
            raise ValueError(
                f"Invalid checksum format: '{checksum_str}'. "
                "Expected 'algorithm:hash' format."
            )
        return cls(algorithm=parts[0], value=parts[1])

    def verify(self, text: str) -> bool:
        """
        Verify that text matches this checksum.

        Args:
            text: Text to verify

        Returns:
            True if checksum matches, False otherwise
        """
        computed = self.compute(text, self.algorithm)
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(self.value, computed.value)

    def matches(self, other: TextChecksum) -> bool:
        """
        Check if another checksum matches this one.

        Args:
            other: TextChecksum to compare

        Returns:
            True if checksums match (same algorithm and value)
        """
        if self.algorithm != other.algorithm:
            return False
        return hmac.compare_digest(self.value, other.value)
