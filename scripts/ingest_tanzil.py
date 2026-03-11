#!/usr/bin/env python3
"""
Tanzil Quran Data Ingestion Script

Downloads Quran text from tanzil.net and populates the surahs + verses tables.

Usage:
    # Download automatically from tanzil.net:
    python scripts/ingest_tanzil.py

    # Use local XML files:
    python scripts/ingest_tanzil.py \\
        --uthmani data/quran-uthmani.xml \\
        --simple  data/quran-simple.xml

Environment variables:
    DATABASE_URL  PostgreSQL connection string (default: postgresql://mizan:mizan@localhost:5432/mizan)

Notes:
    - Tanzil XML files are downloaded from https://tanzil.net/pub/quran/
    - Run after: alembic upgrade head
    - Run before: python scripts/embed_quran.py
"""

import argparse
import hashlib
import io
import sys
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request

import sqlalchemy as sa
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TANZIL_UTHMANI_URL = "https://tanzil.net/pub/quran/quran-uthmani-hafs.xml"
TANZIL_SIMPLE_URL = "https://tanzil.net/pub/quran/quran-simple.xml"

DEFAULT_DB_URL = "postgresql://mizan:mizan@localhost:5432/mizan"

# ---------------------------------------------------------------------------
# Static Surah Metadata
# (number, arabic_name, english_name, transliteration, revelation_type,
#  revelation_order, verse_count, ruku_count, basmalah_status)
# ---------------------------------------------------------------------------

