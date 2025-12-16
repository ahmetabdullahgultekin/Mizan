"""
Integrity Guard - Fail-fast data integrity verification.

Ensures Quranic text has not been corrupted or modified.
"""

import logging
from datetime import datetime
from typing import Final

from mizan.domain.exceptions import IntegrityViolationError
from mizan.domain.repositories import IntegrityReport
from mizan.domain.value_objects import TextChecksum, VerseLocation
from mizan.infrastructure.config import get_settings

logger = logging.getLogger(__name__)


class IntegrityGuard:
    """
    Guards data integrity through checksum verification.

    If any integrity check fails and fail_on_integrity_error is True,
    the system will halt immediately rather than produce incorrect results.
    """

    # Known checksum for the complete Quran (Tanzil Uthmani)
    # This should be computed on first verified ingestion
    EXPECTED_FULL_QURAN_CHECKSUM: Final[str] = ""  # Set after first verified ingestion

    def __init__(self, fail_fast: bool | None = None) -> None:
        """
        Initialize integrity guard.

        Args:
            fail_fast: Whether to raise exception on failure.
                      Defaults to config setting.
        """
        settings = get_settings()
        self._fail_fast = (
            fail_fast if fail_fast is not None
            else settings.fail_on_integrity_error
        )
        self._expected_checksum = settings.expected_quran_checksum

    def verify_text(
        self,
        text: str,
        expected_checksum: TextChecksum,
        context: str = "",
    ) -> bool:
        """
        Verify text against expected checksum.

        Args:
            text: Text to verify
            expected_checksum: Expected checksum
            context: Context for error messages

        Returns:
            True if valid

        Raises:
            IntegrityViolationError: If verification fails and fail_fast is True
        """
        actual_checksum = TextChecksum.compute(text, expected_checksum.algorithm)

        if not expected_checksum.matches(actual_checksum):
            logger.critical(
                "INTEGRITY VIOLATION: Checksum mismatch. "
                f"Expected: {expected_checksum.value[:16]}..., "
                f"Actual: {actual_checksum.value[:16]}... "
                f"Context: {context}"
            )

            if self._fail_fast:
                raise IntegrityViolationError(
                    expected=expected_checksum,
                    actual=actual_checksum,
                    context=context,
                )
            return False

        return True

    def verify_verse(
        self,
        text: str,
        checksum: TextChecksum,
        location: VerseLocation,
    ) -> bool:
        """
        Verify a single verse's integrity.

        Args:
            text: Verse text
            checksum: Expected checksum
            location: Verse location for error context

        Returns:
            True if valid
        """
        return self.verify_text(
            text=text,
            expected_checksum=checksum,
            context=f"Verse {location}",
        )

    def verify_surah(
        self,
        full_text: str,
        checksum: TextChecksum,
        surah_number: int,
    ) -> bool:
        """
        Verify a complete surah's integrity.

        Args:
            full_text: Complete surah text
            checksum: Expected checksum
            surah_number: Surah number for error context

        Returns:
            True if valid
        """
        return self.verify_text(
            text=full_text,
            expected_checksum=checksum,
            context=f"Surah {surah_number}",
        )

    def verify_full_quran(
        self,
        full_text: str,
    ) -> bool:
        """
        Verify the complete Quran text.

        Uses the expected checksum from configuration.

        Args:
            full_text: Complete Quran text

        Returns:
            True if valid
        """
        if not self._expected_checksum:
            logger.warning(
                "No expected Quran checksum configured. "
                "Skipping full Quran verification."
            )
            return True

        expected = TextChecksum(algorithm="sha256", value=self._expected_checksum)
        return self.verify_text(
            text=full_text,
            expected_checksum=expected,
            context="Complete Quran",
        )

    def create_integrity_report(
        self,
        total_verses: int,
        failed_locations: list[VerseLocation],
        expected_checksum: str,
        actual_checksum: str,
    ) -> IntegrityReport:
        """
        Create an integrity report.

        Args:
            total_verses: Total verses checked
            failed_locations: Locations of failed verifications
            expected_checksum: Expected overall checksum
            actual_checksum: Actual computed checksum

        Returns:
            IntegrityReport with details
        """
        is_valid = len(failed_locations) == 0

        if is_valid:
            details = f"All {total_verses} verses passed integrity verification."
        else:
            details = (
                f"INTEGRITY FAILURE: {len(failed_locations)} of {total_verses} "
                f"verses failed verification. "
                f"Failed locations: {', '.join(str(loc) for loc in failed_locations[:10])}"
            )
            if len(failed_locations) > 10:
                details += f" ... and {len(failed_locations) - 10} more"

        return IntegrityReport(
            is_valid=is_valid,
            checked_at=datetime.utcnow(),
            total_verses=total_verses,
            failed_verses=tuple(failed_locations),
            expected_checksum=expected_checksum,
            actual_checksum=actual_checksum,
            details=details,
        )

    @staticmethod
    def compute_checksum(text: str, algorithm: str = "sha256") -> str:
        """
        Compute checksum for text.

        Utility method for computing checksums during ingestion.
        """
        return TextChecksum.compute(text, algorithm).value
