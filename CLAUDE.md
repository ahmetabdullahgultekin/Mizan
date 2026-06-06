# CLAUDE.md — Mizan AI Session Context

> This file provides startup context for AI sessions. Read this first before making any changes.

## What is Mizan?

Mizan Core Engine (MCE) is a scholarly-grade Quranic text analysis platform that combines:
- **High-precision letter/word/Abjad analysis** verified against Tanzil.net standards
- **Semantic (vector) search** across Quran, Tafsir, and Hadith using AI embeddings
- **Islamic knowledge library** for managing and indexing Arabic text sources
- **Interactive frontend** (Next.js) with Playground, Search, and Library pages

## Current State (as of 2026-06-06)

| Component | Status | Notes |
|-----------|--------|-------|
| Backend API (analysis, verses) | ✅ Production | 114 surahs, 6,236 verses ingested |
| Hybrid Semantic Search | ✅ Production | Vector + BM25 keyword + RRF fusion across 4 retrieval paths |
| Verse Embeddings | ✅ Production | 6,236 vectors via intfloat/multilingual-e5-base (768d) |
| Verse Translations | ✅ Production | 6,236 EN (Sahih International) + 6,236 TR (Elmalili Hamdi Yazir) embedded |
| BM25 Keyword Search | ✅ Production | tsvector + GIN indexes on verses + text_chunks |
| ISRI Arabic Stemmer | ✅ Production | Pure-Python root extraction (والدين→ولد, صابرين→صبر) |
| Cross-Encoder Reranker | ✅ Enabled in prod | `ENABLE_RERANKING=true` in `docker-compose.prod.yml`. Default model = `cross-encoder/ms-marco-MiniLM-L-6-v2` (English, ~80MB) — see "Reranker model choice" below. OOM-safe fallback to RRF order. |
| Cascade Embedding Service | ✅ Complete | Local provider active; Gemini cascade optional |
| Frontend Playground | ✅ Production | Shows verse text in results, letter/word/Abjad analysis |
| Frontend `/search` | ✅ Production | Hybrid search with EN/TR translations displayed per verse |
| Frontend `/library` | ✅ Complete | Create spaces, add sources, trigger indexing |
| Favicon + PWA manifest | ✅ Done | favicon.ico, apple-touch-icon, site.webmanifest |
| Morphology (MASAQ) | 🔧 Preview (data pending) | 4 endpoints live (verse, word, root search, root frequency) but `root`/`lemma`/`pattern` are null in prod — `data/masaq/` holds no QAC corpus yet. Each response carries `data_status: "preview"` + a `note` until the corpus is ingested (then it auto-flips to `"complete"`). |
| Library sources (Tafsir/Hadith) | ✅ Production | 1,988 Tafsir + 34,516 Hadith chunks, all 36,504 fully embedded |
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

## Build / Test / Lint

Backend tests run with the `[dev]` extra only — **`torch` / `sentence-transformers`
(the `[ml]` extra) are deliberately NOT installed** for tests. The embedding and
reranking services use lazy imports, and the prefix policy is derived from the
model *name*, so the whole suite (incl. backend-selection tests) runs with no
model download. Only `eval/run_offline_ab.py` needs the `ml` extra.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # NO ml extra — keeps the shared host light

pytest                            # 250 passing (225 unit + integration + property)
                                  # conftest forces init_db_on_startup=False → no Postgres needed