SURAHS = [
    (1,   "الفاتحة",     "The Opening",                   "Al-Fatihah",      "meccan",   5,   7,   1,  "starts_with"),
    (2,   "البقرة",      "The Cow",                       "Al-Baqarah",      "medinan", 87, 286,  40,  "starts_with"),
    (3,   "آل عمران",    "Family of Imran",               "Ali-Imran",       "medinan", 89, 200,  20,  "starts_with"),
    (4,   "النساء",      "The Women",                     "An-Nisa",         "medinan", 92, 176,  24,  "starts_with"),
    (5,   "المائدة",     "The Table Spread",               "Al-Ma'idah",      "medinan",112, 120,  16,  "starts_with"),
    (6,   "الأنعام",     "The Cattle",                    "Al-An'am",        "meccan",  55, 165,  20,  "starts_with"),
    (7,   "الأعراف",     "The Heights",                   "Al-A'raf",        "meccan",  39, 206,  24,  "starts_with"),
    (8,   "الأنفال",     "The Spoils of War",              "Al-Anfal",        "medinan", 88,  75,  10,  "starts_with"),
    (9,   "التوبة",      "The Repentance",                "At-Tawbah",       "medinan",113, 129,  16,  "missing"),
    (10,  "يونس",        "Jonah",                         "Yunus",           "meccan",  51, 109,  11,  "starts_with"),
    (11,  "هود",         "Hud",                           "Hud",             "meccan",  52, 123,  10,  "starts_with"),
    (12,  "يوسف",        "Joseph",                        "Yusuf",           "meccan",  53, 111,  12,  "starts_with"),
    (13,  "الرعد",       "The Thunder",                   "Ar-Ra'd",         "medinan", 96,  43,   6,  "starts_with"),
    (14,  "إبراهيم",     "Abraham",                       "Ibrahim",         "meccan",  72,  52,   7,  "starts_with"),
    (15,  "الحجر",       "The Rocky Tract",               "Al-Hijr",         "meccan",  54,  99,   6,  "starts_with"),
    (16,  "النحل",       "The Bee",                       "An-Nahl",         "meccan",  70, 128,  16,  "starts_with"),
    (17,  "الإسراء",     "The Night Journey",             "Al-Isra",         "meccan",  50, 111,  12,  "starts_with"),
    (18,  "الكهف",       "The Cave",                      "Al-Kahf",         "meccan",  69, 110,  12,  "starts_with"),
    (19,  "مريم",        "Mary",                          "Maryam",          "meccan",  44,  98,   6,  "starts_with"),
    (20,  "طه",          "Ta-Ha",                         "Ta-Ha",           "meccan",  45, 135,   8,  "starts_with"),
    (21,  "الأنبياء",    "The Prophets",                  "Al-Anbiya",       "meccan",  73, 112,   7,  "starts_with"),
    (22,  "الحج",        "The Pilgrimage",                "Al-Hajj",         "medinan",103,  78,  10,  "starts_with"),
    (23,  "المؤمنون",    "The Believers",                 "Al-Mu'minun",     "meccan",  74, 118,   6,  "starts_with"),
    (24,  "النور",       "The Light",                     "An-Nur",          "medinan",102,  64,   9,  "starts_with"),
    (25,  "الفرقان",     "The Criterion",                 "Al-Furqan",       "meccan",  42,  77,   6,  "starts_with"),
    (26,  "الشعراء",     "The Poets",                     "Ash-Shu'ara",     "meccan",  47, 227,  11,  "starts_with"),
    (27,  "النمل",       "The Ant",                       "An-Naml",         "meccan",  48,  93,   7,  "starts_with"),
    (28,  "القصص",       "The Stories",                   "Al-Qasas",        "meccan",  49,  88,   9,  "starts_with"),
    (29,  "العنكبوت",    "The Spider",                    "Al-Ankabut",      "meccan",  85,  69,   7,  "starts_with"),
    (30,  "الروم",       "The Romans",                    "Ar-Rum",          "meccan",  84,  60,   6,  "starts_with"),
    (31,  "لقمان",       "Luqman",                        "Luqman",          "meccan",  57,  34,   4,  "starts_with"),
    (32,  "السجدة",      "The Prostration",               "As-Sajdah",       "meccan",  75,  30,   3,  "starts_with"),
    (33,  "الأحزاب",     "The Combined Forces",           "Al-Ahzab",        "medinan", 90,  73,   9,  "starts_with"),
    (34,  "سبأ",         "Sheba",                         "Saba'",           "meccan",  58,  54,   6,  "starts_with"),
    (35,  "فاطر",        "Originator",                    "Fatir",           "meccan",  43,  45,   5,  "starts_with"),
    (36,  "يس",          "Ya-Sin",                        "Ya-Sin",          "meccan",  41,  83,   5,  "starts_with"),
    (37,  "الصافات",     "Those Who Set the Ranks",       "As-Saffat",       "meccan",  56, 182,   5,  "starts_with"),
    (38,  "ص",           "The Letter Sad",                "Sad",             "meccan",  38,  88,   5,  "starts_with"),
    (39,  "الزمر",       "The Troops",                    "Az-Zumar",        "meccan",  59,  75,   8,  "starts_with"),
    (40,  "غافر",        "The Forgiver",                  "Ghafir",          "meccan",  60,  85,   9,  "starts_with"),
    (41,  "فصلت",        "Explained in Detail",           "Fussilat",        "meccan",  61,  54,   6,  "starts_with"),
    (42,  "الشورى",      "The Consultation",              "Ash-Shura",       "meccan",  62,  53,   5,  "starts_with"),
    (43,  "الزخرف",      "The Ornaments of Gold",         "Az-Zukhruf",      "meccan",  63,  89,   7,  "starts_with"),
    (44,  "الدخان",      "The Smoke",                     "Ad-Dukhan",       "meccan",  64,  59,   3,  "starts_with"),
    (45,  "الجاثية",     "The Crouching",                 "Al-Jathiyah",     "meccan",  65,  37,   4,  "starts_with"),
    (46,  "الأحقاف",     "The Wind-Curved Sandhills",     "Al-Ahqaf",        "meccan",  66,  35,   4,  "starts_with"),
    (47,  "محمد",        "Muhammad",                      "Muhammad",        "medinan", 95,  38,   4,  "starts_with"),
    (48,  "الفتح",       "The Victory",                   "Al-Fath",         "medinan",111,  29,   4,  "starts_with"),
    (49,  "الحجرات",     "The Rooms",                     "Al-Hujurat",      "medinan",106,  18,   2,  "starts_with"),
    (50,  "ق",           "The Letter Qaf",                "Qaf",             "meccan",  34,  45,   3,  "starts_with"),
    (51,  "الذاريات",    "The Winnowing Winds",           "Adh-Dhariyat",    "meccan",  67,  60,   3,  "starts_with"),
    (52,  "الطور",       "The Mount",                     "At-Tur",          "meccan",  76,  49,   2,  "starts_with"),
    (53,  "النجم",       "The Star",                      "An-Najm",         "meccan",  23,  62,   3,  "starts_with"),
    (54,  "القمر",       "The Moon",                      "Al-Qamar",        "meccan",  37,  55,   3,  "starts_with"),
    (55,  "الرحمن",      "The Beneficent",                "Ar-Rahman",       "medinan", 97,  78,   3,  "starts_with"),
    (56,  "الواقعة",     "The Inevitable",                "Al-Waqi'ah",      "meccan",  46,  96,   3,  "starts_with"),
    (57,  "الحديد",      "The Iron",                      "Al-Hadid",        "medinan", 94,  29,   4,  "starts_with"),
    (58,  "المجادلة",    "The Pleading Woman",            "Al-Mujadila",     "medinan",105,  22,   3,  "starts_with"),
    (59,  "الحشر",       "The Exile",                     "Al-Hashr",        "medinan",101,  24,   3,  "starts_with"),
    (60,  "الممتحنة",    "She That Is to Be Examined",    "Al-Mumtahanah",   "medinan", 91,  13,   2,  "starts_with"),
    (61,  "الصف",        "The Ranks",                     "As-Saf",          "medinan",109,  14,   2,  "starts_with"),
    (62,  "الجمعة",      "The Congregation, Friday",      "Al-Jumu'ah",      "medinan",110,  11,   2,  "starts_with"),
    (63,  "المنافقون",   "The Hypocrites",                "Al-Munafiqun",    "medinan",104,  11,   2,  "starts_with"),
    (64,  "التغابن",     "The Mutual Disillusion",        "At-Taghabun",     "medinan",108,  18,   2,  "starts_with"),
    (65,  "الطلاق",      "The Divorce",                   "At-Talaq",        "medinan", 99,  12,   2,  "starts_with"),
    (66,  "التحريم",     "The Prohibition",               "At-Tahrim",       "medinan",107,  12,   2,  "starts_with"),
    (67,  "الملك",       "The Sovereignty",               "Al-Mulk",         "meccan",  77,  30,   2,  "starts_with"),
    (68,  "القلم",       "The Pen",                       "Al-Qalam",        "meccan",   2,  52,   2,  "starts_with"),
    (69,  "الحاقة",      "The Reality",                   "Al-Haqqah",       "meccan",  78,  52,   2,  "starts_with"),
    (70,  "المعارج",     "The Ascending Stairways",       "Al-Ma'arij",      "meccan",  79,  44,   2,  "starts_with"),
    (71,  "نوح",         "Noah",                          "Nuh",             "meccan",  71,  28,   2,  "starts_with"),
    (72,  "الجن",        "The Jinn",                      "Al-Jinn",         "meccan",  40,  28,   2,  "starts_with"),
    (73,  "المزمل",      "The Enshrouded One",            "Al-Muzzammil",    "meccan",   3,  20,   2,  "starts_with"),
    (74,  "المدثر",      "The Cloaked One",               "Al-Muddaththir",  "meccan",   4,  56,   2,  "starts_with"),
    (75,  "القيامة",     "The Resurrection",              "Al-Qiyamah",      "meccan",  31,  40,   2,  "starts_with"),
    (76,  "الإنسان",     "The Man",                       "Al-Insan",        "medinan", 98,  31,   2,  "starts_with"),
    (77,  "المرسلات",    "The Emissaries",                "Al-Mursalat",     "meccan",  33,  50,   2,  "starts_with"),
    (78,  "النبأ",       "The Tidings",                   "An-Naba'",        "meccan",  80,  40,   2,  "starts_with"),
    (79,  "النازعات",    "Those Who Drag Forth",          "An-Nazi'at",      "meccan",  81,  46,   2,  "starts_with"),
    (80,  "عبس",         "He Frowned",                    "'Abasa",          "meccan",  24,  42,   1,  "starts_with"),
    (81,  "التكوير",     "The Overthrowing",              "At-Takwir",       "meccan",   7,  29,   1,  "starts_with"),
    (82,  "الانفطار",    "The Cleaving",                  "Al-Infitar",      "meccan",  82,  19,   1,  "starts_with"),
    (83,  "المطففين",    "The Defrauding",                "Al-Mutaffifin",   "meccan",  86,  36,   1,  "starts_with"),
    (84,  "الانشقاق",    "The Sundering",                 "Al-Inshiqaq",     "meccan",  83,  25,   1,  "starts_with"),
    (85,  "البروج",      "The Mansions of the Stars",     "Al-Buruj",        "meccan",  27,  22,   1,  "starts_with"),
    (86,  "الطارق",      "The Nightcomer",                "At-Tariq",        "meccan",  36,  17,   1,  "starts_with"),
    (87,  "الأعلى",      "The Most High",                 "Al-A'la",         "meccan",   8,  19,   1,  "starts_with"),
    (88,  "الغاشية",     "The Overwhelming",              "Al-Ghashiyah",    "meccan",  68,  26,   1,  "starts_with"),
    (89,  "الفجر",       "The Dawn",                      "Al-Fajr",         "meccan",  10,  30,   1,  "starts_with"),
    (90,  "البلد",       "The City",                      "Al-Balad",        "meccan",  35,  20,   1,  "starts_with"),
    (91,  "الشمس",       "The Sun",                       "Ash-Shams",       "meccan",  26,  15,   1,  "starts_with"),
    (92,  "الليل",       "The Night",                     "Al-Layl",         "meccan",   9,  21,   1,  "starts_with"),
    (93,  "الضحى",       "The Morning Hours",             "Ad-Duha",         "meccan",  11,  11,   1,  "starts_with"),
    (94,  "الشرح",       "The Relief",                    "Ash-Sharh",       "meccan",  12,   8,   1,  "starts_with"),
    (95,  "التين",       "The Fig",                       "At-Tin",          "meccan",  28,   8,   1,  "starts_with"),
    (96,  "العلق",       "The Clot",                      "Al-'Alaq",        "meccan",   1,  19,   1,  "starts_with"),
    (97,  "القدر",       "The Power",                     "Al-Qadr",         "meccan",  25,   5,   1,  "starts_with"),
    (98,  "البينة",      "The Evidence",                  "Al-Bayyinah",     "medinan",100,   8,   1,  "starts_with"),
    (99,  "الزلزلة",     "The Earthquake",                "Az-Zalzalah",     "medinan", 93,   8,   1,  "starts_with"),
    (100, "العاديات",    "The Courser",                   "Al-'Adiyat",      "meccan",  14,  11,   1,  "starts_with"),
    (101, "القارعة",     "The Calamity",                  "Al-Qari'ah",      "meccan",  30,  11,   1,  "starts_with"),
    (102, "التكاثر",     "The Rivalry in World Increase", "At-Takathur",     "meccan",  16,   8,   1,  "starts_with"),
    (103, "العصر",       "The Declining Day",             "Al-'Asr",         "meccan",  13,   3,   1,  "starts_with"),
    (104, "الهمزة",      "The Traducer",                  "Al-Humazah",      "meccan",  32,   9,   1,  "starts_with"),
    (105, "الفيل",       "The Elephant",                  "Al-Fil",          "meccan",  19,   5,   1,  "starts_with"),
    (106, "قريش",        "Quraysh",                       "Quraysh",         "meccan",  29,   4,   1,  "starts_with"),
    (107, "الماعون",     "The Small Kindnesses",          "Al-Ma'un",        "meccan",  17,   7,   1,  "starts_with"),
    (108, "الكوثر",      "The Abundance",                 "Al-Kawthar",      "meccan",  15,   3,   1,  "starts_with"),
    (109, "الكافرون",    "The Disbelievers",              "Al-Kafirun",      "meccan",  18,   6,   1,  "starts_with"),
    (110, "النصر",       "The Divine Support",            "An-Nasr",         "medinan",114,   3,   1,  "starts_with"),
    (111, "المسد",       "The Palm Fiber",                "Al-Masad",        "meccan",   6,   5,   1,  "starts_with"),
    (112, "الإخلاص",     "The Sincerity",                 "Al-Ikhlas",       "meccan",  22,   4,   1,  "starts_with"),
    (113, "الفلق",       "The Daybreak",                  "Al-Falaq",        "meccan",  20,   5,   1,  "starts_with"),
    (114, "الناس",       "Mankind",                       "An-Nas",          "meccan",  21,   6,   1,  "starts_with"),
]

