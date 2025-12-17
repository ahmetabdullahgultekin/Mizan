#!/usr/bin/env python3
"""
Comprehensive database seeding script for Mizan.

This script:
1. Downloads complete Quran metadata from gadingnst/quran-api (page, juz, hizb, manzil, ruku, sajda)
2. Parses local Tanzil XML files for authentic Uthmani text (3 versions)
3. Computes abjad values, word/letter counts, and checksums
4. Seeds the Supabase/PostgreSQL database

Data Sources:
- Tanzil.net XML: Authentic Quran text (uthmani, uthmani-min, simple)
- gadingnst/quran-api: Complete metadata (page, juz, hizb, manzil, ruku, sajda)

Usage:
    python scripts/seed_database.py [--dry-run] [--force]

Requirements:
    - DATABASE_URL environment variable set
    - Internet connection for downloading metadata
"""

import argparse
import asyncio
import hashlib
import json
import logging
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

QURAN_API_URL = "https://raw.githubusercontent.com/gadingnst/quran-api/main/data/quran.json"
PROJECT_ROOT = Path(__file__).parent.parent
QURAN_DATA_PATH = PROJECT_ROOT / "quran"

# Abjad values (Mashriqi system)
ABJAD_MASHRIQI = {
    "ا": 1, "أ": 1, "إ": 1, "آ": 1, "ء": 1, "\u0671": 1,  # Alif variants + Alif Wasla
    "ب": 2, "ج": 3, "د": 4, "ه": 5, "و": 6, "ز": 7, "ح": 8, "ط": 9,
    "ي": 10, "ى": 10, "ئ": 10,  # Ya variants
    "ك": 20, "ل": 30, "م": 40, "ن": 50, "س": 60, "ع": 70, "ف": 80, "ص": 90,
    "ق": 100, "ر": 200, "ش": 300, "ت": 400, "ث": 500, "خ": 600, "ذ": 700, "ض": 800, "ظ": 900,
    "غ": 1000,
}

# Maghribi system (different order for some letters)
ABJAD_MAGHRIBI = {
    "ا": 1, "أ": 1, "إ": 1, "آ": 1, "ء": 1, "\u0671": 1,
    "ب": 2, "ج": 3, "د": 4, "ه": 5, "و": 6, "ز": 7, "ح": 8, "ط": 9,
    "ي": 10, "ى": 10, "ئ": 10,
    "ك": 20, "ل": 30, "م": 40, "ن": 50, "ص": 60, "ع": 70, "ف": 80, "ض": 90,
    "ق": 100, "ر": 200, "س": 300, "ت": 400, "ث": 500, "خ": 600, "ذ": 700, "ش": 800, "ظ": 900,
    "غ": 1000,
}

# Tashkeel (diacritical marks) to remove for normalization
TASHKEEL = re.compile(r"[\u064B-\u065F\u0670]")

# Alif Khanjariyya (superscript Alif)
ALIF_KHANJARIYYA = "\u0670"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class SurahData:
    """Surah metadata."""
    id: int
    name_arabic: str
    name_english: str
    name_transliteration: str
    revelation_type: str  # meccan/medinan
    revelation_order: int
    verse_count: int
    ruku_count: int = 0
    word_count: int = 0
    letter_count: int = 0
    abjad_value: int = 0
    basmalah_status: str = "included"
    checksum: str = ""


@dataclass
class VerseData:
    """Verse data with all metadata."""
    surah_number: int
    verse_number: int
    text_uthmani: str
    text_uthmani_min: str = ""
    text_simple: str = ""
    text_normalized_full: str = ""
    text_no_tashkeel: str = ""
    juz_number: int = 1
    hizb_number: int = 1
    ruku_number: int = 1
    manzil_number: int = 1
    page_number: int = 1
    is_sajdah: bool = False
    sajdah_type: str | None = None
    word_count: int = 0
    letter_count: int = 0
    abjad_value_mashriqi: int = 0
    abjad_value_maghribi: int = 0
    checksum: str = ""


# =============================================================================
# Text Processing Functions
# =============================================================================

def calculate_abjad(text: str, system: str = "mashriqi") -> int:
    """Calculate Abjad value of Arabic text."""
    values = ABJAD_MASHRIQI if system == "mashriqi" else ABJAD_MAGHRIBI
    total = 0
    for char in text:
        if char == ALIF_KHANJARIYYA:
            total += 1  # Count as Alif
        elif char in values:
            total += values[char]
    return total


