#!/usr/bin/env python3
"""
MASAQ Morphology Data Ingestion Script

Downloads and parses Quranic Arabic Corpus (QAC) morphological data and
populates the morphology table.

The script parses the standard QAC morphology format (tab-separated):
    LOCATION    FORM    TAG     FEATURES
    (1:1:1:1)   ...     P       PREFIX|bi+
    (1:1:1:2)   ...     N       STEM|POS:N|LEM:{som|ROOT:smw|M|GEN

Usage:
    # Download from GitHub mirror and ingest:
    python scripts/ingest_masaq.py

    # Use a local QAC morphology file:
    python scripts/ingest_masaq.py --file data/quranic-corpus-morphology.txt

    # Dry run (no data written):
    python scripts/ingest_masaq.py --dry-run

Environment variables:
    DATABASE_URL  PostgreSQL connection string
                  (default: postgresql://mizan:mizan@localhost:5432/mizan)

Notes:
    - Run after: alembic upgrade head && python scripts/ingest_tanzil.py
    - Requires the verses table to be populated (for verse_id foreign key)
"""

import argparse
import os
import re
import sys
import uuid
from pathlib import Path
from urllib.request import Request, urlopen

import sqlalchemy as sa
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_DB_URL = "postgresql://mizan:mizan@localhost:5432/mizan"

# Public GitHub mirrors of the Quranic Arabic Corpus morphology data
QAC_DOWNLOAD_URLS = [
    "https://raw.githubusercontent.com/oazabir/Quran/master/declensions/declensions.txt",
    "https://raw.githubusercontent.com/kaisdukes/quranic-corpus/master/data/quranic-corpus-morphology-0.4.txt",
]

# ---------------------------------------------------------------------------
# QAC Morphology Format Parser
# ---------------------------------------------------------------------------

# POS tag mapping from QAC abbreviations to human-readable labels
POS_TAG_MAP = {
    "N": "N",           # Noun
    "PN": "PN",         # Proper Noun
    "ADJ": "ADJ",       # Adjective
    "V": "V",           # Verb
    "PRON": "PRON",     # Pronoun
    "DEM": "DEM",       # Demonstrative
    "REL": "REL",       # Relative pronoun
    "T": "T",           # Time adverb
    "LOC": "LOC",       # Location adverb
    "P": "P",           # Preposition
    "CONJ": "CONJ",     # Conjunction
    "EMPH": "EMPH",     # Emphatic particle
    "INTG": "INTG",     # Interrogative
    "NEG": "NEG",       # Negative
    "SUP": "SUP",       # Supplementary
    "VOC": "VOC",       # Vocative
    "IMPV": "IMPV",     # Imperative
    "PRT": "PRT",       # Particle
    "REM": "REM",       # Resumption
    "RES": "RES",       # Restriction
    "RET": "RET",       # Retraction
    "CERT": "CERT",     # Certainty
    "ANS": "ANS",       # Answer
    "AVR": "AVR",       # Aversion
    "CAUS": "CAUS",     # Cause
    "AMD": "AMD",       # Amendment
    "CIRC": "CIRC",     # Circumstantial
    "COM": "COM",       # Comitative
    "COND": "COND",     # Conditional
    "EQ": "EQ",         # Equalization
    "EXH": "EXH",       # Exhortation
    "EXL": "EXL",       # Explanation
    "EXP": "EXP",       # Exceptive
    "FUT": "FUT",       # Future
    "INC": "INC",       # Inceptive
    "INT": "INT",       # Interpretation
    "PREV": "PREV",     # Preventive
    "PRO": "PRO",       # Prohibition
    "SUR": "SUR",       # Surprise
    "INL": "INL",       # Initiation particle (lam)
    "ACC": "ACC",       # Accusative particle
    "RSLT": "RSLT",     # Result
}

# Person mapping
PERSON_MAP = {"1": "1", "2": "2", "3": "3"}

# Gender mapping
GENDER_MAP = {"M": "M", "F": "F"}

# Number mapping
NUMBER_MAP = {"S": "S", "D": "D", "P": "P"}

# Case mapping
CASE_MAP = {
    "NOM": "NOM",     # Nominative
    "ACC": "ACC",     # Accusative
    "GEN": "GEN",     # Genitive
}