# ---------------------------------------------------------------------------
# Juz boundaries: (juz_number, surah, verse) — the verse where each Juz starts
# ---------------------------------------------------------------------------

JUZ_STARTS = [
    (1,  1,   1), (2,  2, 142), (3,  2, 253), (4,  3,  93), (5,  4,  24),
    (6,  4, 148), (7,  5,  82), (8,  6, 111), (9,  7,  88), (10, 8,  41),
    (11, 9,  93), (12, 11,  6), (13, 12,  53), (14, 15,   1), (15, 17,   1),
    (16, 18,  75), (17, 21,   1), (18, 23,   1), (19, 25,  21), (20, 27,  56),
    (21, 29,  46), (22, 33,  31), (23, 36,  28), (24, 39,  32), (25, 41,  47),
    (26, 46,   1), (27, 51,  31), (28, 58,   1), (29, 67,   1), (30, 78,   1),
]

# Hizb quarters — each Juz is divided into 2 hizb; each hizb into 4 quarters
# (hizb_number, surah, verse)
HIZB_STARTS = [
    (1,  1,  1), (2,  2,  75), (3,  2, 142), (4,  2, 202),
    (5,  2, 253), (6,  3,  14), (7,  3,  93), (8,  3, 152),
    (9,  4,  24), (10, 4,  88), (11, 4, 148), (12, 5,   1),
    (13, 5,  82), (14, 6,   1), (15, 6, 111), (16, 7,   1),
    (17, 7,  88), (18, 7, 171), (19, 8,  41), (20, 9,   1),
    (21, 9,  93), (22, 10,   1), (23, 11,   6), (24, 11,  97),
    (25, 12,  53), (26, 13,   1), (27, 15,   1), (28, 16,  51),
    (29, 17,   1), (30, 18,   1), (31, 18,  75), (32, 19,  59),
    (33, 21,   1), (34, 22,   1), (35, 23,   1), (36, 24,  21),
    (37, 25,  21), (38, 26,   1), (39, 27,  56), (40, 28,  51),
    (41, 29,  46), (42, 31,  22), (43, 33,  31), (44, 34,  24),
    (45, 36,  28), (46, 37, 145), (47, 39,  32), (48, 40,  41),
    (49, 41,  47), (50, 43,  24), (51, 46,   1), (52, 48,  18),
    (53, 51,  31), (54, 54,  53), (55, 58,   1), (56, 61,   1),
    (57, 67,   1), (58, 72,   1), (59, 78,   1), (60, 87,   1),
]