ruff check src/ tests/            # lint (CI scope)
mypy src/mizan --ignore-missing-imports   # CI uses this; `mypy --strict src/` also clean
```

- CI (`.github/workflows/ci.yml`): ruff + mypy + pytest with `--cov-fail-under=50`
  on Python 3.11 & 3.12, plus a `bandit -r src/ -ll` security job.
- CI/CD deploy is **manual** (self-hosted runner) — merging does NOT auto-deploy.

## Embedding Configuration

Controlled via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `EMBEDDING_PROVIDER` | Primary provider: `local` or `gemini` | `local` |
| `EMBEDDING_MODEL` | Primary model name (see "Pluggable embedding backend" below) | `intfloat/multilingual-e5-base` |
| `EMBEDDING_DIMENSION` | Vector dimension — MUST match the model's output | `768` |
| `EMBEDDING_FALLBACK_PROVIDER` | Fallback provider (empty = disabled) | `""` |
| `EMBEDDING_FALLBACK_MODEL` | Fallback model name | `intfloat/multilingual-e5-base` |
| `GEMINI_API_KEY` | Required if using Gemini | `""` |
| `ENABLE_RERANKING` | Enable cross-encoder re-ranking | `false` |
| `RERANKER_MODEL` | Cross-encoder model name | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| `RERANKER_TOP_K` | Candidates to re-rank | `30` |

### Pluggable embedding backend + model-aware prefix policy (2026-06-06)

The embedding model is selected by `EMBEDDING_MODEL` (already plumbed
config → `factory.py` → `SentenceTransformerEmbeddingService`). The **query/passage
prefix convention is now a property of the chosen backend**, not a hardcoded
application constant:

- `src/mizan/infrastructure/embeddings/prefix_policy.py` resolves a model name to
  its prefix policy. **e5 family** (`intfloat/multilingual-e5-*`, `e5-*`) →
  `query: ` / `passage: ` (required for good e5 recall). **Everything else**
  (gemini, `bge-m3`, `gte-*`, unknown) → no prefix (conservative default —
  never inject a prefix the model was not trained on).
- `IEmbeddingService.query_prefix()` / `.passage_prefix()` expose it; the search
  service (`semantic_search_service.py`) and indexing service
  (`indexing_service.py`) ask the backend for its prefix instead of using a
  module constant. The module-level `QUERY_PREFIX`/`PASSAGE_PREFIX` constants now
  derive from `E5_POLICY` (single source of truth).
- **Default behavior is unchanged**: the prod default is e5-base, so the live
  prefixes stay `query: ` / `passage: ` exactly as before. Selecting a different
  model automatically carries the right convention. `/health` embedding status
  now reports `query_prefix` / `passage_prefix`.

> **Swapping to `intfloat/multilingual-e5-large` is NOT a drop-in env flip.**
> e5-large is **1024-dim** (e5-base is 768-dim). A cutover requires
> `EMBEDDING_MODEL=intfloat/multilingual-e5-large` **+** `EMBEDDING_DIMENSION=1024`
> **+** a `vector(768)→vector(1024)` Alembic migration **+** a full re-embed of all
> verses/translations/library chunks. Keep the default until that migration ships
> under owner sign-off. The prefix policy already handles e5-large correctly.

#### Offline embedding A/B (search-quality frontier)

`eval/run_offline_ab.py` compares embedding models **in-process, offline, and
prod-data-safe** (builds a throwaway index from the local Tanzil Arabic text +
the labelled Arabic eval cases; never reads/writes prod vectors). It reports
MRR / nDCG@k / recall@k / precision@k per model and has a **disk guard** that
refuses to download if it would exceed `--max-disk-pct` (default 85%).

```bash
pip install -e ".[ml]"   # needs torch + sentence-transformers (heavy)
python eval/run_offline_ab.py \
    --models intfloat/multilingual-e5-base intfloat/multilingual-e5-large