# Mood mapping
MOOD_MAP = {
    "IND": "IND",     # Indicative
    "SUBJ": "SUBJ",   # Subjunctive
    "JUS": "JUS",     # Jussive
}

# Voice mapping
VOICE_MAP = {
    "ACT": "ACT",     # Active
    "PASS": "PASS",   # Passive
}


def parse_location(loc_str: str) -> tuple[int, int, int, int] | None:
    """
    Parse QAC location string like (1:2:3:4) into (surah, verse, word, segment).

    Returns None if the format is invalid.
    """
    match = re.match(r"\((\d+):(\d+):(\d+):(\d+)\)", loc_str.strip())
    if not match:
        return None
    return (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)),
        int(match.group(4)),
    )


def parse_features(features_str: str) -> dict[str, str | None]:
    """
    Parse QAC feature string like:
        STEM|POS:N|LEM:{som|ROOT:smw|M|GEN
        PREFIX|bi+

    Returns a dict with extracted features.
    """
    result: dict[str, str | None] = {
        "morpheme_type": "STEM",
        "pos_tag": "UNK",
        "root": None,
        "lemma": None,
        "pattern": None,
        "person": None,
        "gender": None,
        "number": None,
        "case_state": None,
        "mood_voice": None,
    }

    if not features_str:
        return result

    parts = features_str.split("|")

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Morpheme type (first element is often PREFIX, STEM, or SUFFIX)
        if part in ("PREFIX", "STEM", "SUFFIX"):
            result["morpheme_type"] = part
            continue

        # Key:Value pairs
        if ":" in part:
            key, _, value = part.partition(":")
            key = key.strip().upper()
            value = value.strip()

            if key == "POS":
                result["pos_tag"] = POS_TAG_MAP.get(value, value)
            elif key == "ROOT":
                result["root"] = value
            elif key == "LEM":
                result["lemma"] = value
            elif key == "SP":
                # Special/state
                result["case_state"] = value
            elif key == "MOOD":
                result["mood_voice"] = MOOD_MAP.get(value, value)
            elif key == "VOICE":
                voice = VOICE_MAP.get(value, value)
                if result["mood_voice"]:
                    result["mood_voice"] += "/" + voice
                else:
                    result["mood_voice"] = voice
            elif key == "FORM":
                result["pattern"] = value
            elif key == "(":
                # Pattern like (IV) for verb forms
                result["pattern"] = value.rstrip(")")
            continue

        # Standalone tokens
        if part in PERSON_MAP:
            result["person"] = PERSON_MAP[part]
        elif part in GENDER_MAP:
            result["gender"] = GENDER_MAP[part]
        elif part in NUMBER_MAP:
            result["number"] = NUMBER_MAP[part]
        elif part in CASE_MAP:
            result["case_state"] = CASE_MAP[part]
        elif part in MOOD_MAP:
            result["mood_voice"] = MOOD_MAP.get(part, part)
        elif part in VOICE_MAP:
            voice = VOICE_MAP[part]
            if result["mood_voice"]:
                result["mood_voice"] += "/" + voice
            else:
                result["mood_voice"] = voice
        elif part in POS_TAG_MAP:
            result["pos_tag"] = POS_TAG_MAP[part]
        elif part.endswith("+") or part.startswith("+"):
            # Prefix/suffix marker (e.g., "bi+", "+hum")
            pass
        elif part.startswith("(") and part.endswith(")"):
            # Verb form like (IV)
            result["pattern"] = part.strip("()")

    return result


