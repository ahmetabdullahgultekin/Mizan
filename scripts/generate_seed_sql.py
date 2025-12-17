#!/usr/bin/env python3
"""
Generate SQL file for seeding Mizan database.
Outputs SQL that can be pasted into Supabase SQL Editor.
"""

import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Abjad letter values (Mashriqi system)
ABJAD_MASHRIQI = {
    'ا': 1, 'أ': 1, 'إ': 1, 'آ': 1, 'ٱ': 1,
    'ب': 2,
    'ج': 3,
    'د': 4,
    'ه': 5, 'ة': 5,
    'و': 6, 'ؤ': 6,
    'ز': 7,
    'ح': 8,
    'ط': 9,
    'ي': 10, 'ى': 10, 'ئ': 10,
    'ك': 20,
    'ل': 30,
    'م': 40,
    'ن': 50,
    'س': 60,
    'ع': 70,
    'ف': 80,
    'ص': 90,
    'ق': 100,
    'ر': 200,
    'ش': 300,
    'ت': 400,
    'ث': 500,
    'خ': 600,
    'ذ': 700,
    'ض': 800,
    'ظ': 900,
    'غ': 1000,
}

# Maghribi system differences
ABJAD_MAGHRIBI = ABJAD_MASHRIQI.copy()
ABJAD_MAGHRIBI.update({
    'ص': 60,
    'ض': 90,
    'ظ': 800,
    'غ': 900,
    'س': 300,
    'ش': 1000,
})

# Arabic diacritics to remove for normalization
ARABIC_DIACRITICS = re.compile(r'[\u064B-\u0652\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7-\u06E8\u06EA-\u06ED]')

def remove_diacritics(text: str) -> str:
    """Remove Arabic diacritics from text."""
    return ARABIC_DIACRITICS.sub('', text)

def normalize_arabic(text: str) -> str:
    """Normalize Arabic text for consistent comparison."""
    # Remove diacritics
    text = remove_diacritics(text)
    # Normalize alef variants
    text = re.sub(r'[أإآٱ]', 'ا', text)
    # Normalize ya variants
    text = re.sub(r'[ىئ]', 'ي', text)
    # Normalize ta marbuta
    text = text.replace('ة', 'ه')
    # Remove tatweel
    text = text.replace('ـ', '')
    return text

def calculate_abjad(text: str, system: str = 'mashriqi') -> int:
    """Calculate abjad numerical value of Arabic text."""
    values = ABJAD_MASHRIQI if system == 'mashriqi' else ABJAD_MAGHRIBI
    total = 0
    for char in text:
        total += values.get(char, 0)
    return total

def count_arabic_letters(text: str) -> int:
    """Count Arabic letters (excluding diacritics and spaces)."""
    arabic_letter_range = re.compile(r'[\u0621-\u064A]')
    return len(arabic_letter_range.findall(text))

def count_words(text: str) -> int:
    """Count words in Arabic text."""
    words = text.split()
    return len([w for w in words if any('\u0621' <= c <= '\u064A' for c in w)])