# Manzil boundaries: (manzil_number, start_surah, start_verse, end_surah, end_verse)
MANZIL_RANGES = [
    (1,  1,   1,   4, 176),
    (2,  5,   1,   9, 129),
    (3, 10,   1,  16, 128),
    (4, 17,   1,  25,  77),
    (5, 26,   1,  36,  83),
    (6, 37,   1,  49,  18),
    (7, 50,   1, 114,   6),
]

# Sajdah verses (prostration marks): set of (surah, verse)
SAJDAH_VERSES = {
    (7,  206): "obligatory",
    (13,  15): "obligatory",
    (16,  50): "obligatory",
    (17, 109): "obligatory",
    (19,  58): "obligatory",
    (22,  18): "obligatory",
    (22,  77): "recommended",
    (25,  60): "obligatory",
    (27,  26): "obligatory",
    (32,  15): "obligatory",
    (38,  24): "recommended",
    (41,  38): "obligatory",
    (53,  62): "obligatory",
    (84,  21): "obligatory",
    (96,  19): "obligatory",
}

# ---------------------------------------------------------------------------
# Abjad values
# ---------------------------------------------------------------------------

# Mashriqi (Eastern) system — most commonly used
ABJAD_MASHRIQI: dict[str, int] = {
    "ا": 1,  "أ": 1,  "إ": 1,  "آ": 1,  "ٱ": 1,  "ء": 1,
    "ب": 2,
    "ج": 3,
    "د": 4,
    "ه": 5,  "ة": 5,
    "و": 6,  "ؤ": 6,
    "ز": 7,
    "ح": 8,
    "ط": 9,
    "ي": 10, "ى": 10, "ئ": 10,
    "ك": 20,
    "ل": 30,
    "م": 40,
    "ن": 50,
    "س": 60,
    "ع": 70,
    "ف": 80,
    "ص": 90,
    "ق": 100,
    "ر": 200,
    "ش": 300,
    "ت": 400,
    "ث": 500,
    "خ": 600,
    "ذ": 700,
    "ض": 800,
    "ظ": 900,
    "غ": 1000,
}