def remove_tashkeel(text: str) -> str:
    """Remove diacritical marks from Arabic text."""
    return TASHKEEL.sub("", text)


def normalize_arabic(text: str) -> str:
    """Normalize Arabic text for searching."""
    # Remove tashkeel
    normalized = remove_tashkeel(text)
    # Normalize unicode
    normalized = unicodedata.normalize("NFC", normalized)
    # Remove extra whitespace
    normalized = " ".join(normalized.split())
    return normalized


def count_letters(text: str) -> int:
    """Count Arabic letters in text (excluding diacritics and spaces)."""
    count = 0
    for char in text:
        # Count Arabic letters and Alif Khanjariyya
        if char == ALIF_KHANJARIYYA:
            count += 1
        elif "\u0600" <= char <= "\u06FF" and char not in "\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0653\u0654\u0655\u0656\u0657\u0658\u0659\u065A\u065B\u065C\u065D\u065E\u065F":
            # Arabic letter (not a diacritic)
            if not unicodedata.category(char).startswith("M"):  # Not a mark
                count += 1
    return count


def count_words(text: str) -> int:
    """Count words in text (whitespace-delimited, Tanzil standard)."""
    return len(text.split())


def compute_checksum(text: str) -> str:
    """Compute SHA-256 checksum of text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# =============================================================================
# Data Loading Functions
# =============================================================================

def parse_tanzil_xml(xml_path: Path) -> dict[tuple[int, int], str]:
    """Parse Tanzil XML file and return verse texts."""
    verses = {}
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        for sura in root.findall("sura"):
            sura_num = int(sura.get("index"))
            for aya in sura.findall("aya"):
                aya_num = int(aya.get("index"))
                text = aya.get("text", "")
                verses[(sura_num, aya_num)] = text

        logger.info(f"Parsed {len(verses)} verses from {xml_path.name}")
    except Exception as e:
        logger.error(f"Error parsing {xml_path}: {e}")

    return verses


async def download_quran_metadata() -> dict[str, Any]:
    """Download complete Quran metadata from gadingnst/quran-api."""
    logger.info(f"Downloading Quran metadata from {QURAN_API_URL}...")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(QURAN_API_URL)
        response.raise_for_status()
        data = response.json()

    logger.info(f"Downloaded metadata for {len(data.get('data', []))} surahs")
    return data


def extract_surah_metadata(api_data: dict[str, Any]) -> list[SurahData]:
    """Extract surah metadata from API data."""
    surahs = []

    for surah_data in api_data.get("data", []):
        # Determine basmalah status
        basmalah_status = "included"
        if surah_data["number"] == 1:
            basmalah_status = "part_of_first_verse"
        elif surah_data["number"] == 9:
            basmalah_status = "none"

        # Calculate ruku count from verses
        ruku_numbers = set()
        for verse in surah_data.get("verses", []):
            ruku_numbers.add(verse["meta"]["ruku"])

        surah = SurahData(
            id=surah_data["number"],
            name_arabic=surah_data["name"]["short"],
            name_english=surah_data["name"]["translation"]["en"],
            name_transliteration=surah_data["name"]["transliteration"]["en"],
            revelation_type=surah_data["revelation"]["en"].lower(),
            revelation_order=surah_data["sequence"],
            verse_count=surah_data["numberOfVerses"],
            ruku_count=len(ruku_numbers),
            basmalah_status=basmalah_status,
        )
        surahs.append(surah)

    return surahs


def extract_verse_metadata(
    api_data: dict[str, Any],
    uthmani_texts: dict[tuple[int, int], str],
    uthmani_min_texts: dict[tuple[int, int], str],
    simple_texts: dict[tuple[int, int], str],
) -> list[VerseData]:
    """Extract verse data combining API metadata with Tanzil texts."""
    verses = []

    for surah_data in api_data.get("data", []):
        surah_num = surah_data["number"]

        for verse_data in surah_data.get("verses", []):
            verse_num = verse_data["number"]["inSurah"]
            meta = verse_data["meta"]

            # Get text from Tanzil (prefer our XML files)
            text_uthmani = uthmani_texts.get((surah_num, verse_num), verse_data["text"]["arab"])
            text_uthmani_min = uthmani_min_texts.get((surah_num, verse_num), "")
            text_simple = simple_texts.get((surah_num, verse_num), "")

            # Compute derived values
            text_normalized = normalize_arabic(text_uthmani)
            text_no_tashkeel = remove_tashkeel(text_uthmani)

            # Determine sajdah info
            sajda_meta = meta.get("sajda", {})
            is_sajdah = sajda_meta.get("recommended", False) or sajda_meta.get("obligatory", False)
            sajdah_type = None
            if sajda_meta.get("obligatory"):
                sajdah_type = "obligatory"
            elif sajda_meta.get("recommended"):
                sajdah_type = "recommended"

            verse = VerseData(
                surah_number=surah_num,
                verse_number=verse_num,
                text_uthmani=text_uthmani,
                text_uthmani_min=text_uthmani_min,
                text_simple=text_simple,
                text_normalized_full=text_normalized,
                text_no_tashkeel=text_no_tashkeel,
                juz_number=meta.get("juz", 1),
                hizb_number=meta.get("hizbQuarter", 1),  # This is actually hizb quarter
                ruku_number=meta.get("ruku", 1),
                manzil_number=meta.get("manzil", 1),
                page_number=meta.get("page", 1),
                is_sajdah=is_sajdah,
                sajdah_type=sajdah_type,
                word_count=count_words(text_uthmani),
                letter_count=count_letters(text_uthmani),
                abjad_value_mashriqi=calculate_abjad(text_uthmani, "mashriqi"),
                abjad_value_maghribi=calculate_abjad(text_uthmani, "maghribi"),
                checksum=compute_checksum(text_uthmani),
            )
            verses.append(verse)

    return verses


def compute_surah_aggregates(surahs: list[SurahData], verses: list[VerseData]) -> None:
    """Compute aggregate values for surahs from their verses."""
    # Group verses by surah
    verses_by_surah: dict[int, list[VerseData]] = {}
    for verse in verses:
        if verse.surah_number not in verses_by_surah:
            verses_by_surah[verse.surah_number] = []
        verses_by_surah[verse.surah_number].append(verse)

    # Compute aggregates
    for surah in surahs:
        surah_verses = verses_by_surah.get(surah.id, [])

        # Aggregate text for checksum
        all_text = " ".join(v.text_uthmani for v in surah_verses)

        surah.word_count = sum(v.word_count for v in surah_verses)
        surah.letter_count = sum(v.letter_count for v in surah_verses)
        surah.abjad_value = sum(v.abjad_value_mashriqi for v in surah_verses)
        surah.checksum = compute_checksum(all_text)


# =============================================================================
# Database Operations
# =============================================================================

async def create_tables(session: AsyncSession) -> None:
    """Create tables if they don't exist."""
    # Create surahs table
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS surahs (
            id INTEGER PRIMARY KEY,
            name_arabic VARCHAR(100) NOT NULL,
            name_english VARCHAR(100) NOT NULL,
            name_transliteration VARCHAR(100) NOT NULL,
            revelation_type VARCHAR(20) NOT NULL,
            revelation_order INTEGER NOT NULL,
            basmalah_status VARCHAR(30) NOT NULL,
            verse_count INTEGER NOT NULL,
            ruku_count INTEGER NOT NULL,
            word_count INTEGER NOT NULL DEFAULT 0,
            letter_count INTEGER NOT NULL DEFAULT 0,
            abjad_value INTEGER NOT NULL DEFAULT 0,
            checksum VARCHAR(128) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))

    # Create verses table
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS verses (
            id UUID PRIMARY KEY,
            surah_number INTEGER NOT NULL REFERENCES surahs(id),
            verse_number INTEGER NOT NULL,
            text_uthmani TEXT NOT NULL,
            text_uthmani_min TEXT,
            text_simple TEXT,
            text_normalized_full TEXT NOT NULL,
            text_no_tashkeel TEXT NOT NULL,
            qiraat_variants JSONB,
            juz_number INTEGER NOT NULL,
            hizb_number INTEGER NOT NULL,
            ruku_number INTEGER NOT NULL,
            manzil_number INTEGER NOT NULL,
            page_number INTEGER NOT NULL,
            is_sajdah BOOLEAN NOT NULL DEFAULT FALSE,
            sajdah_type VARCHAR(20),
            word_count INTEGER NOT NULL,
            letter_count INTEGER NOT NULL,
            abjad_value_mashriqi INTEGER NOT NULL,
            abjad_value_maghribi INTEGER NOT NULL DEFAULT 0,
            checksum VARCHAR(128) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(surah_number, verse_number)
        )
    """))

    # Create indexes
    await session.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_surahs_revelation_type ON surahs(revelation_type)
    """))
    await session.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_surahs_revelation_order ON surahs(revelation_order)
    """))
    await session.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_verses_surah_verse ON verses(surah_number, verse_number)
    """))
    await session.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_verses_juz ON verses(juz_number)
    """))
    await session.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_verses_page ON verses(page_number)
    """))

    await session.commit()
    logger.info("Tables created successfully")