def compute_checksum(text: str) -> str:
    """Compute SHA256 checksum of text."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def escape_sql_string(s) -> str:
    """Escape string for SQL."""
    if s is None or s is False:
        return 'NULL'
    if not isinstance(s, str):
        s = str(s)
    return "'" + s.replace("'", "''") + "'"

def parse_tanzil_xml(file_path: Path) -> dict:
    """Parse Tanzil XML file and return verses by location."""
    tree = ET.parse(file_path)
    root = tree.getroot()

    verses = {}
    for sura in root.findall('.//sura'):
        surah_num = int(sura.get('index'))
        for aya in sura.findall('aya'):
            verse_num = int(aya.get('index'))
            text = aya.get('text', '')
            verses[(surah_num, verse_num)] = text

    return verses

def load_metadata() -> list:
    """Load metadata from local JSON file."""
    # First try to load from a cached file
    cache_path = Path(__file__).parent / 'quran_metadata.json'
    if cache_path.exists():
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle wrapped format from gadingnst/quran-api
            if isinstance(data, dict) and 'data' in data:
                return data['data']
            return data

    print("ERROR: quran_metadata.json not found. Run with --download-metadata first.", file=sys.stderr)
    sys.exit(1)

def download_metadata():
    """Download and cache metadata."""
    import urllib.request

    url = "https://raw.githubusercontent.com/gadingnst/quran-api/main/data/quran.json"
    cache_path = Path(__file__).parent / 'quran_metadata.json'

    print(f"Downloading metadata from {url}...")

    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode('utf-8'))

    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Saved to {cache_path}")
    return data

# Surah English names
SURAH_ENGLISH_NAMES = [
    "The Opening", "The Cow", "The Family of Imran", "The Women", "The Table Spread",
    "The Cattle", "The Heights", "The Spoils of War", "The Repentance", "Jonah",
    "Hud", "Joseph", "The Thunder", "Abraham", "The Rocky Tract",
    "The Bee", "The Night Journey", "The Cave", "Mary", "Ta-Ha",
    "The Prophets", "The Pilgrimage", "The Believers", "The Light", "The Criterion",
    "The Poets", "The Ant", "The Stories", "The Spider", "The Romans",
    "Luqman", "The Prostration", "The Combined Forces", "Sheba", "The Originator",
    "Ya-Sin", "Those Ranged in Ranks", "Sad", "The Groups", "The Forgiver",
    "Explained in Detail", "The Consultation", "The Ornaments of Gold", "The Smoke", "The Crouching",
    "The Wind-Curved Sandhills", "Muhammad", "The Victory", "The Rooms", "Qaf",
    "The Winnowing Winds", "The Mount", "The Star", "The Moon", "The Beneficent",
    "The Inevitable", "The Iron", "The Pleading Woman", "The Exile", "She That is to be Examined",
    "The Ranks", "The Congregation", "The Hypocrites", "The Mutual Disillusion", "The Divorce",
    "The Prohibition", "The Sovereignty", "The Pen", "The Reality", "The Ascending Stairways",
    "Noah", "The Jinn", "The Enshrouded One", "The Cloaked One", "The Resurrection",
    "The Human", "The Emissaries", "The Tidings", "Those Who Drag Forth", "He Frowned",
    "The Overthrowing", "The Cleaving", "The Defrauding", "The Sundering", "The Mansions of the Stars",
    "The Morning Star", "The Most High", "The Overwhelming", "The Dawn", "The City",
    "The Sun", "The Night", "The Morning Hours", "The Relief", "The Fig",
    "The Clot", "The Power", "The Clear Proof", "The Earthquake", "The Courser",
    "The Calamity", "The Rivalry in World Increase", "The Declining Day", "The Traducer", "The Elephant",
    "The Quraysh", "The Small Kindnesses", "The Abundance", "The Disbelievers", "The Divine Support",
    "The Palm Fiber", "The Sincerity", "The Daybreak", "The Mankind"
]

# Surah transliterations
SURAH_TRANSLITERATIONS = [
    "Al-Fatihah", "Al-Baqarah", "Ali 'Imran", "An-Nisa", "Al-Ma'idah",
    "Al-An'am", "Al-A'raf", "Al-Anfal", "At-Tawbah", "Yunus",
    "Hud", "Yusuf", "Ar-Ra'd", "Ibrahim", "Al-Hijr",
    "An-Nahl", "Al-Isra", "Al-Kahf", "Maryam", "Ta-Ha",
    "Al-Anbya", "Al-Hajj", "Al-Mu'minun", "An-Nur", "Al-Furqan",
    "Ash-Shu'ara", "An-Naml", "Al-Qasas", "Al-'Ankabut", "Ar-Rum",
    "Luqman", "As-Sajdah", "Al-Ahzab", "Saba", "Fatir",
    "Ya-Sin", "As-Saffat", "Sad", "Az-Zumar", "Ghafir",
    "Fussilat", "Ash-Shura", "Az-Zukhruf", "Ad-Dukhan", "Al-Jathiyah",
    "Al-Ahqaf", "Muhammad", "Al-Fath", "Al-Hujurat", "Qaf",
    "Adh-Dhariyat", "At-Tur", "An-Najm", "Al-Qamar", "Ar-Rahman",
    "Al-Waqi'ah", "Al-Hadid", "Al-Mujadila", "Al-Hashr", "Al-Mumtahanah",
    "As-Saf", "Al-Jumu'ah", "Al-Munafiqun", "At-Taghabun", "At-Talaq",
    "At-Tahrim", "Al-Mulk", "Al-Qalam", "Al-Haqqah", "Al-Ma'arij",
    "Nuh", "Al-Jinn", "Al-Muzzammil", "Al-Muddathir", "Al-Qiyamah",
    "Al-Insan", "Al-Mursalat", "An-Naba", "An-Nazi'at", "'Abasa",
    "At-Takwir", "Al-Infitar", "Al-Mutaffifin", "Al-Inshiqaq", "Al-Buruj",
    "At-Tariq", "Al-A'la", "Al-Ghashiyah", "Al-Fajr", "Al-Balad",
    "Ash-Shams", "Al-Layl", "Ad-Duhaa", "Ash-Sharh", "At-Tin",
    "Al-'Alaq", "Al-Qadr", "Al-Bayyinah", "Az-Zalzalah", "Al-'Adiyat",
    "Al-Qari'ah", "At-Takathur", "Al-'Asr", "Al-Humazah", "Al-Fil",
    "Quraysh", "Al-Ma'un", "Al-Kawthar", "Al-Kafirun", "An-Nasr",
    "Al-Masad", "Al-Ikhlas", "Al-Falaq", "An-Nas"
]

# Revelation order
REVELATION_ORDER = [
    5, 87, 89, 92, 112, 55, 39, 88, 113, 51, 52, 53, 96, 72, 54,
    70, 50, 69, 44, 45, 73, 103, 74, 102, 42, 47, 48, 49, 85, 84,
    57, 75, 90, 58, 43, 41, 56, 38, 59, 60, 61, 62, 63, 64, 65,
    66, 95, 111, 106, 34, 67, 76, 23, 37, 97, 46, 94, 105, 101, 91,
    109, 110, 104, 108, 99, 107, 77, 2, 78, 79, 71, 40, 3, 4, 31,
    98, 33, 80, 81, 82, 7, 83, 86, 10, 27, 36, 8, 68, 89, 35,
    26, 9, 11, 12, 28, 1, 25, 100, 93, 14, 30, 16, 13, 32, 19,
    29, 17, 15, 18, 114, 6, 22, 20, 21
]

# Surah revelation types
REVELATION_TYPES = [
    "meccan", "medinan", "medinan", "medinan", "medinan", "meccan", "meccan", "medinan", "medinan", "meccan",
    "meccan", "meccan", "medinan", "meccan", "meccan", "meccan", "meccan", "meccan", "meccan", "meccan",
    "meccan", "medinan", "meccan", "medinan", "meccan", "meccan", "meccan", "meccan", "meccan", "meccan",
    "meccan", "meccan", "medinan", "meccan", "meccan", "meccan", "meccan", "meccan", "meccan", "meccan",
    "meccan", "meccan", "meccan", "meccan", "meccan", "meccan", "medinan", "medinan", "medinan", "meccan",
    "meccan", "meccan", "meccan", "meccan", "medinan", "meccan", "medinan", "medinan", "medinan", "medinan",
    "medinan", "medinan", "medinan", "medinan", "medinan", "medinan", "meccan", "meccan", "meccan", "meccan",
    "meccan", "meccan", "meccan", "meccan", "meccan", "medinan", "meccan", "meccan", "meccan", "meccan",
    "meccan", "meccan", "meccan", "meccan", "meccan", "meccan", "meccan", "meccan", "meccan", "meccan",
    "meccan", "meccan", "meccan", "meccan", "meccan", "meccan", "meccan", "medinan", "medinan", "meccan",
    "meccan", "meccan", "meccan", "meccan", "meccan", "meccan", "meccan", "meccan", "meccan", "medinan",
    "meccan", "meccan", "meccan", "meccan"
]

# Verse counts per surah
VERSE_COUNTS = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99,
    128, 111, 110, 98, 135, 112, 78, 118, 64, 77, 227, 93, 88, 69, 60,
    34, 30, 73, 54, 45, 83, 182, 88, 75, 85, 54, 53, 89, 59, 37,
    35, 38, 29, 18, 45, 60, 49, 62, 55, 78, 96, 29, 22, 24, 13,
    14, 11, 11, 18, 12, 12, 30, 52, 52, 44, 28, 28, 20, 56, 40,
    31, 50, 40, 46, 42, 29, 19, 36, 25, 22, 17, 19, 26, 30, 20,
    15, 21, 11, 8, 8, 19, 5, 8, 8, 11, 11, 8, 3, 9, 5,
    4, 7, 3, 6, 3, 5, 4, 5, 6
]

# Ruku counts per surah
RUKU_COUNTS = [
    1, 40, 20, 24, 16, 20, 24, 10, 16, 11, 10, 12, 6, 7, 6,
    16, 12, 12, 6, 8, 7, 10, 6, 9, 6, 11, 7, 8, 7, 6,
    4, 3, 9, 6, 5, 5, 5, 5, 8, 9, 6, 5, 7, 3, 4,
    4, 4, 4, 2, 3, 3, 2, 3, 3, 3, 3, 4, 3, 3, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1
]

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Generate SQL for Mizan database seeding')
    parser.add_argument('--download-metadata', action='store_true', help='Download metadata first')
    parser.add_argument('--output', '-o', default='seed_data.sql', help='Output SQL file')
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    quran_dir = project_root / 'quran'

    # Download metadata if requested
    if args.download_metadata:
        download_metadata()
        return

    # Load Tanzil XML files
    print("Loading Tanzil XML files...")
    uthmani_path = quran_dir / 'uthmani' / 'quran-uthmani.xml'
    uthmani_min_path = quran_dir / 'uthmani-min' / 'quran-uthmani-min.xml'
    simple_path = quran_dir / 'simple' / 'quran-simple.xml'

    if not uthmani_path.exists():
        print(f"ERROR: {uthmani_path} not found", file=sys.stderr)
        sys.exit(1)

    uthmani_verses = parse_tanzil_xml(uthmani_path)
    uthmani_min_verses = parse_tanzil_xml(uthmani_min_path) if uthmani_min_path.exists() else {}
    simple_verses = parse_tanzil_xml(simple_path) if simple_path.exists() else {}

    print(f"Loaded {len(uthmani_verses)} verses from Tanzil XML")

    # Load metadata
    print("Loading metadata...")
    metadata = load_metadata()

    # Build metadata lookup
    verse_meta = {}
    for surah_data in metadata:
        surah_num = surah_data['number']
        for verse_data in surah_data.get('verses', []):
            # Handle nested number structure
            verse_num_data = verse_data.get('number', {})
            if isinstance(verse_num_data, dict):
                verse_num = verse_num_data.get('inSurah', 1)
            else:
                verse_num = verse_num_data
            meta = verse_data.get('meta', {})
            sajda_data = meta.get('sajda', False)
            # Handle sajda object structure
            if isinstance(sajda_data, dict):
                is_sajda = sajda_data.get('recommended', False) or sajda_data.get('obligatory', False)
            else:
                is_sajda = sajda_data
            verse_meta[(surah_num, verse_num)] = {
                'juz': meta.get('juz', 1),
                'page': meta.get('page', 1),
                'manzil': meta.get('manzil', 1),
                'ruku': meta.get('ruku', 1),
                'hizb': meta.get('hizbQuarter', 1),
                'sajda': sajda_data if is_sajda else False,
            }

    # Generate SQL
    print(f"Generating SQL file: {args.output}")

    now = datetime.utcnow().isoformat()

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write("-- Mizan Database Seed Data\n")
        f.write(f"-- Generated: {now}\n")
        f.write("-- Source: Tanzil.net (quran-uthmani.xml)\n")
        f.write("-- Metadata: gadingnst/quran-api\n\n")

        # Create extension for trigram search
        f.write("-- Enable trigram extension for text search\n")
        f.write("CREATE EXTENSION IF NOT EXISTS pg_trgm;\n\n")

        # Create tables
        f.write("-- Create tables if not exist\n")
        f.write("""
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
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS verses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(surah_number, verse_number)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_surahs_revelation_type ON surahs(revelation_type);
CREATE INDEX IF NOT EXISTS ix_surahs_revelation_order ON surahs(revelation_order);
CREATE INDEX IF NOT EXISTS ix_verses_surah_verse ON verses(surah_number, verse_number);
CREATE INDEX IF NOT EXISTS ix_verses_juz ON verses(juz_number);
CREATE INDEX IF NOT EXISTS ix_verses_hizb ON verses(hizb_number);
CREATE INDEX IF NOT EXISTS ix_verses_manzil ON verses(manzil_number);
CREATE INDEX IF NOT EXISTS ix_verses_page ON verses(page_number);
CREATE INDEX IF NOT EXISTS ix_verses_sajdah ON verses(is_sajdah);