# Maghribi (Western) system — used in North Africa
ABJAD_MAGHRIBI: dict[str, int] = {
    **ABJAD_MASHRIQI,
    "ص": 60,
    "ض": 90,
    "ش": 1000,
    "ظ": 800,
    "غ": 900,
}

# Arabic letter codepoints for letter counting (base letters only)
ARABIC_LETTERS = frozenset(
    "\u0621\u0622\u0623\u0624\u0625\u0626\u0627\u0628\u0629\u062A"
    "\u062B\u062C\u062D\u062E\u062F\u0630\u0631\u0632\u0633\u0634"
    "\u0635\u0636\u0637\u0638\u0639\u063A\u0641\u0642\u0643\u0644"
    "\u0645\u0646\u0647\u0648\u0649\u064A"
    "\u0671"  # Alif Wasla ٱ
)

# Diacritics (tashkeel) and other non-letter marks to strip for normalization
TASHKEEL = frozenset(
    "\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0653\u0654"
    "\u0655\u0656\u0657\u0658\u065C\u065D\u065E\u065F\u0670"
    "\u06D6\u06D7\u06D8\u06D9\u06DA\u06DB\u06DC\u06DF\u06E0"
    "\u06E1\u06E2\u06E3\u06E4\u06E5\u06E6\u06E7\u06E8\u06E9"
    "\u06EA\u06EB\u06EC\u06ED\u06EF"
)

# Alif variants to normalize
ALIF_NORMALIZE = str.maketrans(
    "\u0622\u0623\u0625\u0671",  # آ أ إ ٱ → ا
    "\u0627\u0627\u0627\u0627",
)


# ---------------------------------------------------------------------------
# Text processing helpers
# ---------------------------------------------------------------------------

def strip_tashkeel(text: str) -> str:
    """Remove all diacritical marks from Arabic text."""
    return "".join(ch for ch in text if ch not in TASHKEEL)


def normalize_text(text: str) -> str:
    """
    Full normalization: strip tashkeel + normalize alif variants.
    Used for text_normalized_full column.
    """
    stripped = strip_tashkeel(text)
    return stripped.translate(ALIF_NORMALIZE)


def count_letters(text: str) -> int:
    """Count Arabic base letters (traditional method, counts Alif Wasla)."""
    return sum(1 for ch in text if ch in ARABIC_LETTERS)


def count_words(text: str) -> int:
    """Count words separated by whitespace."""
    return len(text.split())


def calc_abjad(text: str, system: dict[str, int]) -> int:
    """Calculate Abjad (gematria) value for Arabic text."""
    stripped = strip_tashkeel(text)
    return sum(system.get(ch, 0) for ch in stripped)