async def clear_existing_data(session: AsyncSession) -> None:
    """Clear existing data from tables."""
    await session.execute(text("DELETE FROM verses"))
    await session.execute(text("DELETE FROM surahs"))
    await session.commit()
    logger.info("Cleared existing data")


async def insert_surahs(session: AsyncSession, surahs: list[SurahData]) -> None:
    """Insert surah data into database."""
    for surah in surahs:
        await session.execute(text("""
            INSERT INTO surahs (
                id, name_arabic, name_english, name_transliteration,
                revelation_type, revelation_order, basmalah_status,
                verse_count, ruku_count, word_count, letter_count,
                abjad_value, checksum
            ) VALUES (
                :id, :name_arabic, :name_english, :name_transliteration,
                :revelation_type, :revelation_order, :basmalah_status,
                :verse_count, :ruku_count, :word_count, :letter_count,
                :abjad_value, :checksum
            )
        """), {
            "id": surah.id,
            "name_arabic": surah.name_arabic,
            "name_english": surah.name_english,
            "name_transliteration": surah.name_transliteration,
            "revelation_type": surah.revelation_type,
            "revelation_order": surah.revelation_order,
            "basmalah_status": surah.basmalah_status,
            "verse_count": surah.verse_count,
            "ruku_count": surah.ruku_count,
            "word_count": surah.word_count,
            "letter_count": surah.letter_count,
            "abjad_value": surah.abjad_value,
            "checksum": surah.checksum,
        })

    await session.commit()
    logger.info(f"Inserted {len(surahs)} surahs")