python eval/run_offline_ab.py --dry-run   # plan + disk check, no download
```

> **2026-06-06 measured A/B (Arabic path, k=10, 248-verse pool):**
> | model | MRR | nDCG@10 | recall@10 | P@10 |
> |---|---|---|---|---|
> | `multilingual-e5-base` (current prod) | 0.585 | 0.289 | 0.247 | 0.163 |
> | `multilingual-e5-large` | **0.854** | **0.452** | **0.390** | **0.250** |
>
> e5-large is a **large Arabic-recall win** (+0.269 MRR, +0.163 nDCG). It is the
> recommended next embedding upgrade, **gated** behind the 768→1024 migration +
> full re-embed + owner sign-off. Default stays e5-base. Full report:
> `docs/EMBEDDING_AB_2026-06-06.md`.

### Reranker model choice (deliberate, single source of truth)

The reranker model name comes **only** from `Settings.reranker_model` (env
`RERANKER_MODEL`); the `CrossEncoderRerankerService` constructor default mirrors
it so the two cannot drift (they previously did: config shipped ms-marco while
the constructor defaulted to jina).

| | `cross-encoder/ms-marco-MiniLM-L-6-v2` (DEFAULT) | `jinaai/jina-reranker-v2-base-multilingual` (opt-in, recommended for AR/TR) |
|---|---|---|
| Languages | English only | 100+ incl. Arabic/Turkish (MIRACL-ar 78.69) |
| Disk | ~80MB | ~278MB |
| Extra deps | none | `trust_remote_code=True` (`einops` is **already** in the prod image — `docker/Dockerfile` line 14) |
| CX43 cost (8 vCPU/16GB) | small; fits alongside the ~1GB-resident e5-base embedder | +~0.5–1GB resident + slower first-load; still CPU-only |

#### Language-aware reranking (2026-06-05)

The pipeline now routes the **candidate text it feeds the reranker by the
detected query language _and_ the reranker's capability**
(`SemanticSearchService._rerank_text_for` + `detect_query_language`):

| Query language | English-only reranker (ms-marco) | Multilingual reranker (`is_multilingual=True`, e.g. jina) |
|---|---|---|
| English (or plain Latin) | English `translation_text` → `content` | English `translation_text` → `content` |
| Turkish (`çğıöşü…`) | English translation only (native TR not fed) | Turkish translation → Arabic `content` |
| Arabic (Arabic script) | English translation only (native AR not fed) | **Arabic `content`** (the original verse/chunk text) |

**Why this matters:** previously the reranker only ever re-scored candidates
that carried an English `translation_text`, so raw Arabic verse-vector and
keyword hits (no translation on that path) were **never reranked** and stayed
pinned at the RRF floor — the root cause of poor Arabic/Turkish ranking. Now, an
Arabic/Turkish query paired with a multilingual reranker gets native,
language-matched text for **every** candidate. An English-only reranker is never
fed text it cannot score (it keeps the historical English-only behaviour), so
deploying the code change alone is a safe no-op for AR/TR until a multilingual
model is enabled.

> **Activation:** `RERANKER_MODEL` is now wired through `docker-compose.prod.yml`
> (defaults to ms-marco), so the model is env-selectable. Recreate `mizan-api`
> after changing it, and **always A/B with `eval/run_eval.py` before keeping it.**
>
> **⚠️ 2026-06-05 LIVE A/B FINDINGS (the earlier "just set jina, no rebuild" note was WRONG):**
> "multilingual" alone does **not** beat ms-marco on this corpus. Validated against prod:
> | model | loads? | overall MRR | verdict |
> |---|---|---|---|
> | `cross-encoder/ms-marco-MiniLM-L-6-v2` (English) | ✅ | **0.478** | **best validated — current prod** |
> | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` (multilingual, ~118MB) | ✅ | 0.333 ❌ | regresses ALL langs (ar 0.442→0.333) — weak reranker on native text loses to ms-marco on EN translations |
> | `jinaai/jina-reranker-v2-base-multilingual` (~278MB) | ❌ | — | **fails to load**: remote code imports `create_position_ids_from_input_ids`, removed in the image's transformers → needs an **image rebuild with pinned transformers**, then re-validate |
> | `BAAI/bge-reranker-v2-m3` (strong multilingual, ~2.3GB) | — | — | exceeds the **3GB container mem_limit** → needs a mem_limit raise + host RAM headroom, then validate |
>
> So the AR/TR win is real-but-gated: it needs a **strong** multilingual reranker
> (jina via image rebuild, or bge-m3 via more RAM), each requiring infra work AND
> an eval that actually beats 0.478 before keeping. ms-marco stays until then.

On load the service logs `reranker_model_loaded` with `requested_model`,
`loaded_model`, and `matches_intent` so the running model can be confirmed
against intent. `CrossEncoderRerankerService.is_multilingual` is derived from the
model name (single source of truth): jina / `*multilingual*` / `bge-*-m3` → True.

#### Search-quality eval harness (`eval/`)

`eval/run_eval.py` runs a labelled query set (`eval/queries.json`, EN/TR/AR
triples) against a running API and reports **precision@k, recall@k, and MRR** by
language. Use it to prove a ranking change helps before flipping it in prod:

```bash
python eval/run_eval.py                       # against prod
python eval/run_eval.py --base-url http://localhost:8000
python eval/run_eval.py --rerank false        # raw RRF baseline (A/B)
python eval/run_eval.py --json --min-mrr 0.4  # CI gate (non-zero exit if below)
```

> **min_similarity is a cosine-only gate.** It is enforced on each vector
> retrieval path (where scores are true cosine similarities) and is deliberately
> **not** re-applied to RRF-fused or sigmoid-reranked scores, which live on a
> different scale — doing so silently dropped valid hits (fixed 2026-06-05).

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
│   ├── embeddings/   # sentence_transformer_service, gemini_embedding_service, cascade_service, factory, prefix_policy
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
| `src/mizan/infrastructure/embeddings/prefix_policy.py` | Model-aware query/passage prefix policy (e5 → `query: `/`passage: `; else none) |
| `eval/run_offline_ab.py` | Offline, prod-safe embedding-model A/B (MRR/nDCG/recall@k) with disk guard |
| `eval/run_eval.py` | Live end-to-end search-quality eval (HTTP against running API) |
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
- **Server**: Hetzner CX43 (8 vCPU, 16GB RAM) 116.203.222.213 (Docker + Traefik + auto-SSL)
- **DB**: Shared PostgreSQL 17 with pgvector on 127.0.0.1:5432
- **Cache**: Shared Redis 7.4 on 127.0.0.1:6379 (database 1)
- **CI/CD**: GitHub Actions on self-hosted runner `hetzner-cx43`
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