def sha256_checksum(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Juz / Hizb / Manzil lookup builders
# ---------------------------------------------------------------------------

def _build_verse_juz_map(surah_verse_counts: dict[int, int]) -> dict[tuple[int, int], int]:
    """For each (surah, verse), compute which Juz it belongs to."""
    # Flatten JUZ_STARTS to a sorted sequence for comparison
    boundaries = sorted(JUZ_STARTS, key=lambda x: (x[1], x[2]))

    mapping: dict[tuple[int, int], int] = {}
    for surah_num, verse_count in surah_verse_counts.items():
        for verse_num in range(1, verse_count + 1):
            juz = 1
            for (j, s, v) in boundaries:
                if (surah_num, verse_num) >= (s, v):
                    juz = j
            mapping[(surah_num, verse_num)] = juz
    return mapping


def _build_verse_hizb_map(surah_verse_counts: dict[int, int]) -> dict[tuple[int, int], int]:
    """For each (surah, verse), compute which Hizb it belongs to."""
    boundaries = sorted(HIZB_STARTS, key=lambda x: (x[1], x[2]))

    mapping: dict[tuple[int, int], int] = {}
    for surah_num, verse_count in surah_verse_counts.items():
        for verse_num in range(1, verse_count + 1):
            hizb = 1
            for (h, s, v) in boundaries:
                if (surah_num, verse_num) >= (s, v):
                    hizb = h
            mapping[(surah_num, verse_num)] = hizb
    return mapping


def _build_verse_manzil_map(surah_verse_counts: dict[int, int]) -> dict[tuple[int, int], int]:
    """For each (surah, verse), compute which Manzil it belongs to."""
    mapping: dict[tuple[int, int], int] = {}
    for surah_num, verse_count in surah_verse_counts.items():
        for verse_num in range(1, verse_count + 1):
            manzil = 1
            for (m, s_start, v_start, s_end, v_end) in MANZIL_RANGES:
                if (surah_num, verse_num) >= (s_start, v_start):
                    manzil = m
            mapping[(surah_num, verse_num)] = manzil
    return mapping


# ---------------------------------------------------------------------------
# Tanzil XML parsing
# ---------------------------------------------------------------------------

def _fetch_url(url: str, timeout: int = 30) -> bytes:
    """Download URL content with a User-Agent header."""
    req = Request(url, headers={"User-Agent": "Mizan-Ingest/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_tanzil_xml(source: str | bytes | Path) -> dict[int, dict[int, str]]:
    """
    Parse Tanzil XML and return {surah_num: {verse_num: text}}.

    Supports both the <quran><sura index="N"><aya index="N" text="..."/> format
    and the <quran><sura number="N"><verse number="N">...</verse> format.
    """
    if isinstance(source, Path):
        tree = ET.parse(source)
        root = tree.getroot()
    elif isinstance(source, bytes):
        root = ET.fromstring(source)
    else:
        root = ET.fromstring(source)

    result: dict[int, dict[int, str]] = {}

    for sura_el in root:
        tag = sura_el.tag.lower()
        if tag not in ("sura", "surah", "chapter"):
            continue

        s_num = int(sura_el.get("index") or sura_el.get("number") or sura_el.get("id", 0))
        if s_num < 1 or s_num > 114:
            continue

        result[s_num] = {}
        for aya_el in sura_el:
            a_tag = aya_el.tag.lower()
            if a_tag not in ("aya", "ayah", "ayat", "verse"):
                continue

            a_num = int(aya_el.get("index") or aya_el.get("number") or aya_el.get("id", 0))
            # text can be an attribute or element content
            text = aya_el.get("text") or (aya_el.text or "").strip()
            result[s_num][a_num] = text

    return result


# ---------------------------------------------------------------------------
# Database ingestion
# ---------------------------------------------------------------------------

def ingest(
    uthmani_data: dict[int, dict[int, str]],
    simple_data: dict[int, dict[int, str]] | None,
    db_url: str,
    dry_run: bool = False,
) -> None:
    engine = create_engine(db_url, echo=False)

    surah_verse_counts = {s[0]: s[6] for s in SURAHS}

    print("Building metadata lookup tables…")
    juz_map = _build_verse_juz_map(surah_verse_counts)
    hizb_map = _build_verse_hizb_map(surah_verse_counts)
    manzil_map = _build_verse_manzil_map(surah_verse_counts)

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    with engine.begin() as conn:
        # ---- Surahs -------------------------------------------------------
        print("Inserting surahs…")
        for row in SURAHS:
            (num, name_ar, name_en, translit, rev_type, rev_order,
             verse_count, ruku_count, basmalah) = row

            # Compute checksum from surah metadata
            checksum_src = f"{num}|{name_ar}|{verse_count}"
            checksum = sha256_checksum(checksum_src)

            conn.execute(text("""
                INSERT INTO surahs
                    (id, name_arabic, name_english, name_transliteration,
                     revelation_type, revelation_order, basmalah_status,
                     verse_count, ruku_count, word_count, letter_count,
                     abjad_value, checksum, created_at, updated_at)
                VALUES
                    (:id, :name_ar, :name_en, :translit,
                     :rev_type, :rev_order, :basmalah,
                     :verse_count, :ruku_count, 0, 0, 0,
                     :checksum, :now, :now)
                ON CONFLICT (id) DO UPDATE SET
                    name_arabic          = EXCLUDED.name_arabic,
                    name_english         = EXCLUDED.name_english,
                    name_transliteration = EXCLUDED.name_transliteration,
                    revelation_type      = EXCLUDED.revelation_type,
                    revelation_order     = EXCLUDED.revelation_order,
                    basmalah_status      = EXCLUDED.basmalah_status,
                    verse_count          = EXCLUDED.verse_count,
                    ruku_count           = EXCLUDED.ruku_count,
                    checksum             = EXCLUDED.checksum,
                    updated_at           = EXCLUDED.updated_at
            """), {
                "id": num, "name_ar": name_ar, "name_en": name_en,
                "translit": translit, "rev_type": rev_type, "rev_order": rev_order,
                "basmalah": basmalah, "verse_count": verse_count,
                "ruku_count": ruku_count, "checksum": checksum, "now": now,
            })

        # ---- Verses -------------------------------------------------------
        total_inserted = 0
        total_surahs = len(SURAHS)

        for surah_row in SURAHS:
            s_num = surah_row[0]
            verse_count = surah_row[6]
            ruku_count = surah_row[7]

            surah_verses = uthmani_data.get(s_num, {})
            if not surah_verses:
                print(f"  ⚠  Surah {s_num}: no Uthmani text found in XML, skipping")
                continue

            batch_letters = 0
            batch_words = 0
            batch_abjad = 0

            for v_num in range(1, verse_count + 1):
                text_uthmani = surah_verses.get(v_num, "")
                if not text_uthmani:
                    print(f"  ⚠  {s_num}:{v_num} missing from Uthmani XML")
                    continue

                text_simple = (simple_data or {}).get(s_num, {}).get(v_num)
                text_norm = normalize_text(text_uthmani)
                text_no_tash = strip_tashkeel(text_uthmani)

                letters = count_letters(text_norm)
                words = count_words(text_no_tash)
                abjad_m = calc_abjad(text_uthmani, ABJAD_MASHRIQI)
                abjad_g = calc_abjad(text_uthmani, ABJAD_MAGHRIBI)

                batch_letters += letters
                batch_words += words
                batch_abjad += abjad_m

                juz = juz_map.get((s_num, v_num), 1)
                hizb = hizb_map.get((s_num, v_num), 1)
                manzil = manzil_map.get((s_num, v_num), 1)

                # Approximate page number (Madani Mushaf ~15 lines, ~604 pages)
                # Rough calculation: total verses before this verse / 10 (≈10 verses/page avg)
                page_approx = max(1, (sum(r[6] for r in SURAHS[:s_num-1]) + v_num) // 10)
                page_num = min(page_approx, 604)

                # Ruku within surah: approximate based on verse position
                ruku_per_verse = max(1, verse_count // max(ruku_count, 1))
                ruku_num = min(ruku_count, (v_num - 1) // ruku_per_verse + 1)

                is_sajdah = (s_num, v_num) in SAJDAH_VERSES
                sajdah_type = SAJDAH_VERSES.get((s_num, v_num))

                checksum = sha256_checksum(text_uthmani)
                verse_id = uuid.uuid5(
                    uuid.NAMESPACE_DNS,
                    f"mizan.quran.{s_num}.{v_num}"
                )

                conn.execute(text("""
                    INSERT INTO verses
                        (id, surah_number, verse_number,
                         text_uthmani, text_uthmani_min, text_simple,
                         text_normalized_full, text_no_tashkeel,
                         juz_number, hizb_number, ruku_number,
                         manzil_number, page_number,
                         is_sajdah, sajdah_type,
                         word_count, letter_count,
                         abjad_value_mashriqi, abjad_value_maghribi,
                         checksum, created_at)
                    VALUES
                        (:id, :surah, :verse,
                         :text_uth, :text_uth_min, :text_simple,
                         :text_norm, :text_no_tash,
                         :juz, :hizb, :ruku,
                         :manzil, :page,
                         :is_sajdah, :sajdah_type,
                         :words, :letters,
                         :abjad_m, :abjad_g,
                         :checksum, :now)
                    ON CONFLICT (surah_number, verse_number) DO UPDATE SET
                        text_uthmani         = EXCLUDED.text_uthmani,
                        text_uthmani_min     = EXCLUDED.text_uthmani_min,
                        text_simple          = EXCLUDED.text_simple,
                        text_normalized_full = EXCLUDED.text_normalized_full,
                        text_no_tashkeel     = EXCLUDED.text_no_tashkeel,
                        juz_number           = EXCLUDED.juz_number,
                        hizb_number          = EXCLUDED.hizb_number,
                        ruku_number          = EXCLUDED.ruku_number,
                        manzil_number        = EXCLUDED.manzil_number,
                        page_number          = EXCLUDED.page_number,
                        is_sajdah            = EXCLUDED.is_sajdah,
                        sajdah_type          = EXCLUDED.sajdah_type,
                        word_count           = EXCLUDED.word_count,
                        letter_count         = EXCLUDED.letter_count,
                        abjad_value_mashriqi = EXCLUDED.abjad_value_mashriqi,
                        abjad_value_maghribi = EXCLUDED.abjad_value_maghribi,
                        checksum             = EXCLUDED.checksum
                """), {
                    "id": str(verse_id),
                    "surah": s_num, "verse": v_num,
                    "text_uth": text_uthmani,
                    "text_uth_min": text_uthmani,  # same source for now
                    "text_simple": text_simple,
                    "text_norm": text_norm,
                    "text_no_tash": text_no_tash,
                    "juz": juz, "hizb": hizb, "ruku": ruku_num,
                    "manzil": manzil, "page": page_num,
                    "is_sajdah": is_sajdah,
                    "sajdah_type": sajdah_type,
                    "words": words, "letters": letters,
                    "abjad_m": abjad_m, "abjad_g": abjad_g,
                    "checksum": checksum, "now": now,
                })
                total_inserted += 1

            # Update surah-level aggregates
            conn.execute(text("""
                UPDATE surahs SET
                    word_count   = (SELECT SUM(word_count)   FROM verses WHERE surah_number = :s),
                    letter_count = (SELECT SUM(letter_count) FROM verses WHERE surah_number = :s),
                    abjad_value  = (SELECT SUM(abjad_value_mashriqi) FROM verses WHERE surah_number = :s),
                    updated_at   = :now
                WHERE id = :s
            """), {"s": s_num, "now": now})

            print(f"  ✓  Surah {s_num:3d}/{total_surahs} — {total_inserted} verses inserted")

        print(f"\nDone. Total verses inserted: {total_inserted}")

        if dry_run:
            raise Exception("DRY RUN — rolling back")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Tanzil Quran data into Mizan database")
    parser.add_argument(
        "--uthmani", metavar="FILE",
        help="Path to Tanzil Uthmani XML file (default: download from tanzil.net)"
    )
    parser.add_argument(
        "--simple", metavar="FILE",
        help="Path to Tanzil Simple XML file (optional)"
    )
    parser.add_argument(
        "--db-url", default=None,
        help=f"PostgreSQL URL (default: $DATABASE_URL or {DEFAULT_DB_URL})"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Parse and process data but rollback the transaction"
    )
    args = parser.parse_args()

    import os
    db_url = args.db_url or os.environ.get("DATABASE_URL", DEFAULT_DB_URL)

    # ---- Load Uthmani XML ------------------------------------------------
    if args.uthmani:
        print(f"Loading Uthmani XML from: {args.uthmani}")
        uthmani_raw = Path(args.uthmani).read_bytes()
    else:
        print(f"Downloading Uthmani XML from tanzil.net…")
        try:
            uthmani_raw = _fetch_url(TANZIL_UTHMANI_URL)
            print(f"  Downloaded {len(uthmani_raw):,} bytes")
        except Exception as exc:
            print(f"ERROR: Could not download Uthmani XML: {exc}")
            print("Hint: download manually and pass --uthmani <file>")
            sys.exit(1)

    print("Parsing Uthmani XML…")
    uthmani_data = parse_tanzil_xml(uthmani_raw)
    total_verses = sum(len(v) for v in uthmani_data.values())
    print(f"  Parsed {len(uthmani_data)} surahs, {total_verses} verses")

    # ---- Load Simple XML (optional) --------------------------------------
    simple_data: dict[int, dict[int, str]] | None = None
    if args.simple:
        print(f"Loading Simple XML from: {args.simple}")
        simple_raw = Path(args.simple).read_bytes()
        simple_data = parse_tanzil_xml(simple_raw)
    else:
        try:
            print("Downloading Simple XML from tanzil.net…")
            simple_raw = _fetch_url(TANZIL_SIMPLE_URL)
            simple_data = parse_tanzil_xml(simple_raw)
            print(f"  Downloaded and parsed Simple XML")
        except Exception:
            print("  (Simple XML unavailable — text_simple will be NULL)")

    # ---- Ingest ----------------------------------------------------------
    print(f"\nConnecting to database: {db_url[:40]}…")
    try:
        ingest(uthmani_data, simple_data, db_url, dry_run=args.dry_run)
    except Exception as exc:
        if args.dry_run and "DRY RUN" in str(exc):
            print("\nDry run complete — no data written.")
        else:
            print(f"\nERROR during ingestion: {exc}")
            raise


if __name__ == "__main__":
    main()