async def insert_verses(session: AsyncSession, verses: list[VerseData], batch_size: int = 100) -> None:
    """Insert verse data into database in batches."""
    total = len(verses)
    inserted = 0

    for i in range(0, total, batch_size):
        batch = verses[i:i + batch_size]

        for verse in batch:
            verse_id = str(uuid4())
            await session.execute(text("""
                INSERT INTO verses (
                    id, surah_number, verse_number,
                    text_uthmani, text_uthmani_min, text_simple,
                    text_normalized_full, text_no_tashkeel,
                    juz_number, hizb_number, ruku_number, manzil_number, page_number,
                    is_sajdah, sajdah_type,
                    word_count, letter_count, abjad_value_mashriqi, abjad_value_maghribi,
                    checksum
                ) VALUES (
                    :id, :surah_number, :verse_number,
                    :text_uthmani, :text_uthmani_min, :text_simple,
                    :text_normalized_full, :text_no_tashkeel,
                    :juz_number, :hizb_number, :ruku_number, :manzil_number, :page_number,
                    :is_sajdah, :sajdah_type,
                    :word_count, :letter_count, :abjad_value_mashriqi, :abjad_value_maghribi,
                    :checksum
                )
            """), {
                "id": verse_id,
                "surah_number": verse.surah_number,
                "verse_number": verse.verse_number,
                "text_uthmani": verse.text_uthmani,
                "text_uthmani_min": verse.text_uthmani_min or None,
                "text_simple": verse.text_simple or None,
                "text_normalized_full": verse.text_normalized_full,
                "text_no_tashkeel": verse.text_no_tashkeel,
                "juz_number": verse.juz_number,
                "hizb_number": verse.hizb_number,
                "ruku_number": verse.ruku_number,
                "manzil_number": verse.manzil_number,
                "page_number": verse.page_number,
                "is_sajdah": verse.is_sajdah,
                "sajdah_type": verse.sajdah_type,
                "word_count": verse.word_count,
                "letter_count": verse.letter_count,
                "abjad_value_mashriqi": verse.abjad_value_mashriqi,
                "abjad_value_maghribi": verse.abjad_value_maghribi,
                "checksum": verse.checksum,
            })

        await session.commit()
        inserted += len(batch)
        logger.info(f"Inserted {inserted}/{total} verses ({100*inserted//total}%)")

    logger.info(f"Inserted {total} verses successfully")


# =============================================================================
# Main Function
# =============================================================================

