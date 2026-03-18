# CLAUDE.md — Mizan AI Session Context

> This file provides startup context for AI sessions. Read this first before making any changes.

## What is Mizan?

Mizan Core Engine (MCE) is a scholarly-grade Quranic text analysis platform that combines:
- **High-precision letter/word/Abjad analysis** verified against Tanzil.net standards
- **Semantic (vector) search** across Quran, Tafsir, and Hadith using AI embeddings
- **Islamic knowledge library** for managing and indexing Arabic text sources
- **Interactive frontend** (Next.js) with Playground, Search, and Library pages

## Current State (as of 2026-03-18)

| Component | Status | Notes |
|-----------|--------|-------|
| Backend API (analysis, verses) | ✅ Production | 114 surahs, 6,236 verses ingested |
| Hybrid Semantic Search | ✅ Production | Vector + BM25 keyword + RRF fusion across 4 retrieval paths |
| Verse Embeddings | ✅ Production | 6,236 vectors via intfloat/multilingual-e5-base (768d) |
| Verse Translations | ✅ Production | 6,236 EN (Sahih International) + 6,236 TR (Diyanet) embedded |
| BM25 Keyword Search | ✅ Production | tsvector + GIN indexes on verses + text_chunks |
| ISRI Arabic Stemmer | ✅ Production | Pure-Python root extraction (والدين→ولد, صابرين→صبر) |
| Cross-Encoder Reranker | 🔧 Built, disabled | Infrastructure ready; needs multilingual model (ENABLE_RERANKING) |
| Cascade Embedding Service | ✅ Complete | Local provider active; Gemini cascade optional |
| Frontend Playground | ✅ Production | Shows verse text in results, letter/word/Abjad analysis |
| Frontend `/search` | ✅ Production | Quran semantic search with source filters + similarity slider |
| Frontend `/library` | ✅ Complete | Create spaces, add sources, trigger indexing |
| Favicon + PWA manifest | ✅ Done | favicon.ico, apple-touch-icon, site.webmanifest |
| Morphology (MASAQ) | ❌ Not started | Future phase |
| Library sources (Tafsir/Hadith) | 🔧 Scripts ready | Run ingest_tafsir.py / ingest_hadith.py to populate |
| Website i18n (TR/AR) | ✅ Complete | Client-side: en/tr/ar + RTL + language switcher |

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

# 5. Ingest verse translations for cross-lingual search (~10 min)
python scripts/ingest_translations.py    # EN (Sahih International) + TR (Diyanet) from quran.com

# 6. Ingest Tafsir + Hadith (optional, ~30 min on CPU)
python scripts/ingest_tafsir.py          # Ibn Kathir from quran.com API
python scripts/ingest_hadith.py          # Kutub al-Sittah from hadith-api

# 7. Start API server
uvicorn mizan.api.main:app --reload --host 0.0.0.0 --port 8000

# 8. Start frontend (separate terminal)
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
| `ENABLE_RERANKING` | Enable cross-encoder re-ranking | `false` |
| `RERANKER_MODEL` | Cross-encoder model name | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| `RERANKER_TOP_K` | Candidates to re-rank | `30` |

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
│   ├── services/     # AbjadCalculator, LetterCounter, IEmbeddingService, IRerankerService (ports)
│   └── repositories/ # Repository interfaces
├── application/      # Use cases
│   └── services/     # library_service, indexing_service, semantic_search_service
├── infrastructure/
│   ├── embeddings/   # sentence_transformer_service, gemini_embedding_service, cascade_service, factory
│   ├── reranking/    # cross_encoder_service, factory (optional cross-encoder re-ranking)
│   ├── persistence/  # SQLAlchemy models + repositories (incl. verse_translations)
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
| `scripts/ingest_tafsir.py` | Ingest Tafsir Ibn Kathir from quran.com API into text_chunks |
| `scripts/ingest_hadith.py` | Ingest Hadith collections (Bukhari, Muslim, etc.) into text_chunks |
| `scripts/ingest_translations.py` | Fetch EN/TR verse translations from quran.com API + embed |
| `src/mizan/infrastructure/reranking/` | Cross-encoder re-ranking service (optional, disabled by default) |
| `src/mizan/domain/services/reranking_service.py` | IRerankerService port interface |
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

POST /api/v1/search/semantic                    — Hybrid search (vector + BM25 + translations + RRF)
GET  /api/v1/verses/{surah}/{verse}/similar     — Similar verses by embedding
```
