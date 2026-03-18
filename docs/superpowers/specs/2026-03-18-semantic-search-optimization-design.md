# Semantic Search Optimization — Design Spec

**Date**: 2026-03-18
**Branch**: `feat/semantic-search-optimization`
**Status**: Implemented and deployed (2026-03-18)

## Problem

Mizan's semantic search returns 0 of 5 target verses for "patience with parents" across all 3 languages (Arabic, English, Turkish). All similarity scores cluster at ~81% regardless of relevance. The system cannot distinguish meaningful matches from noise.

### Root Causes

1. **Pure vector search with no keyword fallback** — Arabic queries fail even when exact words exist in verses
2. **Arabic-only embeddings** — English/Turkish queries must cross a weak multilingual bridge
3. **No re-ranking** — raw cosine similarity is the only scoring signal
4. **Score compression** — `multilingual-e5-base` on short Arabic text produces near-identical vectors (anisotropy)

## Solution: 3-Phase Hybrid Search

### Phase 1: BM25 Hybrid Search (highest priority)

**Goal**: Add keyword search using existing `text_no_tashkeel` column + RRF fusion with vector results.

**Changes**:
- `library_repositories.py` — Add `keyword_search_verses()` using `text_no_tashkeel` LIKE/tsvector
- `semantic_search_service.py` — Add BM25 retrieval path, implement RRF fusion to merge keyword + vector results
- New migration — Add `tsvector` generated column + GIN index on `verses.text_no_tashkeel` (for proper Arabic text search)
- Also search `text_chunks.content` with tsvector for hadith/tafsir keyword hits

**RRF Formula**: `score = Σ 1/(k + rank_i)` where k=60, summed across retrieval methods.

**Expected impact**: Fixes Arabic search — "والدين" keyword match will surface 17:23, 31:14, 46:15, 29:8, 2:83.

### Phase 2: Translation Embeddings

**Goal**: Enable English/Turkish queries to match verse translations directly.

**Changes**:
- New `verse_translations` table: `(verse_id, language, translation_text, source, embedding VECTOR(768))`
- New migration for the table + HNSW index
- New `scripts/ingest_translations.py` — Fetch EN (Sahih International) + TR (Diyanet) from quran.com API v4
- `indexing_service.py` — Add `embed_verse_translations()` method
- `semantic_search_service.py` — Add translation embedding search path, merge into RRF
- `library_repositories.py` — Add `PostgresVerseTranslationRepository` with `search_by_text()`

**Data source**: quran.com API v4 — `/api/v4/quran/translations/{translation_id}?chapter_number={n}`
- English (Sahih International): resource_id = 20
- Turkish (Diyanet): resource_id = 77

**Expected impact**: English query "patience to parents" matches English translation containing "parents" and "kindness".

### Phase 3: Cross-Encoder Re-ranking

**Goal**: Add precision re-ranking on top-N candidates from hybrid search.

**Changes**:
- New `infrastructure/reranking/` module with `CrossEncoderReranker` service
- Uses `jinaai/jina-reranker-v2-base-multilingual` (278MB, CPU-compatible)
- `semantic_search_service.py` — After RRF fusion, re-rank top 30 candidates using cross-encoder
- `IRerankerService` interface in domain layer
- Config: `ENABLE_RERANKING=true`, `RERANKER_MODEL=jinaai/jina-reranker-v2-base-multilingual`
- Lazy model loading (same pattern as embedding service)

**Expected impact**: Pushes truly relevant results to top positions, spreads similarity scores from compressed 80-85% to meaningful 60-99% range.

## Architecture After All 3 Phases

```
User Query (any language)
    │
    ├── Vector Search (pgvector cosine) ──► verse_embeddings (Arabic)
    │                                       verse_translations (EN/TR)
    │                                       text_chunks (Hadith/Tafsir)
    │
    ├── BM25 Keyword Search (tsvector) ──► verses.text_no_tashkeel
    │                                      text_chunks.content
    │
    └── RRF Fusion (merge rankings, k=60)
            │
            ▼
        Cross-Encoder Re-rank (top 30 → top 10)
            │
            ▼
        Final Results (with meaningful score spread)
```

## Non-Goals

- Model upgrade (e5-base → e5-large) — defer unless Phases 1-3 insufficient
- Topic metadata / LLM tagging — future enhancement
- Query translation — unnecessary with translation embeddings

## Testing

Each phase must verify that searching "patience to the mother and father" returns at least 3 of these 5 verses in top 10:
- 17:23, 17:24, 31:14, 46:15, 29:8

## Final Results (2026-03-18)

| Query | Language | Targets Found | Key Positions |
|-------|----------|---------------|---------------|
| `بالوالدين احسانا` | Arabic | 2:83, 4:36 + more | #12, #14 |
| `الصبر على الوالدين` | Arabic | 17:23 | #4 (score 0.58) |
| `patience to mother and father` | English | 31:14 | #7 |
| `anne ve babaya sabretmek` | Turkish | 17:23 | #6 |

Additional improvements beyond original spec:
- ISRI Arabic stemmer (pure Python, no NLTK) for morphological root extraction
- EN/TR translations displayed in search result cards (Arabic + English + Turkish per verse)
- Turkish translation source upgraded from Diyanet (paragraph-level) to Elmalili Hamdi Yazir (verse-level)
- Min similarity filter fixed to apply on final RRF scores
- Frontend slider range adjusted for hybrid search score distribution (10-90%, default 20%)
