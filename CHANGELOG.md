# Changelog

All notable changes to Mizan Core Engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Language-aware reranking (Arabic/Turkish search quality).** The reranker
  previously only re-scored candidates carrying an English `translation_text`,
  feeding that English text to an English-only cross-encoder — so raw Arabic
  verse-vector and keyword hits were never reranked and stayed pinned at the RRF
  floor (the measured root cause of poor AR/TR ranking). Now
  `detect_query_language()` + `SemanticSearchService._rerank_text_for()` route
  candidate text by query script **and** reranker capability: a multilingual
  reranker (`IRerankerService.is_multilingual` → True for jina / `*multilingual*`
  / `bge-*-m3`) receives native, language-matched text (Arabic `content` for AR
  queries, Turkish translation for TR), while an English-only reranker keeps its
  historical English-only behaviour and is never fed text it cannot score. The
  code change is therefore a safe no-op on AR/TR until a multilingual model is
  enabled (`RERANKER_MODEL=jinaai/jina-reranker-v2-base-multilingual`; `einops`
  is already in the image so no rebuild; reversible by unsetting the env var).
- **Search-quality eval harness (`eval/`).** `eval/queries.json` (labelled
  EN/TR/AR query cases, cross-lingual triples) + `eval/run_eval.py` (stdlib-only)
  report **precision@k / recall@k / MRR** by language against a running API, with
  `--rerank true|false|default` (A/B vs raw RRF), `--base-url`, and a `--min-mrr`
  CI gate. Production baseline (ms-marco): overall P@10=0.288 / MRR=0.524, with
  Arabic the weakest at P@10=0.197 / R@10=0.119.
- **Morphology preview flag** — all four `/morphology/*` endpoints now return a
  `data_status` (`"preview"` / `"complete"`) + `preview` bool, and a `note` when
  in preview. Until the Quranic Arabic Corpus (QAC/MASAQ) dataset is ingested,
  `root`/`lemma`/`pattern` are null and responses self-describe as preview so
  empty linguistic fields are not mistaken for verified output. Auto-flips to
  `"complete"` once real root data is present (no code change needed).
- **Per-request rerank kill-switch** — `SemanticSearchRequest` gains an optional
  `rerank: bool | None` field. `null` (default) keeps the server's configured
  behaviour, `false` bypasses the cross-encoder and returns raw RRF order
  (handy for A/B-ing a query against reranking in the field), `true` forces
  reranking when a reranker is available.

### Fixed
- **Reranked scores were attached to the wrong candidates (latent bug).**
  `rerank()` returns `(document_index, score)` tuples sorted by score, but the
  merge in `_rerank_results` mapped each score back using the *enumerate
  position* instead of the returned `document_index` — so once the reranker
  re-sorted its output, scores landed on the wrong verses. Now mapped via the
  returned `document_index`. (`semantic_search_service.py`)
- **Semantic search: post-fusion `min_similarity` scale-mismatch** — the 0.5
  cosine threshold was being re-applied to RRF-fused / sigmoid-reranked scores
  (which are not cosine similarities), silently dropping valid hits. The cosine
  gate is already enforced on each vector retrieval path; the redundant
  post-fusion filter was removed. (`semantic_search_service.py`)

### Changed
- **Reranker model is now a single source of truth.** The
  `CrossEncoderRerankerService` constructor default and the
  `reranking/__init__.py` docstring now match `Settings.reranker_model`
  (`cross-encoder/ms-marco-MiniLM-L-6-v2`, English) instead of falsely
  advertising the multilingual jina model. Rationale: the pipeline only reranks
  the English `translation_text`. Jina multilingual remains an explicit
  `RERANKER_MODEL` opt-in. The load path now logs `requested_model` /
  `loaded_model` / `matches_intent`. Documented the trade-off + CX43 cost in
  CLAUDE.md.

### Tests
- Added `tests/unit/test_semantic_search_service.py` (RRF fusion + min_similarity
  scaling regression) and `tests/unit/test_reranker_service.py` (model-choice
  single-source-of-truth) plus the rerank kill-switch and morphology-preview-flag
  cases.
- Added `tests/unit/test_language_aware_rerank.py` (query-language detection, the
  text-routing matrix per query-language × reranker capability, a multilingual
  end-to-end rerank of native Arabic hits, and a regression for the reranked-score
  index-mapping bug) plus `is_multilingual` cases in `test_reranker_service.py`.
- **Eval set expanded to 24 labelled cases** (8 EN / 8 TR / 8 AR, cross-lingual
  triples: mercy, patience, charity, forgiveness, prayer, oneness-of-God, light,
  supplication). Added `eval/baseline_2026-06-05.md` with measured production
  numbers (P@10, R@10, MRR by language) and the A/B rerank-on vs rerank-off
  comparison that surfaces the Arabic zero-benefit gap.
- **Hermetic integration test suite** — `settings.init_db_on_startup` flag (new
  `Settings` field, default `True`) lets the test conftest disable the lifespan
  `init_db()` call without patching `is_production`. Eliminates the historical
  22-ERROR mode when no local Postgres is present.
- **Rate-limiter default_limits** — `Limiter(default_limits=["120/minute"])` now
  installed as a catch-all so `SlowAPIMiddleware` enforces a ceiling on every
  route, not just the one decorated `/search/semantic` route. Added
  `tests/integration/test_rate_limiting.py` (3 tests: default limit reaches
  undecorated routes, 429 body names the limit, regression guard that
  `default_limits` is never accidentally removed).
  Full suite is now **225 tests** (all green; ruff + mypy --strict clean).

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
