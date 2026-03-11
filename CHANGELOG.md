# Changelog

All notable changes to Mizan Core Engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - Unreleased

### Added

#### Islamic Knowledge Library (Tier 4)
- **`LibrarySpace`** entity — named collection for grouping text sources
- **`TextSource`** entity — tracks indexing status (PENDING / INDEXING / INDEXED / FAILED)
- **`TextChunk`** entity — individual passages with `VECTOR(768)` embedding column (pgvector)
- **`VerseEmbedding`** entity — separate embedding storage for Quran verses (linked to existing `verses` table)
- New library management API: `POST /api/v1/library/spaces`, `GET /api/v1/library/spaces`, `POST/GET/DELETE /api/v1/library/sources`

#### Semantic Search
- `POST /api/v1/search/semantic` — meaning-based search across all indexed texts
- `GET /api/v1/verses/{surah}/{verse}/similar` — find semantically similar verses
- Configurable `min_similarity` threshold and `source_types` filter (QURAN / TAFSIR / HADITH / OTHER)

#### Embedding Infrastructure
- `IEmbeddingService` interface (port) in domain layer
- `SentenceTransformerEmbeddingService` — local multilingual model (`intfloat/multilingual-e5-base`, 768-dim)
- `GeminiEmbeddingService` — Google Gemini Embedding API (`models/text-embedding-004`, 768-dim)
- `CascadeEmbeddingService` — transparent primary → fallback with dimension-mismatch guard
- `get_embedding_service()` factory (lru_cache singleton) + `get_embedding_status()` for health endpoint
- New config fields: `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `EMBEDDING_FALLBACK_PROVIDER`, `EMBEDDING_FALLBACK_MODEL`, `GEMINI_API_KEY`

#### Data Pipeline Scripts
- `scripts/ingest_tanzil.py` — self-contained script to populate `surahs` (114 rows) and `verses` (6,236 rows) from Tanzil XML; embeds all surah metadata, juz/hizb/manzil boundaries, and sajdah verses
- `scripts/embed_quran.py` — batch-generate `VerseEmbedding` records for all 6,236 verses

#### Frontend Pages
- `/search` — semantic search UI: Arabic-aware input, source-type toggles, similarity slider (50–95%), animated result cards with colour-coded similarity scores
- `/library` — library management UI: create spaces, add text sources with full metadata, trigger indexing, retry/delete sources with live status badges

#### Frontend — API Client & Types
- `website/lib/api/client.ts`: added `createLibrarySpace()`, `listLibrarySpaces()`, `addTextSource()`, `getTextSource()`, `indexTextSource()`, `deleteTextSource()`, `semanticSearch()`, `findSimilarVerses()`
- `website/types/api.ts`: added `VerseAnalysisResponse`, `SourceType`, `IndexingStatus`, `LibrarySpaceResponse`, `TextSourceResponse`, `AddTextSourceRequest`, `SemanticSearchRequest`, `SemanticSearchResponse`
- Navigation updated: `Search` and `Library` links added to main navbar

#### Frontend — Playground Improvements
- Verse selector now loads all 114 surahs dynamically from `GET /api/v1/surahs` (graceful fallback to static list)
- Removed mock 1.5 s delay; playground calls `analyzeVerse()` + `calculateAbjad()` against live API

### Fixed
- `client.ts` `getSurahList()`: backend returns plain array, not `{surahs, total}` — mapping corrected
- `client.ts` `analyzeVerse()`: URL was `/api/v1/analyze/verse/` → corrected to `/api/v1/analysis/verse/${surah}/${verse}`

## [0.1.0] - 2025-01-XX

### Added

#### Core Features
- **Letter Counting**: Multiple methods (Traditional, Uthmani Full, No Wasla)
  - Verified against Tanzil.net and Quran.com standards
  - Al-Fatiha = 139 letters (Traditional method)
  - Basmalah = 19 letters
- **Word Counting**: Whitespace-delimited (Tanzil standard)
  - Al-Fatiha = 29 words
- **Abjad Calculator**: Mashriqi and Maghribi numeral systems
  - All 28 letter values verified against scholarly standards
  - Allah = 66, Basmalah = 786 (universally accepted)
- **Verse Navigation**: Full Quran traversal with validation
  - 114 surahs, 6,236 verses
  - Verse-level metadata and checksums

#### Domain Layer
- `VerseLocation` value object with validation
- `AbjadValue` value object with mathematical properties
- `SurahMetadata` value object
- `TextChecksum` value object (SHA-256/512)
- Domain entities: `Verse`, `Surah`
- Domain services: `AbjadCalculator`, `LetterCounter`, `WordCounter`
- Comprehensive domain exceptions

#### Enumerations
- `AbjadSystem` (Mashriqi, Maghribi)
- `LetterCountMethod` (Traditional, Uthmani Full, No Wasla)
- `ScriptType` (Uthmani, Simple, Uthmani Minimal)
- `RevelationType` (Meccan, Medinan)
- `BasmalahStatus`
- `SajdahType`
- `QiraatType`
- `NormalizationLevel`

#### Infrastructure
- PostgreSQL database with async support (asyncpg)
- Redis caching layer
- SQLAlchemy ORM models
- Alembic migrations
- Text normalization utilities
- Integrity verification system

#### API Layer
- FastAPI REST API
- Health check endpoint
- Verse retrieval endpoints
- Analysis endpoints (letters, words, Abjad)
- OpenAPI documentation

#### Documentation
- `STANDARDS.py` - Scholarly standards documentation
- Verified against authoritative sources:
  - Tanzil.net
  - Quran.com
  - IslamWeb
  - Classical scholarship (Ibn Kathir)

#### Testing
- 138 unit tests
- Property-based testing with Hypothesis
- Test fixtures for common scenarios

### Standards Followed
- Modern Computational standard (Tanzil/Quran.com)
- Mashriqi Abjad numeral system (default)
- Hexagonal Architecture
- SOLID principles

### Verified Values
| Metric | Value | Source |
|--------|-------|--------|
| Al-Fatiha letters | 139 | Tanzil.net |
| Basmalah letters | 19 | Traditional |
| Allah Abjad | 66 | Universal |
| Basmalah Abjad | 786 | Universal |
| Total verses | 6,236 | Consensus |
| Total surahs | 114 | Consensus |

---

## Version History

- **0.1.0** - Initial release with core Quranic text analysis features

[Unreleased]: https://github.com/username/mizan/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/username/mizan/releases/tag/v0.1.0
