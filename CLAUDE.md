# CLAUDE.md — Mizan AI Session Context

> This file provides startup context for AI sessions. Read this first before making any changes.

## What is Mizan?

Mizan Core Engine (MCE) is a scholarly-grade Quranic text analysis platform that combines:
- **High-precision letter/word/Abjad analysis** verified against Tanzil.net standards
- **Semantic (vector) search** across Quran, Tafsir, and Hadith using AI embeddings
- **Islamic knowledge library** for managing and indexing Arabic text sources
- **Interactive frontend** (Next.js) with Playground, Search, and Library pages

## Current State (as of 2026-03-15)

| Component | Status | Notes |
|-----------|--------|-------|
| Backend API (analysis, verses) | ✅ Production | 114 surahs, 6,236 verses ingested |
| Semantic Search backend | ✅ Production | Quran verse search working (Arabic/Turkish/English) |
| Verse Embeddings | ✅ Production | 6,236 vectors via intfloat/multilingual-e5-base (768d) |
| Cascade Embedding Service | ✅ Complete | Local provider active; Gemini cascade optional |
| Frontend Playground | ✅ Production | Shows verse text in results, letter/word/Abjad analysis |
| Frontend `/search` | ✅ Production | Quran semantic search with source filters + similarity slider |
| Frontend `/library` | ✅ Complete | Create spaces, add sources, trigger indexing |
| Favicon + PWA manifest | ✅ Done | favicon.ico, apple-touch-icon, site.webmanifest |
| Morphology (MASAQ) | ❌ Not started | Future phase |
| Library sources (Tafsir/Hadith) | ❌ Not ingested | text_chunks table empty until sources are added |
| Website i18n (TR/AR) | ❌ Planned | Phase 7 — next-intl |

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

## Production Deployment

- **API**: https://mizan-api.rollingcatsoftware.com (FastAPI, port 8000)
- **Website**: https://mizan.rollingcatsoftware.com (Next.js standalone, port 3000)
- **Server**: Hetzner VPS 116.203.222.213 (Docker + Traefik + auto-SSL)
- **DB**: Shared PostgreSQL 17 with pgvector on 127.0.0.1:5432
- **Cache**: Shared Redis 7.4 on 127.0.0.1:6379 (database 1)
- **Deploy**: `/root/projects/infra/deploy.sh [build|restart|logs] mizan`

## Active Branch

Main branch: `master`

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