def parse_qac_line(line: str) -> dict | None:
    """
    Parse a single line of QAC morphology data.

    Expected format (tab-separated):
        LOCATION    FORM    TAG     FEATURES

    Returns a dict with all parsed fields, or None if the line is invalid.
    """
    line = line.strip()
    if not line or line.startswith("#") or line.startswith("LOCATION"):
        return None

    # Split by tabs; some files use mixed whitespace
    parts = re.split(r"\t+", line)
    if len(parts) < 3:
        # Try splitting on multiple spaces
        parts = re.split(r"\s{2,}", line)
    if len(parts) < 3:
        return None

    location = parse_location(parts[0])
    if location is None:
        return None

    surah, verse, word, segment = location
    form = parts[1].strip()
    tag = parts[2].strip()
    features_str = parts[3].strip() if len(parts) > 3 else ""

    features = parse_features(features_str)

    # If the tag itself is a POS tag and features didn't set it
    if features["pos_tag"] == "UNK" and tag in POS_TAG_MAP:
        features["pos_tag"] = POS_TAG_MAP[tag]

    return {
        "surah_number": surah,
        "verse_number": verse,
        "word_number": word,
        "segment_number": segment,
        "form": form,
        "tag": tag,
        **features,
    }


def parse_qac_file(content: str) -> list[dict]:
    """Parse entire QAC morphology file content, return list of parsed records."""
    records = []
    for line_num, line in enumerate(content.splitlines(), 1):
        parsed = parse_qac_line(line)
        if parsed is not None:
            records.append(parsed)

    return records


# ---------------------------------------------------------------------------
# Download helpers
# ---------------------------------------------------------------------------


