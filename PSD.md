# Technical Design Specification: Mizan Core Engine (MCE)

**Project Name:** Mizan Core Engine (MCE)
**Version:** 2.2.0
**Date:** 2025-12-16
**Status:** Approved for Implementation
**Architectural Pattern:** Hexagonal Architecture (Ports and Adapters) / Domain-Driven Design (DDD) / CQRS
**Language:** Python 3.11+

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architectural Principles](#2-architectural-principles)
3. [Quranic Text Handling Requirements](#3-quranic-text-handling-requirements)
4. [Tech Stack & Dependencies](#4-tech-stack--dependencies)
5. [Domain Layer Design](#5-domain-layer-design)
6. [Analysis Engine](#6-analysis-engine)
7. [Service Layer](#7-service-layer)
8. [Data Ingestion & Integrity](#8-data-ingestion--integrity)
9. [Infrastructure Layer](#9-infrastructure-layer)
10. [API Design](#10-api-design)
11. [Error Handling & Domain Exceptions](#11-error-handling--domain-exceptions)
12. [Caching Strategy](#12-caching-strategy)
13. [Audit & Observability](#13-audit--observability)
14. [Scholarly References & Methodology](#14-scholarly-references--methodology)
15. [Implementation Phases](#15-implementation-phases)
16. [Implementation Readiness Checklist](#16-implementation-readiness-checklist)

**Appendices:**
- [Appendix A: Project Structure](#appendix-a-project-structure)
- [Appendix B: Abjad Value Mappings](#appendix-b-abjad-value-mappings)
- [Appendix C: Project Configuration Files](#appendix-c-project-configuration-files)
- [Appendix D: External Data Sources & Schemas](#appendix-d-external-data-sources--schemas)
- [Appendix E: Structural Division Tables](#appendix-e-structural-division-tables)
- [Appendix F: Missing Enum Definitions](#appendix-f-missing-enum-definitions)
- [Appendix G: Entity Variant Matching Algorithm](#appendix-g-entity-variant-matching-algorithm)
- [Appendix H: ArabicNormalizer Implementation](#appendix-h-arabicnormalizer-implementation)
- [Appendix I: Golden Test Datasets](#appendix-i-golden-test-datasets)
- [Appendix J: Configuration Reference](#appendix-j-configuration-reference)

---

## 1. Executive Summary

The **Mizan Core Engine (MCE)** is a high-precision, mission-critical backend system designed for the quantitative, philological, and cryptographic analysis of the Holy Quran.

Named after the Quranic concept of "Balance" (Al-Mizan - الميزان), this system prioritizes **measurement accuracy** above all else. The name reflects both the technical purpose (measuring, counting, weighing letters and words) and the spiritual imperative (maintaining the sacred balance of the Divine text without error or alteration).

### 1.1. Core Objectives

- **Zero-Error Tolerance:** Any counting or calculation error is unacceptable
- **Multi-Script Support:** Handle Uthmani, Imla'i, and simplified scripts
- **Qira'at Awareness:** Support canonical readings (Hafs, Warsh, Qalun, etc.)
- **Scholarly Rigor:** Every methodology decision must cite Islamic scholarly sources
- **Reproducibility:** Every analysis must be fully reproducible with audit trails
- **Immutability:** The Quranic text must never be modified during runtime

### 1.2. Scope Boundaries

**In Scope:**
- Letter, word, and verse counting
- Abjad/Gematria calculations
- Pattern detection (frequency analysis, prime numbers, modular arithmetic)
- Morphological root extraction
- Cross-reference analysis between Surahs

**Out of Scope:**
- Tafsir (interpretation) content
- Audio/Tajweed analysis
- Translation management
- Making theological claims based on numerical analysis

---

## 2. Architectural Principles

### 2.1. Core Principles

1. **Immutability First:** The Quranic text data is treated as "Write-Once, Read-Many." Once ingested and verified via checksums, the core text entities must never be mutated during runtime to preserve the "Mizan" (Balance).

2. **Hexagonal Architecture:** The core domain logic (counting, calculating, rooting) must have zero dependencies on frameworks (FastAPI), databases (Postgres), or external APIs. The domain is the center; everything else is an adapter.

3. **CQRS (Command Query Responsibility Segregation):** Given the read-heavy, immutable nature of Quranic data, separate read models (optimized for queries) from write models (ingestion only).

4. **Strict Typing:** Python Type Hints (`typing` module) must be used throughout. `mypy --strict` compliance is mandatory.

5. **Property-Based Testing:** Standard unit tests are insufficient. We utilize **Hypothesis** to prove mathematical invariants.

6. **Auditability:** Every analysis run generates a cryptographically signed "Receipt" (Audit Log) detailing exactly which script, normalization rules, and counting parameters were used.

7. **Fail-Fast on Integrity Violation:** If any data integrity check fails, the system must halt immediately rather than produce potentially incorrect results.

### 2.2. Layer Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│                 (FastAPI, CLI, WebSocket)                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│           (Use Cases, DTOs, Application Services)            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                            │
│    (Entities, Value Objects, Domain Services, Interfaces)    │
│                   *** NO DEPENDENCIES ***                    │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                       │
│        (PostgreSQL, Redis, External APIs, File System)       │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Quranic Text Handling Requirements

This section defines the Islamic scholarly requirements that **must** be adhered to in the system design.

### 3.1. Mushaf Edition & Provenance

The system must track the exact source of Quranic text with full provenance:

```python
class MushafEdition(StrEnum):
    """Authorized Mushaf editions with scholarly recognition."""
    MADINAH_HAFS = "madinah_hafs"           # King Fahd Complex, Madinah
    MADINAH_WARSH = "madinah_warsh"         # King Fahd Complex, Warsh
    EGYPTIAN_STANDARD = "egyptian_standard"  # Al-Azhar 1924 Edition
    INDO_PAK = "indo_pak"                   # Indo-Pakistani script
    TANZIL_UTHMANI = "tanzil_uthmani"       # Tanzil.net Uthmani
    TANZIL_SIMPLE = "tanzil_simple"         # Tanzil.net Simple
```

**Primary Source:** King Fahd Quran Complex, Madinah (مجمع الملك فهد لطباعة المصحف الشريف)
- This is the most widely authenticated and distributed Mushaf globally
- Verified by committees of senior Ulama

### 3.2. Qira'at (Canonical Readings) Support

The Quran has been transmitted through multiple authentic chains of recitation (Qira'at). These affect letter counts and must be handled distinctly:

```python
class QiraatType(StrEnum):
    """The ten canonical Qira'at and their primary Rawis."""
    # Most common
    HAFS_AN_ASIM = "hafs_an_asim"           # حفص عن عاصم (Most widespread)
    WARSH_AN_NAFI = "warsh_an_nafi"         # ورش عن نافع (North/West Africa)
    QALUN_AN_NAFI = "qalun_an_nafi"         # قالون عن نافع (Libya, Tunisia)

    # Other authenticated Qira'at
    AL_DURI_AN_ABU_AMR = "duri_abu_amr"     # الدوري عن أبي عمرو
    AL_SUSI_AN_ABU_AMR = "susi_abu_amr"     # السوسي عن أبي عمرو
    IBN_KATHIR = "ibn_kathir"               # ابن كثير
    IBN_AMIR = "ibn_amir"                   # ابن عامر
    ASIM = "asim"                           # عاصم
    HAMZA = "hamza"                         # حمزة
    AL_KISAI = "kisai"                      # الكسائي
    KHALAF = "khalaf"                       # خلف العاشر
```

**Example Difference:**
- Al-Fatiha 1:4 (مَالِكِ vs مَلِكِ):
  - Hafs: "Maaliki" (مَالِكِ) - with Alif = 5 letters
  - Warsh: "Maliki" (مَلِكِ) - without Alif = 4 letters

### 3.3. Basmalah Handling (Critical)

The Basmalah (بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ) requires careful handling as its status varies:

```python
class BasmalahStatus(StrEnum):
    """Classification of Basmalah status per Surah."""
    NUMBERED_VERSE = "numbered_verse"       # Counted as verse 1 (Al-Fatiha only)
    OPENING_UNNUMBERED = "opening_unnumbered"  # Present but not a verse (111 Surahs)
    ABSENT = "absent"                       # Not present (At-Tawbah/Surah 9)
    WITHIN_VERSE = "within_verse"           # Part of verse text (An-Naml 27:30)
```

**Per-Surah Basmalah Configuration:**

| Surah | Basmalah Status | Notes |
|-------|-----------------|-------|
| 1 (Al-Fatiha) | `NUMBERED_VERSE` | Counted as Ayah 1 by consensus |
| 2-8, 10-26, 28-114 | `OPENING_UNNUMBERED` | Present but not counted as a verse |
| 9 (At-Tawbah) | `ABSENT` | No Basmalah by Ijma' (consensus) |
| 27 (An-Naml) | `OPENING_UNNUMBERED` + `WITHIN_VERSE` at 27:30 | Contains Basmalah within verse 30 |

### 3.4. Script Types and Character Handling

The system supports three primary script types from Tanzil.net (Version 1.1, February 2021):

```python
class ScriptType(StrEnum):
    """Quranic script variations from Tanzil.net."""
    UTHMANI = "uthmani"              # الرسم العثماني - Original Uthmani orthography
    UTHMANI_MINIMAL = "uthmani_min"  # Uthmani with simplified diacritics
    SIMPLE = "simple"                # الرسم الإملائي - Modern standard spelling
```

**Critical Differences Between Script Types:**

| Feature | Uthmani | Uthmani-min | Simple |
|---------|---------|-------------|--------|
| **Alif Wasla** | `ٱللَّهِ` (U+0671) | `اللَّهِ` (U+0627) | `اللَّهِ` (U+0627) |
| **Huruf Muqatta'at** | `الٓمٓ` (with maddah) | `الم` | `الم` |
| **Small Letters** (ۦ ۧ ۨ) | Present | Partial | Absent |
| **Tanween Placement** | Precise (ًۭ) | Simplified | Standard |
| **Silent Markers** | `حَوْلَهُۥ` | Simplified | Absent |

**Alif Wasla (ٱ) - Critical for Letter Counting:**

The Uthmani script uses **Alif Wasla** (همزة الوصل - U+0671) instead of regular Alif (U+0627) for the definite article:
- Uthmani: `بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ`
- Simple: `بِسْمِ اللَّهِ الرَّحْمَـٰنِ الرَّحِيمِ`

**Decision:** Alif Wasla (ٱ) is counted as a letter equivalent to Alif (ا) for counting purposes, but preserved distinctly for orthographic analysis.

### 3.5. Special Characters Handling

| Character Type | Arabic Name | Unicode | Example | Counting Rule |
|----------------|-------------|---------|---------|---------------|
| Base Letters | الحروف الأصلية | U+0621-U+064A | ا ب ت | Always counted |
| **Alif Wasla** | همزة الوصل | **U+0671** | ٱ | **Counted as Alif** (Uthmani only) |
| Alif Khanjariyya | ألف خنجرية | U+0670 | ـٰ | **Counted as Alif** |
| Tashkeel (Diacritics) | التشكيل | U+064B-U+0652 | ً ٌ ٍ | Configurable (default: ignore) |
| Maddah | المدة | U+0653 | ٓ | Not a separate letter |
| Hamza Above/Below | همزة | U+0654-U+0655 | ٔ ٕ | Combined with carrier |
| Sukun | السكون | U+0652 | ْ | Not counted |
| Shadda | الشدة | U+0651 | ّ | Letter counted once (disputed) |
| Small High Letters | حروف صغيرة | U+06E1-U+06E9 | ۦ ۧ ۨ | Not counted (Uthmani only) |
| Pause Marks | علامات الوقف | Various | ۖ ۗ ۘ ۙ ۚ ۛ | Never counted |
| Sajda Sign | علامة السجدة | U+06E9 | ۩ | Never counted |
| Rub' al-Hizb | ربع الحزب | U+06DE | ۞ | Never counted |
| Tatweel | التطويل | U+0640 | ـ | Never counted |
| End of Ayah | علامة الآية | U+06DD | ۝ | Never counted |

### 3.6. Disputed Counting Matters

The system must document which scholarly opinion it follows:

| Matter | Scholarly Positions | MCE Default | Source |
|--------|--------------------| ------------|--------|
| Shadda Letters | Count as 1 letter (majority) vs 2 letters | 1 letter | Ibn al-Jazari |
| Alif Khanjariyya | Count as letter (majority) vs ignore | Count | Uthmani Rasm tradition |
| Basmalah in counts | Include (Kufan) vs Exclude (Basran) | Configurable | Both positions valid |
| Hamza on carrier | Count carrier or not | Count Hamza only | Modern consensus |

---

## 4. Tech Stack & Dependencies

### 4.1. Core Infrastructure

| Category | Technology | Version | Justification |
|----------|------------|---------|---------------|
| **Core Language** | Python | 3.11+ | Pattern matching, performance, typing |
| **Web Framework** | FastAPI | ≥0.109.0 | High performance, automatic OpenAPI docs |
| **Data Validation** | Pydantic | ≥2.5.0 | Runtime type checking, serialization |
| **Database** | PostgreSQL | 15+ | JSONB support, full-text search, reliability |
| **ORM** | SQLAlchemy | ≥2.0.25 | Type-safe async queries |
| **Caching** | Redis | 7+ | Analysis result caching, rate limiting |
| **Migrations** | Alembic | ≥1.13.0 | Database schema versioning |
| **Containerization** | Docker | Latest | Reproducible deployments |

### 4.2. Arabic NLP & Text Processing (Tier 1-2)

| Library | Version | Purpose | License |
|---------|---------|---------|---------|
| **PyArabic** | ≥0.6.15 | Text normalization, tashkeel removal, hamza unification | MIT |
| **regex** | ≥2023.0 | Advanced Unicode regex for Arabic patterns | Apache 2.0 |

### 4.3. Morphological Data Sources (Tier 3)

| Source | Version | Purpose | License |
|--------|---------|---------|---------|
| **MASAQ Dataset** | 2.0 | Pre-computed morphology (131K entries) | CC BY 4.0 |
| **Quranic Arabic Corpus** | 0.4 | Validation, treebank | GNU GPL |
| **Tanzil.net** | 1.1 | Primary Quran text | Free (with attribution) |

**Note:** We use **pre-annotated scholarly data** for morphology rather than runtime analysis libraries. This ensures:
- 99% accuracy (human-verified)
- Classical Arabic correctness (not MSA assumptions)
- Reproducibility across runs
- No external API dependencies

### 4.4. Machine Learning & Embeddings (Tier 4)

| Library | Version | Purpose | License |
|---------|---------|---------|---------|
| **transformers** | ≥4.36.0 | AraBERT model loading | Apache 2.0 |
| **torch** | ≥2.1.0 | ML backend | BSD |
| **sentence-transformers** | ≥2.2.0 | Sentence embeddings | Apache 2.0 |

**Pre-trained Models Used:**
- `aubmindlab/bert-base-arabertv2` - Arabic BERT for embeddings
- `Omartificial-Intelligence-Space/Arabic-all-nli-triplet-Matryoshka` - Sentence similarity

### 4.5. Graph & Statistical Analysis (Tier 4-5)

| Library | Version | Purpose | License |
|---------|---------|---------|---------|
| **NetworkX** | ≥3.2.0 | Co-occurrence networks, graph algorithms | BSD |
| **NumPy** | ≥1.26.0 | Numerical operations | BSD |
| **SciPy** | ≥1.11.0 | Statistical functions, sparse matrices | BSD |
| **gensim** | ≥4.3.0 | Topic modeling (LDA) | LGPL |

### 4.6. Testing & Quality

| Library | Version | Purpose |
|---------|---------|---------|
| **pytest** | ≥7.4.0 | Test framework |
| **pytest-asyncio** | ≥0.23.0 | Async test support |
| **hypothesis** | ≥6.92.0 | Property-based testing |
| **mypy** | ≥1.8.0 | Static type checking (strict mode) |
| **ruff** | ≥0.1.9 | Linting and formatting |

### 4.7. Analysis Tier Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ANALYSIS TIERS                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  TIER 1: Core Analysis          TIER 2: Entity Search                   │
│  ├── Letter counting            ├── Divine Names (99)                   │
│  ├── Word counting              ├── Prophet names (25)                  │
│  ├── Abjad calculation          ├── Angel names                         │
│  ├── Normalization              ├── Places & Peoples                    │
│  └── Dependencies: PyArabic     └── Dependencies: Reference Data        │
│                                                                          │
│  TIER 3: Morphological          TIER 4: Semantic Analysis               │
│  ├── Root extraction            ├── Word embeddings                     │
│  ├── POS tagging                ├── Verse similarity                    │
│  ├── Lemmatization              ├── Co-occurrence networks              │
│  ├── Pattern (وزن) lookup       ├── Topic modeling                      │
│  └── Dependencies: MASAQ/QAC    └── Dependencies: AraBERT, NetworkX     │
│                                                                          │
│  TIER 5: Structural Analysis    TIER 6: Numerical (Transparent)         │
│  ├── Similarity matrices        ├── Configurable methodology            │
│  ├── Repeated phrase detection  ├── Full audit trail                    │
│  ├── Verse ending patterns      ├── Every match logged                  │
│  ├── Symmetry scoring           ├── Reproducible results                │
│  └── Dependencies: NumPy        └── Dependencies: None (pure logic)     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Domain Layer Design

This layer contains pure business logic with **zero external dependencies**.

### 5.1. Value Objects

```python
from dataclasses import dataclass
from typing import Final

@dataclass(frozen=True, slots=True)
class VerseLocation:
    """Immutable identifier for a verse's position in the Mushaf."""
    surah_number: int  # 1-114
    verse_number: int  # 1-N (varies by Surah)

    def __post_init__(self) -> None:
        if not 1 <= self.surah_number <= 114:
            raise ValueError(f"Invalid surah number: {self.surah_number}")
        if self.verse_number < 1:
            raise ValueError(f"Invalid verse number: {self.verse_number}")

    def __str__(self) -> str:
        return f"{self.surah_number}:{self.verse_number}"


@dataclass(frozen=True, slots=True)
class SurahMetadata:
    """Immutable metadata about a Surah."""
    number: int                           # 1-114
    name_arabic: str                      # الفاتحة
    name_english: str                     # Al-Fatiha
    name_transliteration: str             # Al-Fatihah
    revelation_type: 'RevelationType'     # Meccan or Medinan
    revelation_order: int                 # Order of revelation (1-114)
    verse_count: int                      # Number of verses
    basmalah_status: BasmalahStatus       # How Basmalah is treated
    ruku_count: int                       # Number of Ruku' sections


class RevelationType(StrEnum):
    """Place of revelation."""
    MECCAN = "meccan"     # مكية - Revealed in Makkah
    MEDINAN = "medinan"   # مدنية - Revealed in Madinah


@dataclass(frozen=True, slots=True)
class TextChecksum:
    """Cryptographic hash of text content for integrity verification."""
    algorithm: str  # "sha256"
    value: str      # Hex-encoded hash

    @classmethod
    def compute(cls, text: str, algorithm: str = "sha256") -> 'TextChecksum':
        import hashlib
        h = hashlib.new(algorithm)
        h.update(text.encode('utf-8'))
        return cls(algorithm=algorithm, value=h.hexdigest())


@dataclass(frozen=True, slots=True)
class AbjadValue:
    """Gematria/Abjad numerical value of text."""
    system: 'AbjadSystem'
    value: int
    letter_breakdown: tuple[tuple[str, int], ...]  # Immutable breakdown
```

### 5.2. Enumerations

```python
from enum import StrEnum, auto

class AbjadSystem(StrEnum):
    """Abjad numeral systems used in Islamic tradition."""
    MASHRIQI = "mashriqi"           # Eastern (Levant, Iraq, Gulf)
    MAGHRIBI = "maghribi"           # Western (North Africa, Al-Andalus)

    # The standard mapping (Mashriqi):
    # أ=1, ب=2, ج=3, د=4, ه=5, و=6, ز=7, ح=8, ط=9
    # ي=10, ك=20, ل=30, م=40, ن=50, س=60, ع=70, ف=80, ص=90
    # ق=100, ر=200, ش=300, ت=400, ث=500, خ=600, ذ=700, ض=800, ظ=900, غ=1000


class AnalysisType(StrEnum):
    """Types of analysis operations."""
    # Basic Counting
    LETTER_COUNT = "letter_count"
    WORD_COUNT = "word_count"
    VERSE_COUNT = "verse_count"

    # Frequency Analysis
    LETTER_FREQUENCY = "letter_frequency"
    WORD_FREQUENCY = "word_frequency"
    ROOT_FREQUENCY = "root_frequency"

    # Numerical Analysis
    ABJAD_VALUE = "abjad_value"
    PRIME_CHECK = "prime_check"
    MODULAR_ARITHMETIC = "modular_arithmetic"
    NUMBER_WORD_COUNT = "number_word_count"

    # Morphological Analysis
    ROOT_EXTRACTION = "root_extraction"
    PATTERN_EXTRACTION = "pattern_extraction"      # وزن (verb/noun patterns)
    WORD_TYPE_ANALYSIS = "word_type_analysis"      # اسم/فعل/حرف
    VERB_TENSE_ANALYSIS = "verb_tense_analysis"    # ماضي/مضارع/أمر

    # Search & Pattern
    PATTERN_SEARCH = "pattern_search"
    SPECIFIC_WORD_SEARCH = "specific_word_search"
    ROOT_SEARCH = "root_search"
    PHRASE_SEARCH = "phrase_search"

    # Entity Analysis
    DIVINE_NAME_ANALYSIS = "divine_name_analysis"  # أسماء الله الحسنى
    PROPHET_NAME_ANALYSIS = "prophet_name_analysis"
    PROPER_NOUN_EXTRACTION = "proper_noun_extraction"

    # Structural Analysis
    VERSE_ENDING_PATTERN = "verse_ending_pattern"  # فواصل
    RING_STRUCTURE = "ring_structure"              # بنية دائرية
    PARALLEL_PASSAGE = "parallel_passage"

    # Thematic Analysis
    TOPIC_EXTRACTION = "topic_extraction"
    CROSS_REFERENCE = "cross_reference"
    SEMANTIC_FIELD = "semantic_field"

    # Comparative Analysis
    WORD_PAIR_COMPARISON = "word_pair_comparison"  # الدنيا vs الآخرة
    SURAH_COMPARISON = "surah_comparison"
    MECCAN_MEDINAN_COMPARISON = "meccan_medinan_comparison"

    # Graph/Relationship Analysis
    CO_OCCURRENCE_NETWORK = "co_occurrence_network"
    CONCEPT_MAP = "concept_map"
```

### 5.3. Entities

```python
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from typing import Dict, Any, Optional
from datetime import datetime

@dataclass(frozen=True)
class Verse:
    """
    Aggregate root for a single verse (Ayah).
    Immutable after creation to preserve textual integrity.
    """
    id: UUID
    location: VerseLocation

    # Text content mapped by script type
    content: Dict[ScriptType, str]

    # Qira'at-specific variants (if different from default)
    qiraat_variants: Dict[QiraatType, Dict[ScriptType, str]]

    # Metadata
    surah_metadata: SurahMetadata
    is_sajdah: bool
    sajdah_type: Optional['SajdahType']  # Wajib or Mustahabb
    juz_number: int      # 1-30
    hizb_number: int     # 1-60
    ruku_number: int     # Within Surah
    manzil_number: int   # 1-7
    page_number: int     # In Madinah Mushaf

    # Integrity
    checksum: TextChecksum

    def get_text(
        self,
        script: ScriptType = ScriptType.UTHMANI,
        qiraat: QiraatType = QiraatType.HAFS_AN_ASIM
    ) -> str:
        """Get verse text for specific script and Qira'at."""
        # Check if there's a Qira'at-specific variant
        if qiraat in self.qiraat_variants:
            variants = self.qiraat_variants[qiraat]
            if script in variants:
                return variants[script]

        # Fall back to default content
        if script not in self.content:
            raise KeyError(f"Script type {script} not available for verse {self.location}")
        return self.content[script]


class SajdahType(StrEnum):
    """Types of prostration verses."""
    WAJIB = "wajib"           # واجب - Obligatory (per Hanafi)
    MUSTAHABB = "mustahabb"   # مستحب - Recommended


@dataclass(frozen=True)
class Surah:
    """Aggregate for a complete Surah."""
    metadata: SurahMetadata
    verses: tuple[Verse, ...]  # Immutable tuple
    checksum: TextChecksum     # Hash of complete Surah text

    def __post_init__(self) -> None:
        if len(self.verses) != self.metadata.verse_count:
            raise ValueError(
                f"Verse count mismatch: expected {self.metadata.verse_count}, "
                f"got {len(self.verses)}"
            )
```

### 5.4. Repository Interfaces (Ports)

```python
from abc import ABC, abstractmethod
from typing import List, Optional, AsyncIterator

class IQuranRepository(ABC):
    """
    Port for Quran data access.
    Implementations are in the Infrastructure layer.
    """

    @abstractmethod
    async def get_verse(self, location: VerseLocation) -> Optional[Verse]:
        """Retrieve a single verse by location."""
        ...

    @abstractmethod
    async def get_verse_or_raise(self, location: VerseLocation) -> Verse:
        """Retrieve a single verse, raise VerseNotFoundException if not found."""
        ...

    @abstractmethod
    async def get_surah(self, surah_number: int) -> Surah:
        """Retrieve a complete Surah with all verses."""
        ...

    @abstractmethod
    async def get_verses_in_range(
        self,
        start: VerseLocation,
        end: VerseLocation
    ) -> List[Verse]:
        """Retrieve verses within a range (inclusive)."""
        ...

    @abstractmethod
    async def get_all_verses(self) -> List[Verse]:
        """Retrieve all verses in the Quran."""
        ...

    @abstractmethod
    async def stream_verses(
        self,
        surah_number: Optional[int] = None
    ) -> AsyncIterator[Verse]:
        """Stream verses for memory-efficient processing."""
        ...

    @abstractmethod
    async def get_verse_count(self, surah_number: Optional[int] = None) -> int:
        """Get total verse count, optionally filtered by Surah."""
        ...

    @abstractmethod
    async def get_verses_by_criteria(
        self,
        revelation_type: Optional[RevelationType] = None,
        juz_number: Optional[int] = None,
        has_sajdah: Optional[bool] = None,
    ) -> List[Verse]:
        """Query verses by various criteria."""
        ...

    @abstractmethod
    async def verify_integrity(self) -> 'IntegrityReport':
        """Verify checksums of all stored data."""
        ...


class ISurahMetadataRepository(ABC):
    """Port for Surah metadata access."""

    @abstractmethod
    async def get_metadata(self, surah_number: int) -> SurahMetadata:
        ...

    @abstractmethod
    async def get_all_metadata(self) -> List[SurahMetadata]:
        ...


@dataclass(frozen=True)
class IntegrityReport:
    """Result of integrity verification."""
    is_valid: bool
    checked_at: datetime
    total_verses: int
    failed_verses: tuple[VerseLocation, ...]
    expected_checksum: str
    actual_checksum: str
    details: str
```

### 5.5. Domain Services

```python
class AbjadCalculator:
    """Domain service for Abjad/Gematria calculations."""

    # Mashriqi (Eastern) Abjad values
    MASHRIQI_VALUES: Final[Dict[str, int]] = {
        'ا': 1, 'أ': 1, 'إ': 1, 'آ': 1, 'ء': 1, 'ٱ': 1,  # Alif variants (includes Alif Wasla)
        'ب': 2, 'ج': 3, 'د': 4, 'ه': 5, 'و': 6, 'ز': 7, 'ح': 8, 'ط': 9,
        'ي': 10, 'ى': 10, 'ئ': 10,  # Ya variants
        'ك': 20, 'ل': 30, 'م': 40, 'ن': 50, 'س': 60, 'ع': 70, 'ف': 80, 'ص': 90,
        'ق': 100, 'ر': 200, 'ش': 300, 'ت': 400, 'ث': 500, 'خ': 600,
        'ذ': 700, 'ض': 800, 'ظ': 900, 'غ': 1000,
    }

    # Maghribi (Western) - different ordering for س ش ص ض
    MAGHRIBI_VALUES: Final[Dict[str, int]] = {
        # ... (different mapping)
    }

    def calculate(
        self,
        text: str,
        system: AbjadSystem = AbjadSystem.MASHRIQI
    ) -> AbjadValue:
        """Calculate the Abjad value of text."""
        values = self.MASHRIQI_VALUES if system == AbjadSystem.MASHRIQI else self.MAGHRIBI_VALUES

        breakdown: list[tuple[str, int]] = []
        total = 0

        for char in text:
            if char in values:
                val = values[char]
                breakdown.append((char, val))
                total += val

        return AbjadValue(
            system=system,
            value=total,
            letter_breakdown=tuple(breakdown)
        )


class LetterCounter:
    """Domain service for accurate Arabic letter counting."""

    # Arabic base letters (no diacritics)
    ARABIC_LETTERS: Final[frozenset[str]] = frozenset(
        'ابتثجحخدذرزسشصضطظعغفقكلمنهويءآأؤإئى'
    )

    # Special Alif variants that count as letters
    ALIF_WASLA: Final[str] = '\u0671'          # ٱ - Used in Uthmani script
    ALIF_KHANJARIYYA: Final[str] = '\u0670'    # ـٰ - Superscript Alif

    # Combined set of countable characters
    COUNTABLE_SPECIAL: Final[frozenset[str]] = frozenset([ALIF_WASLA, ALIF_KHANJARIYYA])

    def count_letters(
        self,
        text: str,
        count_alif_wasla: bool = True,
        count_alif_khanjariyya: bool = True,
        count_hamza_separately: bool = True,
    ) -> int:
        """
        Count Arabic letters in text.

        Args:
            text: Arabic text to count
            count_alif_wasla: If True, Alif Wasla (ٱ) counts as Alif
            count_alif_khanjariyya: If True, superscript Alif (ـٰ) counts as Alif
            count_hamza_separately: If True, Hamza is counted as separate letter
        """
        count = 0
        for char in text:
            if char in self.ARABIC_LETTERS:
                count += 1
            elif count_alif_wasla and char == self.ALIF_WASLA:
                count += 1
            elif count_alif_khanjariyya and char == self.ALIF_KHANJARIYYA:
                count += 1
        return count

    def get_letter_frequency(self, text: str) -> Dict[str, int]:
        """Get frequency distribution of each Arabic letter."""
        freq: Dict[str, int] = {}
        for char in text:
            if char in self.ARABIC_LETTERS or char in self.COUNTABLE_SPECIAL:
                # Normalize Alif variants
                normalized = self._normalize_letter(char)
                freq[normalized] = freq.get(normalized, 0) + 1
        return freq

    def _normalize_letter(self, char: str) -> str:
        """Normalize letter variants to base form."""
        # All Alif variants normalize to plain Alif
        ALIF_VARIANTS = {'آ', 'أ', 'إ', 'ا', '\u0670', '\u0671'}  # Includes Alif Wasla
        YA_VARIANTS = {'ي', 'ى', 'ئ'}

        if char in ALIF_VARIANTS:
            return 'ا'
        if char in YA_VARIANTS:
            return 'ي'
        return char
```

---

## 6. Analysis Engine

The analysis engine uses the **Strategy Pattern** for maximum flexibility and extensibility.

### 6.1. Normalization Strategies (Preprocessing)

```python
from abc import ABC, abstractmethod
from typing import Protocol

class INormalizationStrategy(ABC):
    """
    Strategy for text preprocessing before analysis.
    Multiple strategies can be chained in a pipeline.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this strategy."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this strategy does."""
        ...

    @abstractmethod
    def normalize(self, text: str) -> str:
        """Apply normalization and return processed text."""
        ...


class RemoveTashkeelStrategy(INormalizationStrategy):
    """Removes all diacritical marks (tashkeel/harakat)."""

    # Tashkeel Unicode range
    TASHKEEL = frozenset([
        '\u064B',  # Fathatan
        '\u064C',  # Dammatan
        '\u064D',  # Kasratan
        '\u064E',  # Fatha
        '\u064F',  # Damma
        '\u0650',  # Kasra
        '\u0651',  # Shadda
        '\u0652',  # Sukun
        '\u0653',  # Maddah
        '\u0654',  # Hamza above
        '\u0655',  # Hamza below
        '\u0656',  # Subscript Alef
        '\u0657',  # Inverted Damma
        '\u0658',  # Mark Noon Ghunna
        '\u0670',  # Superscript Alef (Alif Khanjariyya)
    ])

    @property
    def name(self) -> str:
        return "remove_tashkeel"

    @property
    def description(self) -> str:
        return "Removes all diacritical marks (fatha, damma, kasra, etc.)"

    def normalize(self, text: str) -> str:
        return ''.join(c for c in text if c not in self.TASHKEEL)


class UnifyAlifsStrategy(INormalizationStrategy):
    """Unifies all Alif variants to plain Alif."""

    ALIF_VARIANTS = {
        'آ': 'ا',  # Alif with Maddah
        'أ': 'ا',  # Alif with Hamza above
        'إ': 'ا',  # Alif with Hamza below
        'ٱ': 'ا',  # Alif Wasla
    }

    @property
    def name(self) -> str:
        return "unify_alifs"

    @property
    def description(self) -> str:
        return "Converts all Alif variants (آ أ إ ٱ) to plain Alif (ا)"

    def normalize(self, text: str) -> str:
        for variant, replacement in self.ALIF_VARIANTS.items():
            text = text.replace(variant, replacement)
        return text


class RemoveNonLettersStrategy(INormalizationStrategy):
    """Removes everything except Arabic letters."""

    ARABIC_LETTERS = frozenset('ابتثجحخدذرزسشصضطظعغفقكلمنهويءآأؤإئى')

    @property
    def name(self) -> str:
        return "letters_only"

    @property
    def description(self) -> str:
        return "Removes all non-letter characters (spaces, punctuation, numbers)"

    def normalize(self, text: str) -> str:
        return ''.join(c for c in text if c in self.ARABIC_LETTERS)


class PreserveAlifKhanjariyyaStrategy(INormalizationStrategy):
    """Converts Alif Khanjariyya (superscript) to regular Alif for counting."""

    @property
    def name(self) -> str:
        return "preserve_alif_khanjariyya"

    @property
    def description(self) -> str:
        return "Converts superscript Alif (ٰ) to regular Alif (ا) so it is counted"

    def normalize(self, text: str) -> str:
        return text.replace('\u0670', 'ا')


class RemoveWaqfSignsStrategy(INormalizationStrategy):
    """Removes Waqf (stop) signs from text."""

    # Common Waqf signs
    WAQF_SIGNS = frozenset(['ۖ', 'ۗ', 'ۘ', 'ۙ', 'ۚ', 'ۛ', 'ۜ', '۞', '۩'])

    @property
    def name(self) -> str:
        return "remove_waqf"

    @property
    def description(self) -> str:
        return "Removes Waqf (pause/stop) signs"

    def normalize(self, text: str) -> str:
        return ''.join(c for c in text if c not in self.WAQF_SIGNS)
```

### 6.2. Calculation Strategies (Processing)

```python
from typing import Union, Dict, Any

class ICalculationStrategy(ABC):
    """Strategy for performing calculations on normalized text."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @property
    @abstractmethod
    def output_schema(self) -> Dict[str, str]:
        """Describes the output structure."""
        ...

    @abstractmethod
    def calculate(self, text: str) -> Dict[str, Any]:
        """Perform calculation and return results."""
        ...


class LetterCountStrategy(ICalculationStrategy):
    """Counts total number of Arabic letters."""

    def __init__(self, counter: LetterCounter):
        self._counter = counter

    @property
    def name(self) -> str:
        return "letter_count"

    @property
    def description(self) -> str:
        return "Counts the total number of Arabic letters"

    @property
    def output_schema(self) -> Dict[str, str]:
        return {"count": "int"}

    def calculate(self, text: str) -> Dict[str, Any]:
        return {"count": self._counter.count_letters(text)}


class LetterFrequencyStrategy(ICalculationStrategy):
    """Calculates frequency of each Arabic letter."""

    def __init__(self, counter: LetterCounter):
        self._counter = counter

    @property
    def name(self) -> str:
        return "letter_frequency"

    @property
    def description(self) -> str:
        return "Returns frequency count for each Arabic letter"

    @property
    def output_schema(self) -> Dict[str, str]:
        return {"frequencies": "Dict[str, int]", "total": "int"}

    def calculate(self, text: str) -> Dict[str, Any]:
        freq = self._counter.get_letter_frequency(text)
        return {
            "frequencies": freq,
            "total": sum(freq.values())
        }


class AbjadCumulativeStrategy(ICalculationStrategy):
    """Calculates cumulative Abjad value of text."""

    def __init__(self, calculator: AbjadCalculator, system: AbjadSystem = AbjadSystem.MASHRIQI):
        self._calculator = calculator
        self._system = system

    @property
    def name(self) -> str:
        return f"abjad_{self._system.value}"

    @property
    def description(self) -> str:
        return f"Calculates Abjad/Gematria value using {self._system.value} system"

    @property
    def output_schema(self) -> Dict[str, str]:
        return {
            "value": "int",
            "system": "str",
            "breakdown": "List[Tuple[str, int]]"
        }

    def calculate(self, text: str) -> Dict[str, Any]:
        result = self._calculator.calculate(text, self._system)
        return {
            "value": result.value,
            "system": result.system.value,
            "breakdown": list(result.letter_breakdown)
        }


class ModularArithmeticStrategy(ICalculationStrategy):
    """Calculates value modulo a given number."""

    def __init__(self, base_strategy: ICalculationStrategy, modulus: int):
        self._base = base_strategy
        self._modulus = modulus

    @property
    def name(self) -> str:
        return f"{self._base.name}_mod_{self._modulus}"

    @property
    def description(self) -> str:
        return f"Calculates {self._base.name} modulo {self._modulus}"

    @property
    def output_schema(self) -> Dict[str, str]:
        return {
            "original_value": "int",
            "modulus": "int",
            "remainder": "int"
        }

    def calculate(self, text: str) -> Dict[str, Any]:
        base_result = self._base.calculate(text)
        # Extract the numeric value (works for count or abjad value)
        value = base_result.get("count") or base_result.get("value", 0)
        return {
            "original_value": value,
            "modulus": self._modulus,
            "remainder": value % self._modulus
        }


class PrimeCheckStrategy(ICalculationStrategy):
    """Checks if a calculated value is prime."""

    def __init__(self, base_strategy: ICalculationStrategy):
        self._base = base_strategy

    @property
    def name(self) -> str:
        return f"{self._base.name}_prime_check"

    @property
    def description(self) -> str:
        return f"Checks if {self._base.name} result is a prime number"

    @property
    def output_schema(self) -> Dict[str, str]:
        return {
            "value": "int",
            "is_prime": "bool",
            "factors": "List[int] | None"
        }

    def calculate(self, text: str) -> Dict[str, Any]:
        base_result = self._base.calculate(text)
        value = base_result.get("count") or base_result.get("value", 0)
        is_prime = self._is_prime(value)

        return {
            "value": value,
            "is_prime": is_prime,
            "factors": None if is_prime else self._get_factors(value)
        }

    @staticmethod
    def _is_prime(n: int) -> bool:
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        for i in range(3, int(n**0.5) + 1, 2):
            if n % i == 0:
                return False
        return True

    @staticmethod
    def _get_factors(n: int) -> list[int]:
        factors = []
        d = 2
        while d * d <= n:
            while n % d == 0:
                factors.append(d)
                n //= d
            d += 1
        if n > 1:
            factors.append(n)
        return factors


class WordCountStrategy(ICalculationStrategy):
    """Counts total number of words in text."""

    @property
    def name(self) -> str:
        return "word_count"

    @property
    def description(self) -> str:
        return "Counts the total number of words (space-separated tokens)"

    @property
    def output_schema(self) -> Dict[str, str]:
        return {"count": "int"}

    def calculate(self, text: str) -> Dict[str, Any]:
        # Words are space-separated in Quranic text
        words = text.split()
        return {"count": len(words)}


class WordFrequencyStrategy(ICalculationStrategy):
    """Calculates frequency of each unique word."""

    @property
    def name(self) -> str:
        return "word_frequency"

    @property
    def description(self) -> str:
        return "Returns frequency count for each unique word"

    @property
    def output_schema(self) -> Dict[str, str]:
        return {
            "frequencies": "Dict[str, int]",
            "unique_count": "int",
            "total_count": "int"
        }

    def calculate(self, text: str) -> Dict[str, Any]:
        from collections import Counter
        words = text.split()
        freq = dict(Counter(words))
        return {
            "frequencies": freq,
            "unique_count": len(freq),
            "total_count": len(words)
        }


class SpecificWordSearchStrategy(ICalculationStrategy):
    """Searches for specific word(s) and counts occurrences.

    This is critical for analyses like:
    - "Yevm" (يوم - Day) appears 365 times
    - "Shahr" (شهر - Month) appears 12 times
    - "Allah" (الله) appears 2699 times
    """

    def __init__(self, target_words: list[str], match_mode: str = "exact"):
        """
        Args:
            target_words: List of words to search for
            match_mode: "exact" for exact match, "root" for root-based matching
        """
        self._target_words = target_words
        self._match_mode = match_mode

    @property
    def name(self) -> str:
        words_str = "_".join(self._target_words[:3])
        suffix = "..." if len(self._target_words) > 3 else ""
        return f"word_search_{words_str}{suffix}"

    @property
    def description(self) -> str:
        return f"Searches for specific words: {', '.join(self._target_words)}"

    @property
    def output_schema(self) -> Dict[str, str]:
        return {
            "matches": "Dict[str, WordSearchResult]",
            "total_matches": "int"
        }

    def calculate(self, text: str) -> Dict[str, Any]:
        from collections import Counter
        words = text.split()
        word_counts = Counter(words)

        matches = {}
        total = 0

        for target in self._target_words:
            if self._match_mode == "exact":
                count = word_counts.get(target, 0)
            else:
                # For root matching, count words containing the target
                count = sum(c for w, c in word_counts.items() if target in w)

            matches[target] = {
                "count": count,
                "target": target,
                "match_mode": self._match_mode
            }
            total += count

        return {
            "matches": matches,
            "total_matches": total
        }


class RootExtractionStrategy(ICalculationStrategy):
    """Extracts Arabic root (جذر) from words for morphological analysis.

    Arabic words are typically derived from 3-letter roots (trilateral).
    Example: كتاب، كاتب، مكتوب، كتب all derive from root ك-ت-ب (k-t-b)
    """

    def __init__(self, root_extractor: "IRootExtractor"):
        """
        Args:
            root_extractor: Service for extracting Arabic roots
        """
        self._extractor = root_extractor

    @property
    def name(self) -> str:
        return "root_extraction"

    @property
    def description(self) -> str:
        return "Extracts Arabic trilateral roots from words"

    @property
    def output_schema(self) -> Dict[str, str]:
        return {
            "roots": "Dict[str, RootInfo]",
            "root_frequency": "Dict[str, int]"
        }

    def calculate(self, text: str) -> Dict[str, Any]:
        from collections import Counter
        words = text.split()

        roots: Dict[str, Any] = {}
        root_counts: Counter = Counter()

        for word in words:
            root = self._extractor.extract(word)
            if root:
                roots[word] = {
                    "word": word,
                    "root": root,
                    "pattern": self._extractor.get_pattern(word)
                }
                root_counts[root] += 1

        return {
            "roots": roots,
            "root_frequency": dict(root_counts)
        }


class IRootExtractor(ABC):
    """Interface for Arabic root extraction service."""

    @abstractmethod
    def extract(self, word: str) -> Optional[str]:
        """Extract the root from an Arabic word."""
        ...

    @abstractmethod
    def get_pattern(self, word: str) -> Optional[str]:
        """Get the morphological pattern (وزن) of a word."""
        ...


class VerseCountStrategy(ICalculationStrategy):
    """Counts verses matching specific criteria."""

    @property
    def name(self) -> str:
        return "verse_count"

    @property
    def description(self) -> str:
        return "Counts the number of verses in the selected scope"

    @property
    def output_schema(self) -> Dict[str, str]:
        return {"count": "int"}

    def calculate(self, text: str) -> Dict[str, Any]:
        # Each verse is typically on a new line or separated by verse markers
        # For pre-processed text, count is passed via context
        # This is a placeholder - actual implementation uses repository
        return {"count": 0}  # Populated by orchestrator
```

### 6.3. Scope Specifications (Filtering)

```python
class IScopeSpecification(ABC):
    """Specification pattern for filtering verses."""

    @abstractmethod
    def is_satisfied_by(self, verse: Verse) -> bool:
        """Returns True if verse matches this specification."""
        ...

    def and_(self, other: 'IScopeSpecification') -> 'IScopeSpecification':
        """Combine with AND logic."""
        return AndSpecification(self, other)

    def or_(self, other: 'IScopeSpecification') -> 'IScopeSpecification':
        """Combine with OR logic."""
        return OrSpecification(self, other)

    def not_(self) -> 'IScopeSpecification':
        """Negate this specification."""
        return NotSpecification(self)


class AndSpecification(IScopeSpecification):
    def __init__(self, left: IScopeSpecification, right: IScopeSpecification):
        self._left = left
        self._right = right

    def is_satisfied_by(self, verse: Verse) -> bool:
        return self._left.is_satisfied_by(verse) and self._right.is_satisfied_by(verse)


class OrSpecification(IScopeSpecification):
    def __init__(self, left: IScopeSpecification, right: IScopeSpecification):
        self._left = left
        self._right = right

    def is_satisfied_by(self, verse: Verse) -> bool:
        return self._left.is_satisfied_by(verse) or self._right.is_satisfied_by(verse)


class NotSpecification(IScopeSpecification):
    def __init__(self, spec: IScopeSpecification):
        self._spec = spec

    def is_satisfied_by(self, verse: Verse) -> bool:
        return not self._spec.is_satisfied_by(verse)


class SurahScope(IScopeSpecification):
    """Filter by specific Surah(s)."""

    def __init__(self, surah_numbers: int | list[int]):
        if isinstance(surah_numbers, int):
            surah_numbers = [surah_numbers]
        self._surahs = frozenset(surah_numbers)

    def is_satisfied_by(self, verse: Verse) -> bool:
        return verse.location.surah_number in self._surahs


class SurahRangeScope(IScopeSpecification):
    """Filter by Surah range (inclusive)."""

    def __init__(self, start: int, end: int):
        self._start = start
        self._end = end

    def is_satisfied_by(self, verse: Verse) -> bool:
        return self._start <= verse.location.surah_number <= self._end


class RevelationTypeScope(IScopeSpecification):
    """Filter by revelation type (Meccan/Medinan)."""

    def __init__(self, revelation_type: RevelationType):
        self._type = revelation_type

    def is_satisfied_by(self, verse: Verse) -> bool:
        return verse.surah_metadata.revelation_type == self._type


class JuzScope(IScopeSpecification):
    """Filter by Juz' (Part) number."""

    def __init__(self, juz_numbers: int | list[int]):
        if isinstance(juz_numbers, int):
            juz_numbers = [juz_numbers]
        self._juz = frozenset(juz_numbers)

    def is_satisfied_by(self, verse: Verse) -> bool:
        return verse.juz_number in self._juz


class ExcludeBasmalahScope(IScopeSpecification):
    """Excludes Basmalah verses from analysis."""

    def is_satisfied_by(self, verse: Verse) -> bool:
        # Basmalah is verse 1 of Al-Fatiha (counted as verse)
        if verse.location.surah_number == 1 and verse.location.verse_number == 1:
            return False  # Exclude

        # For other Surahs, Basmalah is not numbered as a verse
        # So we don't need to exclude anything
        return True


class SajdahVersesScope(IScopeSpecification):
    """Filter to only Sajdah verses."""

    def __init__(self, include: bool = True):
        self._include = include

    def is_satisfied_by(self, verse: Verse) -> bool:
        if self._include:
            return verse.is_sajdah
        return not verse.is_sajdah


class AllVersesScope(IScopeSpecification):
    """Matches all verses (no filtering)."""

    def is_satisfied_by(self, verse: Verse) -> bool:
        return True
```

### 6.4. Strategy Factory

```python
from typing import Type

class StrategyFactory:
    """Factory for creating and managing analysis strategies."""

    def __init__(self):
        self._normalization_strategies: Dict[str, Type[INormalizationStrategy]] = {}
        self._calculation_strategies: Dict[str, Type[ICalculationStrategy]] = {}
        self._letter_counter = LetterCounter()
        self._abjad_calculator = AbjadCalculator()

        # Register default strategies
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register built-in strategies."""
        # Normalization
        self.register_normalization(RemoveTashkeelStrategy)
        self.register_normalization(UnifyAlifsStrategy)
        self.register_normalization(RemoveNonLettersStrategy)
        self.register_normalization(PreserveAlifKhanjariyyaStrategy)
        self.register_normalization(RemoveWaqfSignsStrategy)

    def register_normalization(self, strategy_class: Type[INormalizationStrategy]) -> None:
        instance = strategy_class()
        self._normalization_strategies[instance.name] = strategy_class

    def get_normalization(self, name: str) -> INormalizationStrategy:
        if name not in self._normalization_strategies:
            raise StrategyNotFoundException(f"Normalization strategy not found: {name}")
        return self._normalization_strategies[name]()

    def get_calculation(self, name: str) -> ICalculationStrategy:
        """Get calculation strategy by name."""
        if name == "letter_count":
            return LetterCountStrategy(self._letter_counter)
        elif name == "letter_frequency":
            return LetterFrequencyStrategy(self._letter_counter)
        elif name == "abjad_mashriqi":
            return AbjadCumulativeStrategy(self._abjad_calculator, AbjadSystem.MASHRIQI)
        elif name == "abjad_maghribi":
            return AbjadCumulativeStrategy(self._abjad_calculator, AbjadSystem.MAGHRIBI)
        elif name.startswith("letter_count_mod_"):
            modulus = int(name.split("_")[-1])
            return ModularArithmeticStrategy(
                LetterCountStrategy(self._letter_counter),
                modulus
            )
        elif name == "letter_count_prime":
            return PrimeCheckStrategy(LetterCountStrategy(self._letter_counter))
        else:
            raise StrategyNotFoundException(f"Calculation strategy not found: {name}")

    def build_scope(self, config: Dict[str, Any]) -> IScopeSpecification:
        """Build scope specification from configuration dict."""
        specs: list[IScopeSpecification] = []

        if "surah" in config:
            specs.append(SurahScope(config["surah"]))

        if "surah_range" in config:
            start, end = config["surah_range"]
            specs.append(SurahRangeScope(start, end))

        if "revelation_type" in config:
            specs.append(RevelationTypeScope(RevelationType(config["revelation_type"])))

        if "juz" in config:
            specs.append(JuzScope(config["juz"]))

        if config.get("exclude_basmalah", False):
            specs.append(ExcludeBasmalahScope())

        if config.get("sajdah_only", False):
            specs.append(SajdahVersesScope(include=True))

        if not specs:
            return AllVersesScope()

        # Combine all specs with AND
        result = specs[0]
        for spec in specs[1:]:
            result = result.and_(spec)

        return result

    def list_available_strategies(self) -> Dict[str, list[str]]:
        """List all available strategy names."""
        return {
            "normalization": list(self._normalization_strategies.keys()),
            "calculation": [
                "letter_count",
                "letter_frequency",
                "abjad_mashriqi",
                "abjad_maghribi",
                "letter_count_mod_N",  # Template
                "letter_count_prime",
            ]
        }
```

### 6.5. Entity Search Strategies (Tier 2)

Strategies for searching Divine Names, Prophets, and other named entities with variant handling.

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set
from abc import ABC, abstractmethod


@dataclass
class EntityMatch:
    """Single entity match with context."""
    entity_type: str                # divine_name, prophet, place, people
    entity_key: str                 # Normalized key
    entity_name_ar: str             # Arabic display name
    entity_name_en: str             # English name
    location: VerseLocation
    word_index: int
    matched_form: str               # Actual text form matched
    context_before: str             # Text before match
    context_after: str              # Text after match
    match_method: str               # exact, lemma, variant


@dataclass
class EntitySearchResult:
    """Result of entity search."""
    entity_type: str
    entity_key: str
    total_occurrences: int
    matches: List[EntityMatch]
    unique_forms: Set[str]          # All forms this entity appears in
    surah_distribution: Dict[int, int]  # {surah_num: count}


class IEntitySearchStrategy(ABC):
    """Interface for entity search strategies."""

    @property
    @abstractmethod
    def entity_type(self) -> str:
        """Type of entities this strategy searches."""
        ...

    @abstractmethod
    async def search(
        self,
        entity_key: str,
        scope: IScopeSpecification,
    ) -> EntitySearchResult:
        """Search for entity occurrences."""
        ...

    @abstractmethod
    async def search_all(
        self,
        scope: IScopeSpecification,
    ) -> Dict[str, EntitySearchResult]:
        """Search for all entities of this type."""
        ...


class DivineNameSearchStrategy(IEntitySearchStrategy):
    """
    Search strategy for Divine Names (أسماء الله الحسنى).

    Handles:
    - Exact matches (الله، الرحمن، الرحيم)
    - With prefixes (بالله، والله، لله)
    - Variant spellings (اللّٰه، ٱللَّه)
    """

    def __init__(
        self,
        entity_repo: IEntityOccurrenceRepository,
        normalizer: ArabicNormalizer,
    ):
        self._repo = entity_repo
        self._normalizer = normalizer

    @property
    def entity_type(self) -> str:
        return "divine_name"

    async def search(
        self,
        entity_key: str,
        scope: IScopeSpecification,
    ) -> EntitySearchResult:
        """Search for a specific Divine Name."""

        # Normalize the search key
        normalized_key = self._normalizer.full_normalize(entity_key)

        # Get pre-indexed occurrences
        occurrences = await self._repo.get_by_entity_key(
            entity_type=self.entity_type,
            entity_key=normalized_key,
            scope=scope,
        )

        # Build result
        matches = [self._to_match(occ) for occ in occurrences]
        unique_forms = {m.matched_form for m in matches}
        surah_dist = self._compute_surah_distribution(matches)

        return EntitySearchResult(
            entity_type=self.entity_type,
            entity_key=normalized_key,
            total_occurrences=len(matches),
            matches=matches,
            unique_forms=unique_forms,
            surah_distribution=surah_dist,
        )

    async def search_all(
        self,
        scope: IScopeSpecification,
    ) -> Dict[str, EntitySearchResult]:
        """Search for all Divine Names in scope."""
        results = {}
        for name in DIVINE_NAMES.keys():
            result = await self.search(name, scope)
            if result.total_occurrences > 0:
                results[name] = result
        return results

    async def get_name_pairs(
        self,
        scope: IScopeSpecification,
    ) -> List[Dict[str, Any]]:
        """
        Find Divine Name pairs that appear together.

        Returns pairs like (الغفور، الرحيم) that co-occur in verses.
        """
        # Get all verses with multiple Divine Names
        verses_with_names = await self._repo.get_verses_with_multiple_entities(
            entity_type=self.entity_type,
            min_count=2,
            scope=scope,
        )

        pairs = []
        for verse_data in verses_with_names:
            names_in_verse = verse_data['entities']
            # Generate all pairs
            for i, name1 in enumerate(names_in_verse):
                for name2 in names_in_verse[i+1:]:
                    pairs.append({
                        'name1': name1,
                        'name2': name2,
                        'location': verse_data['location'],
                    })

        return pairs


class ProphetSearchStrategy(IEntitySearchStrategy):
    """Search strategy for Prophet names."""

    def __init__(
        self,
        entity_repo: IEntityOccurrenceRepository,
        normalizer: ArabicNormalizer,
    ):
        self._repo = entity_repo
        self._normalizer = normalizer

    @property
    def entity_type(self) -> str:
        return "prophet"

    async def search(
        self,
        entity_key: str,
        scope: IScopeSpecification,
    ) -> EntitySearchResult:
        """Search for a specific Prophet."""
        normalized_key = self._normalizer.full_normalize(entity_key)

        occurrences = await self._repo.get_by_entity_key(
            entity_type=self.entity_type,
            entity_key=normalized_key,
            scope=scope,
        )

        matches = [self._to_match(occ) for occ in occurrences]

        return EntitySearchResult(
            entity_type=self.entity_type,
            entity_key=normalized_key,
            total_occurrences=len(matches),
            matches=matches,
            unique_forms={m.matched_form for m in matches},
            surah_distribution=self._compute_surah_distribution(matches),
        )

    async def get_prophet_stories(
        self,
        prophet_name: str,
        scope: IScopeSpecification,
    ) -> List[Dict[str, Any]]:
        """
        Get verse ranges that form contiguous prophet stories.

        Identifies narrative blocks about a specific prophet.
        """
        result = await self.search(prophet_name, scope)

        # Group matches by surah and find contiguous ranges
        by_surah: Dict[int, List[int]] = {}
        for match in result.matches:
            surah = match.location.surah_number
            verse = match.location.verse_number
            by_surah.setdefault(surah, []).append(verse)

        stories = []
        for surah, verses in by_surah.items():
            # Find contiguous ranges (with some gap tolerance)
            ranges = self._find_narrative_ranges(sorted(verses), gap_tolerance=5)
            for start, end in ranges:
                stories.append({
                    'prophet': prophet_name,
                    'surah': surah,
                    'verse_start': start,
                    'verse_end': end,
                    'mention_count': len([v for v in verses if start <= v <= end]),
                })

        return stories
```

### 6.6. Semantic Analysis Strategies (Tier 4) ⚠️ EXPERIMENTAL

> **⚠️ EXPERIMENTAL STATUS - NOT FOR PRODUCTION**
>
> This tier uses machine learning models (AraBERT) trained on **Modern Standard Arabic**.
> The Quran is written in **Classical Arabic (7th century)**, which has different:
> - Vocabulary meanings (semantic shift over 1400 years)
> - Grammatical structures
> - Contextual usage patterns
>
> **Limitations:**
> - Similarity scores may not reflect theological/scholarly similarity
> - Results require human validation before any claims
> - Use for **exploratory research only**, not definitive analysis
>
> **Validation Required Before Production:**
> - [ ] Test against known similar verses (from tafsir)
> - [ ] Measure precision/recall against scholarly sources
> - [ ] If accuracy < 80%, do not expose in API

Strategies for semantic similarity, co-occurrence networks, and topic analysis.

```python
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import networkx as nx


@dataclass
class SimilarVerse:
    """A verse similar to the query verse."""
    location: VerseLocation
    similarity_score: float
    text: str
    shared_words: List[str]
    shared_roots: List[str]


@dataclass
class CoOccurrenceEdge:
    """Edge in co-occurrence network."""
    word1: str
    word2: str
    weight: int                     # Co-occurrence count
    verses: List[VerseLocation]     # Where they co-occur


class VerseSimilarityStrategy:
    """
    ⚠️ EXPERIMENTAL: Find semantically similar verses using embeddings.

    Uses AraBERT embeddings to compute verse-to-verse similarity.

    WARNING: AraBERT is trained on Modern Standard Arabic, not Classical Arabic.
    Results may not accurately reflect Quranic semantic relationships.
    Use for exploratory research only.
    """

    def __init__(
        self,
        embedding_service: 'ArabicEmbeddingService',
        repository: IQuranRepository,
    ):
        self._embedder = embedding_service
        self._repo = repository
        self._verse_embeddings: Dict[str, np.ndarray] = {}  # Cached embeddings

    async def build_index(self) -> None:
        """Pre-compute embeddings for all verses."""
        all_verses = await self._repo.get_all()

        for verse in all_verses:
            key = f"{verse.location.surah_number}:{verse.location.verse_number}"
            # Use normalized text for embedding
            embedding = self._embedder.embed_text(verse.text_normalized)
            self._verse_embeddings[key] = embedding

    async def find_similar(
        self,
        query_location: VerseLocation,
        top_k: int = 10,
        min_similarity: float = 0.7,
        exclude_same_surah: bool = False,
    ) -> List[SimilarVerse]:
        """Find verses most similar to the query verse."""

        query_key = f"{query_location.surah_number}:{query_location.verse_number}"
        if query_key not in self._verse_embeddings:
            raise VerseNotFoundException(f"No embedding for verse: {query_location}")

        query_embedding = self._verse_embeddings[query_key]
        query_verse = await self._repo.get_verse(query_location)

        similarities = []
        for key, embedding in self._verse_embeddings.items():
            if key == query_key:
                continue

            surah, verse = map(int, key.split(':'))
            if exclude_same_surah and surah == query_location.surah_number:
                continue

            # Cosine similarity
            sim = self._cosine_similarity(query_embedding, embedding)
            if sim >= min_similarity:
                loc = VerseLocation(surah, verse)
                similarities.append((loc, sim))

        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Build results
        results = []
        for loc, sim in similarities[:top_k]:
            verse = await self._repo.get_verse(loc)
            shared = self._find_shared_words(query_verse.text_normalized, verse.text_normalized)
            results.append(SimilarVerse(
                location=loc,
                similarity_score=sim,
                text=verse.text_uthmani,
                shared_words=shared['words'],
                shared_roots=shared['roots'],
            ))

        return results

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


class CoOccurrenceNetworkStrategy:
    """
    Build and analyze word co-occurrence networks.

    Useful for finding:
    - Words that frequently appear together
    - Central concepts in the Quran
    - Semantic clusters
    """

    def __init__(
        self,
        morphology_repo: IMorphologyRepository,
        normalizer: ArabicNormalizer,
        window_size: int = 5,
    ):
        self._morph_repo = morphology_repo
        self._normalizer = normalizer
        self._window_size = window_size
        self._graph: Optional[nx.Graph] = None

    async def build_network(
        self,
        scope: IScopeSpecification,
        use_lemmas: bool = True,
        min_word_freq: int = 5,
        exclude_stop_words: bool = True,
    ) -> nx.Graph:
        """
        Build co-occurrence network for verses in scope.

        Args:
            scope: Which verses to include
            use_lemmas: Use lemmas instead of surface forms
            min_word_freq: Minimum word frequency to include
            exclude_stop_words: Exclude common function words
        """
        self._graph = nx.Graph()

        # Get all morphology data for scope
        verse_morphs = await self._morph_repo.get_by_scope(scope)

        # Count word frequencies first
        word_freq: Dict[str, int] = {}
        for verse_data in verse_morphs:
            for word in verse_data:
                key = word.lemma if use_lemmas and word.lemma else word.word_text_normalized
                if exclude_stop_words and self._is_stop_word(word):
                    continue
                word_freq[key] = word_freq.get(key, 0) + 1

        # Filter by minimum frequency
        valid_words = {w for w, f in word_freq.items() if f >= min_word_freq}

        # Build co-occurrence edges
        for verse_data in verse_morphs:
            words = []
            for word in verse_data:
                key = word.lemma if use_lemmas and word.lemma else word.word_text_normalized
                if key in valid_words:
                    words.append(key)

            # Create edges within window
            for i, word1 in enumerate(words):
                for j in range(i + 1, min(i + self._window_size + 1, len(words))):
                    word2 = words[j]
                    if word1 != word2:
                        if self._graph.has_edge(word1, word2):
                            self._graph[word1][word2]['weight'] += 1
                        else:
                            self._graph.add_edge(word1, word2, weight=1)

        return self._graph

    def get_central_words(self, top_n: int = 20) -> List[Tuple[str, float]]:
        """Get most central words by eigenvector centrality."""
        if not self._graph:
            raise ValueError("Network not built. Call build_network first.")

        centrality = nx.eigenvector_centrality(self._graph, weight='weight')
        sorted_words = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        return sorted_words[:top_n]

    def get_word_neighbors(
        self,
        word: str,
        top_n: int = 10,
    ) -> List[Tuple[str, int]]:
        """Get words most frequently co-occurring with given word."""
        if not self._graph or word not in self._graph:
            return []

        neighbors = [
            (n, self._graph[word][n]['weight'])
            for n in self._graph.neighbors(word)
        ]
        return sorted(neighbors, key=lambda x: x[1], reverse=True)[:top_n]

    def find_communities(self) -> List[Set[str]]:
        """Find semantic communities using Louvain algorithm."""
        if not self._graph:
            raise ValueError("Network not built. Call build_network first.")

        from networkx.algorithms.community import louvain_communities
        communities = louvain_communities(self._graph, weight='weight')
        return [set(c) for c in communities]

    def _is_stop_word(self, word: WordMorphologyModel) -> bool:
        """Check if word is a stop word (particle, preposition, etc.)."""
        return word.pos_tag in ('PART', 'PREP', 'CONJ', 'DET', 'PRON')
```

### 6.7. Structural Analysis Tools (Tier 5) ⚠️ RESEARCH TOOLS

> **⚠️ RESEARCH TOOLS - REQUIRES SCHOLARLY INTERPRETATION**
>
> These tools compute **numerical scores** but cannot determine **meaning**.
>
> **What These Tools CAN Do (Objective):**
> - ✅ Extract verse ending patterns (فواصل) - factual string matching
> - ✅ Find repeated phrases - factual n-gram extraction
> - ✅ Compute word overlap between verse pairs - factual counting
>
> **What These Tools CANNOT Do (Subjective):**
> - ❌ Prove ring composition exists
> - ❌ Determine if symmetry is intentional or coincidental
> - ❌ Make theological claims about structure
>
> **Usage Guidelines:**
> - Treat scores as **data points**, not **conclusions**
> - High symmetry score ≠ confirmed ring structure
> - All findings require scholarly validation

Tools to assist scholars in identifying structural patterns like ring composition.

```python
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import numpy as np


@dataclass
class RepeatedPhrase:
    """A phrase that repeats within a Surah - OBJECTIVE, factual extraction."""
    phrase: str
    occurrences: List[Tuple[int, int]]  # (verse_num, word_index)
    word_count: int


@dataclass
class VerseEndingPattern:
    """Analysis of verse ending patterns (فواصل) - OBJECTIVE, factual."""
    surah_number: int
    total_verses: int
    ending_patterns: Dict[str, List[int]]  # pattern -> verse numbers
    most_common_ending: str
    rhyme_consistency: float  # 0-1 score


@dataclass
class SymmetryAnalysis:
    """
    Analysis of potential ring structure symmetry.

    ⚠️ WARNING: symmetry_score is a NUMERICAL METRIC, not proof of intentional structure.
    High scores may be coincidental. Requires scholarly interpretation.
    """
    surah_number: int
    proposed_center: int
    symmetry_score: float           # 0-1 score (METRIC ONLY, NOT PROOF)
    verse_pairs: List[Dict[str, Any]]  # Paired verses with similarities
    thematic_matches: List[str]


class StructuralAnalysisTool:
    """
    Tools for analyzing structural patterns in the Quran.

    ⚠️ RESEARCH TOOLS - NOT AUTOMATED DETECTION
    These provide data for scholars to interpret, not conclusions.
    """

    def __init__(
        self,
        repository: IQuranRepository,
        morphology_repo: IMorphologyRepository,
        similarity_strategy: VerseSimilarityStrategy,
    ):
        self._repo = repository
        self._morph_repo = morphology_repo
        self._similarity = similarity_strategy

    async def compute_verse_similarity_matrix(
        self,
        surah_number: int,
        similarity_type: str = "lexical",
    ) -> np.ndarray:
        """
        Compute pairwise similarity matrix for all verses in a Surah.

        This can help identify potential ring structures when
        verses at positions i and n-i have high similarity.

        Args:
            surah_number: Surah to analyze
            similarity_type: "lexical" (word overlap), "semantic" (embeddings), "root" (shared roots)

        Returns:
            n x n similarity matrix where n = number of verses
        """
        verses = await self._repo.get_verses_by_surah(surah_number)
        n = len(verses)
        matrix = np.zeros((n, n))

        for i, verse_i in enumerate(verses):
            for j, verse_j in enumerate(verses):
                if i <= j:
                    if similarity_type == "lexical":
                        sim = self._lexical_similarity(verse_i, verse_j)
                    elif similarity_type == "semantic":
                        sim = await self._semantic_similarity(verse_i, verse_j)
                    elif similarity_type == "root":
                        sim = await self._root_similarity(verse_i, verse_j)
                    else:
                        raise ValueError(f"Unknown similarity type: {similarity_type}")

                    matrix[i, j] = sim
                    matrix[j, i] = sim  # Symmetric

        return matrix

    async def find_repeated_phrases(
        self,
        surah_number: int,
        min_words: int = 3,
        min_occurrences: int = 2,
    ) -> List[RepeatedPhrase]:
        """
        Find phrases that repeat within a Surah.

        Repeated phrases often serve as structural markers.
        """
        verses = await self._repo.get_verses_by_surah(surah_number)

        # Extract all n-grams
        phrase_locations: Dict[str, List[Tuple[int, int]]] = {}

        for verse in verses:
            words = verse.text_normalized.split()
            for start in range(len(words) - min_words + 1):
                for length in range(min_words, min(len(words) - start + 1, 10)):
                    phrase = ' '.join(words[start:start + length])
                    location = (verse.location.verse_number, start)
                    phrase_locations.setdefault(phrase, []).append(location)

        # Filter to repeated phrases
        results = []
        for phrase, locations in phrase_locations.items():
            if len(locations) >= min_occurrences:
                results.append(RepeatedPhrase(
                    phrase=phrase,
                    occurrences=locations,
                    word_count=len(phrase.split()),
                ))

        # Sort by occurrence count and length
        results.sort(key=lambda x: (len(x.occurrences), x.word_count), reverse=True)
        return results

    async def analyze_verse_endings(
        self,
        surah_number: int,
    ) -> VerseEndingPattern:
        """
        Analyze verse ending patterns (فواصل).

        The فواصل are the endings of verses which often follow
        specific phonetic patterns, especially in Meccan surahs.
        """
        verses = await self._repo.get_verses_by_surah(surah_number)

        ending_patterns: Dict[str, List[int]] = {}

        for verse in verses:
            words = verse.text_normalized.split()
            if not words:
                continue

            last_word = words[-1]
            # Extract ending pattern (last 2-3 characters)
            if len(last_word) >= 2:
                pattern = last_word[-2:]
                ending_patterns.setdefault(pattern, []).append(verse.location.verse_number)

        # Find most common ending
        most_common = max(ending_patterns.items(), key=lambda x: len(x[1]))

        # Calculate rhyme consistency
        max_pattern_count = len(most_common[1])
        total_verses = len(verses)
        consistency = max_pattern_count / total_verses if total_verses > 0 else 0

        return VerseEndingPattern(
            surah_number=surah_number,
            total_verses=total_verses,
            ending_patterns=ending_patterns,
            most_common_ending=most_common[0],
            rhyme_consistency=consistency,
        )

    async def compute_symmetry_score(
        self,
        surah_number: int,
        center_verse: int,
    ) -> SymmetryAnalysis:
        """
        Compute how symmetrically verses mirror around a proposed center.

        For ring composition, verses at positions (center - k) and (center + k)
        should have thematic/lexical similarity.

        Args:
            surah_number: Surah to analyze
            center_verse: Proposed center verse number

        Returns:
            Analysis with symmetry score and verse pairings
        """
        verses = await self._repo.get_verses_by_surah(surah_number)
        n = len(verses)

        if center_verse < 1 or center_verse > n:
            raise ValueError(f"Invalid center verse: {center_verse}")

        # Compute similarity for mirrored pairs
        verse_pairs = []
        total_similarity = 0
        pair_count = 0

        # How many verses on each side of center
        before_center = center_verse - 1
        after_center = n - center_verse

        # Pair verses symmetrically
        max_pairs = min(before_center, after_center)

        for k in range(1, max_pairs + 1):
            verse_before = center_verse - k
            verse_after = center_verse + k

            if verse_before >= 1 and verse_after <= n:
                v1 = verses[verse_before - 1]  # 0-indexed
                v2 = verses[verse_after - 1]

                similarity = self._lexical_similarity(v1, v2)
                total_similarity += similarity
                pair_count += 1

                verse_pairs.append({
                    'before': verse_before,
                    'after': verse_after,
                    'similarity': similarity,
                    'shared_words': self._get_shared_words(v1, v2),
                })

        symmetry_score = total_similarity / pair_count if pair_count > 0 else 0

        return SymmetryAnalysis(
            surah_number=surah_number,
            proposed_center=center_verse,
            symmetry_score=symmetry_score,
            verse_pairs=verse_pairs,
            thematic_matches=[],  # Would need manual annotation
        )

    def _lexical_similarity(self, verse1: Verse, verse2: Verse) -> float:
        """Compute Jaccard similarity of word sets."""
        words1 = set(verse1.text_normalized.split())
        words2 = set(verse2.text_normalized.split())

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0

    def _get_shared_words(self, verse1: Verse, verse2: Verse) -> List[str]:
        """Get words shared between two verses."""
        words1 = set(verse1.text_normalized.split())
        words2 = set(verse2.text_normalized.split())
        return list(words1 & words2)
```

---

## 7. Service Layer

### 7.1. Data Transfer Objects (DTOs)

```python
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

class AnalysisConfig(BaseModel):
    """Configuration for an analysis run."""

    model_config = {"strict": True}

    # Target configuration
    target_script: ScriptType = ScriptType.UTHMANI
    target_qiraat: QiraatType = QiraatType.HAFS_AN_ASIM

    # Pipeline configuration
    normalization_strategies: List[str] = Field(
        default_factory=lambda: ["remove_tashkeel", "remove_waqf"]
    )
    calculation_method: str

    # Scope configuration
    scope: Dict[str, Any] = Field(default_factory=dict)

    # Global options
    include_basmalah: bool = True

    @field_validator("normalization_strategies")
    @classmethod
    def validate_strategies(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one normalization strategy is required")
        return v


class VerseAnalysisRecord(BaseModel):
    """Result for a single verse."""
    location: str  # "2:255" format
    surah_name: str
    raw_text: str
    normalized_text: str
    result: Dict[str, Any]


class AnalysisResult(BaseModel):
    """Complete result of an analysis run."""

    # Identification
    analysis_id: UUID
    timestamp: datetime

    # Configuration used (for reproducibility)
    config: AnalysisConfig
    config_hash: str  # SHA-256 of serialized config

    # Results
    verse_count: int
    records: List[VerseAnalysisRecord]
    aggregate: Dict[str, Any]

    # Audit
    audit_receipt: 'AuditReceipt'

    # Performance
    execution_time_ms: float


class AuditReceipt(BaseModel):
    """Cryptographic receipt for audit trail."""

    receipt_id: UUID
    timestamp: datetime

    # What was analyzed
    scope_description: str
    verse_count: int

    # How it was analyzed
    script_type: str
    qiraat_type: str
    normalization_pipeline: List[str]
    calculation_method: str

    # Data integrity
    source_data_checksum: str  # Hash of input verses
    result_checksum: str       # Hash of results

    # Signature (for future HSM integration)
    signature: Optional[str] = None
```

### 7.2. Application Service

```python
from uuid import uuid4
from datetime import datetime
import hashlib
import json
import time

class MizanAnalyzerService:
    """
    Application service that orchestrates analysis operations.
    This is the main entry point for all analysis use cases.
    """

    def __init__(
        self,
        repository: IQuranRepository,
        strategy_factory: StrategyFactory,
        cache: Optional['IAnalysisCache'] = None,
    ):
        self._repo = repository
        self._factory = strategy_factory
        self._cache = cache

    async def execute_analysis(self, config: AnalysisConfig) -> AnalysisResult:
        """
        Execute a complete analysis pipeline.

        Steps:
        1. Check cache for existing result
        2. Fetch verses from repository
        3. Apply scope filtering
        4. Build normalization pipeline
        5. Process each verse through pipeline
        6. Aggregate results
        7. Generate audit receipt
        8. Cache result
        """
        start_time = time.perf_counter()
        analysis_id = uuid4()

        # Generate config hash for caching and reproducibility
        config_hash = self._hash_config(config)

        # Check cache
        if self._cache:
            cached = await self._cache.get(config_hash)
            if cached:
                return cached

        # 1. Fetch all verses
        all_verses = await self._repo.get_all_verses()

        # 2. Apply scope filtering
        scope_spec = self._factory.build_scope(config.scope)
        filtered_verses = [v for v in all_verses if scope_spec.is_satisfied_by(v)]

        # 3. Handle Basmalah exclusion
        if not config.include_basmalah:
            filtered_verses = self._exclude_basmalahs(filtered_verses)

        # 4. Build pipeline
        norm_strategies = [
            self._factory.get_normalization(name)
            for name in config.normalization_strategies
        ]
        calc_strategy = self._factory.get_calculation(config.calculation_method)

        # 5. Process verses
        records: List[VerseAnalysisRecord] = []
        source_texts: List[str] = []

        for verse in filtered_verses:
            # Get text for specified script and Qira'at
            raw_text = verse.get_text(config.target_script, config.target_qiraat)
            source_texts.append(raw_text)

            # Apply normalization pipeline
            normalized_text = raw_text
            for strategy in norm_strategies:
                normalized_text = strategy.normalize(normalized_text)

            # Calculate
            result = calc_strategy.calculate(normalized_text)

            records.append(VerseAnalysisRecord(
                location=str(verse.location),
                surah_name=verse.surah_metadata.name_arabic,
                raw_text=raw_text,
                normalized_text=normalized_text,
                result=result
            ))

        # 6. Aggregate results
        aggregate = self._aggregate_results(records, calc_strategy.name)

        # 7. Generate audit receipt
        source_checksum = self._hash_texts(source_texts)
        result_checksum = self._hash_results(records)

        audit_receipt = AuditReceipt(
            receipt_id=uuid4(),
            timestamp=datetime.utcnow(),
            scope_description=self._describe_scope(config.scope),
            verse_count=len(filtered_verses),
            script_type=config.target_script.value,
            qiraat_type=config.target_qiraat.value,
            normalization_pipeline=config.normalization_strategies,
            calculation_method=config.calculation_method,
            source_data_checksum=source_checksum,
            result_checksum=result_checksum,
        )

        execution_time = (time.perf_counter() - start_time) * 1000

        result = AnalysisResult(
            analysis_id=analysis_id,
            timestamp=datetime.utcnow(),
            config=config,
            config_hash=config_hash,
            verse_count=len(filtered_verses),
            records=records,
            aggregate=aggregate,
            audit_receipt=audit_receipt,
            execution_time_ms=execution_time,
        )

        # 8. Cache result
        if self._cache:
            await self._cache.set(config_hash, result)

        return result

    def _exclude_basmalahs(self, verses: List[Verse]) -> List[Verse]:
        """
        Exclude Basmalah verses based on scholarly rules.

        - Al-Fatiha 1:1 is the Basmalah (counted as verse) - EXCLUDE
        - At-Tawbah has no Basmalah - nothing to exclude
        - Other Surahs: Basmalah is not numbered, already excluded
        - An-Naml 27:30 contains Basmalah WITHIN verse - KEEP (it's part of the verse)
        """
        return [
            v for v in verses
            if not (v.location.surah_number == 1 and v.location.verse_number == 1)
        ]

    def _aggregate_results(
        self,
        records: List[VerseAnalysisRecord],
        calculation_type: str
    ) -> Dict[str, Any]:
        """Aggregate individual verse results."""
        if not records:
            return {"total": 0, "count": 0}

        # Extract numeric values from results
        values: List[int] = []
        for record in records:
            result = record.result
            if "count" in result:
                values.append(result["count"])
            elif "value" in result:
                values.append(result["value"])

        if not values:
            return {"verse_count": len(records)}

        import statistics

        aggregate = {
            "verse_count": len(records),
            "total": sum(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
        }

        # Add letter frequency aggregation if applicable
        if calculation_type == "letter_frequency":
            combined_freq: Dict[str, int] = {}
            for record in records:
                for letter, count in record.result.get("frequencies", {}).items():
                    combined_freq[letter] = combined_freq.get(letter, 0) + count
            aggregate["combined_frequency"] = combined_freq

        return aggregate

    @staticmethod
    def _hash_config(config: AnalysisConfig) -> str:
        """Generate deterministic hash of configuration."""
        config_json = config.model_dump_json(exclude_none=True)
        return hashlib.sha256(config_json.encode()).hexdigest()

    @staticmethod
    def _hash_texts(texts: List[str]) -> str:
        """Hash list of source texts."""
        combined = "\n".join(texts)
        return hashlib.sha256(combined.encode()).hexdigest()

    @staticmethod
    def _hash_results(records: List[VerseAnalysisRecord]) -> str:
        """Hash analysis results."""
        data = json.dumps([r.model_dump() for r in records], sort_keys=True, default=str)
        return hashlib.sha256(data.encode()).hexdigest()

    @staticmethod
    def _describe_scope(scope: Dict[str, Any]) -> str:
        """Generate human-readable scope description."""
        if not scope:
            return "Entire Quran"

        parts = []
        if "surah" in scope:
            parts.append(f"Surah {scope['surah']}")
        if "surah_range" in scope:
            parts.append(f"Surahs {scope['surah_range'][0]}-{scope['surah_range'][1]}")
        if "revelation_type" in scope:
            parts.append(f"{scope['revelation_type'].title()} verses")
        if "juz" in scope:
            parts.append(f"Juz {scope['juz']}")
        if scope.get("exclude_basmalah"):
            parts.append("(excluding Basmalah)")

        return ", ".join(parts) if parts else "Custom scope"
```

---

## 8. Data Ingestion & Integrity

### 8.1. Available Data Sources

The project uses Tanzil.net Quran Text (Version 1.1, February 2021) as the primary data source.

**Local File Structure:**

```
quran/
├── uthmani/
│   ├── quran-uthmani.xml       # PRIMARY SOURCE
│   ├── quran-uthmani.txt
│   ├── quran-uthmani-aya.txt
│   └── quran-uthmani.sql
├── uthmani-min/
│   ├── quran-uthmani-min.xml   # SECONDARY SOURCE
│   ├── quran-uthmani-min.txt
│   ├── quran-uthmani-min-aya.txt
│   └── quran-uthmani-min.sql
└── simple/
    ├── quran-simple.xml        # TERTIARY SOURCE
    ├── quran-simple.txt
    ├── quran-simple-aya.txt
    └── quran-simple.sql
```

**Download Configuration Used:**
- Pause marks: Included (ۛ ۖ ۗ ۘ ۙ ۚ)
- Sajdah signs (۩): Included
- Rub-el-hizb signs (۞): Included
- Tatweel below superscript alefs: Included (الرَّحْمَـٰن)

### 8.2. Tanzil XML Structure

The XML files follow this structure:

```xml
<?xml version="1.0" encoding="utf-8" ?>
<quran>
    <sura index="1" name="الفاتحة">
        <aya index="1" text="بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ" />
        <aya index="2" text="ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَـٰلَمِينَ" />
        <!-- ... -->
    </sura>
    <sura index="2" name="البقرة">
        <!-- Note: bismillah attribute for Surahs 2-114 (except 9) -->
        <aya index="1" text="الٓمٓ" bismillah="بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ" />
        <aya index="2" text="ذَٰلِكَ ٱلْكِتَـٰبُ لَا رَيْبَ ۛ فِيهِ ۛ هُدًۭى لِّلْمُتَّقِينَ" />
        <!-- ... -->
    </sura>
</quran>
```

**Key XML Attributes:**
- `sura@index`: Surah number (1-114)
- `sura@name`: Arabic name of the Surah
- `aya@index`: Verse number within Surah
- `aya@text`: Verse text content
- `aya@bismillah`: Basmalah text (only on first verse of Surahs 2-114, except 9)

### 8.3. Reference Data for Entity Analysis

```python
from typing import Final, Dict, List, Set

# =============================================================================
# DIVINE NAMES (أسماء الله الحسنى)
# =============================================================================
# The 99 Beautiful Names of Allah as mentioned in Quran and Hadith
# Reference: Various scholarly compilations, most notably from Sahih al-Bukhari

DIVINE_NAMES: Final[Dict[str, Dict[str, Any]]] = {
    "الله": {"transliteration": "Allah", "meaning": "The God", "root": "أ-ل-ه"},
    "الرحمن": {"transliteration": "Ar-Rahman", "meaning": "The Most Gracious", "root": "ر-ح-م"},
    "الرحيم": {"transliteration": "Ar-Raheem", "meaning": "The Most Merciful", "root": "ر-ح-م"},
    "الملك": {"transliteration": "Al-Malik", "meaning": "The King", "root": "م-ل-ك"},
    "القدوس": {"transliteration": "Al-Quddus", "meaning": "The Holy", "root": "ق-د-س"},
    "السلام": {"transliteration": "As-Salam", "meaning": "The Peace", "root": "س-ل-م"},
    "المؤمن": {"transliteration": "Al-Mu'min", "meaning": "The Guardian of Faith", "root": "أ-م-ن"},
    "المهيمن": {"transliteration": "Al-Muhaymin", "meaning": "The Protector", "root": "ه-م-ن"},
    "العزيز": {"transliteration": "Al-Aziz", "meaning": "The Mighty", "root": "ع-ز-ز"},
    "الجبار": {"transliteration": "Al-Jabbar", "meaning": "The Compeller", "root": "ج-ب-ر"},
    "المتكبر": {"transliteration": "Al-Mutakabbir", "meaning": "The Supreme", "root": "ك-ب-ر"},
    "الخالق": {"transliteration": "Al-Khaliq", "meaning": "The Creator", "root": "خ-ل-ق"},
    "البارئ": {"transliteration": "Al-Bari", "meaning": "The Evolver", "root": "ب-ر-أ"},
    "المصور": {"transliteration": "Al-Musawwir", "meaning": "The Fashioner", "root": "ص-و-ر"},
    "الغفار": {"transliteration": "Al-Ghaffar", "meaning": "The Forgiver", "root": "غ-ف-ر"},
    "القهار": {"transliteration": "Al-Qahhar", "meaning": "The Subduer", "root": "ق-ه-ر"},
    "الوهاب": {"transliteration": "Al-Wahhab", "meaning": "The Bestower", "root": "و-ه-ب"},
    "الرزاق": {"transliteration": "Ar-Razzaq", "meaning": "The Provider", "root": "ر-ز-ق"},
    "الفتاح": {"transliteration": "Al-Fattah", "meaning": "The Opener", "root": "ف-ت-ح"},
    "العليم": {"transliteration": "Al-Alim", "meaning": "The All-Knowing", "root": "ع-ل-م"},
    "القابض": {"transliteration": "Al-Qabid", "meaning": "The Constrictor", "root": "ق-ب-ض"},
    "الباسط": {"transliteration": "Al-Basit", "meaning": "The Expander", "root": "ب-س-ط"},
    "الخافض": {"transliteration": "Al-Khafid", "meaning": "The Abaser", "root": "خ-ف-ض"},
    "الرافع": {"transliteration": "Ar-Rafi", "meaning": "The Exalter", "root": "ر-ف-ع"},
    "المعز": {"transliteration": "Al-Mu'izz", "meaning": "The Honorer", "root": "ع-ز-ز"},
    "المذل": {"transliteration": "Al-Mudhill", "meaning": "The Humiliator", "root": "ذ-ل-ل"},
    "السميع": {"transliteration": "As-Sami", "meaning": "The All-Hearing", "root": "س-م-ع"},
    "البصير": {"transliteration": "Al-Basir", "meaning": "The All-Seeing", "root": "ب-ص-ر"},
    "الحكم": {"transliteration": "Al-Hakam", "meaning": "The Judge", "root": "ح-ك-م"},
    "العدل": {"transliteration": "Al-Adl", "meaning": "The Just", "root": "ع-د-ل"},
    "اللطيف": {"transliteration": "Al-Latif", "meaning": "The Subtle", "root": "ل-ط-ف"},
    "الخبير": {"transliteration": "Al-Khabir", "meaning": "The Aware", "root": "خ-ب-ر"},
    "الحليم": {"transliteration": "Al-Halim", "meaning": "The Forbearing", "root": "ح-ل-م"},
    "العظيم": {"transliteration": "Al-Azim", "meaning": "The Magnificent", "root": "ع-ظ-م"},
    "الغفور": {"transliteration": "Al-Ghafur", "meaning": "The Forgiving", "root": "غ-ف-ر"},
    "الشكور": {"transliteration": "Ash-Shakur", "meaning": "The Appreciative", "root": "ش-ك-ر"},
    "العلي": {"transliteration": "Al-Ali", "meaning": "The High", "root": "ع-ل-و"},
    "الكبير": {"transliteration": "Al-Kabir", "meaning": "The Great", "root": "ك-ب-ر"},
    "الحفيظ": {"transliteration": "Al-Hafiz", "meaning": "The Preserver", "root": "ح-ف-ظ"},
    "المقيت": {"transliteration": "Al-Muqit", "meaning": "The Nourisher", "root": "ق-و-ت"},
    "الحسيب": {"transliteration": "Al-Hasib", "meaning": "The Reckoner", "root": "ح-س-ب"},
    "الجليل": {"transliteration": "Al-Jalil", "meaning": "The Majestic", "root": "ج-ل-ل"},
    "الكريم": {"transliteration": "Al-Karim", "meaning": "The Generous", "root": "ك-ر-م"},
    "الرقيب": {"transliteration": "Ar-Raqib", "meaning": "The Watchful", "root": "ر-ق-ب"},
    "المجيب": {"transliteration": "Al-Mujib", "meaning": "The Responsive", "root": "ج-و-ب"},
    "الواسع": {"transliteration": "Al-Wasi", "meaning": "The Vast", "root": "و-س-ع"},
    "الحكيم": {"transliteration": "Al-Hakim", "meaning": "The Wise", "root": "ح-ك-م"},
    "الودود": {"transliteration": "Al-Wadud", "meaning": "The Loving", "root": "و-د-د"},
    "المجيد": {"transliteration": "Al-Majid", "meaning": "The Glorious", "root": "م-ج-د"},
    "الباعث": {"transliteration": "Al-Ba'ith", "meaning": "The Resurrector", "root": "ب-ع-ث"},
    "الشهيد": {"transliteration": "Ash-Shahid", "meaning": "The Witness", "root": "ش-ه-د"},
    "الحق": {"transliteration": "Al-Haqq", "meaning": "The Truth", "root": "ح-ق-ق"},
    "الوكيل": {"transliteration": "Al-Wakil", "meaning": "The Trustee", "root": "و-ك-ل"},
    "القوي": {"transliteration": "Al-Qawi", "meaning": "The Strong", "root": "ق-و-ي"},
    "المتين": {"transliteration": "Al-Matin", "meaning": "The Firm", "root": "م-ت-ن"},
    "الولي": {"transliteration": "Al-Wali", "meaning": "The Protecting Friend", "root": "و-ل-ي"},
    "الحميد": {"transliteration": "Al-Hamid", "meaning": "The Praiseworthy", "root": "ح-م-د"},
    # ... remaining names follow same pattern
}

# =============================================================================
# PROPHETS MENTIONED IN QURAN (الأنبياء)
# =============================================================================
# 25 Prophets explicitly named in the Quran

PROPHETS: Final[Dict[str, Dict[str, Any]]] = {
    "آدم": {"transliteration": "Adam", "mentions": 25, "surah_first": 2},
    "إدريس": {"transliteration": "Idris", "mentions": 2, "surah_first": 19},
    "نوح": {"transliteration": "Nuh (Noah)", "mentions": 43, "surah_first": 3},
    "هود": {"transliteration": "Hud", "mentions": 7, "surah_first": 7},
    "صالح": {"transliteration": "Salih", "mentions": 9, "surah_first": 7},
    "إبراهيم": {"transliteration": "Ibrahim (Abraham)", "mentions": 69, "surah_first": 2},
    "لوط": {"transliteration": "Lut (Lot)", "mentions": 27, "surah_first": 6},
    "إسماعيل": {"transliteration": "Ismail (Ishmael)", "mentions": 12, "surah_first": 2},
    "إسحاق": {"transliteration": "Ishaq (Isaac)", "mentions": 17, "surah_first": 2},
    "يعقوب": {"transliteration": "Yaqub (Jacob)", "mentions": 16, "surah_first": 2},
    "يوسف": {"transliteration": "Yusuf (Joseph)", "mentions": 27, "surah_first": 6},
    "أيوب": {"transliteration": "Ayyub (Job)", "mentions": 4, "surah_first": 4},
    "شعيب": {"transliteration": "Shu'ayb", "mentions": 11, "surah_first": 7},
    "موسى": {"transliteration": "Musa (Moses)", "mentions": 136, "surah_first": 2},
    "هارون": {"transliteration": "Harun (Aaron)", "mentions": 20, "surah_first": 2},
    "ذو الكفل": {"transliteration": "Dhul-Kifl", "mentions": 2, "surah_first": 21},
    "داود": {"transliteration": "Dawud (David)", "mentions": 16, "surah_first": 2},
    "سليمان": {"transliteration": "Sulayman (Solomon)", "mentions": 17, "surah_first": 2},
    "إلياس": {"transliteration": "Ilyas (Elijah)", "mentions": 2, "surah_first": 6},
    "اليسع": {"transliteration": "Al-Yasa (Elisha)", "mentions": 2, "surah_first": 6},
    "يونس": {"transliteration": "Yunus (Jonah)", "mentions": 4, "surah_first": 4},
    "زكريا": {"transliteration": "Zakariya (Zechariah)", "mentions": 7, "surah_first": 3},
    "يحيى": {"transliteration": "Yahya (John)", "mentions": 5, "surah_first": 3},
    "عيسى": {"transliteration": "Isa (Jesus)", "mentions": 25, "surah_first": 2},
    "محمد": {"transliteration": "Muhammad", "mentions": 4, "surah_first": 3},  # Also أحمد in 61:6
}

# =============================================================================
# ANGELS (الملائكة)
# =============================================================================

ANGELS: Final[Dict[str, Dict[str, Any]]] = {
    "جبريل": {"transliteration": "Jibril (Gabriel)", "role": "Revelation", "mentions": 3},
    "ميكائيل": {"transliteration": "Mikail (Michael)", "role": "Provisions", "mentions": 1},
    "مالك": {"transliteration": "Malik", "role": "Guardian of Hell", "mentions": 1},
    "هاروت": {"transliteration": "Harut", "role": "Test in Babylon", "mentions": 1},
    "ماروت": {"transliteration": "Marut", "role": "Test in Babylon", "mentions": 1},
}

# =============================================================================
# SIGNIFICANT PLACES (الأماكن)
# =============================================================================

PLACES: Final[Dict[str, Dict[str, Any]]] = {
    "مكة": {"transliteration": "Makkah", "also_called": ["بكة"], "mentions": 1},
    "بكة": {"transliteration": "Bakkah", "same_as": "مكة", "mentions": 1},
    "المدينة": {"transliteration": "Al-Madinah", "also_called": ["يثرب"], "mentions": 4},
    "يثرب": {"transliteration": "Yathrib", "same_as": "المدينة", "mentions": 1},
    "مصر": {"transliteration": "Misr (Egypt)", "mentions": 5},
    "بابل": {"transliteration": "Babylon", "mentions": 1},
    "سيناء": {"transliteration": "Sinai", "also_called": ["طور سينين"], "mentions": 2},
    "الأرض المقدسة": {"transliteration": "The Holy Land", "mentions": 1},
    "سبأ": {"transliteration": "Saba (Sheba)", "mentions": 2},
    "الأحقاف": {"transliteration": "Al-Ahqaf", "mentions": 1},
    "الحجر": {"transliteration": "Al-Hijr", "mentions": 1},
    "مدين": {"transliteration": "Madyan (Midian)", "mentions": 3},
    "الجودي": {"transliteration": "Al-Judi", "role": "Where Ark rested", "mentions": 1},
    "بدر": {"transliteration": "Badr", "mentions": 1},
    "حنين": {"transliteration": "Hunayn", "mentions": 1},
}

# =============================================================================
# NATIONS & PEOPLES (الأقوام)
# =============================================================================

PEOPLES: Final[Dict[str, Dict[str, Any]]] = {
    "بني إسرائيل": {"transliteration": "Bani Isra'il", "mentions": 43},
    "قريش": {"transliteration": "Quraysh", "mentions": 1},
    "عاد": {"transliteration": "Aad", "prophet": "هود", "mentions": 24},
    "ثمود": {"transliteration": "Thamud", "prophet": "صالح", "mentions": 26},
    "أصحاب الأيكة": {"transliteration": "People of the Wood", "prophet": "شعيب", "mentions": 4},
    "أصحاب مدين": {"transliteration": "People of Madyan", "prophet": "شعيب", "mentions": 3},
    "قوم لوط": {"transliteration": "People of Lut", "mentions": 13},
    "قوم نوح": {"transliteration": "People of Nuh", "mentions": 8},
    "قوم فرعون": {"transliteration": "People of Pharaoh", "mentions": 9},
    "أصحاب الرس": {"transliteration": "People of Ar-Rass", "mentions": 2},
    "أصحاب الكهف": {"transliteration": "People of the Cave", "mentions": 1},
    "أصحاب الفيل": {"transliteration": "People of the Elephant", "mentions": 1},
    "الروم": {"transliteration": "Romans", "mentions": 1},
    "يأجوج ومأجوج": {"transliteration": "Gog and Magog", "mentions": 2},
}

# =============================================================================
# NUMBER WORDS (الأعداد)
# =============================================================================

NUMBER_WORDS: Final[Dict[str, Dict[str, Any]]] = {
    "واحد": {"value": 1, "variants": ["أحد", "واحدة"]},
    "اثنان": {"value": 2, "variants": ["اثنين", "اثنتان", "اثنتين"]},
    "ثلاثة": {"value": 3, "variants": ["ثلاث"]},
    "أربعة": {"value": 4, "variants": ["أربع"]},
    "خمسة": {"value": 5, "variants": ["خمس"]},
    "ستة": {"value": 6, "variants": ["ست"]},
    "سبعة": {"value": 7, "variants": ["سبع"]},
    "ثمانية": {"value": 8, "variants": ["ثمان", "ثماني"]},
    "تسعة": {"value": 9, "variants": ["تسع"]},
    "عشرة": {"value": 10, "variants": ["عشر"]},
    "أحد عشر": {"value": 11, "variants": []},
    "اثنا عشر": {"value": 12, "variants": ["اثني عشر"]},
    "تسعة عشر": {"value": 19, "variants": []},
    "عشرون": {"value": 20, "variants": ["عشرين"]},
    "ثلاثون": {"value": 30, "variants": ["ثلاثين"]},
    "أربعون": {"value": 40, "variants": ["أربعين"]},
    "خمسون": {"value": 50, "variants": ["خمسين"]},
    "ستون": {"value": 60, "variants": ["ستين"]},
    "سبعون": {"value": 70, "variants": ["سبعين"]},
    "ثمانون": {"value": 80, "variants": ["ثمانين"]},
    "تسعون": {"value": 90, "variants": []},
    "مائة": {"value": 100, "variants": ["مئة"]},
    "ألف": {"value": 1000, "variants": []},
    "ألفين": {"value": 2000, "variants": []},
    "خمسين ألف": {"value": 50000, "variants": []},
    "مائة ألف": {"value": 100000, "variants": []},
}

# =============================================================================
# WORD PAIRS FOR COMPARISON (الكلمات المتقابلة)
# =============================================================================
# Famous pairs often cited in numerical analysis

WORD_PAIRS: Final[List[Dict[str, Any]]] = [
    {"word1": "الدنيا", "word2": "الآخرة", "claim": "Equal count"},
    {"word1": "الحياة", "word2": "الموت", "claim": "Equal count"},
    {"word1": "النفع", "word2": "الفساد", "claim": "Equal count"},
    {"word1": "الملائكة", "word2": "الشياطين", "claim": "Equal count"},
    {"word1": "الرجل", "word2": "المرأة", "claim": "Equal count"},
    {"word1": "الصالحات", "word2": "السيئات", "claim": "Equal count"},
    {"word1": "يوم", "word2": None, "claim": "365 occurrences"},
    {"word1": "شهر", "word2": None, "claim": "12 occurrences"},
    {"word1": "قل", "word2": None, "claim": "332 occurrences"},
]

# =============================================================================
# SAJDAH VERSES (آيات السجدة)
# =============================================================================
# The 15 verses requiring prostration (سجدة التلاوة)

SAJDAH_VERSES: Final[List[tuple[int, int]]] = [
    (7, 206),    # Al-A'raf
    (13, 15),    # Ar-Ra'd
    (16, 50),    # An-Nahl
    (17, 109),   # Al-Isra
    (19, 58),    # Maryam
    (22, 18),    # Al-Hajj
    (22, 77),    # Al-Hajj (second)
    (25, 60),    # Al-Furqan
    (27, 26),    # An-Naml
    (32, 15),    # As-Sajdah
    (38, 24),    # Sad
    (41, 38),    # Fussilat
    (53, 62),    # An-Najm
    (84, 21),    # Al-Inshiqaq
    (96, 19),    # Al-Alaq
]
```

### 8.4. Sealed Ingestion Pipeline

The Quranic text is **never** manually entered. All data comes through a verified pipeline.

```python
from pathlib import Path
from dataclasses import dataclass
import hashlib
import xml.etree.ElementTree as ET

@dataclass(frozen=True)
class IngestionSource:
    """Verified source for Quranic text."""
    name: str
    file_path: Path
    script_type: ScriptType
    expected_sha256: str
    version: str


# Local sources with their verified checksums
VERIFIED_SOURCES: Dict[str, IngestionSource] = {
    "tanzil_uthmani": IngestionSource(
        name="Tanzil.net Uthmani",
        file_path=Path("quran/uthmani/quran-uthmani.xml"),
        script_type=ScriptType.UTHMANI,
        expected_sha256="<COMPUTE_ON_FIRST_INGESTION>",
        version="1.1",
    ),
    "tanzil_uthmani_min": IngestionSource(
        name="Tanzil.net Uthmani Minimal",
        file_path=Path("quran/uthmani-min/quran-uthmani-min.xml"),
        script_type=ScriptType.UTHMANI_MINIMAL,
        expected_sha256="<COMPUTE_ON_FIRST_INGESTION>",
        version="1.1",
    ),
    "tanzil_simple": IngestionSource(
        name="Tanzil.net Simple",
        file_path=Path("quran/simple/quran-simple.xml"),
        script_type=ScriptType.SIMPLE,
        expected_sha256="<COMPUTE_ON_FIRST_INGESTION>",
        version="1.1",
    ),
}


class QuranIngestionService:
    """
    Handles secure ingestion of Quranic text data.

    Security measures:
    1. Verify file checksum before processing
    2. Parse with secure XML parser (no external entities)
    3. Validate all verse counts match expected values
    4. Generate content checksums for future verification
    """

    EXPECTED_VERSE_COUNTS: Final[Dict[int, int]] = {
        1: 7, 2: 286, 3: 200, 4: 176, 5: 120, 6: 165, 7: 206, 8: 75,
        9: 129, 10: 109, 11: 123, 12: 111, 13: 43, 14: 52, 15: 99,
        16: 128, 17: 111, 18: 110, 19: 98, 20: 135, 21: 112, 22: 78,
        23: 118, 24: 64, 25: 77, 26: 227, 27: 93, 28: 88, 29: 69,
        30: 60, 31: 34, 32: 30, 33: 73, 34: 54, 35: 45, 36: 83,
        37: 182, 38: 88, 39: 75, 40: 85, 41: 54, 42: 53, 43: 89,
        44: 59, 45: 37, 46: 35, 47: 38, 48: 29, 49: 18, 50: 45,
        51: 60, 52: 49, 53: 62, 54: 55, 55: 78, 56: 96, 57: 29,
        58: 22, 59: 24, 60: 13, 61: 14, 62: 11, 63: 11, 64: 18,
        65: 12, 66: 12, 67: 30, 68: 52, 69: 52, 70: 44, 71: 28,
        72: 28, 73: 20, 74: 56, 75: 40, 76: 31, 77: 50, 78: 40,
        79: 46, 80: 42, 81: 29, 82: 19, 83: 36, 84: 25, 85: 22,
        86: 17, 87: 19, 88: 26, 89: 30, 90: 20, 91: 15, 92: 21,
        93: 11, 94: 8, 95: 8, 96: 19, 97: 5, 98: 8, 99: 8,
        100: 11, 101: 11, 102: 8, 103: 3, 104: 9, 105: 5, 106: 4,
        107: 7, 108: 3, 109: 6, 110: 3, 111: 5, 112: 4, 113: 5, 114: 6,
    }

    TOTAL_VERSES: Final[int] = 6236
    TOTAL_SURAHS: Final[int] = 114

    # Complete Surah metadata for seeding database
    # Source: King Fahd Complex, Tanzil.net, scholarly consensus
    SURAH_METADATA: Final[List[Dict[str, Any]]] = [
        # num, arabic, english, transliteration, rev_type, rev_order, verses, basmalah, ruku
        {"num": 1, "ar": "الفاتحة", "en": "Al-Fatihah", "tr": "Al-Fatihah", "rev": "meccan", "order": 5, "verses": 7, "basmalah": "numbered_verse", "ruku": 1},
        {"num": 2, "ar": "البقرة", "en": "Al-Baqarah", "tr": "Al-Baqarah", "rev": "medinan", "order": 87, "verses": 286, "basmalah": "opening_unnumbered", "ruku": 40},
        {"num": 3, "ar": "آل عمران", "en": "Aal-i-Imraan", "tr": "Ali 'Imran", "rev": "medinan", "order": 89, "verses": 200, "basmalah": "opening_unnumbered", "ruku": 20},
        {"num": 4, "ar": "النساء", "en": "An-Nisaa", "tr": "An-Nisa", "rev": "medinan", "order": 92, "verses": 176, "basmalah": "opening_unnumbered", "ruku": 24},
        {"num": 5, "ar": "المائدة", "en": "Al-Maaidah", "tr": "Al-Ma'idah", "rev": "medinan", "order": 112, "verses": 120, "basmalah": "opening_unnumbered", "ruku": 16},
        {"num": 6, "ar": "الأنعام", "en": "Al-An'aam", "tr": "Al-An'am", "rev": "meccan", "order": 55, "verses": 165, "basmalah": "opening_unnumbered", "ruku": 20},
        {"num": 7, "ar": "الأعراف", "en": "Al-A'raaf", "tr": "Al-A'raf", "rev": "meccan", "order": 39, "verses": 206, "basmalah": "opening_unnumbered", "ruku": 24},
        {"num": 8, "ar": "الأنفال", "en": "Al-Anfaal", "tr": "Al-Anfal", "rev": "medinan", "order": 88, "verses": 75, "basmalah": "opening_unnumbered", "ruku": 10},
        {"num": 9, "ar": "التوبة", "en": "At-Tawbah", "tr": "At-Tawbah", "rev": "medinan", "order": 113, "verses": 129, "basmalah": "absent", "ruku": 16},
        {"num": 10, "ar": "يونس", "en": "Yunus", "tr": "Yunus", "rev": "meccan", "order": 51, "verses": 109, "basmalah": "opening_unnumbered", "ruku": 11},
        {"num": 11, "ar": "هود", "en": "Hud", "tr": "Hud", "rev": "meccan", "order": 52, "verses": 123, "basmalah": "opening_unnumbered", "ruku": 10},
        {"num": 12, "ar": "يوسف", "en": "Yusuf", "tr": "Yusuf", "rev": "meccan", "order": 53, "verses": 111, "basmalah": "opening_unnumbered", "ruku": 12},
        {"num": 13, "ar": "الرعد", "en": "Ar-Ra'd", "tr": "Ar-Ra'd", "rev": "medinan", "order": 96, "verses": 43, "basmalah": "opening_unnumbered", "ruku": 6},
        {"num": 14, "ar": "إبراهيم", "en": "Ibrahim", "tr": "Ibrahim", "rev": "meccan", "order": 72, "verses": 52, "basmalah": "opening_unnumbered", "ruku": 7},
        {"num": 15, "ar": "الحجر", "en": "Al-Hijr", "tr": "Al-Hijr", "rev": "meccan", "order": 54, "verses": 99, "basmalah": "opening_unnumbered", "ruku": 6},
        {"num": 16, "ar": "النحل", "en": "An-Nahl", "tr": "An-Nahl", "rev": "meccan", "order": 70, "verses": 128, "basmalah": "opening_unnumbered", "ruku": 16},
        {"num": 17, "ar": "الإسراء", "en": "Al-Israa", "tr": "Al-Isra", "rev": "meccan", "order": 50, "verses": 111, "basmalah": "opening_unnumbered", "ruku": 12},
        {"num": 18, "ar": "الكهف", "en": "Al-Kahf", "tr": "Al-Kahf", "rev": "meccan", "order": 69, "verses": 110, "basmalah": "opening_unnumbered", "ruku": 12},
        {"num": 19, "ar": "مريم", "en": "Maryam", "tr": "Maryam", "rev": "meccan", "order": 44, "verses": 98, "basmalah": "opening_unnumbered", "ruku": 6},
        {"num": 20, "ar": "طه", "en": "Taa-Haa", "tr": "Ta-Ha", "rev": "meccan", "order": 45, "verses": 135, "basmalah": "opening_unnumbered", "ruku": 8},
        {"num": 21, "ar": "الأنبياء", "en": "Al-Anbiyaa", "tr": "Al-Anbiya", "rev": "meccan", "order": 73, "verses": 112, "basmalah": "opening_unnumbered", "ruku": 7},
        {"num": 22, "ar": "الحج", "en": "Al-Hajj", "tr": "Al-Hajj", "rev": "medinan", "order": 103, "verses": 78, "basmalah": "opening_unnumbered", "ruku": 10},
        {"num": 23, "ar": "المؤمنون", "en": "Al-Muminoon", "tr": "Al-Mu'minun", "rev": "meccan", "order": 74, "verses": 118, "basmalah": "opening_unnumbered", "ruku": 6},
        {"num": 24, "ar": "النور", "en": "An-Noor", "tr": "An-Nur", "rev": "medinan", "order": 102, "verses": 64, "basmalah": "opening_unnumbered", "ruku": 9},
        {"num": 25, "ar": "الفرقان", "en": "Al-Furqaan", "tr": "Al-Furqan", "rev": "meccan", "order": 42, "verses": 77, "basmalah": "opening_unnumbered", "ruku": 6},
        {"num": 26, "ar": "الشعراء", "en": "Ash-Shu'araa", "tr": "Ash-Shu'ara", "rev": "meccan", "order": 47, "verses": 227, "basmalah": "opening_unnumbered", "ruku": 11},
        {"num": 27, "ar": "النمل", "en": "An-Naml", "tr": "An-Naml", "rev": "meccan", "order": 48, "verses": 93, "basmalah": "opening_unnumbered", "ruku": 7},
        {"num": 28, "ar": "القصص", "en": "Al-Qasas", "tr": "Al-Qasas", "rev": "meccan", "order": 49, "verses": 88, "basmalah": "opening_unnumbered", "ruku": 9},
        {"num": 29, "ar": "العنكبوت", "en": "Al-Ankaboot", "tr": "Al-'Ankabut", "rev": "meccan", "order": 85, "verses": 69, "basmalah": "opening_unnumbered", "ruku": 7},
        {"num": 30, "ar": "الروم", "en": "Ar-Room", "tr": "Ar-Rum", "rev": "meccan", "order": 84, "verses": 60, "basmalah": "opening_unnumbered", "ruku": 6},
        {"num": 31, "ar": "لقمان", "en": "Luqman", "tr": "Luqman", "rev": "meccan", "order": 57, "verses": 34, "basmalah": "opening_unnumbered", "ruku": 4},
        {"num": 32, "ar": "السجدة", "en": "As-Sajdah", "tr": "As-Sajdah", "rev": "meccan", "order": 75, "verses": 30, "basmalah": "opening_unnumbered", "ruku": 3},
        {"num": 33, "ar": "الأحزاب", "en": "Al-Ahzaab", "tr": "Al-Ahzab", "rev": "medinan", "order": 90, "verses": 73, "basmalah": "opening_unnumbered", "ruku": 9},
        {"num": 34, "ar": "سبأ", "en": "Saba", "tr": "Saba", "rev": "meccan", "order": 58, "verses": 54, "basmalah": "opening_unnumbered", "ruku": 6},
        {"num": 35, "ar": "فاطر", "en": "Faatir", "tr": "Fatir", "rev": "meccan", "order": 43, "verses": 45, "basmalah": "opening_unnumbered", "ruku": 5},
        {"num": 36, "ar": "يس", "en": "Yaseen", "tr": "Ya-Sin", "rev": "meccan", "order": 41, "verses": 83, "basmalah": "opening_unnumbered", "ruku": 5},
        {"num": 37, "ar": "الصافات", "en": "As-Saaffaat", "tr": "As-Saffat", "rev": "meccan", "order": 56, "verses": 182, "basmalah": "opening_unnumbered", "ruku": 5},
        {"num": 38, "ar": "ص", "en": "Saad", "tr": "Sad", "rev": "meccan", "order": 38, "verses": 88, "basmalah": "opening_unnumbered", "ruku": 5},
        {"num": 39, "ar": "الزمر", "en": "Az-Zumar", "tr": "Az-Zumar", "rev": "meccan", "order": 59, "verses": 75, "basmalah": "opening_unnumbered", "ruku": 8},
        {"num": 40, "ar": "غافر", "en": "Ghafir", "tr": "Ghafir", "rev": "meccan", "order": 60, "verses": 85, "basmalah": "opening_unnumbered", "ruku": 9},
        {"num": 41, "ar": "فصلت", "en": "Fussilat", "tr": "Fussilat", "rev": "meccan", "order": 61, "verses": 54, "basmalah": "opening_unnumbered", "ruku": 6},
        {"num": 42, "ar": "الشورى", "en": "Ash-Shura", "tr": "Ash-Shura", "rev": "meccan", "order": 62, "verses": 53, "basmalah": "opening_unnumbered", "ruku": 5},
        {"num": 43, "ar": "الزخرف", "en": "Az-Zukhruf", "tr": "Az-Zukhruf", "rev": "meccan", "order": 63, "verses": 89, "basmalah": "opening_unnumbered", "ruku": 7},
        {"num": 44, "ar": "الدخان", "en": "Ad-Dukhaan", "tr": "Ad-Dukhan", "rev": "meccan", "order": 64, "verses": 59, "basmalah": "opening_unnumbered", "ruku": 3},
        {"num": 45, "ar": "الجاثية", "en": "Al-Jaathiya", "tr": "Al-Jathiyah", "rev": "meccan", "order": 65, "verses": 37, "basmalah": "opening_unnumbered", "ruku": 4},
        {"num": 46, "ar": "الأحقاف", "en": "Al-Ahqaaf", "tr": "Al-Ahqaf", "rev": "meccan", "order": 66, "verses": 35, "basmalah": "opening_unnumbered", "ruku": 4},
        {"num": 47, "ar": "محمد", "en": "Muhammad", "tr": "Muhammad", "rev": "medinan", "order": 95, "verses": 38, "basmalah": "opening_unnumbered", "ruku": 4},
        {"num": 48, "ar": "الفتح", "en": "Al-Fath", "tr": "Al-Fath", "rev": "medinan", "order": 111, "verses": 29, "basmalah": "opening_unnumbered", "ruku": 4},
        {"num": 49, "ar": "الحجرات", "en": "Al-Hujuraat", "tr": "Al-Hujurat", "rev": "medinan", "order": 106, "verses": 18, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 50, "ar": "ق", "en": "Qaaf", "tr": "Qaf", "rev": "meccan", "order": 34, "verses": 45, "basmalah": "opening_unnumbered", "ruku": 3},
        {"num": 51, "ar": "الذاريات", "en": "Adh-Dhaariyat", "tr": "Adh-Dhariyat", "rev": "meccan", "order": 67, "verses": 60, "basmalah": "opening_unnumbered", "ruku": 3},
        {"num": 52, "ar": "الطور", "en": "At-Tur", "tr": "At-Tur", "rev": "meccan", "order": 76, "verses": 49, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 53, "ar": "النجم", "en": "An-Najm", "tr": "An-Najm", "rev": "meccan", "order": 23, "verses": 62, "basmalah": "opening_unnumbered", "ruku": 3},
        {"num": 54, "ar": "القمر", "en": "Al-Qamar", "tr": "Al-Qamar", "rev": "meccan", "order": 37, "verses": 55, "basmalah": "opening_unnumbered", "ruku": 3},
        {"num": 55, "ar": "الرحمن", "en": "Ar-Rahmaan", "tr": "Ar-Rahman", "rev": "medinan", "order": 97, "verses": 78, "basmalah": "opening_unnumbered", "ruku": 3},
        {"num": 56, "ar": "الواقعة", "en": "Al-Waaqia", "tr": "Al-Waqi'ah", "rev": "meccan", "order": 46, "verses": 96, "basmalah": "opening_unnumbered", "ruku": 3},
        {"num": 57, "ar": "الحديد", "en": "Al-Hadid", "tr": "Al-Hadid", "rev": "medinan", "order": 94, "verses": 29, "basmalah": "opening_unnumbered", "ruku": 4},
        {"num": 58, "ar": "المجادلة", "en": "Al-Mujaadila", "tr": "Al-Mujadila", "rev": "medinan", "order": 105, "verses": 22, "basmalah": "opening_unnumbered", "ruku": 3},
        {"num": 59, "ar": "الحشر", "en": "Al-Hashr", "tr": "Al-Hashr", "rev": "medinan", "order": 101, "verses": 24, "basmalah": "opening_unnumbered", "ruku": 3},
        {"num": 60, "ar": "الممتحنة", "en": "Al-Mumtahana", "tr": "Al-Mumtahanah", "rev": "medinan", "order": 91, "verses": 13, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 61, "ar": "الصف", "en": "As-Saff", "tr": "As-Saf", "rev": "medinan", "order": 109, "verses": 14, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 62, "ar": "الجمعة", "en": "Al-Jumu'a", "tr": "Al-Jumu'ah", "rev": "medinan", "order": 110, "verses": 11, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 63, "ar": "المنافقون", "en": "Al-Munaafiqoon", "tr": "Al-Munafiqun", "rev": "medinan", "order": 104, "verses": 11, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 64, "ar": "التغابن", "en": "At-Taghaabun", "tr": "At-Taghabun", "rev": "medinan", "order": 108, "verses": 18, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 65, "ar": "الطلاق", "en": "At-Talaaq", "tr": "At-Talaq", "rev": "medinan", "order": 99, "verses": 12, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 66, "ar": "التحريم", "en": "At-Tahrim", "tr": "At-Tahrim", "rev": "medinan", "order": 107, "verses": 12, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 67, "ar": "الملك", "en": "Al-Mulk", "tr": "Al-Mulk", "rev": "meccan", "order": 77, "verses": 30, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 68, "ar": "القلم", "en": "Al-Qalam", "tr": "Al-Qalam", "rev": "meccan", "order": 2, "verses": 52, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 69, "ar": "الحاقة", "en": "Al-Haaqqa", "tr": "Al-Haqqah", "rev": "meccan", "order": 78, "verses": 52, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 70, "ar": "المعارج", "en": "Al-Ma'aarij", "tr": "Al-Ma'arij", "rev": "meccan", "order": 79, "verses": 44, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 71, "ar": "نوح", "en": "Nooh", "tr": "Nuh", "rev": "meccan", "order": 71, "verses": 28, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 72, "ar": "الجن", "en": "Al-Jinn", "tr": "Al-Jinn", "rev": "meccan", "order": 40, "verses": 28, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 73, "ar": "المزمل", "en": "Al-Muzzammil", "tr": "Al-Muzzammil", "rev": "meccan", "order": 3, "verses": 20, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 74, "ar": "المدثر", "en": "Al-Muddaththir", "tr": "Al-Muddaththir", "rev": "meccan", "order": 4, "verses": 56, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 75, "ar": "القيامة", "en": "Al-Qiyaama", "tr": "Al-Qiyamah", "rev": "meccan", "order": 31, "verses": 40, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 76, "ar": "الإنسان", "en": "Al-Insaan", "tr": "Al-Insan", "rev": "medinan", "order": 98, "verses": 31, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 77, "ar": "المرسلات", "en": "Al-Mursalaat", "tr": "Al-Mursalat", "rev": "meccan", "order": 33, "verses": 50, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 78, "ar": "النبأ", "en": "An-Naba", "tr": "An-Naba", "rev": "meccan", "order": 80, "verses": 40, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 79, "ar": "النازعات", "en": "An-Naazi'aat", "tr": "An-Nazi'at", "rev": "meccan", "order": 81, "verses": 46, "basmalah": "opening_unnumbered", "ruku": 2},
        {"num": 80, "ar": "عبس", "en": "Abasa", "tr": "'Abasa", "rev": "meccan", "order": 24, "verses": 42, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 81, "ar": "التكوير", "en": "At-Takwir", "tr": "At-Takwir", "rev": "meccan", "order": 7, "verses": 29, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 82, "ar": "الانفطار", "en": "Al-Infitaar", "tr": "Al-Infitar", "rev": "meccan", "order": 82, "verses": 19, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 83, "ar": "المطففين", "en": "Al-Mutaffifin", "tr": "Al-Mutaffifin", "rev": "meccan", "order": 86, "verses": 36, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 84, "ar": "الانشقاق", "en": "Al-Inshiqaaq", "tr": "Al-Inshiqaq", "rev": "meccan", "order": 83, "verses": 25, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 85, "ar": "البروج", "en": "Al-Burooj", "tr": "Al-Buruj", "rev": "meccan", "order": 27, "verses": 22, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 86, "ar": "الطارق", "en": "At-Taariq", "tr": "At-Tariq", "rev": "meccan", "order": 36, "verses": 17, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 87, "ar": "الأعلى", "en": "Al-A'laa", "tr": "Al-A'la", "rev": "meccan", "order": 8, "verses": 19, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 88, "ar": "الغاشية", "en": "Al-Ghaashiya", "tr": "Al-Ghashiyah", "rev": "meccan", "order": 68, "verses": 26, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 89, "ar": "الفجر", "en": "Al-Fajr", "tr": "Al-Fajr", "rev": "meccan", "order": 10, "verses": 30, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 90, "ar": "البلد", "en": "Al-Balad", "tr": "Al-Balad", "rev": "meccan", "order": 35, "verses": 20, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 91, "ar": "الشمس", "en": "Ash-Shams", "tr": "Ash-Shams", "rev": "meccan", "order": 26, "verses": 15, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 92, "ar": "الليل", "en": "Al-Lail", "tr": "Al-Layl", "rev": "meccan", "order": 9, "verses": 21, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 93, "ar": "الضحى", "en": "Ad-Dhuhaa", "tr": "Ad-Duha", "rev": "meccan", "order": 11, "verses": 11, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 94, "ar": "الشرح", "en": "Ash-Sharh", "tr": "Ash-Sharh", "rev": "meccan", "order": 12, "verses": 8, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 95, "ar": "التين", "en": "At-Tin", "tr": "At-Tin", "rev": "meccan", "order": 28, "verses": 8, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 96, "ar": "العلق", "en": "Al-Alaq", "tr": "Al-'Alaq", "rev": "meccan", "order": 1, "verses": 19, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 97, "ar": "القدر", "en": "Al-Qadr", "tr": "Al-Qadr", "rev": "meccan", "order": 25, "verses": 5, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 98, "ar": "البينة", "en": "Al-Bayyina", "tr": "Al-Bayyinah", "rev": "medinan", "order": 100, "verses": 8, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 99, "ar": "الزلزلة", "en": "Az-Zalzala", "tr": "Az-Zalzalah", "rev": "medinan", "order": 93, "verses": 8, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 100, "ar": "العاديات", "en": "Al-Aadiyaat", "tr": "Al-'Adiyat", "rev": "meccan", "order": 14, "verses": 11, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 101, "ar": "القارعة", "en": "Al-Qaari'a", "tr": "Al-Qari'ah", "rev": "meccan", "order": 30, "verses": 11, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 102, "ar": "التكاثر", "en": "At-Takaathur", "tr": "At-Takathur", "rev": "meccan", "order": 16, "verses": 8, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 103, "ar": "العصر", "en": "Al-Asr", "tr": "Al-'Asr", "rev": "meccan", "order": 13, "verses": 3, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 104, "ar": "الهمزة", "en": "Al-Humaza", "tr": "Al-Humazah", "rev": "meccan", "order": 32, "verses": 9, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 105, "ar": "الفيل", "en": "Al-Fil", "tr": "Al-Fil", "rev": "meccan", "order": 19, "verses": 5, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 106, "ar": "قريش", "en": "Quraish", "tr": "Quraysh", "rev": "meccan", "order": 29, "verses": 4, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 107, "ar": "الماعون", "en": "Al-Maa'un", "tr": "Al-Ma'un", "rev": "meccan", "order": 17, "verses": 7, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 108, "ar": "الكوثر", "en": "Al-Kauthar", "tr": "Al-Kawthar", "rev": "meccan", "order": 15, "verses": 3, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 109, "ar": "الكافرون", "en": "Al-Kaafiroon", "tr": "Al-Kafirun", "rev": "meccan", "order": 18, "verses": 6, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 110, "ar": "النصر", "en": "An-Nasr", "tr": "An-Nasr", "rev": "medinan", "order": 114, "verses": 3, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 111, "ar": "المسد", "en": "Al-Masad", "tr": "Al-Masad", "rev": "meccan", "order": 6, "verses": 5, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 112, "ar": "الإخلاص", "en": "Al-Ikhlaas", "tr": "Al-Ikhlas", "rev": "meccan", "order": 22, "verses": 4, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 113, "ar": "الفلق", "en": "Al-Falaq", "tr": "Al-Falaq", "rev": "meccan", "order": 20, "verses": 5, "basmalah": "opening_unnumbered", "ruku": 1},
        {"num": 114, "ar": "الناس", "en": "An-Naas", "tr": "An-Nas", "rev": "meccan", "order": 21, "verses": 6, "basmalah": "opening_unnumbered", "ruku": 1},
    ]

    async def ingest_from_file(
        self,
        file_path: Path,
        source: IngestionSource,
    ) -> 'IngestionResult':
        """
        Ingest Quran data from XML file with full verification.
        """
        # Step 1: Verify file checksum
        actual_checksum = self._compute_file_checksum(file_path)
        if actual_checksum != source.expected_sha256:
            raise IntegrityViolationException(
                f"File checksum mismatch. Expected: {source.expected_sha256}, "
                f"Got: {actual_checksum}"
            )

        # Step 2: Parse XML securely (disable external entities)
        parser = ET.XMLParser()
        tree = ET.parse(file_path, parser)
        root = tree.getroot()

        # Step 3: Extract and validate verses
        verses: List[Verse] = []
        basmalahs: Dict[int, str] = {}  # Store Basmalah per Surah
        surah_verse_counts: Dict[int, int] = {}

        for sura_elem in root.findall(".//sura"):
            surah_num = int(sura_elem.get("index", 0))
            surah_name = sura_elem.get("name", "")
            surah_verse_counts[surah_num] = 0

            for aya_elem in sura_elem.findall("aya"):
                verse_num = int(aya_elem.get("index", 0))
                text = aya_elem.get("text", "")

                # Handle Basmalah attribute (present on first verse of Surahs 2-114, except 9)
                bismillah = aya_elem.get("bismillah")
                if bismillah:
                    basmalahs[surah_num] = bismillah

                surah_verse_counts[surah_num] += 1

                # Create verse entity with Basmalah metadata
                verses.append(self._create_verse(
                    surah_num=surah_num,
                    verse_num=verse_num,
                    text=text,
                    surah_name=surah_name,
                    script_type=source.script_type,
                    has_bismillah_attr=bismillah is not None,
                    bismillah_text=bismillah,
                ))

        # Step 4: Validate counts
        self._validate_verse_counts(surah_verse_counts)

        # Step 5: Generate content checksum
        content_checksum = self._compute_content_checksum(verses)

        return IngestionResult(
            source=source,
            verses=verses,
            content_checksum=content_checksum,
            verified=True,
        )

    def _compute_file_checksum(self, path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _validate_verse_counts(self, counts: Dict[int, int]) -> None:
        """Validate that verse counts match expected values exactly."""
        for surah_num, expected_count in self.EXPECTED_VERSE_COUNTS.items():
            actual_count = counts.get(surah_num, 0)
            if actual_count != expected_count:
                raise IntegrityViolationException(
                    f"Verse count mismatch for Surah {surah_num}. "
                    f"Expected: {expected_count}, Got: {actual_count}"
                )

        if len(counts) != self.TOTAL_SURAHS:
            raise IntegrityViolationException(
                f"Surah count mismatch. Expected: {self.TOTAL_SURAHS}, "
                f"Got: {len(counts)}"
            )

    def _compute_content_checksum(self, verses: List[Verse]) -> str:
        """Compute deterministic checksum of all verse content."""
        all_text = "\n".join(
            f"{v.location}:{v.content[ScriptType.UTHMANI]}"
            for v in sorted(verses, key=lambda x: (x.location.surah_number, x.location.verse_number))
        )
        return hashlib.sha256(all_text.encode()).hexdigest()

    def _create_verse(
        self,
        surah: int,
        verse: int,
        text: str,
        edition: MushafEdition
    ) -> Verse:
        """Create a Verse entity from ingested data."""
        # Implementation would include full metadata loading
        pass


@dataclass
class IngestionResult:
    source: IngestionSource
    verses: List[Verse]
    content_checksum: str
    verified: bool
```

### 8.2. Boot-Time Integrity Verification

```python
class IntegrityGuard:
    """
    Verifies data integrity on every application startup.
    If verification fails, the application MUST NOT start.
    """

    def __init__(
        self,
        repository: IQuranRepository,
        expected_checksum: str,
    ):
        self._repo = repository
        self._expected = expected_checksum

    async def verify_or_fail(self) -> None:
        """
        Verify database integrity. Raises exception if verification fails.

        This MUST be called during application startup, before accepting
        any requests.
        """
        report = await self._repo.verify_integrity()

        if not report.is_valid:
            raise IntegrityViolationException(
                f"CRITICAL: Database integrity check failed!\n"
                f"Expected checksum: {self._expected}\n"
                f"Actual checksum: {report.actual_checksum}\n"
                f"Details: {report.details}\n"
                f"The application cannot start with corrupted data."
            )

        if report.actual_checksum != self._expected:
            raise IntegrityViolationException(
                f"CRITICAL: Database checksum mismatch!\n"
                f"Expected: {self._expected}\n"
                f"Actual: {report.actual_checksum}\n"
                f"This may indicate unauthorized data modification."
            )
```

### 8.5. Morphological Data Ingestion (MASAQ/QAC)

The morphological analysis data comes from pre-annotated scholarly datasets rather than runtime NLP libraries. This ensures accuracy and reproducibility.

**Data Sources:**
- **MASAQ Dataset** (Primary): 131K morphological entries, CC BY 4.0
- **Quranic Arabic Corpus** (Validation): Version 0.4, GNU GPL

```python
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class MASAQEntry:
    """Single morphological entry from MASAQ dataset."""
    surah: int
    verse: int
    word_index: int
    word_text: str
    root: Optional[str]
    lemma: Optional[str]
    pos_tag: str
    pattern: Optional[str]
    person: Optional[str]
    gender: Optional[str]
    number: Optional[str]
    case: Optional[str]
    state: Optional[str]
    aspect: Optional[str]
    mood: Optional[str]
    voice: Optional[str]
    prefix: Optional[str]
    suffix: Optional[str]


class MorphologyIngestionService:
    """
    Ingests morphological data from MASAQ and QAC datasets.

    The ingestion process:
    1. Load MASAQ JSON/CSV files
    2. Validate entry counts against expected totals
    3. Cross-reference with QAC for validation
    4. Populate word_morphology table
    5. Index entity occurrences for fast lookup
    """

    EXPECTED_WORD_COUNT: Final[int] = 77430  # Total words in Quran
    EXPECTED_MORPHOLOGY_ENTRIES: Final[int] = 131000  # MASAQ has ~131K entries

    def __init__(
        self,
        masaq_path: Path,
        qac_path: Optional[Path] = None,
        normalizer: 'ArabicNormalizer' = None,
    ):
        self.masaq_path = masaq_path
        self.qac_path = qac_path
        self.normalizer = normalizer or ArabicNormalizer()

    async def ingest_masaq(self, session: AsyncSession) -> MorphologyIngestionResult:
        """Ingest MASAQ dataset into database."""

        # Load MASAQ data (supports JSON and CSV)
        if self.masaq_path.suffix == '.json':
            entries = self._load_masaq_json()
        else:
            entries = self._load_masaq_csv()

        # Validate entry count
        if len(entries) < self.EXPECTED_WORD_COUNT:
            raise IntegrityViolationException(
                f"MASAQ entry count {len(entries)} < expected {self.EXPECTED_WORD_COUNT}"
            )

        # Process and insert entries
        morphology_models: List[WordMorphologyModel] = []
        entity_occurrences: List[EntityOccurrenceModel] = []

        for entry in entries:
            # Create morphology model
            morph = WordMorphologyModel(
                surah_number=entry.surah,
                verse_number=entry.verse,
                word_index=entry.word_index,
                word_text=entry.word_text,
                word_text_clean=self.normalizer.remove_tashkeel(entry.word_text),
                word_text_normalized=self.normalizer.full_normalize(entry.word_text),
                root=entry.root,
                lemma=entry.lemma,
                pos_tag=entry.pos_tag,
                pattern=entry.pattern,
                person=entry.person,
                gender=entry.gender,
                number=entry.number,
                case=entry.case,
                state=entry.state,
                aspect=entry.aspect,
                mood=entry.mood,
                voice=entry.voice,
                prefix=entry.prefix,
                suffix=entry.suffix,
                is_divine_name=self._is_divine_name(entry),
                is_prophet_name=self._is_prophet_name(entry),
                is_proper_noun=self._is_proper_noun(entry),
                source='masaq',
            )
            morphology_models.append(morph)

            # Create entity occurrence if applicable
            if morph.is_divine_name or morph.is_prophet_name or morph.is_proper_noun:
                entity = self._create_entity_occurrence(entry, morph)
                if entity:
                    entity_occurrences.append(entity)

        # Bulk insert
        session.add_all(morphology_models)
        session.add_all(entity_occurrences)
        await session.commit()

        return MorphologyIngestionResult(
            total_words=len(morphology_models),
            total_entities=len(entity_occurrences),
            source='masaq',
        )

    def _is_divine_name(self, entry: MASAQEntry) -> bool:
        """Check if word is a Divine Name."""
        # Compare normalized form against DIVINE_NAMES reference
        normalized = self.normalizer.full_normalize(entry.word_text)
        return normalized in DIVINE_NAMES or entry.lemma in DIVINE_NAMES

    def _is_prophet_name(self, entry: MASAQEntry) -> bool:
        """Check if word is a Prophet's name."""
        normalized = self.normalizer.full_normalize(entry.word_text)
        return normalized in PROPHETS or entry.lemma in PROPHETS

    def _is_proper_noun(self, entry: MASAQEntry) -> bool:
        """Check if word is a proper noun (place, person, etc.)."""
        # MASAQ marks proper nouns with specific POS tags
        return entry.pos_tag in ('PN', 'PROPN') or entry.lemma in PLACES or entry.lemma in PEOPLES


@dataclass
class MorphologyIngestionResult:
    """Result of morphology ingestion."""
    total_words: int
    total_entities: int
    source: str
    errors: List[str] = field(default_factory=list)
```

### 8.6. Arabic Text Normalization Strategy

Text normalization is critical for accurate searching and comparison. We implement a **multi-level normalization strategy** that allows users to choose the appropriate level for their use case.

```python
from enum import StrEnum
from typing import Final
import pyarabic.araby as araby


class NormalizationLevel(StrEnum):
    """
    Levels of Arabic text normalization.

    Each level includes all normalizations from previous levels.
    """
    NONE = "none"                    # No normalization - exact text
    TASHKEEL_REMOVED = "no_tashkeel" # Remove diacritics (harakat)
    TATWEEL_REMOVED = "no_tatweel"   # Remove kashida/tatweel
    HAMZA_UNIFIED = "hamza_unified"  # Unify hamza forms (أ إ آ ء → ا)
    ALIF_UNIFIED = "alif_unified"    # Unify alif forms (ٱ → ا)
    YA_UNIFIED = "ya_unified"        # Unify ya/alif maqsura (ى → ي)
    FULL = "full"                    # All normalizations applied


class ArabicNormalizer:
    """
    Multi-level Arabic text normalizer for Quranic analysis.

    Handles the specific characters found in Uthmani script including:
    - Alif Wasla (ٱ U+0671)
    - Small letters (ۛ ۖ ۗ etc.)
    - Superscript Alif (ـٰ)
    """

    # Character sets for normalization
    TASHKEEL: Final[frozenset[str]] = frozenset([
        '\u064B',  # FATHATAN
        '\u064C',  # DAMMATAN
        '\u064D',  # KASRATAN
        '\u064E',  # FATHA
        '\u064F',  # DAMMA
        '\u0650',  # KASRA
        '\u0651',  # SHADDA
        '\u0652',  # SUKUN
        '\u0653',  # MADDAH
        '\u0654',  # HAMZA ABOVE
        '\u0655',  # HAMZA BELOW
        '\u0656',  # SUBSCRIPT ALEF
        '\u0657',  # INVERTED DAMMA
        '\u0658',  # MARK NOON GHUNNA
        '\u065C',  # VOWEL SIGN DOT BELOW
        '\u0670',  # SUPERSCRIPT ALEF (Alif Khanjariyya)
    ])

    SMALL_LETTERS: Final[frozenset[str]] = frozenset([
        '\u06D6',  # SMALL HIGH LIGATURE SAD WITH LAM WITH ALEF MAKSURA
        '\u06D7',  # SMALL HIGH LIGATURE QAF WITH LAM WITH ALEF MAKSURA
        '\u06D8',  # SMALL HIGH MEEM INITIAL FORM
        '\u06D9',  # SMALL HIGH LAM ALEF
        '\u06DA',  # SMALL HIGH JEEM
        '\u06DB',  # SMALL HIGH THREE DOTS
        '\u06DC',  # SMALL HIGH SEEN
        '\u06DD',  # END OF AYAH
        '\u06DE',  # START OF RUB EL HIZB
        '\u06DF',  # SMALL HIGH ROUNDED ZERO
        '\u06E0',  # SMALL HIGH UPRIGHT RECTANGULAR ZERO
        '\u06E1',  # SMALL HIGH DOTLESS HEAD OF KHAH
        '\u06E2',  # SMALL HIGH MEEM ISOLATED FORM
        '\u06E3',  # SMALL LOW SEEN
        '\u06E4',  # SMALL HIGH MADDA
        '\u06E5',  # SMALL WAW
        '\u06E6',  # SMALL YEH
        '\u06E7',  # SMALL HIGH YEH
        '\u06E8',  # SMALL HIGH NOON
        '\u06EA',  # EMPTY CENTRE LOW STOP
        '\u06EB',  # EMPTY CENTRE HIGH STOP
        '\u06EC',  # ROUNDED HIGH STOP WITH FILLED CENTRE
        '\u06ED',  # SMALL LOW MEEM
    ])

    HAMZA_FORMS: Final[Dict[str, str]] = {
        '\u0623': '\u0627',  # ALEF WITH HAMZA ABOVE → ALEF
        '\u0625': '\u0627',  # ALEF WITH HAMZA BELOW → ALEF
        '\u0622': '\u0627',  # ALEF WITH MADDA ABOVE → ALEF
        '\u0624': '\u0648',  # WAW WITH HAMZA → WAW
        '\u0626': '\u064A',  # YEH WITH HAMZA → YEH
    }

    ALIF_FORMS: Final[Dict[str, str]] = {
        '\u0671': '\u0627',  # ALIF WASLA → ALEF
        '\u0672': '\u0627',  # ALEF WITH WAVY HAMZA ABOVE → ALEF
        '\u0673': '\u0627',  # ALEF WITH WAVY HAMZA BELOW → ALEF
        '\u0675': '\u0627',  # HIGH HAMZA ALEF → ALEF
    }

    def normalize(self, text: str, level: NormalizationLevel) -> str:
        """
        Normalize Arabic text to the specified level.

        Args:
            text: Arabic text to normalize
            level: Target normalization level

        Returns:
            Normalized text
        """
        if level == NormalizationLevel.NONE:
            return text

        result = text

        # Level 1: Remove tashkeel (diacritics)
        if level.value >= NormalizationLevel.TASHKEEL_REMOVED.value:
            result = self.remove_tashkeel(result)

        # Level 2: Remove tatweel (kashida)
        if level.value >= NormalizationLevel.TATWEEL_REMOVED.value:
            result = self.remove_tatweel(result)

        # Level 3: Unify hamza forms
        if level.value >= NormalizationLevel.HAMZA_UNIFIED.value:
            result = self.unify_hamza(result)

        # Level 4: Unify alif forms (including Alif Wasla)
        if level.value >= NormalizationLevel.ALIF_UNIFIED.value:
            result = self.unify_alif(result)

        # Level 5: Unify ya/alif maqsura
        if level.value >= NormalizationLevel.YA_UNIFIED.value:
            result = self.unify_ya(result)

        return result

    def remove_tashkeel(self, text: str) -> str:
        """Remove all diacritical marks (tashkeel/harakat)."""
        return ''.join(c for c in text if c not in self.TASHKEEL)

    def remove_tatweel(self, text: str) -> str:
        """Remove tatweel/kashida character."""
        return text.replace('\u0640', '')

    def remove_small_letters(self, text: str) -> str:
        """Remove Quranic small letters (pause marks, etc.)."""
        return ''.join(c for c in text if c not in self.SMALL_LETTERS)

    def unify_hamza(self, text: str) -> str:
        """Unify all hamza forms to base letters."""
        result = text
        for hamza, base in self.HAMZA_FORMS.items():
            result = result.replace(hamza, base)
        # Also normalize standalone hamza optionally
        # result = result.replace('\u0621', '')  # Remove standalone hamza
        return result

    def unify_alif(self, text: str) -> str:
        """Unify all alif forms including Alif Wasla."""
        result = text
        for alif, base in self.ALIF_FORMS.items():
            result = result.replace(alif, base)
        return result

    def unify_ya(self, text: str) -> str:
        """Unify alif maqsura (ى) to ya (ي)."""
        return text.replace('\u0649', '\u064A')

    def full_normalize(self, text: str) -> str:
        """Apply full normalization (all levels)."""
        return self.normalize(text, NormalizationLevel.FULL)

    def for_search(self, text: str) -> str:
        """
        Normalize text for search purposes.
        Removes tashkeel and unifies hamza/alif for better matching.
        """
        result = self.remove_tashkeel(text)
        result = self.remove_tatweel(result)
        result = self.unify_hamza(result)
        result = self.unify_alif(result)
        return result
```

### 8.7. Transparent Word Counting Methodology

For numerical analysis claims (e.g., "يوم appears 365 times"), transparency and reproducibility are critical. Our counting system requires explicit methodology declaration.

```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import StrEnum


class WordFormInclusion(StrEnum):
    """What word forms to include in count."""
    EXACT_ONLY = "exact"           # Only exact form: يوم
    WITH_PREFIXES = "prefixes"     # Include: بيوم، ليوم، فيوم
    WITH_SUFFIXES = "suffixes"     # Include: يومكم، يومهم
    WITH_BOTH = "both"             # Include both prefixes and suffixes
    ALL_DERIVATIVES = "derivatives" # Include: يومئذ، أيام، يومين


@dataclass(frozen=True)
class WordCountMethodology:
    """
    Explicit declaration of counting methodology for full reproducibility.

    Every numerical claim MUST declare its methodology so results can be:
    1. Verified independently
    2. Compared fairly with other counts
    3. Understood by scholars
    """

    # What to count
    target_word: str                          # Base word to search for
    target_root: Optional[str] = None         # Optional: search by root instead
    form_inclusion: WordFormInclusion = WordFormInclusion.EXACT_ONLY

    # Specific forms to include/exclude (for fine-grained control)
    include_forms: frozenset[str] = field(default_factory=frozenset)
    exclude_forms: frozenset[str] = field(default_factory=frozenset)

    # Normalization before matching
    normalization_level: NormalizationLevel = NormalizationLevel.TASHKEEL_REMOVED

    # Scope options
    include_basmalah: bool = True
    include_basmalah_fatiha: bool = True      # Count Fatiha's basmalah as verse
    include_basmalah_others: bool = False     # Count other surahs' basmalah (not verse)
    scope_meccan_only: bool = False
    scope_medinan_only: bool = False

    def describe(self) -> str:
        """Generate human-readable methodology description."""
        parts = [f"Target: '{self.target_word}'"]

        if self.target_root:
            parts.append(f"Root: {self.target_root}")

        parts.append(f"Form inclusion: {self.form_inclusion.value}")
        parts.append(f"Normalization: {self.normalization_level.value}")

        if self.include_forms:
            parts.append(f"Explicit includes: {', '.join(self.include_forms)}")
        if self.exclude_forms:
            parts.append(f"Explicit excludes: {', '.join(self.exclude_forms)}")

        scope_parts = []
        if not self.include_basmalah:
            scope_parts.append("excluding all basmalah")
        if self.scope_meccan_only:
            scope_parts.append("Meccan surahs only")
        if self.scope_medinan_only:
            scope_parts.append("Medinan surahs only")

        if scope_parts:
            parts.append(f"Scope: {', '.join(scope_parts)}")

        return " | ".join(parts)


@dataclass
class WordMatch:
    """Single word match with full context."""
    location: VerseLocation
    word_index: int
    matched_form: str           # Actual form found in text
    normalized_form: str        # After normalization
    match_reason: str           # Why this matched (e.g., "exact", "prefix بـ", "root match")
    verse_text: str             # Full verse for context


@dataclass
class WordCountResult:
    """
    Complete result of a word count with full audit trail.

    This result contains everything needed to:
    1. Verify the count independently
    2. Understand exactly what was counted
    3. Reproduce the result
    """

    # Query parameters
    methodology: WordCountMethodology
    scope_description: str

    # Results
    total_count: int
    matches: List[WordMatch]

    # Verification
    query_checksum: str         # SHA-256 of methodology + scope
    result_checksum: str        # SHA-256 of all match locations
    executed_at: datetime
    execution_time_ms: int

    def to_audit_dict(self) -> Dict[str, Any]:
        """Generate audit-ready dictionary for logging."""
        return {
            "methodology": self.methodology.describe(),
            "scope": self.scope_description,
            "total_count": self.total_count,
            "match_locations": [f"{m.location}:{m.word_index}" for m in self.matches],
            "query_checksum": self.query_checksum,
            "result_checksum": self.result_checksum,
            "executed_at": self.executed_at.isoformat(),
        }


class TransparentWordCounter:
    """
    Word counter with full methodology transparency and audit trail.

    Usage:
        counter = TransparentWordCounter(repository, normalizer)

        # Count "يوم" with explicit methodology
        methodology = WordCountMethodology(
            target_word="يوم",
            form_inclusion=WordFormInclusion.EXACT_ONLY,
            normalization_level=NormalizationLevel.TASHKEEL_REMOVED,
        )

        result = await counter.count(methodology, EntireQuranScope())
        print(f"Found {result.total_count} matches")
        print(f"Methodology: {result.methodology.describe()}")
    """

    def __init__(
        self,
        repository: IQuranRepository,
        morphology_repo: IMorphologyRepository,
        normalizer: ArabicNormalizer,
    ):
        self._repo = repository
        self._morph_repo = morphology_repo
        self._normalizer = normalizer

    async def count(
        self,
        methodology: WordCountMethodology,
        scope: IScopeSpecification,
    ) -> WordCountResult:
        """
        Count word occurrences with explicit methodology.

        Returns detailed result with every match logged.
        """
        start_time = datetime.utcnow()
        matches: List[WordMatch] = []

        # Get verses in scope
        verses = await self._repo.get_verses_by_scope(scope)

        # Prepare target for matching
        target_normalized = self._normalizer.normalize(
            methodology.target_word,
            methodology.normalization_level
        )

        for verse in verses:
            # Skip basmalah if configured
            if not self._should_include_verse(verse, methodology):
                continue

            # Get morphology data for this verse
            word_morphs = await self._morph_repo.get_verse_morphology(verse.location)

            for word_morph in word_morphs:
                if self._matches(word_morph, target_normalized, methodology):
                    matches.append(WordMatch(
                        location=verse.location,
                        word_index=word_morph.word_index,
                        matched_form=word_morph.word_text,
                        normalized_form=word_morph.word_text_normalized,
                        match_reason=self._get_match_reason(word_morph, methodology),
                        verse_text=verse.text_uthmani,
                    ))

        end_time = datetime.utcnow()
        execution_time = int((end_time - start_time).total_seconds() * 1000)

        return WordCountResult(
            methodology=methodology,
            scope_description=scope.describe(),
            total_count=len(matches),
            matches=matches,
            query_checksum=self._compute_query_checksum(methodology, scope),
            result_checksum=self._compute_result_checksum(matches),
            executed_at=start_time,
            execution_time_ms=execution_time,
        )

    def _matches(
        self,
        word: WordMorphologyModel,
        target: str,
        methodology: WordCountMethodology,
    ) -> bool:
        """Check if word matches according to methodology."""

        # Check exclusions first
        if word.word_text_normalized in methodology.exclude_forms:
            return False

        # Check explicit inclusions
        if word.word_text_normalized in methodology.include_forms:
            return True

        # Root-based matching
        if methodology.target_root and word.root == methodology.target_root:
            return True

        # Form-based matching
        word_normalized = word.word_text_normalized

        if methodology.form_inclusion == WordFormInclusion.EXACT_ONLY:
            return word_normalized == target

        elif methodology.form_inclusion == WordFormInclusion.WITH_PREFIXES:
            return word_normalized == target or word_normalized.endswith(target)

        elif methodology.form_inclusion == WordFormInclusion.WITH_SUFFIXES:
            return word_normalized == target or word_normalized.startswith(target)

        elif methodology.form_inclusion == WordFormInclusion.WITH_BOTH:
            return target in word_normalized

        elif methodology.form_inclusion == WordFormInclusion.ALL_DERIVATIVES:
            # Use lemma matching for derivatives
            return word.lemma and self._normalizer.full_normalize(word.lemma) == target

        return False

    def _compute_query_checksum(
        self,
        methodology: WordCountMethodology,
        scope: IScopeSpecification,
    ) -> str:
        """Compute deterministic checksum of query parameters."""
        import hashlib
        query_str = f"{methodology.describe()}|{scope.describe()}"
        return hashlib.sha256(query_str.encode()).hexdigest()[:16]

    def _compute_result_checksum(self, matches: List[WordMatch]) -> str:
        """Compute checksum of results for verification."""
        import hashlib
        locations = sorted(f"{m.location}:{m.word_index}" for m in matches)
        return hashlib.sha256("|".join(locations).encode()).hexdigest()[:16]
```

---

## 9. Infrastructure Layer

### 9.1. SQLAlchemy Database Models

```python
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Enum, ForeignKey,
    Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class SurahMetadataModel(Base):
    """Database model for Surah metadata."""
    __tablename__ = "surah_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name_arabic: Mapped[str] = mapped_column(String(100), nullable=False)
    name_english: Mapped[str] = mapped_column(String(100), nullable=False)
    name_transliteration: Mapped[str] = mapped_column(String(100), nullable=False)
    revelation_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'meccan' or 'medinan'
    revelation_order: Mapped[int] = mapped_column(Integer, nullable=False)
    verse_count: Mapped[int] = mapped_column(Integer, nullable=False)
    basmalah_status: Mapped[str] = mapped_column(String(30), nullable=False)
    ruku_count: Mapped[int] = mapped_column(Integer, nullable=False)
    juz_start: Mapped[int] = mapped_column(Integer, nullable=False)  # Starting Juz
    hizb_start: Mapped[int] = mapped_column(Integer, nullable=False)  # Starting Hizb

    # Relationships
    verses: Mapped[list["VerseModel"]] = relationship(
        "VerseModel", back_populates="surah", lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint("number >= 1 AND number <= 114", name="valid_surah_number"),
        CheckConstraint("revelation_type IN ('meccan', 'medinan')", name="valid_revelation_type"),
        Index("idx_surah_number", "number"),
    )


class VerseModel(Base):
    """Database model for Quran verses."""
    __tablename__ = "verses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    surah_number: Mapped[int] = mapped_column(
        Integer, ForeignKey("surah_metadata.number"), nullable=False
    )
    verse_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Text content for each script type (stored as JSONB)
    text_uthmani: Mapped[str] = mapped_column(Text, nullable=False)
    text_uthmani_min: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    text_simple: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Basmalah handling
    has_bismillah_attr: Mapped[bool] = mapped_column(Boolean, default=False)
    bismillah_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Precomputed checksums for integrity
    checksum_uthmani: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256

    # Metadata flags
    is_sajdah: Mapped[bool] = mapped_column(Boolean, default=False)
    juz_number: Mapped[int] = mapped_column(Integer, nullable=False)
    hizb_number: Mapped[int] = mapped_column(Integer, nullable=False)
    rub_number: Mapped[int] = mapped_column(Integer, nullable=False)  # Quarter of Hizb
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)  # Madinah Mushaf page

    # Audit fields
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    source_id: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., 'tanzil_uthmani'

    # Relationships
    surah: Mapped["SurahMetadataModel"] = relationship(
        "SurahMetadataModel", back_populates="verses"
    )

    __table_args__ = (
        UniqueConstraint("surah_number", "verse_number", name="uq_verse_location"),
        CheckConstraint("surah_number >= 1 AND surah_number <= 114", name="valid_surah"),
        CheckConstraint("verse_number >= 1", name="valid_verse"),
        CheckConstraint("juz_number >= 1 AND juz_number <= 30", name="valid_juz"),
        Index("idx_verse_location", "surah_number", "verse_number"),
        Index("idx_juz", "juz_number"),
        Index("idx_sajdah", "is_sajdah"),
    )


class IngestionLogModel(Base):
    """Audit log for data ingestion operations."""
    __tablename__ = "ingestion_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[str] = mapped_column(String(50), nullable=False)
    source_name: Mapped[str] = mapped_column(String(200), nullable=False)
    file_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    content_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    verse_count: Mapped[int] = mapped_column(Integer, nullable=False)
    surah_count: Mapped[int] = mapped_column(Integer, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # 'success', 'failed'
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AnalysisAuditModel(Base):
    """Audit log for analysis operations."""
    __tablename__ = "analysis_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)  # UUID
    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False)
    scope_description: Mapped[str] = mapped_column(Text, nullable=False)
    normalization_strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    calculation_strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    result_summary: Mapped[dict] = mapped_column(JSONB, nullable=False)
    input_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    execution_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    script_type: Mapped[str] = mapped_column(String(20), nullable=False)

    __table_args__ = (
        Index("idx_analysis_type", "analysis_type"),
        Index("idx_executed_at", "executed_at"),
    )


class WordMorphologyModel(Base):
    """
    Pre-computed morphological analysis from MASAQ/QAC datasets.

    This table stores scholarly-verified morphological annotations
    for every word in the Quran. We use pre-computed data rather than
    runtime analysis to ensure:
    - 99% accuracy (human-verified by Arabic linguists)
    - Classical Arabic correctness (not MSA assumptions)
    - Reproducibility across all analysis runs

    Source: MASAQ Dataset (Mendeley) + Quranic Arabic Corpus (Leeds)
    """
    __tablename__ = "word_morphology"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Location identifiers
    surah_number: Mapped[int] = mapped_column(Integer, nullable=False)
    verse_number: Mapped[int] = mapped_column(Integer, nullable=False)
    word_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-based position in verse

    # Word forms
    word_text: Mapped[str] = mapped_column(String(100), nullable=False)  # Original text
    word_text_clean: Mapped[str] = mapped_column(String(100), nullable=False)  # Tashkeel removed
    word_text_normalized: Mapped[str] = mapped_column(String(100), nullable=False)  # Fully normalized

    # Core morphological features (from MASAQ)
    root: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # ك-ت-ب (trilateral/quadrilateral)
    root_type: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)  # trilateral, quadrilateral
    lemma: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Dictionary form
    pattern: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)  # فَعَلَ، فَاعِل، مَفْعُول

    # Part of Speech
    pos_tag: Mapped[str] = mapped_column(String(20), nullable=False)  # N, V, PART, DET, etc.
    pos_arabic: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)  # اسم، فعل، حرف
    pos_detailed: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Detailed classification

    # Grammatical features (for nouns/adjectives)
    case: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # NOM, ACC, GEN (رفع، نصب، جر)
    state: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)  # DEF, INDEF (معرفة، نكرة)
    gender: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # M, F (مذكر، مؤنث)
    number: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # S, D, P (مفرد، مثنى، جمع)

    # Grammatical features (for verbs)
    person: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # 1, 2, 3
    aspect: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # PERF, IMPF, IMP (ماضي، مضارع، أمر)
    mood: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # IND, SUBJ, JUS (رفع، نصب، جزم)
    voice: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # ACT, PASS (معلوم، مجهول)

    # Affixes
    prefix: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Attached prefixes
    suffix: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Attached suffixes

    # Syntactic role (from QAC treebank where available)
    syntactic_role: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)  # SUBJ, OBJ, PRED, etc.

    # Entity flags (for quick filtering)
    is_divine_name: Mapped[bool] = mapped_column(Boolean, default=False)
    is_prophet_name: Mapped[bool] = mapped_column(Boolean, default=False)
    is_proper_noun: Mapped[bool] = mapped_column(Boolean, default=False)

    # Data source tracking
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # 'masaq', 'qac', 'manual'
    source_confidence: Mapped[Optional[float]] = mapped_column(nullable=True)  # 0.0-1.0

    __table_args__ = (
        UniqueConstraint("surah_number", "verse_number", "word_index", name="uq_word_location"),
        Index("idx_word_location", "surah_number", "verse_number", "word_index"),
        Index("idx_root", "root"),
        Index("idx_lemma", "lemma"),
        Index("idx_pos", "pos_tag"),
        Index("idx_word_text_normalized", "word_text_normalized"),
        Index("idx_divine_name", "is_divine_name"),
        Index("idx_prophet_name", "is_prophet_name"),
    )


class EntityOccurrenceModel(Base):
    """
    Pre-indexed entity occurrences for fast entity searches.

    This denormalized table enables O(1) lookups for:
    - "Where does الرحمن appear?"
    - "Which verses mention موسى?"
    - "All occurrences of مصر"
    """
    __tablename__ = "entity_occurrences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Entity identification
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)  # divine_name, prophet, place, people
    entity_key: Mapped[str] = mapped_column(String(50), nullable=False)  # Normalized key (e.g., "الرحمن")
    entity_name_ar: Mapped[str] = mapped_column(String(100), nullable=False)  # Arabic display name
    entity_name_en: Mapped[str] = mapped_column(String(100), nullable=False)  # English name

    # Location
    surah_number: Mapped[int] = mapped_column(Integer, nullable=False)
    verse_number: Mapped[int] = mapped_column(Integer, nullable=False)
    word_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Context
    matched_form: Mapped[str] = mapped_column(String(100), nullable=False)  # Actual form in text
    context_before: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # 3 words before
    context_after: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # 3 words after

    __table_args__ = (
        Index("idx_entity_type_key", "entity_type", "entity_key"),
        Index("idx_entity_location", "surah_number", "verse_number"),
    )
```

### 9.2. PostgreSQL Repository Implementation

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func

class PostgresQuranRepository(IQuranRepository):
    """PostgreSQL implementation of the Quran repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_verse(self, location: VerseLocation) -> Optional[Verse]:
        stmt = select(VerseModel).where(
            VerseModel.surah_number == location.surah_number,
            VerseModel.verse_number == location.verse_number,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_verse_or_raise(self, location: VerseLocation) -> Verse:
        verse = await self.get_verse(location)
        if verse is None:
            raise VerseNotFoundException(f"Verse not found: {location}")
        return verse

    async def get_surah(self, surah_number: int) -> Surah:
        stmt = select(VerseModel).where(
            VerseModel.surah_number == surah_number
        ).order_by(VerseModel.verse_number)

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        if not models:
            raise SurahNotFoundException(f"Surah not found: {surah_number}")

        verses = tuple(self._to_entity(m) for m in models)
        metadata = verses[0].surah_metadata

        # Compute Surah checksum
        all_text = "\n".join(v.content[ScriptType.UTHMANI] for v in verses)
        checksum = TextChecksum.compute(all_text)

        return Surah(
            metadata=metadata,
            verses=verses,
            checksum=checksum,
        )

    async def get_verses_in_range(
        self,
        start: VerseLocation,
        end: VerseLocation
    ) -> List[Verse]:
        # Build query for range
        stmt = select(VerseModel).where(
            # Start condition
            ((VerseModel.surah_number == start.surah_number) &
             (VerseModel.verse_number >= start.verse_number)) |
            ((VerseModel.surah_number > start.surah_number) &
             (VerseModel.surah_number < end.surah_number)) |
            ((VerseModel.surah_number == end.surah_number) &
             (VerseModel.verse_number <= end.verse_number))
        ).order_by(VerseModel.surah_number, VerseModel.verse_number)

        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_all_verses(self) -> List[Verse]:
        stmt = select(VerseModel).order_by(
            VerseModel.surah_number,
            VerseModel.verse_number
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def stream_verses(
        self,
        surah_number: Optional[int] = None
    ) -> AsyncIterator[Verse]:
        stmt = select(VerseModel)
        if surah_number:
            stmt = stmt.where(VerseModel.surah_number == surah_number)
        stmt = stmt.order_by(VerseModel.surah_number, VerseModel.verse_number)

        result = await self._session.stream(stmt)
        async for row in result:
            yield self._to_entity(row.VerseModel)

    async def get_verse_count(self, surah_number: Optional[int] = None) -> int:
        stmt = select(func.count(VerseModel.id))
        if surah_number:
            stmt = stmt.where(VerseModel.surah_number == surah_number)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_verses_by_criteria(
        self,
        revelation_type: Optional[RevelationType] = None,
        juz_number: Optional[int] = None,
        has_sajdah: Optional[bool] = None,
    ) -> List[Verse]:
        stmt = select(VerseModel)

        if revelation_type:
            stmt = stmt.where(VerseModel.revelation_type == revelation_type.value)
        if juz_number:
            stmt = stmt.where(VerseModel.juz_number == juz_number)
        if has_sajdah is not None:
            stmt = stmt.where(VerseModel.is_sajdah == has_sajdah)

        stmt = stmt.order_by(VerseModel.surah_number, VerseModel.verse_number)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def verify_integrity(self) -> IntegrityReport:
        """Verify integrity of all stored verses."""
        all_verses = await self.get_all_verses()

        failed: List[VerseLocation] = []
        all_content: List[str] = []

        for verse in all_verses:
            # Verify individual verse checksum
            text = verse.content.get(ScriptType.UTHMANI, "")
            expected = verse.checksum
            actual = TextChecksum.compute(text)

            if actual.value != expected.value:
                failed.append(verse.location)

            all_content.append(f"{verse.location}:{text}")

        # Compute overall checksum
        actual_checksum = hashlib.sha256(
            "\n".join(all_content).encode()
        ).hexdigest()

        return IntegrityReport(
            is_valid=len(failed) == 0,
            checked_at=datetime.utcnow(),
            total_verses=len(all_verses),
            failed_verses=tuple(failed),
            expected_checksum="",  # Set from config
            actual_checksum=actual_checksum,
            details=f"Checked {len(all_verses)} verses, {len(failed)} failed"
        )

    def _to_entity(self, model: 'VerseModel') -> Verse:
        """Convert database model to domain entity."""
        # Implementation maps SQLAlchemy model to domain Verse
        pass
```

---

## 10. API Design

### 10.1. FastAPI Application Structure

```python
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - runs integrity check on startup."""
    # Startup: Verify database integrity
    integrity_guard = get_integrity_guard()
    try:
        await integrity_guard.verify_or_fail()
        print("Database integrity verified successfully")
    except IntegrityViolationException as e:
        print(f"FATAL: {e}")
        raise SystemExit(1)

    yield

    # Shutdown: Clean up resources
    await close_database_connections()


app = FastAPI(
    title="Mizan Core Engine API",
    description="High-precision Quranic text analysis system",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 10.2. API Endpoints

```python
from fastapi import APIRouter, Query, Path
from typing import Annotated

router = APIRouter(prefix="/api/v1", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResult)
async def run_analysis(
    request: AnalysisRequest,
    analyzer: Annotated[MizanAnalyzerService, Depends(get_analyzer)],
) -> AnalysisResult:
    """
    Execute a Quranic text analysis.

    This endpoint accepts a configuration specifying:
    - Which script and Qira'at to use
    - Which verses to include (scope)
    - How to normalize the text
    - What calculation to perform

    Returns detailed results with audit trail.
    """
    config = AnalysisConfig(
        target_script=ScriptType(request.script),
        target_qiraat=QiraatType(request.qiraat) if request.qiraat else QiraatType.HAFS_AN_ASIM,
        normalization_strategies=request.pipeline.normalization,
        calculation_method=request.pipeline.calculation,
        scope=request.filters or {},
        include_basmalah=request.options.get("include_basmalah", True),
    )

    try:
        return await analyzer.execute_analysis(config)
    except StrategyNotFoundException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Analysis failed")


@router.get("/verse/{surah}/{verse}", response_model=VerseResponse)
async def get_verse(
    surah: Annotated[int, Path(ge=1, le=114)],
    verse: Annotated[int, Path(ge=1)],
    script: Annotated[ScriptType, Query()] = ScriptType.UTHMANI,
    qiraat: Annotated[QiraatType, Query()] = QiraatType.HAFS_AN_ASIM,
    repo: Annotated[IQuranRepository, Depends(get_repository)],
) -> VerseResponse:
    """Retrieve a single verse with specified script and Qira'at."""
    location = VerseLocation(surah, verse)

    try:
        verse_entity = await repo.get_verse_or_raise(location)
        return VerseResponse(
            location=str(verse_entity.location),
            text=verse_entity.get_text(script, qiraat),
            surah_name=verse_entity.surah_metadata.name_arabic,
            surah_name_english=verse_entity.surah_metadata.name_english,
        )
    except VerseNotFoundException:
        raise HTTPException(status_code=404, detail=f"Verse not found: {surah}:{verse}")


@router.get("/surah/{surah_number}", response_model=SurahResponse)
async def get_surah(
    surah_number: Annotated[int, Path(ge=1, le=114)],
    script: Annotated[ScriptType, Query()] = ScriptType.UTHMANI,
    repo: Annotated[IQuranRepository, Depends(get_repository)],
) -> SurahResponse:
    """Retrieve a complete Surah."""
    try:
        surah = await repo.get_surah(surah_number)
        return SurahResponse(
            number=surah.metadata.number,
            name_arabic=surah.metadata.name_arabic,
            name_english=surah.metadata.name_english,
            verse_count=surah.metadata.verse_count,
            revelation_type=surah.metadata.revelation_type.value,
            verses=[
                {"number": v.location.verse_number, "text": v.content[script]}
                for v in surah.verses
            ]
        )
    except SurahNotFoundException:
        raise HTTPException(status_code=404, detail=f"Surah not found: {surah_number}")


@router.get("/strategies", response_model=StrategiesResponse)
async def list_strategies(
    factory: Annotated[StrategyFactory, Depends(get_strategy_factory)],
) -> StrategiesResponse:
    """List all available analysis strategies."""
    return StrategiesResponse(strategies=factory.list_available_strategies())


@router.get("/health", response_model=HealthResponse)
async def health_check(
    repo: Annotated[IQuranRepository, Depends(get_repository)],
) -> HealthResponse:
    """Health check endpoint for container orchestration."""
    verse_count = await repo.get_verse_count()
    return HealthResponse(
        status="healthy",
        verse_count=verse_count,
        expected_verses=6236,
        timestamp=datetime.utcnow(),
    )


@router.get("/integrity", response_model=IntegrityReport)
async def check_integrity(
    repo: Annotated[IQuranRepository, Depends(get_repository)],
) -> IntegrityReport:
    """Run integrity verification (admin endpoint)."""
    return await repo.verify_integrity()
```

### 10.3. Request/Response Models

```python
class AnalysisRequest(BaseModel):
    """Request body for analysis endpoint."""

    script: str = "uthmani"
    qiraat: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    pipeline: 'PipelineConfig'
    options: Dict[str, Any] = Field(default_factory=dict)


class PipelineConfig(BaseModel):
    """Analysis pipeline configuration."""

    normalization: List[str] = Field(
        default=["remove_tashkeel", "remove_waqf"],
        description="List of normalization strategy names to apply in order"
    )
    calculation: str = Field(
        description="Name of the calculation strategy"
    )


class VerseResponse(BaseModel):
    location: str
    text: str
    surah_name: str
    surah_name_english: str


class SurahResponse(BaseModel):
    number: int
    name_arabic: str
    name_english: str
    verse_count: int
    revelation_type: str
    verses: List[Dict[str, Any]]


class StrategiesResponse(BaseModel):
    strategies: Dict[str, List[str]]


class HealthResponse(BaseModel):
    status: str
    verse_count: int
    expected_verses: int
    timestamp: datetime
```

### 10.4. Complete API Schemas

#### Analysis Request (Full Schema)

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Literal
from enum import StrEnum


class ScopeType(StrEnum):
    """Scope specification types."""
    ENTIRE_QURAN = "entire_quran"
    SURAH = "surah"
    SURAH_RANGE = "surah_range"
    VERSE_RANGE = "verse_range"
    JUZ = "juz"
    HIZB = "hizb"
    MANZIL = "manzil"
    REVELATION_TYPE = "revelation_type"


class ScopeSpecification(BaseModel):
    """Specifies which verses to include in analysis."""

    type: ScopeType = Field(description="Type of scope specification")

    # For SURAH scope
    surah_number: Optional[int] = Field(None, ge=1, le=114)

    # For SURAH_RANGE scope
    start_surah: Optional[int] = Field(None, ge=1, le=114)
    end_surah: Optional[int] = Field(None, ge=1, le=114)

    # For VERSE_RANGE scope
    start_verse: Optional[str] = Field(None, pattern=r"^\d{1,3}:\d{1,3}$")
    end_verse: Optional[str] = Field(None, pattern=r"^\d{1,3}:\d{1,3}$")

    # For JUZ, HIZB, MANZIL scopes
    part_number: Optional[int] = None

    # For REVELATION_TYPE scope
    revelation_type: Optional[Literal["meccan", "medinan"]] = None

    # Common options
    exclude_basmalah: bool = Field(False, description="Exclude Basmalah from scope")

    class Config:
        json_schema_extra = {
            "examples": [
                {"type": "entire_quran"},
                {"type": "surah", "surah_number": 1},
                {"type": "surah_range", "start_surah": 1, "end_surah": 10},
                {"type": "verse_range", "start_verse": "2:255", "end_verse": "2:257"},
                {"type": "juz", "part_number": 30},
                {"type": "revelation_type", "revelation_type": "meccan"},
            ]
        }


class NormalizationConfig(BaseModel):
    """Text normalization configuration."""

    level: Literal["none", "tashkeel_removed", "hamza_unified",
                   "alif_unified", "ya_unified", "full"] = "tashkeel_removed"

    # Fine-grained control
    remove_tashkeel: bool = True
    unify_hamza: bool = False
    unify_alif: bool = False
    unify_ya: bool = False
    remove_small_letters: bool = False
    preserve_alif_khanjariyya: bool = True  # Important for counting


class WordCountRequest(BaseModel):
    """Request for transparent word counting."""

    target_word: str = Field(..., description="Word to count")
    target_root: Optional[str] = Field(None, description="Root for ROOT_BASED matching")

    form_inclusion: Literal[
        "exact_only", "with_prefixes", "with_suffixes",
        "with_both", "lemma_based", "root_based", "all_derivatives"
    ] = "exact_only"

    normalization: NormalizationConfig = Field(default_factory=NormalizationConfig)
    scope: ScopeSpecification = Field(default_factory=lambda: ScopeSpecification(type=ScopeType.ENTIRE_QURAN))
    include_basmalah: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "target_word": "يوم",
                "form_inclusion": "exact_only",
                "normalization": {"level": "tashkeel_removed"},
                "scope": {"type": "entire_quran"},
                "include_basmalah": True
            }
        }


class EntitySearchRequest(BaseModel):
    """Request for entity search (Divine Names, Prophets, etc.)."""

    entity_type: Literal["divine_name", "prophet", "angel", "place", "people"]
    entity_key: Optional[str] = Field(None, description="Specific entity to search, or None for all")
    include_prefixed_forms: bool = True
    scope: ScopeSpecification = Field(default_factory=lambda: ScopeSpecification(type=ScopeType.ENTIRE_QURAN))


class AnalysisRequestComplete(BaseModel):
    """Complete analysis request with all options."""

    # Script and Qira'at selection
    script: Literal["uthmani", "uthmani_min", "simple"] = "uthmani"
    qiraat: Literal["hafs", "warsh", "qalun"] = "hafs"

    # Scope specification
    scope: ScopeSpecification = Field(default_factory=lambda: ScopeSpecification(type=ScopeType.ENTIRE_QURAN))

    # Normalization configuration
    normalization: NormalizationConfig = Field(default_factory=NormalizationConfig)

    # Analysis type
    analysis_type: Literal[
        "letter_count", "letter_frequency", "word_count", "word_frequency",
        "specific_word_search", "root_extraction", "abjad_cumulative",
        "verse_count", "entity_search", "verse_similarity"
    ]

    # Analysis-specific parameters
    parameters: Dict[str, Any] = Field(default_factory=dict)

    # Options
    include_basmalah: bool = True
    generate_audit_receipt: bool = True


#### Analysis Response (Full Schema)

```python
class WordMatch(BaseModel):
    """A single word match in search results."""
    surah: int
    verse: int
    word_index: int
    matched_form: str
    base_form: str
    has_prefix: bool
    has_suffix: bool
    context_before: Optional[str] = None
    context_after: Optional[str] = None


class WordCountResult(BaseModel):
    """Result of transparent word count."""

    # Methodology (for reproducibility)
    target_word: str
    form_inclusion: str
    normalization_level: str
    scope_description: str
    include_basmalah: bool

    # Results
    count: int
    matches: List[WordMatch]

    # Audit trail
    methodology_description: str  # Human-readable
    checksum: str  # SHA256 of methodology + scope
    timestamp: datetime


class EntitySearchResult(BaseModel):
    """Result of entity search."""
    entity_type: str
    entity_key: str
    occurrences: List[WordMatch]
    total_count: int
    forms_found: Dict[str, int]  # Form → count mapping


class LetterCountResult(BaseModel):
    """Result of letter counting analysis."""
    total_letters: int
    letter_frequencies: Dict[str, int]
    scope_description: str
    normalization_applied: str


class AbjadResult(BaseModel):
    """Result of Abjad calculation."""
    text: str
    total_value: int
    letter_values: Dict[str, int]
    system: Literal["mashriqi", "maghribi"]


class AnalysisResponse(BaseModel):
    """Generic analysis response wrapper."""
    success: bool
    analysis_type: str
    result: Dict[str, Any]  # Type-specific result

    # Audit information
    audit_receipt_id: Optional[str] = None
    execution_time_ms: float
    timestamp: datetime

    # Methodology transparency
    methodology: Dict[str, str]


#### Error Response Schema

```python
class ErrorDetail(BaseModel):
    """Detailed error information."""
    field: Optional[str] = None
    message: str
    code: str


class ErrorResponse(BaseModel):
    """Standard error response format."""
    success: Literal[False] = False
    error: str
    error_code: str
    details: List[ErrorDetail] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Verse not found",
                "error_code": "VERSE_NOT_FOUND",
                "details": [{"field": "location", "message": "Surah 1 has only 7 verses", "code": "INVALID_VERSE"}],
                "timestamp": "2024-12-16T10:30:00Z",
                "request_id": "abc-123"
            }
        }
```

### 10.5. API Endpoint Summary

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| `GET` | `/health` | Health check | - | `HealthResponse` |
| `GET` | `/integrity` | Integrity verification | - | `IntegrityReport` |
| `GET` | `/verse/{surah}/{verse}` | Get single verse | Query params | `VerseResponse` |
| `GET` | `/surah/{number}` | Get entire Surah | Query params | `SurahResponse` |
| `GET` | `/strategies` | List available strategies | - | `StrategiesResponse` |
| `POST` | `/analyze` | Run analysis | `AnalysisRequestComplete` | `AnalysisResponse` |
| `POST` | `/count/words` | Transparent word count | `WordCountRequest` | `WordCountResult` |
| `POST` | `/search/entities` | Search entities | `EntitySearchRequest` | `EntitySearchResult` |
| `POST` | `/search/divine-names` | Search Divine Names | `EntitySearchRequest` | `EntitySearchResult` |
| `POST` | `/search/prophets` | Search Prophet mentions | `EntitySearchRequest` | `EntitySearchResult` |
| `GET` | `/morphology/{surah}/{verse}/{word}` | Get word morphology | Path params | `MorphologyResponse` |

---

## 11. Error Handling & Domain Exceptions

```python
class MizanException(Exception):
    """Base exception for all Mizan errors."""

    def __init__(self, message: str, code: str, details: Optional[Dict] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class DomainException(MizanException):
    """Base for domain layer exceptions."""
    pass


class InfrastructureException(MizanException):
    """Base for infrastructure layer exceptions."""
    pass


class ApplicationException(MizanException):
    """Base for application layer exceptions."""
    pass


# Domain Exceptions
class VerseNotFoundException(DomainException):
    """Raised when a verse cannot be found."""

    def __init__(self, location: VerseLocation | str):
        super().__init__(
            message=f"Verse not found: {location}",
            code="VERSE_NOT_FOUND",
            details={"location": str(location)}
        )


class SurahNotFoundException(DomainException):
    """Raised when a Surah cannot be found."""

    def __init__(self, surah_number: int):
        super().__init__(
            message=f"Surah not found: {surah_number}",
            code="SURAH_NOT_FOUND",
            details={"surah_number": surah_number}
        )


class IntegrityViolationException(DomainException):
    """
    Raised when data integrity check fails.
    This is a CRITICAL exception that should halt the application.
    """

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="INTEGRITY_VIOLATION",
            details=details or {}
        )


class InvalidVerseLocationException(DomainException):
    """Raised when verse location is invalid."""

    def __init__(self, surah: int, verse: int, reason: str):
        super().__init__(
            message=f"Invalid verse location {surah}:{verse}: {reason}",
            code="INVALID_LOCATION",
            details={"surah": surah, "verse": verse, "reason": reason}
        )


# Application Exceptions
class StrategyNotFoundException(ApplicationException):
    """Raised when a requested strategy does not exist."""

    def __init__(self, strategy_name: str, strategy_type: str = "unknown"):
        super().__init__(
            message=f"{strategy_type.title()} strategy not found: {strategy_name}",
            code="STRATEGY_NOT_FOUND",
            details={"strategy_name": strategy_name, "strategy_type": strategy_type}
        )


class InvalidConfigurationException(ApplicationException):
    """Raised when analysis configuration is invalid."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            code="INVALID_CONFIGURATION",
            details={"field": field} if field else {}
        )


class AnalysisException(ApplicationException):
    """Raised when analysis execution fails."""

    def __init__(self, message: str, stage: str):
        super().__init__(
            message=f"Analysis failed at {stage}: {message}",
            code="ANALYSIS_FAILED",
            details={"stage": stage}
        )


# Infrastructure Exceptions
class DatabaseException(InfrastructureException):
    """Raised for database-related errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            details={"original_error": str(original_error)} if original_error else {}
        )


class CacheException(InfrastructureException):
    """Raised for cache-related errors."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="CACHE_ERROR"
        )
```

---

## 12. Caching Strategy

```python
from abc import ABC, abstractmethod
from typing import Optional
import json
import redis.asyncio as redis

class IAnalysisCache(ABC):
    """Port for caching analysis results."""

    @abstractmethod
    async def get(self, config_hash: str) -> Optional[AnalysisResult]:
        """Retrieve cached result by config hash."""
        ...

    @abstractmethod
    async def set(
        self,
        config_hash: str,
        result: AnalysisResult,
        ttl_seconds: int = 3600
    ) -> None:
        """Cache result with TTL."""
        ...

    @abstractmethod
    async def invalidate(self, config_hash: str) -> None:
        """Invalidate a specific cache entry."""
        ...

    @abstractmethod
    async def clear_all(self) -> None:
        """Clear all cached results."""
        ...


class RedisAnalysisCache(IAnalysisCache):
    """Redis implementation of analysis cache."""

    KEY_PREFIX = "mizan:analysis:"

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client

    async def get(self, config_hash: str) -> Optional[AnalysisResult]:
        key = f"{self.KEY_PREFIX}{config_hash}"
        data = await self._redis.get(key)

        if data is None:
            return None

        try:
            return AnalysisResult.model_validate_json(data)
        except Exception:
            # Invalid cache data, remove it
            await self.invalidate(config_hash)
            return None

    async def set(
        self,
        config_hash: str,
        result: AnalysisResult,
        ttl_seconds: int = 3600
    ) -> None:
        key = f"{self.KEY_PREFIX}{config_hash}"
        data = result.model_dump_json()
        await self._redis.setex(key, ttl_seconds, data)

    async def invalidate(self, config_hash: str) -> None:
        key = f"{self.KEY_PREFIX}{config_hash}"
        await self._redis.delete(key)

    async def clear_all(self) -> None:
        pattern = f"{self.KEY_PREFIX}*"
        cursor = 0
        while True:
            cursor, keys = await self._redis.scan(cursor, match=pattern)
            if keys:
                await self._redis.delete(*keys)
            if cursor == 0:
                break


class InMemoryAnalysisCache(IAnalysisCache):
    """In-memory LRU cache for development/testing."""

    def __init__(self, max_size: int = 100):
        from functools import lru_cache
        self._cache: Dict[str, AnalysisResult] = {}
        self._max_size = max_size

    async def get(self, config_hash: str) -> Optional[AnalysisResult]:
        return self._cache.get(config_hash)

    async def set(
        self,
        config_hash: str,
        result: AnalysisResult,
        ttl_seconds: int = 3600
    ) -> None:
        if len(self._cache) >= self._max_size:
            # Remove oldest entry (simple LRU approximation)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        self._cache[config_hash] = result

    async def invalidate(self, config_hash: str) -> None:
        self._cache.pop(config_hash, None)

    async def clear_all(self) -> None:
        self._cache.clear()
```

---

## 13. Audit & Observability

### 13.1. Domain Events

```python
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from abc import ABC, abstractmethod
from typing import List

@dataclass(frozen=True)
class DomainEvent(ABC):
    """Base class for all domain events."""
    event_id: UUID
    timestamp: datetime

    @property
    @abstractmethod
    def event_type(self) -> str:
        ...


@dataclass(frozen=True)
class AnalysisCompletedEvent(DomainEvent):
    """Emitted when an analysis completes successfully."""
    analysis_id: UUID
    config_hash: str
    verse_count: int
    execution_time_ms: float

    @property
    def event_type(self) -> str:
        return "analysis.completed"


@dataclass(frozen=True)
class AnalysisFailedEvent(DomainEvent):
    """Emitted when an analysis fails."""
    analysis_id: UUID
    error_code: str
    error_message: str

    @property
    def event_type(self) -> str:
        return "analysis.failed"


@dataclass(frozen=True)
class IntegrityCheckPassedEvent(DomainEvent):
    """Emitted when boot-time integrity check passes."""
    checksum: str
    verse_count: int

    @property
    def event_type(self) -> str:
        return "integrity.passed"


@dataclass(frozen=True)
class IntegrityCheckFailedEvent(DomainEvent):
    """Emitted when integrity check fails (CRITICAL)."""
    expected_checksum: str
    actual_checksum: str
    failed_verses: tuple[str, ...]

    @property
    def event_type(self) -> str:
        return "integrity.failed"


class IEventPublisher(ABC):
    """Port for publishing domain events."""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        ...

    @abstractmethod
    async def publish_many(self, events: List[DomainEvent]) -> None:
        ...
```

### 13.2. Structured Logging

```python
import structlog
from typing import Any

def configure_logging() -> None:
    """Configure structured logging for the application."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


class AnalysisLogger:
    """Specialized logger for analysis operations."""

    def __init__(self):
        self._log = structlog.get_logger("mizan.analysis")

    def log_analysis_started(
        self,
        analysis_id: UUID,
        config_hash: str,
        scope_description: str
    ) -> None:
        self._log.info(
            "analysis_started",
            analysis_id=str(analysis_id),
            config_hash=config_hash,
            scope=scope_description,
        )

    def log_analysis_completed(
        self,
        analysis_id: UUID,
        verse_count: int,
        execution_time_ms: float,
    ) -> None:
        self._log.info(
            "analysis_completed",
            analysis_id=str(analysis_id),
            verse_count=verse_count,
            execution_time_ms=execution_time_ms,
        )

    def log_analysis_failed(
        self,
        analysis_id: UUID,
        error: Exception,
    ) -> None:
        self._log.error(
            "analysis_failed",
            analysis_id=str(analysis_id),
            error_type=type(error).__name__,
            error_message=str(error),
            exc_info=error,
        )

    def log_integrity_violation(
        self,
        expected: str,
        actual: str,
    ) -> None:
        self._log.critical(
            "integrity_violation",
            expected_checksum=expected,
            actual_checksum=actual,
            action="APPLICATION_HALT",
        )
```

---

## 14. Scholarly References & Methodology

### 14.1. Methodology Declaration

This section documents the scholarly positions followed by the Mizan Core Engine. **All numerical analysis must be interpreted with these methodological constraints in mind.**

#### Text Source Authentication

| Aspect | Decision | Source/Justification |
|--------|----------|---------------------|
| Primary Text Source | King Fahd Complex, Madinah | Most widely authenticated, reviewed by senior Ulama |
| Default Qira'at | Hafs 'an 'Asim | Most widespread globally (~95% of Muslims) |
| Script Standard | Uthmani Rasm | Preserves original orthography, essential for accurate counting |

#### Counting Methodology

| Aspect | Decision | Scholarly Source |
|--------|----------|------------------|
| Shadda Treatment | Counts as 1 letter | Majority position; Ibn al-Jazari's *Al-Nashr* |
| Alif Khanjariyya | Counted as Alif | Follows Uthmani Rasm tradition |
| Hamza on Carrier | Count Hamza, not carrier | Modern scholarly consensus |
| Basmalah in Al-Fatiha | Counted as Verse 1 | Ijma' (scholarly consensus) |
| Basmalah in other Surahs | Not counted as verse | Standard Mushaf numbering |
| Waqf Signs | Never counted | Not part of original text |

#### Verse Count Standard

The system uses the **Kufan count** (6,236 verses), which is the standard in:
- King Fahd Complex Mushaf
- Egyptian Standard Mushaf
- Most printed Mushafs worldwide

### 14.2. Reference Works

The following scholarly works inform the methodology:

1. **Al-Itqan fi 'Ulum al-Quran** - Imam al-Suyuti
   - Verse counting methodologies
   - Differences between counting schools (Kufan, Basran, etc.)

2. **Al-Nashr fi al-Qira'at al-'Ashr** - Ibn al-Jazari
   - Qira'at differences and their textual implications
   - Letter pronunciation variants

3. **Al-Muqni' fi Rasm Masahif al-Amsar** - Abu 'Amr al-Dani
   - Uthmani orthography rules
   - Regional Mushaf variations

4. **Lisan al-Arab** - Ibn Manzur
   - Arabic root identification
   - Classical letter definitions

5. **Al-Tibyan fi Adab Hamalat al-Quran** - Imam al-Nawawi
   - Proper handling of Quranic text
   - Scholarly protocols

### 14.3. Limitations & Disclaimers

**IMPORTANT:** The Mizan Core Engine is a **tool for scholarly research**, not a source of religious guidance.

1. **Numerical analysis is descriptive, not prescriptive** - The system describes patterns; it does not claim these patterns prove or disprove anything theological.

2. **Methodology affects results** - Different counting methodologies (Kufan vs Basran, etc.) produce different numbers. Results are only meaningful within their methodological context.

3. **Scholarly disagreement exists** - On many counting details, legitimate scholarly disagreement exists. The system's defaults represent one valid position among several.

4. **Not a replacement for traditional scholarship** - This tool assists research; it does not replace the centuries of Islamic scholarly tradition.

5. **Qira'at support is partial** - Full support for all 10 Qira'at with their variants is a long-term goal. Current support focuses on Hafs 'an 'Asim.

---

## 15. Implementation Phases

> **Implementation Philosophy:**
> - **Ship PROVEN features first** - Tier 1-3 (deterministic, reliable)
> - **Defer EXPERIMENTAL features** - Tier 4-5 (requires validation)
> - **Performance-first design** - Pre-compute, index, cache

---

### Phase 1: Core Foundation ✅ PROVEN

**Objective:** Domain layer + Core analysis (100% deterministic operations)

**Duration Target:** Complete before any other phase

**Deliverables:**
- [ ] Value Objects: `VerseLocation`, `TextChecksum`, `AbjadValue`
- [ ] Entities: `Verse`, `Surah`, `SurahMetadata`
- [ ] Enumerations: All `StrEnum` types
- [ ] Repository Interfaces
- [ ] Domain Services: `LetterCounter`, `AbjadCalculator`
- [ ] `ArabicNormalizer` (multi-level normalization)
- [ ] `TransparentWordCounter` (with methodology)
- [ ] Domain Exceptions
- [ ] **Unit tests: 100% coverage, property-based tests**

**Performance Requirements:**
- Letter/word counting: O(n) where n = text length
- Abjad calculation: O(n)
- All operations must be deterministic

---

### Phase 2: Data Layer + Ingestion ✅ PROVEN

**Objective:** PostgreSQL persistence with performance optimization

**Deliverables:**
- [ ] SQLAlchemy async models (`VerseModel`, `SurahMetadataModel`)
- [ ] Database migrations (Alembic)
- [ ] Tanzil XML ingestion service
- [ ] Integrity guard (boot-time verification)
- [ ] **Pre-computed normalized text columns** (see Performance section)
- [ ] **Database indexes** (see Performance section)

**Performance Requirements:**
- Ingestion: < 30 seconds for all 6,236 verses
- Verse lookup by location: < 5ms
- Surah retrieval: < 20ms

---

### Phase 3: Analysis Strategies ✅ PROVEN

**Objective:** Implement Tier 1-2 analysis strategies

**Deliverables:**
- [ ] Normalization Strategies (all)
- [ ] Letter Calculation Strategies
- [ ] Word Calculation Strategies
- [ ] Abjad Strategies
- [ ] Scope Specifications (all)
- [ ] Strategy Factory
- [ ] **Property-based tests (Hypothesis, 1000+ examples)**

**Performance Requirements:**
- Strategy execution: < 100ms for single Surah scope
- Full Quran analysis: < 2 seconds

---

### Phase 4: Morphology + Entity Search ✅ PROVEN (Data Lookup)

**Objective:** Integrate MASAQ morphological data and entity search

**Deliverables:**
- [ ] `WordMorphologyModel` (database table)
- [ ] `EntityOccurrenceModel` (pre-indexed entities)
- [ ] MASAQ ingestion service
- [ ] Entity search strategies (Divine Names, Prophets)
- [ ] **Pre-indexed entity occurrences** (see Performance section)

**Performance Requirements:**
- Morphology lookup: O(1) - database index lookup
- Entity search (single entity): < 50ms
- Entity search (all Divine Names): < 500ms

---

### Phase 5: Application Layer + API ✅ PROVEN

**Objective:** REST API with caching

**Deliverables:**
- [ ] `MizanAnalyzerService`
- [ ] FastAPI application
- [ ] All endpoints (see Section 10.5)
- [ ] Redis caching layer
- [ ] Audit receipt generation
- [ ] Rate limiting
- [ ] OpenAPI documentation

**Performance Requirements:**
- API response (cached): < 10ms
- API response (uncached): < 200ms
- Concurrent requests: 100+ RPS

---

### Phase 6: DevOps + Production ✅ PROVEN

**Objective:** Production-ready deployment

**Deliverables:**
- [ ] Docker containerization
- [ ] Docker Compose (PostgreSQL + Redis + API)
- [ ] Health check endpoints
- [ ] Structured logging (JSON)
- [ ] Performance benchmarks (documented)
- [ ] Security review

---

### Phase 7: EXPERIMENTAL Features ⚠️ (Deferred)

> **⚠️ DO NOT IMPLEMENT UNTIL PHASES 1-6 COMPLETE**
>
> These features require validation research before implementation.

**Tier 4: Semantic Analysis (EXPERIMENTAL)**
- [ ] AraBERT integration
- [ ] Verse embeddings pre-computation
- [ ] Similarity search
- [ ] **REQUIRED: Validation against scholarly tafsir (>80% accuracy)**

**Tier 5: Structural Analysis (RESEARCH TOOLS)**
- [ ] Ring composition scoring
- [ ] Symmetry analysis
- [ ] **REQUIRED: Clear "research tool" labeling in UI/API**

**Go/No-Go Criteria:**
- If semantic accuracy < 80%: Do not expose in production API
- If scholarly validation unavailable: Keep as internal research tool only

---

## 15.1. Performance Design Requirements

### 15.1.1. Pre-Computation Strategy

**Problem:** Runtime text processing is expensive.
**Solution:** Pre-compute and store normalized forms during ingestion.

```sql
-- VerseModel should store pre-computed normalized text
CREATE TABLE verses (
    id SERIAL PRIMARY KEY,
    surah_number INT NOT NULL,
    verse_number INT NOT NULL,

    -- Original text (immutable)
    text_uthmani TEXT NOT NULL,
    text_uthmani_min TEXT NOT NULL,
    text_simple TEXT NOT NULL,

    -- PRE-COMPUTED normalized forms (for fast search/count)
    text_normalized_full TEXT NOT NULL,      -- Full normalization
    text_no_tashkeel TEXT NOT NULL,          -- Diacritics removed only
    text_search TEXT NOT NULL,               -- Optimized for search

    -- PRE-COMPUTED counts (avoid runtime counting)
    letter_count INT NOT NULL,
    word_count INT NOT NULL,
    abjad_value_mashriqi INT NOT NULL,

    -- Structural metadata
    juz_number INT NOT NULL,
    hizb_number INT NOT NULL,
    page_number INT NOT NULL,

    UNIQUE(surah_number, verse_number)
);
```

**Performance Impact:**
| Operation | Without Pre-compute | With Pre-compute |
|-----------|--------------------|--------------------|
| Word count (full Quran) | ~500ms (runtime) | ~5ms (SUM query) |
| Letter frequency | ~800ms | ~10ms |
| Normalized search | ~300ms | ~20ms |

### 15.1.2. Database Indexing Strategy

```sql
-- Primary lookup indexes
CREATE INDEX idx_verse_location ON verses(surah_number, verse_number);
CREATE INDEX idx_verse_juz ON verses(juz_number);
CREATE INDEX idx_verse_hizb ON verses(hizb_number);

-- Full-text search (PostgreSQL)
CREATE INDEX idx_verse_text_search ON verses USING GIN(to_tsvector('arabic', text_search));

-- Morphology indexes (critical for Tier 3)
CREATE INDEX idx_morph_location ON word_morphology(surah_number, verse_number, word_index);
CREATE INDEX idx_morph_root ON word_morphology(root);
CREATE INDEX idx_morph_lemma ON word_morphology(lemma);
CREATE INDEX idx_morph_pos ON word_morphology(pos_tag);

-- Entity search indexes
CREATE INDEX idx_entity_type_key ON entity_occurrences(entity_type, entity_key);
CREATE INDEX idx_entity_location ON entity_occurrences(surah_number, verse_number);
```

**Query Performance Targets:**
| Query Type | Target | Index Used |
|------------|--------|------------|
| Single verse by location | < 1ms | `idx_verse_location` |
| All verses in Juz | < 10ms | `idx_verse_juz` |
| Words by root | < 20ms | `idx_morph_root` |
| Entity search | < 50ms | `idx_entity_type_key` |

### 15.1.3. Caching Strategy

```python
CACHE_CONFIG = {
    # High-frequency, immutable data - cache aggressively
    "verse_by_location": {
        "ttl": 86400,  # 24 hours (data never changes)
        "key_pattern": "mizan:verse:{surah}:{verse}",
    },
    "surah_metadata": {
        "ttl": 86400,
        "key_pattern": "mizan:surah:{number}",
    },

    # Analysis results - cache by methodology hash
    "analysis_result": {
        "ttl": 3600,  # 1 hour
        "key_pattern": "mizan:analysis:{methodology_hash}",
    },

    # Entity occurrences - pre-load at startup
    "entity_occurrences": {
        "ttl": 86400,
        "key_pattern": "mizan:entity:{type}:{key}",
        "preload": True,  # Load all into Redis at boot
    },
}
```

**Cache Hit Targets:**
| Endpoint | Cache Hit Rate Target |
|----------|----------------------|
| GET /verse | > 95% |
| GET /surah | > 95% |
| POST /analyze (same query) | > 80% |
| POST /search/entities | > 90% |

### 15.1.4. Connection Pooling

```python
# Database connection pool
DATABASE_CONFIG = {
    "pool_size": 10,          # Base connections
    "max_overflow": 20,       # Additional under load
    "pool_timeout": 30,       # Wait for connection
    "pool_recycle": 1800,     # Recycle connections (30 min)
    "pool_pre_ping": True,    # Verify connection health
}

# Redis connection pool
REDIS_CONFIG = {
    "max_connections": 50,
    "socket_timeout": 5,
    "socket_connect_timeout": 5,
    "retry_on_timeout": True,
}
```

### 15.1.5. Async Everywhere

```python
# ALL database operations MUST be async
async def get_verse(self, location: VerseLocation) -> Verse:
    async with self._session() as session:
        result = await session.execute(
            select(VerseModel).where(
                VerseModel.surah_number == location.surah_number,
                VerseModel.verse_number == location.verse_number
            )
        )
        return self._to_domain(result.scalar_one())

# ALL API endpoints MUST be async
@router.get("/verse/{surah}/{verse}")
async def get_verse(surah: int, verse: int) -> VerseResponse:
    ...
```

### 15.1.6. Batch Operations

```python
# WRONG: N+1 queries
for verse_num in range(1, 287):
    verse = await repo.get_verse(VerseLocation(2, verse_num))  # 286 queries!

# RIGHT: Single batch query
verses = await repo.get_verses_in_surah(2)  # 1 query
```

### 15.1.7. Performance Benchmarks (Required)

Before production deployment, the following benchmarks MUST pass:

| Operation | Target | Method |
|-----------|--------|--------|
| Single verse lookup | < 5ms (p99) | `GET /verse/1/1` |
| Surah retrieval (Al-Baqarah) | < 50ms (p99) | `GET /surah/2` |
| Letter count (full Quran) | < 100ms | `POST /analyze` |
| Word count (full Quran) | < 100ms | `POST /analyze` |
| Entity search (Allah) | < 50ms | `POST /search/entities` |
| Concurrent load (100 RPS) | < 200ms (p99) | Load test |
| Memory usage (idle) | < 512MB | Container metrics |
| Memory usage (under load) | < 1GB | Container metrics |

---

## 16. Implementation Readiness Checklist

This section summarizes the implementation readiness of the Mizan Core Engine based on this PSD.

### 16.1. Data Sources ✅ READY

| Component | Status | Notes |
|-----------|--------|-------|
| **Primary Text Sources** | | |
| Tanzil Uthmani XML | ✅ Ready | `quran/uthmani/quran-uthmani.xml` |
| Tanzil Uthmani-min XML | ✅ Ready | `quran/uthmani-min/quran-uthmani-min.xml` |
| Tanzil Simple XML | ✅ Ready | `quran/simple/quran-simple.xml` |
| XML Structure Documented | ✅ Ready | Section 8.2 |
| Basmalah Handling Documented | ✅ Ready | Section 3.3, bismillah attribute |
| Surah Metadata (114 Surahs) | ✅ Ready | Section 8.3 SURAH_METADATA |
| Verse Counts per Surah | ✅ Ready | EXPECTED_VERSE_COUNTS |
| **Morphological Data Sources (Tier 3)** | | |
| MASAQ Dataset | ✅ Specified | 131K entries, CC BY 4.0, Section 8.5 |
| Quranic Arabic Corpus (QAC) | ✅ Specified | 77,430 words, GNU GPL, validation source |
| Morphology Ingestion Pipeline | ✅ Specified | `MorphologyIngestionService`, Section 8.5 |
| **Reference Data** | | |
| Divine Names (99+) | ✅ Specified | Section 6.4, with variants |
| Prophet Names (25+) | ✅ Specified | Section 6.4, with variants |
| Angel Names | ✅ Specified | Section 6.4 |
| Place Names | ✅ Specified | Section 6.4 |
| People Names | ✅ Specified | Section 6.4 |

### 16.2. Domain Layer ✅ FULLY SPECIFIED

| Component | Status | PSD Section |
|-----------|--------|-------------|
| `VerseLocation` Value Object | ✅ Specified | 5.1 |
| `TextChecksum` Value Object | ✅ Specified | 5.1 |
| `AbjadValue` Value Object | ✅ Specified | 5.1 |
| `SurahMetadata` Value Object | ✅ Specified | 5.1 |
| `Verse` Entity | ✅ Specified | 5.3 |
| `Surah` Entity | ✅ Specified | 5.3 |
| `AnalysisResult` Entity | ✅ Specified | 5.3 |
| All Enumerations | ✅ Specified | 5.2 |
| `IQuranRepository` Interface | ✅ Specified | 5.4 |
| `ISurahMetadataRepository` Interface | ✅ Specified | 5.4 |
| `LetterCounter` Service | ✅ Specified | 5.5 |
| `AbjadCalculator` Service | ✅ Specified | 5.5 |
| Domain Exceptions | ✅ Specified | 11 |

### 16.3. Analysis Engine ✅ FULLY SPECIFIED

| Strategy Type | Strategies | Status |
|---------------|------------|--------|
| **Tier 1-2: Core Analysis** | | |
| Normalization | `RemoveTashkeelStrategy`, `UnifyAlifsStrategy`, `PreserveAllStrategy`, `CompositeNormalizationStrategy` | ✅ Specified |
| Advanced Normalization | `ArabicNormalizer` with multi-level normalization (Section 8.6) | ✅ Specified |
| Calculation (Letter) | `LetterCountStrategy`, `LetterFrequencyStrategy` | ✅ Specified |
| Calculation (Abjad) | `AbjadCumulativeStrategy`, `ModularArithmeticStrategy`, `PrimeCheckStrategy` | ✅ Specified |
| Calculation (Word) | `WordCountStrategy`, `WordFrequencyStrategy`, `SpecificWordSearchStrategy`, `RootExtractionStrategy`, `VerseCountStrategy` | ✅ Specified |
| Transparent Counting | `TransparentWordCounter`, `WordCountMethodology` (Section 8.7) | ✅ Specified |
| Scope | `EntireQuranScope`, `SurahScope`, `VerseRangeScope`, `JuzScope`, `RevelationTypeScope` | ✅ Specified |
| **Tier 3: Entity Search (Section 6.5)** | | |
| Divine Name Search | `DivineNameSearchStrategy` with variant handling | ✅ Specified |
| Prophet Search | `ProphetSearchStrategy` with story context | ✅ Specified |
| General Entity | `IEntitySearchStrategy` interface | ✅ Specified |
| **Tier 4: Semantic Analysis ⚠️ EXPERIMENTAL** | | |
| Verse Similarity | `VerseSimilarityStrategy` with AraBERT | ⚠️ Experimental |
| Co-occurrence Network | `CoOccurrenceNetworkStrategy` | ✅ Specified (deterministic) |
| Community Detection | Louvain algorithm | ✅ Specified (deterministic) |
| **Tier 5: Structural Analysis ⚠️ RESEARCH TOOLS** | | |
| Verse Ending Analysis | `فواصل` pattern detection | ✅ Specified (objective) |
| Repeated Phrase Detection | Cross-verse phrase matching | ✅ Specified (objective) |
| Structural Tools | `StructuralAnalysisTool` | ⚠️ Research tool |
| Symmetry Analysis | Chiastic structure scoring | ⚠️ Research tool |
| **Factory & Orchestration** | | |
| Factory | `StrategyFactory` | ✅ Specified |

### 16.4. Infrastructure Layer ✅ FULLY SPECIFIED

| Component | Status | PSD Section |
|-----------|--------|-------------|
| **Database Models** | | |
| SQLAlchemy Models | ✅ Specified | 9.1 |
| `VerseModel` | ✅ Specified | 9.1 |
| `SurahMetadataModel` | ✅ Specified | 9.1 |
| `IngestionLogModel` | ✅ Specified | 9.1 |
| `AnalysisAuditModel` | ✅ Specified | 9.1 |
| `WordMorphologyModel` | ✅ Specified | 9.1 (Tier 3) |
| `EntityOccurrenceModel` | ✅ Specified | 9.1 (Tier 3) |
| **Repositories** | | |
| `PostgresQuranRepository` | ✅ Specified | 9.2 |
| **Ingestion Services** | | |
| `QuranIngestionService` | ✅ Specified | 8.3 |
| `MorphologyIngestionService` | ✅ Specified | 8.5 |
| Integrity Guard | ✅ Specified | 8.4 |
| **Text Processing Services** | | |
| `ArabicNormalizer` | ✅ Specified | 8.6 |
| `TransparentWordCounter` | ✅ Specified | 8.7 |
| **Caching** | | |
| Redis Cache Configuration | ✅ Specified | 12 |

### 16.5. API Layer ✅ FULLY SPECIFIED

| Component | Status | PSD Section |
|-----------|--------|-------------|
| FastAPI Application | ✅ Specified | 10.1 |
| Analysis Endpoints | ✅ Specified | 10.2 |
| Verse/Surah Endpoints | ✅ Specified | 10.2 |
| Health Endpoint | ✅ Specified | 10.2 |
| Request/Response DTOs | ✅ Specified | 10.2 |
| Error Responses | ✅ Specified | 11 |

### 16.6. DevOps ✅ FULLY SPECIFIED

| Component | Status | PSD Section |
|-----------|--------|-------------|
| `pyproject.toml` | ✅ Specified | Appendix C |
| Optional Dependencies: `[minimal]` | ✅ Specified | Core without ML |
| Optional Dependencies: `[ml]` | ✅ Specified | Full ML capabilities |
| Optional Dependencies: `[dev]` | ✅ Specified | Development tools |
| `docker-compose.yml` | ✅ Specified | Appendix C |
| `Dockerfile` | ✅ Specified | Appendix C |
| `alembic.ini` | ✅ Specified | Appendix C |
| `.env.example` | ✅ Specified | Appendix C |
| Project Structure | ✅ Specified | Appendix A |

### 16.7. Items Requiring First-Run Computation

These items will be computed during the first data ingestion:

| Item | Action |
|------|--------|
| **Tier 1-2: Core Setup** | |
| SHA-256 checksums of Tanzil XML files | Run `sha256sum quran/uthmani/quran-uthmani.xml` etc. |
| Content checksums | Computed during ingestion |
| Juz/Hizb/Rub boundaries per verse | Use Tanzil Juz meta file or scholarly reference |
| Page numbers (Madinah Mushaf) | Use Tanzil page meta file |
| Sajdah verse locations | 15 verses (documented in scholarly sources) |
| **Tier 3: Morphological Data** | |
| MASAQ Dataset download | Download from `data.mendeley.com/datasets/9yvrzxktmr/5` |
| MASAQ data ingestion | Run `MorphologyIngestionService.ingest_masaq()` |
| Entity occurrence indexing | Pre-index Divine Names, Prophets, etc. |
| Morphology validation | Cross-check with QAC for 99%+ accuracy |
| **Tier 4: Semantic Analysis (Optional)** | |
| AraBERT model download | Download `aubmindlab/bert-base-arabertv2` (~500MB) |
| Verse embeddings pre-computation | Run `VerseSimilarityStrategy.build_index()` |
| Embedding index serialization | Save FAISS/numpy index to disk |
| **Tier 5: Structural Analysis (Optional)** | |
| Verse similarity matrices | Compute per-surah on demand |
| Co-occurrence networks | Build on first query, cache results |

### 16.8. Implementation Order Recommendation

```
PHASE 1: Foundation (Tier 1-2)
==============================

1. Project Setup
   ├── Create project directory structure (Appendix A)
   ├── Copy pyproject.toml, docker-compose.yml, Dockerfile
   ├── Initialize git repository
   └── Run: pip install -e ".[dev]"

2. Domain Layer (Zero Dependencies)
   ├── src/mizan/domain/enums/*.py
   ├── src/mizan/domain/value_objects/*.py
   ├── src/mizan/domain/entities/*.py
   ├── src/mizan/domain/services/*.py
   ├── src/mizan/domain/repositories/interfaces.py
   ├── src/mizan/domain/exceptions.py
   └── tests/unit/domain/

3. Core Analysis Engine
   ├── src/mizan/analysis/strategies/normalization/
   ├── src/mizan/analysis/strategies/calculation/
   ├── src/mizan/analysis/strategies/scope/
   ├── src/mizan/analysis/factory.py
   ├── src/mizan/infrastructure/text/normalizer.py (ArabicNormalizer)
   ├── src/mizan/infrastructure/text/counter.py (TransparentWordCounter)
   └── tests/property/

4. Infrastructure Layer
   ├── docker-compose up -d (PostgreSQL + Redis)
   ├── src/mizan/infrastructure/persistence/models.py
   ├── alembic init & migrations
   ├── src/mizan/infrastructure/persistence/repositories.py
   ├── src/mizan/infrastructure/ingestion/
   └── scripts/ingest_tanzil.py (FIRST DATA INGESTION)

5. Application Layer
   ├── src/mizan/application/services/
   ├── src/mizan/application/dtos/
   └── tests/integration/

6. API Layer
   ├── src/mizan/api/main.py
   ├── src/mizan/api/routers/
   ├── src/mizan/api/dependencies.py
   └── Run: uvicorn mizan.api.main:app --reload

PHASE 2: Morphology & Entities (Tier 3)
========================================

7. Morphological Data Integration
   ├── Download MASAQ dataset
   ├── src/mizan/infrastructure/persistence/models.py (add WordMorphologyModel)
   ├── src/mizan/infrastructure/persistence/models.py (add EntityOccurrenceModel)
   ├── alembic revision --autogenerate (new tables)
   ├── src/mizan/infrastructure/ingestion/morphology_service.py
   ├── scripts/ingest_masaq.py (MASAQ DATA INGESTION)
   └── tests/integration/test_morphology.py

8. Entity Search Strategies
   ├── src/mizan/analysis/strategies/entity/divine_names.py
   ├── src/mizan/analysis/strategies/entity/prophets.py
   ├── src/mizan/api/routers/entities.py
   └── tests/integration/test_entity_search.py

PHASE 3: Advanced Analysis (Tier 4-5) [Optional]
=================================================

9. Semantic Analysis (requires ML dependencies)
   ├── pip install -e ".[ml]"
   ├── Download AraBERT model
   ├── src/mizan/analysis/strategies/semantic/similarity.py
   ├── src/mizan/analysis/strategies/semantic/cooccurrence.py
   ├── scripts/precompute_embeddings.py
   └── tests/integration/test_semantic.py

10. Structural Analysis Tools
    ├── src/mizan/analysis/tools/structural.py
    ├── src/mizan/api/routers/structural.py
    └── tests/integration/test_structural.py
```

### 16.9. Final Verification Checklist

Before marking the project as production-ready:

**Phase 1: Core System (Required)**
- [ ] All Tanzil XML files ingested successfully
- [ ] File checksums recorded and verified
- [ ] Total verse count = 6,236
- [ ] All 114 Surahs with correct verse counts
- [ ] Basmalah handling verified for all Surahs
- [ ] Letter count for Al-Fatiha matches scholarly consensus
- [ ] Abjad value for Bismillah = 786 (Mashriqi system)
- [ ] ArabicNormalizer handles all diacritic edge cases
- [ ] TransparentWordCounter produces auditable results
- [ ] Property-based tests passing with 1000+ examples
- [ ] Boot-time integrity check passes
- [ ] API documentation accessible at `/docs`
- [ ] All endpoints return correct responses
- [ ] Audit trail logging working
- [ ] Redis caching functional
- [ ] Docker containers healthy

**Phase 2: Morphology & Entities (Required for Full Analysis)**
- [ ] MASAQ dataset downloaded and validated
- [ ] 77,430 words with morphological data (EXPECTED_WORD_COUNT)
- [ ] WordMorphologyModel populated with all entries
- [ ] Root extraction accuracy validated against QAC
- [ ] Divine Names search returns all 99+ names
- [ ] Prophet Names search returns all 25+ prophets
- [ ] EntityOccurrenceModel indexed for fast lookups
- [ ] Entity variant matching working (e.g., الله, اللّٰه)

**Phase 3: Advanced Analysis (Optional)**
- [ ] AraBERT model loaded successfully (if ML enabled)
- [ ] Verse embeddings pre-computed (6,236 vectors)
- [ ] Similarity search returning semantically relevant verses
- [ ] Co-occurrence network building correctly
- [ ] Community detection identifying word clusters
- [ ] Structural analysis tools operational
- [ ] Ring structure scoring producing valid results

---

## Appendix A: Project Structure

```
mizan/
├── src/
│   └── mizan/
│       ├── __init__.py
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── entities/
│       │   │   ├── __init__.py
│       │   │   ├── verse.py
│       │   │   └── surah.py
│       │   ├── value_objects/
│       │   │   ├── __init__.py
│       │   │   ├── verse_location.py
│       │   │   ├── checksum.py
│       │   │   └── abjad_value.py
│       │   ├── enums/
│       │   │   ├── __init__.py
│       │   │   ├── script_type.py
│       │   │   ├── qiraat_type.py
│       │   │   └── basmalah_status.py
│       │   ├── services/
│       │   │   ├── __init__.py
│       │   │   ├── letter_counter.py
│       │   │   └── abjad_calculator.py
│       │   ├── repositories/
│       │   │   ├── __init__.py
│       │   │   └── interfaces.py
│       │   └── exceptions.py
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── strategies/
│       │   │   ├── __init__.py
│       │   │   ├── normalization/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── base.py
│       │   │   │   ├── remove_tashkeel.py
│       │   │   │   └── unify_alifs.py
│       │   │   ├── calculation/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── base.py
│       │   │   │   ├── letter_count.py
│       │   │   │   ├── word_count.py
│       │   │   │   └── abjad.py
│       │   │   ├── scope/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── base.py
│       │   │   │   └── specifications.py
│       │   │   ├── entity/                    # Tier 3
│       │   │   │   ├── __init__.py
│       │   │   │   ├── base.py
│       │   │   │   ├── divine_names.py
│       │   │   │   └── prophets.py
│       │   │   └── semantic/                  # Tier 4
│       │   │       ├── __init__.py
│       │   │       ├── similarity.py
│       │   │       └── cooccurrence.py
│       │   ├── tools/                         # Tier 5
│       │   │   ├── __init__.py
│       │   │   └── structural.py
│       │   └── factory.py
│       ├── application/
│       │   ├── __init__.py
│       │   ├── services/
│       │   │   ├── __init__.py
│       │   │   └── analyzer_service.py
│       │   ├── dtos/
│       │   │   ├── __init__.py
│       │   │   ├── requests.py
│       │   │   └── responses.py
│       │   └── events/
│       │       ├── __init__.py
│       │       └── domain_events.py
│       ├── infrastructure/
│       │   ├── __init__.py
│       │   ├── persistence/
│       │   │   ├── __init__.py
│       │   │   ├── models.py
│       │   │   ├── repositories.py
│       │   │   └── migrations/
│       │   ├── cache/
│       │   │   ├── __init__.py
│       │   │   └── redis_cache.py
│       │   ├── ingestion/
│       │   │   ├── __init__.py
│       │   │   ├── quran_ingestion.py
│       │   │   └── morphology_service.py      # Tier 3
│       │   ├── text/                          # Text processing
│       │   │   ├── __init__.py
│       │   │   ├── normalizer.py              # ArabicNormalizer
│       │   │   └── counter.py                 # TransparentWordCounter
│       │   └── integrity/
│       │       ├── __init__.py
│       │       └── guard.py
│       └── api/
│           ├── __init__.py
│           ├── main.py
│           ├── dependencies.py
│           ├── routers/
│           │   ├── __init__.py
│           │   ├── analysis.py
│           │   ├── verses.py
│           │   ├── entities.py                # Tier 3
│           │   ├── semantic.py                # Tier 4
│           │   ├── structural.py              # Tier 5
│           │   └── health.py
│           └── middleware/
│               ├── __init__.py
│               └── error_handler.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── domain/
│   │   ├── analysis/
│   │   └── text/                              # Normalizer, Counter tests
│   ├── integration/
│   │   ├── infrastructure/
│   │   ├── test_morphology.py
│   │   ├── test_entity_search.py
│   │   ├── test_semantic.py
│   │   └── test_structural.py
│   └── property/
│       └── test_invariants.py
├── scripts/
│   ├── ingest_tanzil.py
│   ├── ingest_masaq.py                        # Tier 3
│   ├── precompute_embeddings.py               # Tier 4
│   └── verify_integrity.py
├── data/                                      # External datasets
│   ├── masaq/                                 # MASAQ morphology
│   └── embeddings/                            # Pre-computed embeddings
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── alembic/
│   └── versions/
├── pyproject.toml
├── alembic.ini
└── README.md
```

---

## Appendix B: Abjad Value Mappings

### Mashriqi (Eastern) System

| Letter | Name | Value | Letter | Name | Value |
|--------|------|-------|--------|------|-------|
| ا | Alif | 1 | ي | Ya | 10 |
| ب | Ba | 2 | ك | Kaf | 20 |
| ج | Jim | 3 | ل | Lam | 30 |
| د | Dal | 4 | م | Mim | 40 |
| ه | Ha | 5 | ن | Nun | 50 |
| و | Waw | 6 | س | Sin | 60 |
| ز | Zayn | 7 | ع | 'Ayn | 70 |
| ح | Ha | 8 | ف | Fa | 80 |
| ط | Ta | 9 | ص | Sad | 90 |
| ق | Qaf | 100 | ث | Tha | 500 |
| ر | Ra | 200 | خ | Kha | 600 |
| ش | Shin | 300 | ذ | Dhal | 700 |
| ت | Ta | 400 | ض | Dad | 800 |
| ظ | Zha | 900 | غ | Ghayn | 1000 |

---

## Appendix C: Project Configuration Files

### pyproject.toml

```toml
[project]
name = "mizan"
version = "0.1.0"
description = "High-precision Quranic text analysis engine"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.11"
authors = [
    { name = "Mizan Contributors" }
]
keywords = ["quran", "arabic", "analysis", "abjad", "gematria", "islamic"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Text Processing :: Linguistic",
    "Topic :: Religion",
    "Natural Language :: Arabic",
]

dependencies = [
    # Core Web Framework
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "httpx>=0.26.0",

    # Database
    "sqlalchemy[asyncio]>=2.0.25",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",

    # Caching
    "redis>=5.0.0",

    # Logging
    "structlog>=24.1.0",

    # Arabic NLP (Tier 1-2)
    "pyarabic>=0.6.15",
    "regex>=2023.12.0",

    # Machine Learning & Embeddings (Tier 4)
    "transformers>=4.36.0",
    "torch>=2.1.0",
    "sentence-transformers>=2.2.0",

    # Graph & Statistical Analysis (Tier 4-5)
    "networkx>=3.2.0",
    "numpy>=1.26.0",
    "scipy>=1.11.0",

    # Topic Modeling (Tier 4)
    "gensim>=4.3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "hypothesis>=6.92.0",
    "mypy>=1.8.0",
    "ruff>=0.1.9",
    "pre-commit>=3.6.0",
]

# Minimal install without ML dependencies (for basic text analysis)
minimal = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy[asyncio]>=2.0.25",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "redis>=5.0.0",
    "structlog>=24.1.0",
    "pyarabic>=0.6.15",
]

# Full ML capabilities
ml = [
    "transformers>=4.36.0",
    "torch>=2.1.0",
    "sentence-transformers>=2.2.0",
    "gensim>=4.3.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/mizan"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --tb=short"
filterwarnings = ["ignore::DeprecationWarning"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
plugins = ["pydantic.mypy"]

[[tool.mypy.overrides]]
module = ["redis.*", "asyncpg.*"]
ignore_missing_imports = true

[tool.ruff]
target-version = "py311"
line-length = 100
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = ["E501"]  # line length handled by formatter

[tool.ruff.isort]
known-first-party = ["mizan"]
```

### docker-compose.yml

```yaml
version: "3.9"

services:
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: mizan-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://mizan:mizan@db:5432/mizan
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=INFO
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./quran:/app/quran:ro  # Read-only Quran data
    command: >
      uvicorn mizan.api.main:app --host 0.0.0.0 --port 8000 --reload
    networks:
      - mizan-network

  db:
    image: postgres:15-alpine
    container_name: mizan-db
    environment:
      POSTGRES_USER: mizan
      POSTGRES_PASSWORD: mizan
      POSTGRES_DB: mizan
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mizan -d mizan"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - mizan-network

  redis:
    image: redis:7-alpine
    container_name: mizan-redis
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - mizan-network

  adminer:
    image: adminer
    container_name: mizan-adminer
    ports:
      - "8080:8080"
    depends_on:
      - db
    networks:
      - mizan-network

volumes:
  postgres-data:
  redis-data:

networks:
  mizan-network:
    driver: bridge
```

### docker/Dockerfile

```dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir build && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels -e .

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user for security
RUN groupadd -r mizan && useradd -r -g mizan mizan

# Install runtime dependencies only
COPY --from=builder /app/wheels /app/wheels
RUN pip install --no-cache-dir --no-index --find-links=/app/wheels mizan && \
    rm -rf /app/wheels

# Copy application code
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

# Copy Quran data (read-only)
COPY quran/ quran/

# Set ownership
RUN chown -R mizan:mizan /app

USER mizan

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

# Default command
CMD ["uvicorn", "mizan.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### alembic.ini (excerpt)

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

sqlalchemy.url = driver://user:pass@localhost/dbname

[post_write_hooks]
hooks = ruff
ruff.type = exec
ruff.executable = ruff
ruff.options = format REVISION_SCRIPT_FILENAME

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic
```

### Environment Variables (.env.example)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://mizan:mizan@localhost:5432/mizan

# Redis Cache
REDIS_URL=redis://localhost:6379/0

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
DEBUG=false

# Security
SECRET_KEY=your-secret-key-here-change-in-production

# Integrity Verification
EXPECTED_QURAN_CHECKSUM=<computed-sha256-on-first-ingestion>
FAIL_ON_INTEGRITY_ERROR=true
```

---

## Appendix D: External Data Sources & Schemas

### D.1. MASAQ Dataset

**Source:** Mendeley Data - https://data.mendeley.com/datasets/9yvrzxktmr/5
**License:** Creative Commons Attribution 4.0 (CC BY 4.0)
**Citation:** Sawalha, M., Al-Shargi, F., et al. (2024). "Morphologically-Analyzed and Syntactically-Annotated Quran Dataset"

#### Available Formats

| Format | File Extension | Use Case |
|--------|---------------|----------|
| Tab-Separated Values | `.tsv` | Primary ingestion format |
| Comma-Separated Values | `.csv` | Alternative text format |
| SQLite Database | `.db` | Direct database queries |
| JSON | `.json` | API/web integration |

#### Schema (20 Columns)

```python
MASAQ_SCHEMA: Final[Dict[str, type]] = {
    # Location identifiers
    "sura_no": int,           # Surah number (1-114)
    "aya_no": int,            # Verse number
    "word_no": int,           # Word position in verse (1-indexed)
    "segment_no": int,        # Morpheme segment within word

    # Text forms
    "word_uthmani": str,      # Uthmani script word
    "word_imlaei": str,       # Imla'i (simplified) script
    "segment_uthmani": str,   # Morpheme in Uthmani
    "segment_imlaei": str,    # Morpheme in Imla'i

    # Morphological analysis
    "morpheme_type": str,     # PREFIX, STEM, SUFFIX
    "pos_tag": str,           # Part-of-speech (N, V, PART, DET, etc.)
    "root": str,              # Trilateral/quadrilateral root (e.g., ك-ت-ب)
    "lemma": str,             # Dictionary form
    "pattern": str,           # Morphological pattern (فَعَلَ، فَاعِل)

    # Grammatical features
    "person": str,            # 1, 2, 3 or None
    "gender": str,            # M, F or None
    "number": str,            # S (singular), D (dual), P (plural)
    "case_state": str,        # NOM, ACC, GEN / DEF, INDEF
    "mood_voice": str,        # IND, SUBJ, JUS / ACT, PASS

    # Syntactic annotation
    "syntactic_role": str,    # One of 72 syntactic roles
    "irab_description": str,  # Traditional Arabic grammar description
}
```

#### Morphological Tags (POS)

| Tag | Arabic Term | English | Example |
|-----|-------------|---------|---------|
| `N` | اسم | Noun | كِتَاب |
| `PN` | اسم علم | Proper Noun | مُحَمَّد |
| `ADJ` | صفة | Adjective | كَبِير |
| `V` | فعل | Verb | كَتَبَ |
| `PRON` | ضمير | Pronoun | هُوَ |
| `DEM` | اسم إشارة | Demonstrative | هَذَا |
| `REL` | اسم موصول | Relative | الَّذِي |
| `PREP` | حرف جر | Preposition | فِي |
| `CONJ` | حرف عطف | Conjunction | وَ |
| `PART` | حرف | Particle | إِنَّ |
| `DET` | أداة تعريف | Determiner | الـ |
| `NEG` | حرف نفي | Negation | لَا |
| `INTG` | حرف استفهام | Interrogative | هَلْ |
| `VOC` | حرف نداء | Vocative | يَا |
| `INL` | حروف مقطعة | Quranic Initials | الم |

#### Syntactic Roles (72 Tags)

Major categories include:
- **Subject types:** فاعل، نائب فاعل، اسم إن، اسم كان
- **Object types:** مفعول به، مفعول فيه، مفعول معه، مفعول لأجله
- **Complement types:** خبر، حال، تمييز، بدل، نعت
- **Governance:** مجرور، منصوب، مرفوع، مجزوم

### D.2. Quranic Arabic Corpus (QAC)

**Source:** https://corpus.quran.com/download/
**License:** GNU General Public License
**Version:** 0.4

#### File Format (Pipe-Delimited)

```
SURAH|VERSE|WORD|ARABIC_TEXT|MORPHOLOGICAL_FEATURES
1|1|1|بِسْمِ|bi+ POS:P LEM:bi
1|1|2|ٱللَّهِ|POS:PN LEM:{ll~ah ROOT:Alh GEN
1|1|3|ٱلرَّحْمَٰنِ|Al+ POS:ADJ LEM:r~aHoma`n ROOT:rHm GEN
1|1|4|ٱلرَّحِيمِ|Al+ POS:ADJ LEM:r~aHiym ROOT:rHm GEN
```

#### Feature Encoding

| Feature | Format | Example |
|---------|--------|---------|
| Prefix | `prefix+` | `bi+`, `wa+`, `fa+` |
| Part of Speech | `POS:TAG` | `POS:N`, `POS:V` |
| Lemma | `LEM:form` | `LEM:kitAb` |
| Root | `ROOT:letters` | `ROOT:ktb` |
| Gender | `M` or `F` | `M` |
| Number | `S`, `D`, `P` | `P` (plural) |
| Case | `NOM`, `ACC`, `GEN` | `GEN` |
| Person | `1`, `2`, `3` | `3` |
| Aspect | `PERF`, `IMPF`, `IMPV` | `PERF` |

### D.3. Tanzil Metadata

**Source:** https://tanzil.net/docs/quran_metadata
**Download:** `quran-data.xml` (Version 1.0)

The metadata XML contains Juz, Hizb, Rub, Manzil, Page, and Sajda boundaries for all verses.

---

## Appendix E: Structural Division Tables

### E.1. Juz Boundaries (30 Parts)

| Juz | Arabic Name | Start Surah | Start Verse | End Surah | End Verse |
|-----|-------------|-------------|-------------|-----------|-----------|
| 1 | آلم | 1 (Al-Fatiha) | 1 | 2 (Al-Baqarah) | 141 |
| 2 | سَيَقُولُ | 2 (Al-Baqarah) | 142 | 2 (Al-Baqarah) | 252 |
| 3 | تِلْكَ الرُّسُلُ | 2 (Al-Baqarah) | 253 | 3 (Al-Imran) | 92 |
| 4 | لَنْ تَنَالُوا | 3 (Al-Imran) | 93 | 4 (An-Nisa) | 23 |
| 5 | وَالْمُحْصَنَاتُ | 4 (An-Nisa) | 24 | 4 (An-Nisa) | 147 |
| 6 | لَا يُحِبُّ اللَّهُ | 4 (An-Nisa) | 148 | 5 (Al-Ma'idah) | 81 |
| 7 | وَإِذَا سَمِعُوا | 5 (Al-Ma'idah) | 82 | 6 (Al-An'am) | 110 |
| 8 | وَلَوْ أَنَّنَا | 6 (Al-An'am) | 111 | 7 (Al-A'raf) | 87 |
| 9 | قَالَ الْمَلَأُ | 7 (Al-A'raf) | 88 | 8 (Al-Anfal) | 40 |
| 10 | وَاعْلَمُوا | 8 (Al-Anfal) | 41 | 9 (At-Tawbah) | 92 |
| 11 | يَعْتَذِرُونَ | 9 (At-Tawbah) | 93 | 11 (Hud) | 5 |
| 12 | وَمَا مِنْ دَابَّةٍ | 11 (Hud) | 6 | 12 (Yusuf) | 52 |
| 13 | وَمَا أُبَرِّئُ | 12 (Yusuf) | 53 | 14 (Ibrahim) | 52 |
| 14 | رُبَمَا | 15 (Al-Hijr) | 1 | 16 (An-Nahl) | 128 |
| 15 | سُبْحَانَ الَّذِي | 17 (Al-Isra) | 1 | 18 (Al-Kahf) | 74 |
| 16 | قَالَ أَلَمْ | 18 (Al-Kahf) | 75 | 20 (Ta-Ha) | 135 |
| 17 | اقْتَرَبَ | 21 (Al-Anbiya) | 1 | 22 (Al-Hajj) | 78 |
| 18 | قَدْ أَفْلَحَ | 23 (Al-Mu'minun) | 1 | 25 (Al-Furqan) | 20 |
| 19 | وَقَالَ الَّذِينَ | 25 (Al-Furqan) | 21 | 27 (An-Naml) | 55 |
| 20 | أَمَّنْ خَلَقَ | 27 (An-Naml) | 56 | 29 (Al-Ankabut) | 45 |
| 21 | اتْلُ مَا أُوحِيَ | 29 (Al-Ankabut) | 46 | 33 (Al-Ahzab) | 30 |
| 22 | وَمَنْ يَقْنُتْ | 33 (Al-Ahzab) | 31 | 36 (Ya-Sin) | 27 |
| 23 | وَمَا لِيَ | 36 (Ya-Sin) | 28 | 39 (Az-Zumar) | 31 |
| 24 | فَمَنْ أَظْلَمُ | 39 (Az-Zumar) | 32 | 41 (Fussilat) | 46 |
| 25 | إِلَيْهِ يُرَدُّ | 41 (Fussilat) | 47 | 45 (Al-Jathiyah) | 37 |
| 26 | حم | 46 (Al-Ahqaf) | 1 | 51 (Adh-Dhariyat) | 30 |
| 27 | قَالَ فَمَا خَطْبُكُمْ | 51 (Adh-Dhariyat) | 31 | 57 (Al-Hadid) | 29 |
| 28 | قَدْ سَمِعَ | 58 (Al-Mujadila) | 1 | 66 (At-Tahrim) | 12 |
| 29 | تَبَارَكَ | 67 (Al-Mulk) | 1 | 77 (Al-Mursalat) | 50 |
| 30 | عَمَّ | 78 (An-Naba) | 1 | 114 (An-Nas) | 6 |

### E.2. Hizb Boundaries (60 Parts)

| Hizb | Start Surah | Start Verse | | Hizb | Start Surah | Start Verse |
|------|-------------|-------------|---|------|-------------|-------------|
| 1 | 1 | 1 | | 31 | 18 | 75 |
| 2 | 2 | 75 | | 32 | 20 | 1 |
| 3 | 2 | 142 | | 33 | 21 | 1 |
| 4 | 2 | 203 | | 34 | 22 | 1 |
| 5 | 2 | 253 | | 35 | 23 | 1 |
| 6 | 3 | 15 | | 36 | 24 | 21 |
| 7 | 3 | 93 | | 37 | 25 | 21 |
| 8 | 4 | 1 | | 38 | 26 | 111 |
| 9 | 4 | 24 | | 39 | 27 | 56 |
| 10 | 4 | 88 | | 40 | 28 | 51 |
| 11 | 4 | 148 | | 41 | 29 | 46 |
| 12 | 5 | 27 | | 42 | 31 | 22 |
| 13 | 5 | 82 | | 43 | 33 | 31 |
| 14 | 6 | 36 | | 44 | 34 | 24 |
| 15 | 6 | 111 | | 45 | 36 | 28 |
| 16 | 7 | 1 | | 46 | 37 | 145 |
| 17 | 7 | 88 | | 47 | 39 | 32 |
| 18 | 7 | 171 | | 48 | 40 | 41 |
| 19 | 8 | 41 | | 49 | 41 | 47 |
| 20 | 9 | 34 | | 50 | 43 | 24 |
| 21 | 9 | 93 | | 51 | 46 | 1 |
| 22 | 10 | 26 | | 52 | 48 | 18 |
| 23 | 11 | 6 | | 53 | 51 | 31 |
| 24 | 11 | 84 | | 54 | 55 | 1 |
| 25 | 12 | 53 | | 55 | 58 | 1 |
| 26 | 13 | 19 | | 56 | 62 | 1 |
| 27 | 15 | 1 | | 57 | 67 | 1 |
| 28 | 16 | 51 | | 58 | 72 | 1 |
| 29 | 17 | 1 | | 59 | 78 | 1 |
| 30 | 17 | 99 | | 60 | 87 | 1 |

### E.3. Manzil Boundaries (7 Parts for Weekly Reading)

| Manzil | Start Surah | End Surah | Chapters | Arabic Name |
|--------|-------------|-----------|----------|-------------|
| 1 | 1 (Al-Fatiha) | 4 (An-Nisa) | 4 | فَاتِحَة - نِسَاء |
| 2 | 5 (Al-Ma'idah) | 9 (At-Tawbah) | 5 | مَائِدَة - تَوْبَة |
| 3 | 10 (Yunus) | 16 (An-Nahl) | 7 | يُونُس - نَحْل |
| 4 | 17 (Al-Isra) | 25 (Al-Furqan) | 9 | إِسْرَاء - فُرْقَان |
| 5 | 26 (Ash-Shu'ara) | 36 (Ya-Sin) | 11 | شُعَرَاء - يس |
| 6 | 37 (As-Saffat) | 49 (Al-Hujurat) | 13 | صَافَّات - حُجُرَات |
| 7 | 50 (Qaf) | 114 (An-Nas) | 65 | ق - نَاس |

### E.4. Sajdah (Prostration) Verse Locations

```python
SAJDAH_VERSES: Final[List[Tuple[int, int, str]]] = [
    # (surah, verse, type: "obligatory" or "recommended")
    (7, 206, "recommended"),    # Al-A'raf
    (13, 15, "recommended"),    # Ar-Ra'd
    (16, 50, "recommended"),    # An-Nahl
    (17, 109, "recommended"),   # Al-Isra
    (19, 58, "recommended"),    # Maryam
    (22, 18, "recommended"),    # Al-Hajj (first)
    (22, 77, "recommended"),    # Al-Hajj (second)
    (25, 60, "recommended"),    # Al-Furqan
    (27, 26, "recommended"),    # An-Naml
    (32, 15, "obligatory"),     # As-Sajdah
    (38, 24, "recommended"),    # Sad
    (41, 38, "obligatory"),     # Fussilat
    (53, 62, "obligatory"),     # An-Najm
    (84, 21, "obligatory"),     # Al-Inshiqaq
    (96, 19, "obligatory"),     # Al-Alaq
]
```

---

## Appendix F: Missing Enum Definitions

### F.1. WordFormInclusion Enum

```python
class WordFormInclusion(StrEnum):
    """Specifies which word forms to include in counting/search."""

    EXACT_ONLY = "exact_only"
    """Match only the exact form as specified (e.g., يَوْم matches يَوْم only)."""

    WITH_PREFIXES = "with_prefixes"
    """Include forms with attached prefixes (بِيَوْم، وَيَوْم، فَيَوْم، لِيَوْم)."""

    WITH_SUFFIXES = "with_suffixes"
    """Include forms with attached suffixes (يَوْمَهُ، يَوْمِهِ، يَوْمًا)."""

    WITH_BOTH = "with_both"
    """Include forms with both prefixes and suffixes (وَيَوْمَهُمْ)."""

    LEMMA_BASED = "lemma_based"
    """Match all forms sharing the same lemma (dictionary form)."""

    ROOT_BASED = "root_based"
    """Match all forms derived from the same root (e.g., ROOT:y-w-m)."""

    ALL_DERIVATIVES = "all_derivatives"
    """Include all morphological derivatives including plurals (يَوْم، أَيَّام، يَوْمَئِذٍ)."""
```

### F.2. Arabic Prefix/Suffix Definitions

```python
ARABIC_PREFIXES: Final[Dict[str, str]] = {
    "بِ": "bi (with/by)",
    "وَ": "wa (and)",
    "فَ": "fa (so/then)",
    "لِ": "li (for/to)",
    "كَ": "ka (like/as)",
    "الْ": "al (the)",
    "سَ": "sa (will - future marker)",
    "أَ": "a (interrogative)",
}

ARABIC_SUFFIXES: Final[Dict[str, str]] = {
    # Possessive pronouns
    "هُ": "hu (his)",
    "هَا": "ha (her)",
    "هُمْ": "hum (their - masc)",
    "هُنَّ": "hunna (their - fem)",
    "كَ": "ka (your - masc sing)",
    "كِ": "ki (your - fem sing)",
    "كُمْ": "kum (your - plural)",
    "نَا": "na (our)",
    "ي": "i/ya (my)",
    # Case endings
    "ًا": "tanwin fatha (accusative indefinite)",
    "ٌ": "tanwin damma (nominative indefinite)",
    "ٍ": "tanwin kasra (genitive indefinite)",
}
```

---

## Appendix G: Entity Variant Matching Algorithm

### G.1. Prefix-Aware Entity Matching

```python
class EntityVariantMatcher:
    """
    Matches entity names accounting for Arabic prefixes and suffixes.

    Arabic entities can appear with attached particles:
    - الله → بِاللَّهِ (with Allah), وَاللَّهِ (and Allah), لِلَّهِ (for Allah)
    - موسى → فَمُوسَى (then Moses), وَمُوسَى (and Moses)
    """

    # Prefixes that can attach to entities
    MATCHABLE_PREFIXES: Final[frozenset[str]] = frozenset([
        "بِ", "وَ", "فَ", "لِ", "كَ",  # Prepositions/conjunctions
        "أَ", "يَا",                    # Interrogative/vocative
    ])

    # Combined prefix patterns (e.g., وَبِ = "and with")
    COMBINED_PREFIXES: Final[frozenset[str]] = frozenset([
        "وَبِ", "فَبِ", "وَلِ", "فَلِ", "أَفَ", "وَلَ",
    ])

    def __init__(
        self,
        entity_forms: Set[str],
        include_prefixes: bool = True,
        include_combined: bool = True,
    ):
        """
        Args:
            entity_forms: Set of base entity forms to match (e.g., {"الله", "اللّٰه"})
            include_prefixes: Whether to match prefixed forms
            include_combined: Whether to match combined prefix forms
        """
        self._base_forms = frozenset(entity_forms)
        self._include_prefixes = include_prefixes
        self._include_combined = include_combined
        self._all_forms = self._build_all_forms()

    def _build_all_forms(self) -> frozenset[str]:
        """Generate all matchable forms including prefixed variants."""
        all_forms = set(self._base_forms)

        if self._include_prefixes:
            for base in self._base_forms:
                for prefix in self.MATCHABLE_PREFIXES:
                    all_forms.add(prefix + base)

        if self._include_combined:
            for base in self._base_forms:
                for prefix in self.COMBINED_PREFIXES:
                    all_forms.add(prefix + base)

        return frozenset(all_forms)

    def matches(self, word: str) -> bool:
        """Check if word matches any entity form."""
        return word in self._all_forms

    def extract_base_form(self, word: str) -> Optional[str]:
        """Extract the base entity form from a potentially prefixed word."""
        if word in self._base_forms:
            return word

        # Try stripping prefixes
        for prefix in sorted(self.COMBINED_PREFIXES | self.MATCHABLE_PREFIXES,
                           key=len, reverse=True):
            if word.startswith(prefix):
                remainder = word[len(prefix):]
                if remainder in self._base_forms:
                    return remainder

        return None

    def find_in_text(self, text: str) -> List[EntityMatch]:
        """Find all entity matches in text with positions."""
        matches = []
        words = text.split()

        for idx, word in enumerate(words):
            if self.matches(word):
                base = self.extract_base_form(word)
                matches.append(EntityMatch(
                    matched_form=word,
                    base_form=base,
                    word_index=idx,
                    has_prefix=word != base,
                ))

        return matches
```

### G.2. Divine Name Variants

```python
DIVINE_NAME_VARIANTS: Final[Dict[str, Set[str]]] = {
    "الله": {"اللَّهِ", "اللَّهُ", "اللَّهَ", "اللّٰهِ", "اللّٰهُ", "اللّٰهَ"},
    "الرحمن": {"الرَّحْمَٰنِ", "الرَّحْمَٰنُ", "الرَّحْمٰنِ"},
    "الرحيم": {"الرَّحِيمِ", "الرَّحِيمُ", "الرَّحِيمَ"},
    "الرب": {"الرَّبِّ", "الرَّبُّ", "رَبِّ", "رَبُّ", "رَبَّ"},
    # ... (full list in reference data section)
}
```

---

## Appendix H: ArabicNormalizer Implementation

### H.1. Complete Implementation

```python
from enum import StrEnum
from typing import Final, Dict
import unicodedata


class NormalizationLevel(StrEnum):
    """Levels of Arabic text normalization."""
    NONE = "none"                       # No normalization
    TASHKEEL_REMOVED = "no_tashkeel"   # Remove diacritics only
    HAMZA_UNIFIED = "hamza_unified"     # + Unify hamza forms
    ALIF_UNIFIED = "alif_unified"       # + Unify alif forms
    YA_UNIFIED = "ya_unified"           # + Unify ya/alif maqsura
    FULL = "full"                       # All normalizations


class ArabicNormalizer:
    """
    Multi-level Arabic text normalizer for Quranic analysis.

    Normalization is cumulative: each level includes all previous levels.
    """

    # Tashkeel (diacritical marks) - Unicode range
    TASHKEEL: Final[frozenset[str]] = frozenset([
        '\u064B',  # FATHATAN
        '\u064C',  # DAMMATAN
        '\u064D',  # KASRATAN
        '\u064E',  # FATHA
        '\u064F',  # DAMMA
        '\u0650',  # KASRA
        '\u0651',  # SHADDA
        '\u0652',  # SUKUN
        '\u0653',  # MADDAH ABOVE
        '\u0654',  # HAMZA ABOVE
        '\u0655',  # HAMZA BELOW
        '\u0656',  # SUBSCRIPT ALEF
        '\u0657',  # INVERTED DAMMA
        '\u0658',  # NOON GHUNNA
        '\u0670',  # SUPERSCRIPT ALEF (Alif Khanjariyya)
    ])

    # Hamza forms → Alif
    HAMZA_MAP: Final[Dict[str, str]] = {
        '\u0623': '\u0627',  # ALEF WITH HAMZA ABOVE → ALEF
        '\u0625': '\u0627',  # ALEF WITH HAMZA BELOW → ALEF
        '\u0622': '\u0627',  # ALEF WITH MADDA → ALEF
        '\u0624': '\u0648',  # WAW WITH HAMZA → WAW
        '\u0626': '\u064A',  # YEH WITH HAMZA → YEH
    }

    # Alif forms → Plain Alif
    ALIF_MAP: Final[Dict[str, str]] = {
        '\u0671': '\u0627',  # ALEF WASLA → ALEF
        '\u0622': '\u0627',  # ALEF WITH MADDA → ALEF
        '\u0623': '\u0627',  # ALEF WITH HAMZA ABOVE → ALEF
        '\u0625': '\u0627',  # ALEF WITH HAMZA BELOW → ALEF
    }

    # Ya/Alif Maqsura unification
    YA_MAP: Final[Dict[str, str]] = {
        '\u0649': '\u064A',  # ALEF MAKSURA → YEH
    }

    # Small letter markers (Quranic orthography)
    SMALL_LETTERS: Final[frozenset[str]] = frozenset([
        '\u06E5',  # SMALL WAW
        '\u06E6',  # SMALL YEH
        '\u06E2',  # SMALL HIGH MEEM
        '\u06E7',  # SMALL HIGH YEH
        '\u06E8',  # SMALL HIGH NOON
    ])

    def normalize(self, text: str, level: NormalizationLevel) -> str:
        """
        Normalize Arabic text to the specified level.

        Normalization is cumulative:
        - TASHKEEL_REMOVED: Removes diacritics
        - HAMZA_UNIFIED: + Unifies hamza carriers
        - ALIF_UNIFIED: + Unifies alif variants
        - YA_UNIFIED: + Unifies ya/alif maqsura
        - FULL: All normalizations + removes small letters
        """
        if level == NormalizationLevel.NONE:
            return text

        # Start with Unicode NFC normalization
        result = unicodedata.normalize('NFC', text)

        # Level 1: Remove tashkeel
        result = self._remove_tashkeel(result)
        if level == NormalizationLevel.TASHKEEL_REMOVED:
            return result

        # Level 2: Unify hamza
        result = self._unify_hamza(result)
        if level == NormalizationLevel.HAMZA_UNIFIED:
            return result

        # Level 3: Unify alif
        result = self._unify_alif(result)
        if level == NormalizationLevel.ALIF_UNIFIED:
            return result

        # Level 4: Unify ya
        result = self._unify_ya(result)
        if level == NormalizationLevel.YA_UNIFIED:
            return result

        # Level 5 (FULL): Remove small letters
        result = self._remove_small_letters(result)
        return result

    def _remove_tashkeel(self, text: str) -> str:
        """Remove all diacritical marks."""
        return ''.join(c for c in text if c not in self.TASHKEEL)

    def _unify_hamza(self, text: str) -> str:
        """Unify hamza forms to their carrier letters."""
        return ''.join(self.HAMZA_MAP.get(c, c) for c in text)

    def _unify_alif(self, text: str) -> str:
        """Unify alif variants to plain alif."""
        return ''.join(self.ALIF_MAP.get(c, c) for c in text)

    def _unify_ya(self, text: str) -> str:
        """Unify alif maqsura to ya."""
        return ''.join(self.YA_MAP.get(c, c) for c in text)

    def _remove_small_letters(self, text: str) -> str:
        """Remove small letter markers."""
        return ''.join(c for c in text if c not in self.SMALL_LETTERS)

    def for_search(self, text: str) -> str:
        """Normalize text for search matching (full normalization)."""
        return self.normalize(text, NormalizationLevel.FULL).strip()

    def for_display(self, text: str) -> str:
        """Keep original text for display purposes."""
        return unicodedata.normalize('NFC', text)
```

---

## Appendix I: Golden Test Datasets

### I.1. Verified Word Counts (Scholarly Consensus)

**Important Note:** Word counts in the Quran are subject to methodology. The counts below use the methodology specified in parentheses.

```python
GOLDEN_WORD_COUNTS: Final[Dict[str, Dict]] = {
    # Words with scholarly consensus
    "الله": {
        "count": 2698,
        "methodology": "EXACT_ONLY, includes all case forms",
        "source": "Multiple scholarly sources agree",
    },
    "رب": {
        "count": 975,
        "methodology": "LEMMA_BASED, all forms of رب",
        "source": "Corpus.quran.com",
    },
    "قال": {
        "count": 1722,
        "methodology": "ROOT_BASED (ق-و-ل), verb forms only",
        "source": "MASAQ dataset",
    },

    # DISPUTED - Multiple counts depending on methodology
    "يوم": {
        "counts": {
            "exact_singular": 217,      # يَوْم only
            "with_prefixes": 365,       # Disputed claim
            "all_forms": 475,           # All derivatives
        },
        "note": "The '365 days miracle' claim uses selective inclusion",
        "source": "WikiIslam analysis",
    },
}
```

### I.2. Abjad Verification Values

```python
GOLDEN_ABJAD_VALUES: Final[Dict[str, int]] = {
    # Mashriqi (Eastern) System
    "بسم الله الرحمن الرحيم": 786,
    "الله": 66,
    "محمد": 92,
    "علي": 110,
    "الحمد": 82,
    "الفاتحة": 592,  # First Surah name
}
```

### I.3. Structure Verification

```python
STRUCTURAL_VERIFICATION: Final[Dict] = {
    "total_surahs": 114,
    "total_verses": 6236,
    "total_words": 77430,       # Per QAC
    "total_letters": 320015,    # Varies by counting method
    "total_unique_words": 14870,
    "total_roots": 1726,
    "bismillah_count": 114,     # Including An-Naml 27:30
    "sajdah_count": 15,
}
```

---

## Appendix J: Configuration Reference

### J.1. Environment Variables

```bash
# ===========================================
# Mizan Core Engine Configuration
# ===========================================

# --- Database ---
DATABASE_URL=postgresql+asyncpg://mizan:mizan@localhost:5432/mizan
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# --- Redis Cache ---
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=3600
CACHE_ENABLED=true

# --- API Server ---
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_RELOAD=false

# --- Logging ---
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json  # json, text
LOG_FILE=/var/log/mizan/app.log

# --- Security ---
SECRET_KEY=your-256-bit-secret-key-here
CORS_ORIGINS=["http://localhost:3000"]
RATE_LIMIT_PER_MINUTE=100

# --- Integrity ---
FAIL_ON_INTEGRITY_ERROR=true
EXPECTED_VERSE_COUNT=6236
EXPECTED_WORD_COUNT=77430

# --- Feature Flags ---
ENABLE_ML_FEATURES=true
ENABLE_SEMANTIC_SEARCH=true
ENABLE_STRUCTURAL_ANALYSIS=true

# --- External Data ---
MASAQ_DATA_PATH=/data/masaq/masaq_v5.tsv
TANZIL_DATA_PATH=/data/quran/uthmani
EMBEDDINGS_PATH=/data/embeddings/verse_embeddings.npy

# --- ML Models ---
ARABERT_MODEL=aubmindlab/bert-base-arabertv2
EMBEDDING_DIMENSION=768
SIMILARITY_THRESHOLD=0.7
```

### J.2. Configuration Schema

```python
from pydantic import BaseSettings, Field

class MizanSettings(BaseSettings):
    """Application configuration with validation."""

    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    database_pool_size: int = Field(10, env="DATABASE_POOL_SIZE")

    # Cache
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    cache_ttl_seconds: int = Field(3600, env="CACHE_TTL_SECONDS")
    cache_enabled: bool = Field(True, env="CACHE_ENABLED")

    # API
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")

    # Integrity
    fail_on_integrity_error: bool = Field(True, env="FAIL_ON_INTEGRITY_ERROR")
    expected_verse_count: int = Field(6236, env="EXPECTED_VERSE_COUNT")

    # Feature Flags
    enable_ml_features: bool = Field(True, env="ENABLE_ML_FEATURES")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

---

*End of Technical Design Specification*

*Version 2.2.0 - December 2025*

*بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ*