""")

        # Clear existing data
        f.write("-- Clear existing data\n")
        f.write("TRUNCATE TABLE verses CASCADE;\n")
        f.write("TRUNCATE TABLE surahs CASCADE;\n\n")

        # Insert surahs
        f.write("-- Insert surahs\n")
        f.write("INSERT INTO surahs (id, name_arabic, name_english, name_transliteration, revelation_type, revelation_order, basmalah_status, verse_count, ruku_count, word_count, letter_count, abjad_value, checksum) VALUES\n")

        surah_rows = []
        surah_aggregates = {}  # Store aggregates for later

        for i in range(114):
            surah_num = i + 1

            # Get Arabic name from metadata
            arabic_name = metadata[i].get('name', {}).get('short', f'سورة {surah_num}')
            english_name = SURAH_ENGLISH_NAMES[i]
            transliteration = SURAH_TRANSLITERATIONS[i]

            # Calculate aggregates from verses
            total_text = ""
            for verse_num in range(1, VERSE_COUNTS[i] + 1):
                text = uthmani_verses.get((surah_num, verse_num), "")
                total_text += text + " "

            word_count = count_words(total_text)
            letter_count = count_arabic_letters(total_text)
            abjad_value = calculate_abjad(total_text)
            checksum = compute_checksum(total_text)

            surah_aggregates[surah_num] = {
                'word_count': word_count,
                'letter_count': letter_count,
                'abjad_value': abjad_value,
            }

            # Determine basmalah status
            if surah_num == 1:
                basmalah = "included_in_first_verse"
            elif surah_num == 9:
                basmalah = "none"
            else:
                basmalah = "separate"

            row = f"({surah_num}, {escape_sql_string(arabic_name)}, {escape_sql_string(english_name)}, {escape_sql_string(transliteration)}, '{REVELATION_TYPES[i]}', {REVELATION_ORDER[i]}, '{basmalah}', {VERSE_COUNTS[i]}, {RUKU_COUNTS[i]}, {word_count}, {letter_count}, {abjad_value}, {escape_sql_string(checksum)})"
            surah_rows.append(row)

        f.write(",\n".join(surah_rows))
        f.write(";\n\n")

        # Insert verses
        f.write("-- Insert verses\n")

        batch_size = 100
        verse_rows = []
        verse_count = 0

        for surah_num in range(1, 115):
            for verse_num in range(1, VERSE_COUNTS[surah_num - 1] + 1):
                text_uthmani = uthmani_verses.get((surah_num, verse_num), "")
                text_uthmani_min = uthmani_min_verses.get((surah_num, verse_num))
                text_simple = simple_verses.get((surah_num, verse_num))

                # Normalized forms
                text_normalized = normalize_arabic(text_uthmani).lower()
                text_no_tashkeel = remove_diacritics(text_uthmani)

                # Get metadata
                meta = verse_meta.get((surah_num, verse_num), {})
                juz = meta.get('juz', 1)
                page = meta.get('page', 1)
                manzil = meta.get('manzil', 1)
                ruku = meta.get('ruku', 1)
                hizb = meta.get('hizb', 1)
                sajda = meta.get('sajda', False)

                # Handle sajda info
                is_sajdah = False
                sajdah_type = None
                if isinstance(sajda, dict):
                    if sajda.get('obligatory', False):
                        is_sajdah = True
                        sajdah_type = 'obligatory'
                    elif sajda.get('recommended', False):
                        is_sajdah = True
                        sajdah_type = 'recommended'
                elif sajda:
                    is_sajdah = True
                    sajdah_type = 'recommended'

                # Compute values
                word_count = count_words(text_uthmani)
                letter_count = count_arabic_letters(text_uthmani)
                abjad_mashriqi = calculate_abjad(text_uthmani, 'mashriqi')
                abjad_maghribi = calculate_abjad(text_uthmani, 'maghribi')
                checksum = compute_checksum(text_uthmani)

                # Generate UUID
                verse_id = str(uuid4())

                row = f"('{verse_id}', {surah_num}, {verse_num}, {escape_sql_string(text_uthmani)}, {escape_sql_string(text_uthmani_min)}, {escape_sql_string(text_simple)}, {escape_sql_string(text_normalized)}, {escape_sql_string(text_no_tashkeel)}, NULL, {juz}, {hizb}, {ruku}, {manzil}, {page}, {str(is_sajdah).upper()}, {escape_sql_string(sajdah_type)}, {word_count}, {letter_count}, {abjad_mashriqi}, {abjad_maghribi}, {escape_sql_string(checksum)})"

                verse_rows.append(row)
                verse_count += 1

                # Write in batches
                if len(verse_rows) >= batch_size:
                    f.write(f"INSERT INTO verses (id, surah_number, verse_number, text_uthmani, text_uthmani_min, text_simple, text_normalized_full, text_no_tashkeel, qiraat_variants, juz_number, hizb_number, ruku_number, manzil_number, page_number, is_sajdah, sajdah_type, word_count, letter_count, abjad_value_mashriqi, abjad_value_maghribi, checksum) VALUES\n")
                    f.write(",\n".join(verse_rows))
                    f.write(";\n\n")
                    verse_rows = []

        # Write remaining verses
        if verse_rows:
            f.write(f"INSERT INTO verses (id, surah_number, verse_number, text_uthmani, text_uthmani_min, text_simple, text_normalized_full, text_no_tashkeel, qiraat_variants, juz_number, hizb_number, ruku_number, manzil_number, page_number, is_sajdah, sajdah_type, word_count, letter_count, abjad_value_mashriqi, abjad_value_maghribi, checksum) VALUES\n")
            f.write(",\n".join(verse_rows))
            f.write(";\n\n")

        # Verification queries
        f.write("-- Verification\n")
        f.write("SELECT 'Surahs:', COUNT(*) FROM surahs;\n")
        f.write("SELECT 'Verses:', COUNT(*) FROM verses;\n")
        f.write("SELECT 'Al-Fatihah verses:', COUNT(*) FROM verses WHERE surah_number = 1;\n")

    print(f"Generated SQL with {verse_count} verses")
    print(f"Output: {args.output}")

if __name__ == '__main__':
    main()
