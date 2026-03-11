# CLAUDE.md — Mizan AI Session Context

> This file provides startup context for AI sessions. Read this first before making any changes.

## What is Mizan?

Mizan Core Engine (MCE) is a scholarly-grade Quranic text analysis platform that combines:
- **High-precision letter/word/Abjad analysis** verified against Tanzil.net standards
- **Semantic (vector) search** across Quran, Tafsir, and Hadith using AI embeddings
- **Islamic knowledge library** for managing and indexing Arabic text sources
- **Interactive frontend** (Next.js) with Playground, Search, and Library pages

## Current State (as of 2026-03-11)

| Component | Status | Notes |
|-----------|--------|-------|
| Backend API (analysis, verses) | ✅ Code complete | Verses table may be empty — run `ingest_tanzil.py` |
| Semantic Search backend | ✅ Code complete | pgvector migration must be applied first |
| Cascade Embedding Service | ✅ Complete | Gemini primary → local fallback |
| Frontend Playground | ✅ Real API | Mock removed; calls `analyzeVerse()` + `calculateAbjad()` |
| Frontend `/search` | ✅ Complete | Semantic search UI with filters and similarity slider |
| Frontend `/library` | ✅ Complete | Create spaces, add sources, trigger indexing |
| Quran data (verses table) | ⚠️ Script ready | Run `python scripts/ingest_tanzil.py` to populate |
| Embeddings (verse_embeddings) | ⚠️ Script ready | Run `python scripts/embed_quran.py` after ingest |
| Morphology (MASAQ) | ❌ Not started | Future phase |

## Startup Sequence (Full Stack)

```bash
# 1. Start infrastructure (pgvector-enabled PostgreSQL + Redis)
docker-compose up -d

# 2. Apply all database migrations
alembic upgrade head

# 3. Ingest Quran text (114 surahs + 6236 verses)
python scripts/ingest_tanzil.py

# 4. Generate verse embeddings (~5 min on CPU)
python scripts/embed_quran.py

# 5. Start API server
uvicorn mizan.api.main:app --reload --host 0.0.0.0 --port 8000

# 6. Start frontend (separate terminal)
cd website && npm run dev
```

## Embedding Configuration

Controlled via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `EMBEDDING_PROVIDER` | Primary provider: `local` or `gemini` | `local` |
| `EMBEDDING_MODEL` | Primary model name | `intfloat/multilingual-e5-base` |
| `EMBEDDING_FALLBACK_PROVIDER` | Fallback provider (empty = disabled) | `""` |
| `EMBEDDING_FALLBACK_MODEL` | Fallback model name | `intfloat/multilingual-e5-base` |
| `GEMINI_API_KEY` | Required if using Gemini | `""` |

**Cascade mode** (Gemini first, local on failure):
```env
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=models/text-embedding-004
EMBEDDING_FALLBACK_PROVIDER=local
EMBEDDING_FALLBACK_MODEL=intfloat/multilingual-e5-base
GEMINI_API_KEY=your-key-here
```

> **Important**: Primary and fallback models MUST have the same embedding dimension (768). Mixing dimensions breaks vector search.

## Architecture

```
src/mizan/
├── domain/           # Core logic — no external deps
│   ├── entities/     # Verse, Surah, TextSource, TextChunk, LibrarySpace
│   ├── services/     # AbjadCalculator, LetterCounter, IEmbeddingService (port)
│   └── repositories/ # Repository interfaces
├── application/      # Use cases
│   └── services/     # library_service, indexing_service, semantic_search_service
├── infrastructure/
│   ├── embeddings/   # sentence_transformer_service, gemini_embedding_service, cascade_service, factory
│   ├── persistence/  # SQLAlchemy models + repositories
│   └── config.py     # Settings (pydantic-settings)
└── api/
    └── routers/      # verses, analysis, library, semantic_search
```

## Critical Files

| File | Purpose |
|------|---------|
| `src/mizan/infrastructure/config.py` | All settings including embedding config |
| `src/mizan/infrastructure/embeddings/factory.py` | Embedding service creation + cascade logic |
| `src/mizan/api/main.py` | FastAPI app — routers registered here |
| `src/mizan/infrastructure/persistence/models.py` | All SQLAlchemy models |
| `alembic/versions/` | Database migrations — apply with `alembic upgrade head` |
| `scripts/ingest_tanzil.py` | Populate surahs + verses tables from Tanzil XML |
| `scripts/embed_quran.py` | Generate verse embeddings into verse_embeddings table |
| `website/lib/api/client.ts` | Frontend API client — all backend calls go here |
| `website/types/api.ts` | TypeScript types matching backend response shapes |
| `website/config/navigation.ts` | Nav links (Home, Playground, Search, Library, Docs, About) |

## Active Branch

Development branch: `claude/fix-email-display-rwMGK`

## Key API Endpoints

```
GET  /health                                    — Service health + embedding status
GET  /api/v1/surahs                             — List all 114 surahs
GET  /api/v1/verses/{surah}/{verse}             — Get verse with metadata
GET  /api/v1/analysis/verse/{surah}/{verse}     — Full analysis (letters, words, abjad)
GET  /api/v1/analysis/letters/count             — Letter count for arbitrary text
GET  /api/v1/analysis/abjad                     — Abjad value for arbitrary text

POST /api/v1/library/spaces                     — Create library space
GET  /api/v1/library/spaces                     — List all spaces
POST /api/v1/library/spaces/{id}/sources        — Add text source
GET  /api/v1/library/sources/{id}               — Source detail + indexing status
POST /api/v1/library/sources/{id}/index         — Start indexing (async)
DELETE /api/v1/library/sources/{id}             — Delete source + chunks

POST /api/v1/search/semantic                    — Semantic search across indexed texts
GET  /api/v1/verses/{surah}/{verse}/similar     — Similar verses by embedding
```
