# Changelog

All notable changes to Mizan Core Engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial public release preparation
- Comprehensive documentation

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