async def seed_database(dry_run: bool = False, force: bool = False) -> None:
    """Main seeding function."""
    logger.info("=" * 60)
    logger.info("Mizan Database Seeding Script")
    logger.info("=" * 60)

    # Get database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)

    # Ensure async driver
    if "postgresql://" in database_url and "+asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

    logger.info(f"Database: {database_url.split('@')[-1] if '@' in database_url else 'configured'}")

    # Step 1: Load Tanzil XML files
    logger.info("\n[1/5] Loading Tanzil XML files...")

    uthmani_path = QURAN_DATA_PATH / "uthmani" / "quran-uthmani.xml"
    uthmani_min_path = QURAN_DATA_PATH / "uthmani-min" / "quran-uthmani-min.xml"
    simple_path = QURAN_DATA_PATH / "simple" / "quran-simple.xml"

    uthmani_texts = parse_tanzil_xml(uthmani_path) if uthmani_path.exists() else {}
    uthmani_min_texts = parse_tanzil_xml(uthmani_min_path) if uthmani_min_path.exists() else {}
    simple_texts = parse_tanzil_xml(simple_path) if simple_path.exists() else {}

    if not uthmani_texts:
        logger.error(f"No Uthmani text found at {uthmani_path}")
        sys.exit(1)

    # Step 2: Download metadata from API
    logger.info("\n[2/5] Downloading Quran metadata...")
    api_data = await download_quran_metadata()

    # Step 3: Extract and process data
    logger.info("\n[3/5] Processing data...")

    surahs = extract_surah_metadata(api_data)
    logger.info(f"Extracted {len(surahs)} surahs")

    verses = extract_verse_metadata(api_data, uthmani_texts, uthmani_min_texts, simple_texts)
    logger.info(f"Extracted {len(verses)} verses")

    # Compute surah aggregates
    compute_surah_aggregates(surahs, verses)

    # Print sample data
    if surahs:
        s = surahs[0]
        logger.info(f"\nSample Surah: {s.name_arabic} ({s.name_english})")
        logger.info(f"  - Verses: {s.verse_count}, Words: {s.word_count}, Letters: {s.letter_count}")
        logger.info(f"  - Abjad: {s.abjad_value}, Revelation: {s.revelation_type}")

    if verses:
        v = verses[0]
        logger.info(f"\nSample Verse: {v.surah_number}:{v.verse_number}")
        logger.info(f"  - Text: {v.text_uthmani[:50]}...")
        logger.info(f"  - Page: {v.page_number}, Juz: {v.juz_number}, Hizb: {v.hizb_number}")
        logger.info(f"  - Words: {v.word_count}, Letters: {v.letter_count}, Abjad: {v.abjad_value_mashriqi}")

    if dry_run:
        logger.info("\n[DRY RUN] Skipping database operations")
        logger.info(f"Would insert {len(surahs)} surahs and {len(verses)} verses")
        return

    # Step 4: Connect and seed database
    logger.info("\n[4/5] Connecting to database...")

    engine = create_async_engine(
        database_url,
        echo=False,
        connect_args={"statement_cache_size": 0, "prepared_statement_cache_size": 0},
    )

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check for existing data
        result = await session.execute(text("SELECT COUNT(*) FROM surahs"))
        existing_count = result.scalar() or 0

        if existing_count > 0 and not force:
            logger.warning(f"Database already contains {existing_count} surahs")
            logger.warning("Use --force to clear and reseed")
            return

        # Create tables (if needed)
        await create_tables(session)

        if force and existing_count > 0:
            logger.info("Clearing existing data...")
            await clear_existing_data(session)

        # Step 5: Insert data
        logger.info("\n[5/5] Inserting data...")
        await insert_surahs(session, surahs)
        await insert_verses(session, verses)

    await engine.dispose()

    logger.info("\n" + "=" * 60)
    logger.info("Database seeding completed successfully!")
    logger.info(f"  - Surahs: {len(surahs)}")
    logger.info(f"  - Verses: {len(verses)}")
    logger.info("=" * 60)


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Seed the Mizan database with Quran data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/seed_database.py --dry-run    # Test without database changes
  python scripts/seed_database.py              # Seed empty database
  python scripts/seed_database.py --force      # Clear and reseed

Environment:
  DATABASE_URL    PostgreSQL connection string (required)
        """
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process data without database operations",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Clear existing data and reseed",
    )

    args = parser.parse_args()

    asyncio.run(seed_database(dry_run=args.dry_run, force=args.force))


if __name__ == "__main__":
    main()
