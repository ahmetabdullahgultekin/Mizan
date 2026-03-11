<div align="center">

# Mizan Core Engine

### High-Precision Quranic Text Analysis System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-138%20passed-brightgreen.svg)](#testing)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

*Named after the Quranic concept of "Balance" (Al-Mizan - الميزان)*

[Features](#features) | [Quick Start](#quick-start) | [API Reference](#api-reference) | [Documentation](#documentation) | [Contributing](#contributing)

</div>

---

## Overview

Mizan Core Engine (MCE) is a scholarly-grade Quranic text analysis system that prioritizes **measurement accuracy** above all else. Every calculation is verified against authoritative sources including [Tanzil.net](https://tanzil.net), [Quran.com](https://quran.com), and classical Islamic scholarship.

### Why Mizan?

- **Verified Accuracy**: All algorithms tested against globally accepted scholarly standards
- **Transparent Methodology**: Clear documentation of counting methods and their sources
- **Reproducible Results**: Every analysis includes methodology metadata for verification
- **Multiple Standards Support**: Choose between different scholarly traditions

## Features

### Core Analysis Capabilities

| Feature | Description | Status |
|---------|-------------|--------|
| **Letter Counting** | Multiple methods (Traditional, Uthmani Full, Base-only) | ✅ Verified |
| **Word Counting** | Whitespace-delimited (Tanzil standard) | ✅ Verified |
| **Abjad Calculations** | Mashriqi & Maghribi numeral systems | ✅ Verified |
| **Verse Navigation** | Full Quran traversal with validation | ✅ Complete |
| **Text Integrity** | SHA-256/512 checksums for verification | ✅ Complete |
| **Multi-Script Support** | Uthmani, Simple (Imla'i), Uthmani-min | ✅ Complete |
| **Islamic Knowledge Library** | Manage and index Quran, Tafsir, Hadith sources | ✅ Complete |
| **Semantic Search** | AI-powered meaning-based search across all indexed texts | ✅ Complete |
| **Verse Similarity** | Find similar verses using embedding vectors | ✅ Complete |

### Verified Against Global Standards

| Metric | Our Value | Standard | Source |
|--------|-----------|----------|--------|
| Al-Fatiha letters | 139 | 139 | Tanzil.net |
| Basmalah letters | 19 | 19 | Traditional consensus |
| Allah (الله) Abjad | 66 | 66 | Universal |
| Basmalah Abjad | 786 | 786 | Universal |
| All 28 letter values | 100% | 100% | Scholarly standard |

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Docker & Docker Compose (for full stack)
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/mizan.git
cd mizan

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### Using Docker (Recommended)

```bash
# Start all services (PostgreSQL, Redis, API)
docker-compose up -d

# Check service health
docker-compose ps

# View API logs
docker-compose logs -f api
```

### Manual Setup

```bash
# Set environment variables
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/mizan
export REDIS_URL=redis://localhost:6379/0

# Run database migrations
alembic upgrade head

# Seed Quran text (114 surahs + 6,236 verses)
python scripts/ingest_tanzil.py

# Generate verse embeddings (optional — required for semantic search)
python scripts/embed_quran.py

# Start the API server
uvicorn mizan.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Verify Installation

```bash
# Run tests
pytest

# Check API health
curl http://localhost:8000/health
```

## API Reference

### Health Check

```http
GET /health
```

Returns service health status, embedding mode, and version information.

### Verse Retrieval

```http
GET /api/v1/verses/{surah}/{verse}
GET /api/v1/surahs
```

Retrieve verses and surah metadata.

**Example:**
```bash
curl http://localhost:8000/api/v1/verses/1/1
curl http://localhost:8000/api/v1/surahs
```

### Verse Analysis

```http
GET /api/v1/analysis/verse/{surah}/{verse}
```

Full analysis of a verse: letter counts, word counts, Abjad values, letter frequency.

### Letter Analysis

```http
GET /api/v1/analysis/letters/count?text={arabic_text}&method={method}
```

Count letters in Arabic text using specified methodology.

**Parameters:**
- `text`: Arabic text to analyze
- `method`: `traditional` (default), `uthmani_full`, or `no_wasla`

**Example:**
```bash
curl "http://localhost:8000/api/v1/analysis/letters/count?text=بسم%20الله%20الرحمن%20الرحيم"
```

### Abjad Calculation

```http
GET /api/v1/analysis/abjad?text={arabic_text}&system={system}
```

Calculate Abjad (gematria) value of Arabic text.

**Parameters:**
- `text`: Arabic text to analyze
- `system`: `mashriqi` (default) or `maghribi`

**Example:**
```bash
curl "http://localhost:8000/api/v1/analysis/abjad?text=الله"
# Returns: {"value": 66, "system": "mashriqi", ...}
```

### Islamic Knowledge Library

```http
POST   /api/v1/library/spaces                    # Create a library space
GET    /api/v1/library/spaces                    # List all spaces
POST   /api/v1/library/spaces/{id}/sources       # Add a text source
GET    /api/v1/library/sources/{id}              # Source detail + indexing status
POST   /api/v1/library/sources/{id}/index        # Start indexing (async)
DELETE /api/v1/library/sources/{id}              # Delete source and its chunks
```

### Semantic Search

```http
POST /api/v1/search/semantic
```

Search Islamic texts by meaning — not just keywords.

**Request body:**
```json
{
  "query": "mercy and forgiveness",
  "source_types": ["QURAN", "TAFSIR"],
  "limit": 10,
  "min_similarity": 0.70
}
```

### Verse Similarity

```http
GET /api/v1/verses/{surah}/{verse}/similar?limit=5
```

Find semantically similar verses using embedding vectors.

### Word Count

```http
GET /api/v1/analysis/words/count?text={arabic_text}
```

Count words in Arabic text (whitespace-delimited).

## Architecture

Mizan follows **Hexagonal Architecture** (Ports & Adapters) with strict separation of concerns:

```
src/mizan/
├── domain/           # Core business logic (no external dependencies)
│   ├── entities/     # Verse, Surah, LibrarySpace, TextSource, TextChunk
│   ├── enums/        # Type-safe enumerations (SourceType, IndexingStatus, …)
│   ├── services/     # AbjadCalculator, LetterCounter, IEmbeddingService (port)
│   ├── value_objects/# Immutable value objects
│   └── repositories/ # Repository interfaces (ports)
├── application/      # Use cases and DTOs
│   ├── dtos/         # Request/Response objects
│   └── services/     # library_service, indexing_service, semantic_search_service
├── infrastructure/   # External adapters
│   ├── embeddings/   # SentenceTransformer, Gemini, CascadeEmbeddingService, factory
│   ├── persistence/  # Database models + repository implementations
│   ├── cache/        # Redis implementation
│   └── text/         # Text processing utilities
└── api/              # FastAPI REST interface
    └── routers/      # verses, analysis, library, semantic_search

scripts/
├── ingest_tanzil.py  # Populate surahs + verses tables from Tanzil XML
└── embed_quran.py    # Generate verse embeddings (batch)
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `API_PREFIX` | API route prefix | `/api/v1` |
| `EMBEDDING_PROVIDER` | Embedding backend: `local` or `gemini` | `local` |
| `EMBEDDING_MODEL` | Model name for primary provider | `intfloat/multilingual-e5-base` |
| `EMBEDDING_FALLBACK_PROVIDER` | Fallback provider (empty = disabled) | `""` |
| `EMBEDDING_FALLBACK_MODEL` | Model name for fallback provider | `intfloat/multilingual-e5-base` |
| `GEMINI_API_KEY` | Google Gemini API key (if using Gemini) | `""` |

### Letter Counting Methods

| Method | Alif Wasla | Alif Khanjariyya | Use Case |
|--------|------------|------------------|----------|
| `TRADITIONAL` | ✅ Included | ❌ Excluded | Default, matches scholarly consensus |
| `UTHMANI_FULL` | ✅ Included | ✅ Included | Full Uthmani character analysis |
| `NO_WASLA` | ❌ Excluded | ❌ Excluded | Base letter analysis |

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/mizan --cov-report=html

# Run specific test categories
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests
pytest -k "abjad"          # Tests matching pattern
```

### Test Coverage

- **138 tests** covering domain logic, value objects, and services
- Property-based testing with Hypothesis for edge cases
- Integration tests for API endpoints

## Documentation

- [Standards Documentation](src/mizan/domain/STANDARDS.py) - Scholarly standards we follow
- [API Documentation](http://localhost:8000/docs) - Interactive Swagger UI (when running)
- [Architecture Decision Records](docs/adr/) - Design decisions (coming soon)

## Scholarly Standards

Mizan follows the **Modern Computational** standard used by authoritative sources:

### Authoritative Sources

- **[Tanzil.net](https://tanzil.net)** - Primary Quran text (Medina Mushaf verified)
- **[Quran.com](https://quran.com)** - Quranic Arabic Corpus
- **[IslamWeb](https://islamweb.net)** - Classical scholarly references
- **Wikipedia** - Abjad numeral standards

### Key Statistics (Verified)

| Statistic | Value | Source |
|-----------|-------|--------|
| Total Surahs | 114 | Consensus |
| Total Verses | 6,236 | Tanzil/Quran.com |
| Total Words | ~77,430 | Tanzil |
| Total Letters | ~325,666 | Tanzil (Uthmani) |

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run linting
ruff check src/
ruff format src/

# Run type checking
mypy src/mizan
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Tanzil.net](https://tanzil.net) - For providing verified Quran text
- [Quran.com](https://quran.com) - For the Quranic Arabic Corpus
- The Islamic scholarly tradition for establishing counting methodologies

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/mizan/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/mizan/discussions)

---

<div align="center">

**بسم الله الرحمن الرحيم**

*In the name of Allah, the Most Gracious, the Most Merciful*

</div>