def fetch_url(url: str, timeout: int = 60) -> bytes:
    """Download URL content with a User-Agent header."""
    req = Request(url, headers={"User-Agent": "Mizan-Ingest/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def download_qac_data() -> str | None:
    """Try to download QAC morphology data from known mirrors."""
    for url in QAC_DOWNLOAD_URLS:
        try:
            print(f"  Trying: {url}")
            raw = fetch_url(url)
            content = raw.decode("utf-8", errors="replace")
            # Verify it looks like QAC data
            if "(1:1:1:" in content:
                print(f"  Downloaded {len(raw):,} bytes")
                return content
            else:
                print(f"  Downloaded but does not look like QAC morphology data")
        except Exception as exc:
            print(f"  Failed: {exc}")
    return None


# ---------------------------------------------------------------------------
# Synthetic morphology data generator
# ---------------------------------------------------------------------------

# When no external data source is available, we generate basic morphological
# data from the existing verse text in the database. This provides a starting
# point that can be enriched later with full QAC data.


def generate_from_verses(db_url: str) -> list[dict]:
    """
    Generate basic morphological records from existing verse text.

    This creates one STEM record per word (space-delimited) from the
    uthmani text, with minimal POS tagging based on simple heuristics.
    """
    engine = create_engine(db_url, echo=False)
    records = []

    # Common Arabic particles/prepositions for basic POS tagging
    PARTICLES = {
        "فِى", "فِي", "مِن", "مِنْ", "عَلَىٰ", "عَلَى", "إِلَىٰ", "إِلَى",
        "عَن", "عَنْ", "بَيْنَ", "حَتَّىٰ", "حَتَّى", "مَعَ",
    }
    CONJUNCTIONS = {"وَ", "فَ", "ثُمَّ", "أَوْ", "أَمْ", "بَلْ", "لَٰكِنَّ", "لَٰكِن"}
    PRONOUNS = {
        "هُوَ", "هِىَ", "هِيَ", "هُمْ", "هُنَّ", "أَنتَ", "أَنتِ",
        "أَنتُمْ", "أَنَا۠", "أَنَا", "نَحْنُ", "هُمَا", "أَنتُمَا",
    }
    DEMONSTRATIVES = {
        "هَٰذَا", "هَٰذِهِ", "ذَٰلِكَ", "تِلْكَ", "هَٰؤُلَآءِ",
        "أُو۟لَٰٓئِكَ", "ذَٰلِكُمُ",
    }
    NEGATIONS = {"لَا", "لَمْ", "لَن", "مَا", "لَيْسَ"}

    def simple_pos(word: str) -> str:
        """Assign a basic POS tag based on simple heuristics."""
        if word in PARTICLES:
            return "P"
        if word in CONJUNCTIONS:
            return "CONJ"
        if word in PRONOUNS:
            return "PRON"
        if word in DEMONSTRATIVES:
            return "DEM"
        if word in NEGATIONS:
            return "NEG"
        if word == "ٱللَّهِ" or word == "ٱللَّهُ" or word == "ٱللَّهَ":
            return "PN"
        # Default to noun
        return "N"

    with engine.connect() as conn:
        result = conn.execute(
            sa.text(
                "SELECT surah_number, verse_number, text_uthmani "
                "FROM verses ORDER BY surah_number, verse_number"
            )
        )
        for row in result:
            surah_num, verse_num, text_uthmani = row
            words = text_uthmani.split()
            for word_idx, word in enumerate(words, 1):
                pos = simple_pos(word)
                records.append({
                    "surah_number": surah_num,
                    "verse_number": verse_num,
                    "word_number": word_idx,
                    "segment_number": 1,
                    "form": word,
                    "tag": pos,
                    "morpheme_type": "STEM",
                    "pos_tag": pos,
                    "root": None,
                    "lemma": None,
                    "pattern": None,
                    "person": None,
                    "gender": None,
                    "number": None,
                    "case_state": None,
                    "mood_voice": None,
                })

    print(f"  Generated {len(records):,} basic morphology records from verse text")
    return records


# ---------------------------------------------------------------------------
# Database ingestion
# ---------------------------------------------------------------------------


def build_verse_id_map(engine: sa.engine.Engine) -> dict[tuple[int, int], str]:
    """Build a map of (surah, verse) -> verse UUID from the verses table."""
    verse_map: dict[tuple[int, int], str] = {}
    with engine.connect() as conn:
        result = conn.execute(
            sa.text("SELECT surah_number, verse_number, id FROM verses")
        )
        for row in result:
            verse_map[(row[0], row[1])] = str(row[2])
    return verse_map


def ingest(
    records: list[dict],
    db_url: str,
    batch_size: int = 500,
    dry_run: bool = False,
) -> None:
    """Insert morphology records into the database."""
    engine = create_engine(db_url, echo=False)

    print("Building verse ID lookup map...")
    verse_map = build_verse_id_map(engine)
    if not verse_map:
        print("ERROR: No verses found in database. Run ingest_tanzil.py first.")
        sys.exit(1)
    print(f"  Found {len(verse_map):,} verses in database")

    # Check for existing morphology data
    with engine.connect() as conn:
        existing_count = conn.execute(
            sa.text("SELECT COUNT(*) FROM morphology")
        ).scalar()
        if existing_count and existing_count > 0:
            print(f"  Found {existing_count:,} existing morphology records")
            print("  Skipping duplicates (based on location)")

    total_inserted = 0
    total_skipped = 0
    batch: list[dict] = []

    with engine.begin() as conn:
        for record in records:
            key = (record["surah_number"], record["verse_number"])
            verse_id = verse_map.get(key)
            if verse_id is None:
                total_skipped += 1
                continue

            row = {
                "surah_number": record["surah_number"],
                "verse_number": record["verse_number"],
                "word_number": record["word_number"],
                "segment_number": record["segment_number"],
                "verse_id": verse_id,
                "word_uthmani": record.get("form", ""),
                "word_imlaei": record.get("form", ""),
                "segment_uthmani": record.get("form"),
                "segment_imlaei": record.get("form"),
                "morpheme_type": record.get("morpheme_type", "STEM"),
                "pos_tag": record.get("pos_tag", "UNK"),
                "root": record.get("root"),
                "lemma": record.get("lemma"),
                "pattern": record.get("pattern"),
                "person": record.get("person"),
                "gender": record.get("gender"),
                "number": record.get("number"),
                "case_state": record.get("case_state"),
                "mood_voice": record.get("mood_voice"),
                "syntactic_role": None,
                "irab_description": None,
            }
            batch.append(row)

            if len(batch) >= batch_size:
                _insert_batch(conn, batch, existing_count > 0 if existing_count else False)
                total_inserted += len(batch)
                print(f"\r  Inserted {total_inserted:,} records...", end="", flush=True)
                batch = []

        # Insert remaining batch
        if batch:
            _insert_batch(conn, batch, existing_count > 0 if existing_count else False)
            total_inserted += len(batch)

        if dry_run:
            raise Exception("DRY RUN -- rolling back")

    print(f"\n  Total inserted: {total_inserted:,}")
    if total_skipped:
        print(f"  Skipped (no matching verse): {total_skipped:,}")


def _insert_batch(conn: sa.Connection, batch: list[dict], skip_duplicates: bool) -> None:
    """Insert a batch of morphology records."""
    if skip_duplicates:
        # Use INSERT ... ON CONFLICT DO NOTHING approach
        # We create a unique check on (surah, verse, word, segment)
        for row in batch:
            conn.execute(
                sa.text("""
                    INSERT INTO morphology
                        (surah_number, verse_number, word_number, segment_number,
                         verse_id, word_uthmani, word_imlaei,
                         segment_uthmani, segment_imlaei,
                         morpheme_type, pos_tag, root, lemma, pattern,
                         person, gender, number, case_state, mood_voice,
                         syntactic_role, irab_description)
                    SELECT
                        :surah_number, :verse_number, :word_number, :segment_number,
                        :verse_id, :word_uthmani, :word_imlaei,
                        :segment_uthmani, :segment_imlaei,
                        :morpheme_type, :pos_tag, :root, :lemma, :pattern,
                        :person, :gender, :number, :case_state, :mood_voice,
                        :syntactic_role, :irab_description
                    WHERE NOT EXISTS (
                        SELECT 1 FROM morphology
                        WHERE surah_number = :surah_number
                          AND verse_number = :verse_number
                          AND word_number = :word_number
                          AND segment_number = :segment_number
                    )
                """),
                row,
            )
    else:
        for row in batch:
            conn.execute(
                sa.text("""
                    INSERT INTO morphology
                        (surah_number, verse_number, word_number, segment_number,
                         verse_id, word_uthmani, word_imlaei,
                         segment_uthmani, segment_imlaei,
                         morpheme_type, pos_tag, root, lemma, pattern,
                         person, gender, number, case_state, mood_voice,
                         syntactic_role, irab_description)
                    VALUES
                        (:surah_number, :verse_number, :word_number, :segment_number,
                         :verse_id, :word_uthmani, :word_imlaei,
                         :segment_uthmani, :segment_imlaei,
                         :morpheme_type, :pos_tag, :root, :lemma, :pattern,
                         :person, :gender, :number, :case_state, :mood_voice,
                         :syntactic_role, :irab_description)
                """),
                row,
            )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest MASAQ/QAC morphological data into Mizan database"
    )
    parser.add_argument(
        "--file",
        metavar="FILE",
        help="Path to QAC morphology text file (default: download from GitHub)",
    )
    parser.add_argument(
        "--db-url",
        default=None,
        help=f"PostgreSQL URL (default: $DATABASE_URL or {DEFAULT_DB_URL})",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Batch size for database inserts (default: 500)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and process data but rollback the transaction",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate basic morphology from existing verse text (fallback mode)",
    )
    args = parser.parse_args()

    db_url = args.db_url or os.environ.get("DATABASE_URL", DEFAULT_DB_URL)

    records: list[dict] = []

    if args.generate:
        # Fallback: generate basic morphology from verse text
        print("Generating morphology from existing verse text...")
        records = generate_from_verses(db_url)

    elif args.file:
        # Load from local file
        print(f"Loading QAC morphology from: {args.file}")
        content = Path(args.file).read_text(encoding="utf-8")
        records = parse_qac_file(content)
        print(f"  Parsed {len(records):,} morphology records")

    else:
        # Try downloading from known sources
        print("Downloading QAC morphology data...")
        content = download_qac_data()
        if content:
            records = parse_qac_file(content)
            print(f"  Parsed {len(records):,} morphology records")
        else:
            print("\nCould not download QAC data from any known source.")
            print("Falling back to generating basic morphology from verse text...")
            records = generate_from_verses(db_url)

    if not records:
        print("ERROR: No morphology records to insert.")
        sys.exit(1)

    # Ingest
    print(f"\nConnecting to database: {db_url[:40]}...")
    try:
        ingest(records, db_url, batch_size=args.batch_size, dry_run=args.dry_run)
    except Exception as exc:
        if args.dry_run and "DRY RUN" in str(exc):
            print("\nDry run complete -- no data written.")
        else:
            print(f"\nERROR during ingestion: {exc}")
            raise

    print("\nMorphology ingestion complete.")


if __name__ == "__main__":
    main()
