"""
Backward-compatibility re-exports.

The three repository classes have been extracted into dedicated modules:
  - quran_repository.py      → PostgresQuranRepository
  - surah_repository.py      → PostgresSurahMetadataRepository
  - morphology_repository.py → PostgresMorphologyRepository

This shim re-exports all three so existing imports continue to work.
"""

from mizan.infrastructure.persistence.quran_repository import PostgresQuranRepository
from mizan.infrastructure.persistence.surah_repository import PostgresSurahMetadataRepository
from mizan.infrastructure.persistence.morphology_repository import PostgresMorphologyRepository

__all__ = [
    "PostgresQuranRepository",
    "PostgresSurahMetadataRepository",
    "PostgresMorphologyRepository",
]
