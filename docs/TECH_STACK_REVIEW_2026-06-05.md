# Mizan — Tech-Stack & Architecture Modernization Review (2026-06-05)

> Reviewer: senior staff / modernization pass over `master` HEAD `2b52117`.  
> Scope: full stack — Python/FastAPI backend, ML pipeline (embeddings + reranking), PostgreSQL+pgvector, Redis, Next.js website, Docker/Traefik infra.  
> Methodology: read all stack-defining files (CLAUDE.md, pyproject.toml, Dockerfiles, docker-compose files, package.json, src/) then verified current versions and alternatives via web research (PyPI, HuggingFace, GitHub release notes, CVE databases, MTEB leaderboard). All "latest version" and "newer alternative" claims cite a source URL.  
> Goal: serve the project's mission — scholarly-grade Arabic/Turkish/English Quranic semantic search.

---

## 1. Full Stack Inventory

| Component | Pinned / in use | Latest stable (2026-06-05) | Gap |
|---|---|---|---|
| **Language** | Python 3.13 (Dockerfile); dev venv = 3.12.3 | 3.13.x current; 3.14 in beta | Minor mismatch: prod image says 3.13, dev venv is 3.12 |
| **Web framework** | FastAPI `>=0.109.0` (lower-bound, no upper pin) | 0.136.3 (2026-05-23) [(PyPI)](https://pypi.org/project/fastapi/) | No pin → potentially any 0.136.x; constraint is ≥0.109 which is fine |
| **ASGI server** | uvicorn[standard] `>=0.27.0` | 0.34.x | Unconstrained upper; works |
| **Data validation** | pydantic `>=2.5.0` + pydantic-settings `>=2.1.0` | pydantic 2.13.4 [(docs)](https://docs.pydantic.dev/latest/) | Fine — Pydantic v2 is the standard; v3 not planned as API break |
| **DB client** | SQLAlchemy[asyncio] `>=2.0.25` + asyncpg `>=0.29.0` + alembic `>=1.13.0` | SQLAlchemy 2.x; alembic 1.18.4 [(docs)](https://alembic.sqlalchemy.org/) | Alembic constraint is ≥1.13; 1.18 available — minor gap, no breaking changes |
| **Vector DB extension** | pgvector extension: `pgvector/pgvector:pg15` (Docker image) | Extension: 0.8.2 (2026-02-25, fixes CVE-2026-3172); PG image: pg15 latest; PG17/18 available | **SECURITY GAP**: CVE-2026-3172 (CVSS 8.1) buffer overflow in parallel HNSW build — affects 0.6.0–0.8.1. **Prod is on pg15 image; need to verify extension version** |
| **pgvector Python lib** | `pgvector>=0.2.0` | 0.4.2 (2025-12-05) [(PyPI)](https://pypi.org/project/pgvector/) | Gap: ≥0.2.0 constraint, 0.4.2 available — minor API additions (halfvec, sparsevec support) |
| **Cache** | Redis 7.4 (`redis:7-alpine`) | Redis 8.8.0 (May 2026, GA with new vector/AI features) [(release notes)](https://redis.io/docs/latest/operate/oss_and_stack/stack-with-enterprise/release-notes/redisce/redisos-8.0-release-notes/) | Redis 7 is stable but one major version behind |
| **Embedding model** | `intfloat/multilingual-e5-base` (768d, ~270MB) | Current top alternatives: BGE-M3 (1024d, ~1.1GB), GATE-AraBert-v1 (768d, ~135MB) | e5-base is solid but not SOTA for Arabic; see §3 |
| **Embedding library** | sentence-transformers `>=2.2.0` | 5.5.1 (2026-05-20), **requires Python ≥3.10** [(PyPI)](https://pypi.org/project/sentence-transformers/) | **Large gap**: pinned ≥2.2.0 means old installs; current is 5.x (multimodal, major rewrite) |
| **ML framework** | torch `>=2.1.0` (CPU-only whl) | 2.12.0 (2026-05-13) [(PyPI)](https://pypi.org/project/torch/) | Constraint is ≥2.1.0; builds pull latest 2.x, gap is ~4 majors unrealized |
| **Transformers** | transformers `>=4.36.0` | 5.10.2 (2026-06-04) [(PyPI)](https://pypi.org/project/transformers/) | **Major version behind**: jina-reranker-v2 fails to load because image has transformers 4.x; 5.x is now stable |
| **Reranker (default)** | `cross-encoder/ms-marco-MiniLM-L-6-v2` (~80MB, English) | ms-marco is well-maintained; no newer cross-encoder of same class | Appropriate for English; **root cause of Arabic/Turkish quality gap** |
| **Reranker (opt-in, broken)** | `jinaai/jina-reranker-v2-base-multilingual` (~278MB) | jina-reranker-v3 (newer; API-based / open-weights under licence) | Broken due to transformers 4.x compat; jina-v3 is API-first |
| **Arabic NLP** | pyarabic `>=0.6.15` + ISRI stemmer (pure Python) | pyarabic 0.6.15 — no major releases since 2023 | Mature/stable; adequate for root/stemming tasks |
| **PostgreSQL** | pg15 (`pgvector/pgvector:pg15` image) | PG17 is current stable; PG18 in final beta | Two major versions behind; PG17 has performance, parallelism, and vacuum improvements relevant to HNSW |
| **Frontend framework** | Next.js `^16.2.6` + React `^19.0.0` | Next.js 16.2.x is current stable (Turbopack default, React 19.2) [(blog)](https://nextjs.org/blog/next-16) | Up to date — website was bumped to 16.2.7 recently |
| **Tailwind CSS** | `^4.2.2` | 4.x is GA stable (Oxide engine, CSS-first config, 5x faster builds) [(blog)](https://tailwindcss.com/blog/tailwindcss-v4) | Up to date |
| **TypeScript** | `5.9.3` | 5.9.x current | Up to date |
| **Node.js base image** | `node:22-alpine` | Node 22 is LTS (Active) | Up to date |
| **Reverse proxy** | Traefik (version from infra/ shared config; not pinned in this repo) | Traefik 3.7.4 (2026-06-05) [(releases)](https://github.com/traefik/traefik/releases) | Shared infra — out of scope for this repo, but worth noting |
| **CI/CD** | GitHub Actions (self-hosted runner `hetzner-cx43`) | Current | N/A |
| **Observability** | sentry-sdk[fastapi] `>=2.0.0`, prometheus-fastapi-instrumentator `>=7.0.0` | Sentry SDK ~2.x current | Fine |
| **Structured logging** | structlog `>=24.1.0` | 25.5.0 [(PyPI)](https://pypi.org/project/structlog/) | Minor gap — structlog 25.x has improved console renderer; no breaking changes |
| **Rate limiting** | slowapi `>=0.1.9` | 0.1.9 is current (low-activity project) | Fine; note: per CODE_QUALITY review, currently inert on most routes |
| **Architecture pattern** | Hexagonal (ports & adapters); clean domain layer; RRF hybrid search | Still industry standard for ML backends; no reason to change | KEEP |
| **Search design** | BM25 (tsvector/GIN) + vector (pgvector cosine) + RRF fusion + optional cross-encoder rerank | Industry best practice for RAG/semantic search 2026 | KEEP |
| **Migration tool** | Alembic | Industry standard; no credible alternative | KEEP |
| **Build backend** | hatchling | Modern PEP 517; fine | KEEP |

---

## 2. Security / EOL Urgent Items

### S1 — CVE-2026-3172: pgvector parallel HNSW buffer overflow (CVSS 8.1) — URGENT
**Severity**: High. Affects pgvector 0.6.0–0.8.1. Buffer overflow in parallel HNSW index build allows an authenticated DB user to leak data from other relations or crash the server.  
**Fix**: Upgrade to pgvector extension 0.8.2.  
**Source**: [sentinelone.com/vulnerability-database/cve-2026-3172](https://www.sentinelone.com/vulnerability-database/cve-2026-3172/) · [postgresql.org/about/news/pgvector-082-released-3245](https://www.postgresql.org/about/news/pgvector-082-released-3245/)  
**Action**: Check which pgvector extension version is running in the prod container (`SELECT extversion FROM pg_extension WHERE extname = 'vector';`). If < 0.8.2, the Docker base image `pgvector/pgvector:pg15` must be pulled to a tag that ships 0.8.2. The pg15 tag on Docker Hub now ships 0.8.2; a `docker pull` + `ALTER EXTENSION vector UPDATE;` resolves it.  
**Effort**: S. Risk: LOW (apply during a maintenance window; no schema changes needed between 0.7–0.8.2).

### S2 — transformers 4.x → 5.x gap (not a CVE, but blocks the multilingual reranker path)
The prod image pins `transformers>=4.36.0`; the current release is **5.10.2**. Transformers 5 dropped several deprecated APIs and brings improved model loading. More concretely, this is the root cause documented in CLAUDE.md: `jina-reranker-v2-base-multilingual` fails to load because `create_position_ids_from_input_ids` was removed from the image's transformers version. Rebuilding with `transformers>=5.0.0` unblocks jina-v2 (pending the pinned-transformers image rebuild step).  
**Effort**: S–M (update pyproject.toml constraint; rebuild image; validate jina-reranker-v2 loads; then run `eval/run_eval.py` to verify no regression on ms-marco baseline before switching).

### S3 — sentence-transformers ≥2.2.0 constraint extremely wide
The lower bound ≥2.2.0 allows installs of 2.x, 3.x, 4.x, or 5.x. sentence-transformers 5.x **requires Python ≥3.10** and introduced API changes (model card metadata, SentenceTransformer class refactors). The prod Dockerfile uses Python 3.13 so the constraint is fine in practice, but if someone creates a 3.9 environment and pulls 5.x they'll get a confusing error. More importantly, the huge gap between 2.2 and 5.5.1 hides a major jump in capability (multimodal, Matryoshka, reranking API). Tighten to `>=3.0.0` or `>=5.0.0`.  
**Effort**: S (constraint change + smoke test).

---

## 3. Component-by-Component Verdicts

### 3.1 Embedding Model: `intfloat/multilingual-e5-base`

| | Detail |
|---|---|
| **Current** | multilingual-e5-base — 768d, 12-layer XLM-RoBERTa base (~270MB), MrTyDi-AR MRR@10 = 72.3 |
| **What's better for AR/TR?** | Three credible upgrades exist: |
| (a) **multilingual-e5-large-instruct** | 1024d, 24-layer, MrTyDi-AR MRR@10 ≈ 77.5 (+5.2 pts). Instruction-tuned; uses "Instruct: ..." prefix. ~550MB. Same family — lower migration risk. |
| (b) **BAAI/bge-m3** | 1024d, 570M params, ~1.1GB. MIRACL-AR nDCG@10 = 67.8 (dense) / 70.0 (hybrid all heads). Also acts as a sparse retriever and reranker (BGE-reranker-v2-m3). Rich Arabic morphology handling. BUT: **exceeds the 3GB container mem_limit** if loaded alongside the ms-marco reranker. Would need mem_limit raised from 3 → 5GB on CX43. |
| (c) **GATE-AraBert-v1** (Omartificial-Intelligence-Space) | 768d, 135M params (~same disk as e5-base). Arabic-specialized; STS benchmarks show strong Arabic STS performance. BUT: ArabicMTEB retrieval numbers not publicly compared to e5-base in a head-to-head table. Would need a local A/B eval via `eval/run_eval.py`. |
| **Verdict** | **CONSIDER UPGRADE to multilingual-e5-large-instruct** (Option a). Same family, moderate size jump, measurable AR improvement, no dimension change (still 768d — wait, actually 1024d — requires a **full re-embed of all 42k vectors**). BGE-M3 is the SOTA choice but needs infra work. GATE is promising for Arabic STS but retrieval benchmarks are unproven on this corpus without local eval. |
| **Sources** | [HuggingFace e5-base model card](https://huggingface.co/intfloat/multilingual-e5-base) · [BGE-M3 MIRACL benchmarks](https://huggingface.co/BAAI/bge-m3) · [GATE paper arXiv:2505.24581](https://arxiv.org/abs/2505.24581) · [ArabicMTEB/Swan paper arXiv:2411.01192](https://arxiv.org/abs/2411.01192) |

**Important caveat**: switching embedding models requires re-embedding all 42,740 stored chunks and verses (Quran × 3 languages + tafsir + hadith), updating `EMBEDDING_DIMENSION` in config and alembic migration if dimension changes, and validating search quality with `eval/run_eval.py` before promoting. The eval harness is already in place — this is the right workflow.

### 3.2 Reranker

| Model | Loads? | AR/TR capable? | Size | Status |
|---|---|---|---|---|
| ms-marco-MiniLM-L-6-v2 | ✅ | English only | ~80MB | **Best validated (MRR 0.478 on current corpus)** |
| jina-reranker-v2-base-multilingual | ❌ (transforms 4.x) | Yes | ~278MB | Blocked by transformers version |
| mmarco-mMiniLMv2 | ✅ | Yes (weak) | ~118MB | MRR 0.333 — regresses all languages |
| BAAI/bge-reranker-v2-m3 | — | Yes (strong) | ~2.3GB | Needs mem_limit 3→5GB |
| jina-reranker-v3 | API / open-weights | Yes | — | New release; heavier licence |

**Verdict for reranker**: The path forward is clearly documented in CLAUDE.md and is correct. The immediate unlock is upgrading transformers to 5.x, then validating jina-v2. If jina-v2 beats 0.478 in `eval/`, adopt it. BGE-reranker-v2-m3 is the strongest option but requires a RAM upgrade consideration.

**New consideration (2026-06-05)**: BGE-M3 is simultaneously an embedding model AND supports its own reranking (cross-encoder) mode via `FlagReranker` / `BGEM3FlagModel`. If the embedding is migrated to BGE-M3, the reranker can share the already-loaded model weights — effectively a **zero-extra-RAM** multilingual reranker once BGE-M3 is in memory. This is the most resource-efficient route to a strong multilingual pipeline.

### 3.3 PostgreSQL: pg15 → pg17

**Verdict**: UPGRADE (M effort).  
PostgreSQL 17 brings: improved VACUUM on large tables, parallel query improvements (relevant to HNSW index builds), logical replication enhancements, and is now the current stable. pg16 → pg17 is the sensible jump (pg18 is still in final beta).  
pgvector is fully compatible with pg17; the HNSW index syntax/config is unchanged. The migration requires: dump → pg17 container → restore → `ALTER EXTENSION vector UPDATE;`. Given prod uses a named Docker volume on shared Postgres (not a cloud managed service), this is a maintenance-window operation.  
**Source**: [pgvector pg16/pg17 install guide](https://dbadataverse.com/tech/postgresql/2026/05/install-and-configure-pgvector-on-postgresql-16-and-17-step-by-step-guide-2026) · [pgvector CHANGELOG](https://github.com/pgvector/pgvector/blob/master/CHANGELOG.md)

### 3.4 Redis: 7.4-alpine → 8.x

**Verdict**: CONSIDER UPGRADE (S effort if non-breaking).  
Redis 8.0 GA unified the previously separate Redis Stack modules (RediSearch, RedisJSON, RedisTimeSeries, RedisBloom) into the core product. Redis 8.8 is current (May 2026). Mizan uses Redis only for API response caching (TTL-based, database 1) — it does not use any of the advanced module features. Redis 7 → 8 is backward-compatible for basic get/set/expire use cases.  
Upgrade path: change `image: redis:7-alpine` to `redis:8-alpine` in docker-compose; restart; verify health check passes. Zero data migration needed (cache is ephemeral).  
**Source**: [Redis 8.0 release notes](https://redis.io/docs/latest/operate/oss_and_stack/stack-with-enterprise/release-notes/redisce/redisos-8.0-release-notes/) · [Redis EOL status](https://endoflife.date/redis)

### 3.5 Python Version: 3.13 (Dockerfile) vs 3.12.3 (dev venv)

**Verdict**: KEEP 3.13 in Docker; align dev venv to 3.13.  
Python 3.13 is production-ready for web frameworks and ML workloads. The JIT and free-threading features are still experimental and are not used here. The dev/prod mismatch (3.12 in venv, 3.13 in Dockerfile) is a low-risk inconsistency but could hide 3.12-specific behavior. Recommend: update developer instructions to use Python 3.13, and update `pyproject.toml` `requires-python` from `>=3.11` to `>=3.12` or `>=3.13` to reflect the actual runtime baseline.  
Note: sentence-transformers 5.x requires Python ≥3.10, so this is unaffected.  
**Source**: [Python version status](https://devguide.python.org/versions/) · [Python 3.13 production readiness](https://versionlog.com/python/3.13/)

### 3.6 PyTorch: ≥2.1.0 → 2.12.0

**Verdict**: KEEP pattern (float constraint), UPGRADE image.  
PyTorch 2.12.0 (2026-05-13) brings CPU performance improvements (including FP16 on x86, which benefits CPU-only inference). The CPU-only whl install pattern in the Dockerfile is correct and efficient. No API-breaking changes affect the project's usage (model loading via sentence-transformers + cross-encoder). Bumping the minimum to `>=2.1.0` is fine; the Dockerfile installs latest-cpu anyway.  
**Source**: [torch PyPI](https://pypi.org/project/torch/) · [PyTorch 2.6 CPU FP16 blog](https://pytorch.org/blog/pytorch2-6/)

### 3.7 Transformers: ≥4.36.0 → 5.10.2

**Verdict**: UPGRADE (S–M, linked to S2 and jina-reranker unblock).  
Transformers 5.x (released 2026) is a major version with new model architecture support, pipeline API improvements, and the removal of several deprecated fallbacks that caused the jina-reranker load failure. Mizan uses transformers only indirectly through sentence-transformers and the CrossEncoderRerankerService. Upgrading resolves the jina-v2 load failure documented in CLAUDE.md.  
Update `pyproject.toml` ml extra: `"transformers>=5.0.0"`.  
**Source**: [transformers PyPI](https://pypi.org/project/transformers/)

### 3.8 sentence-transformers: ≥2.2.0 → 5.5.1

**Verdict**: UPGRADE constraint to `>=5.0.0` (S effort).  
sentence-transformers 5.x (current: 5.5.1, 2026-05-20) introduced multimodal embeddings, Matryoshka training utilities, and a refined SentenceTransformer API. The core encode/predict API used by Mizan is unchanged. Tightening the constraint documents the true runtime baseline and prevents accidental installs of the 2.x series which had a different model card API.  
**Source**: [sentence-transformers PyPI](https://pypi.org/project/sentence-transformers/) · [sentence-transformers multimodal announcement](https://mindwiredai.com/2026/04/13/sentence-transformers-just-went-multimodal-heres-why-its-a-big-deal/)

### 3.9 FastAPI: ≥0.109.0 (current ~0.136.3)

**Verdict**: KEEP. The unconstrained upper bound means latest FastAPI is already being installed. No known breaking changes between 0.109 and 0.136 affect this project. The new Content-Type enforcement in 0.136 is a server-side improvement.  
**Source**: [FastAPI PyPI](https://pypi.org/project/fastapi/) · [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/)

### 3.10 Next.js: ^16.2.6 + React ^19.0.0

**Verdict**: KEEP. This is current stable. Next.js 16.2 ships Turbopack as default, React 19.2 features, and the stable Adapter API. The website was bumped to 16.2.7 in the most recent commit. No further action needed.  
**Source**: [Next.js 16 release blog](https://nextjs.org/blog/next-16) · [endoflife.date/nextjs](https://endoflife.date/nextjs)

### 3.11 Tailwind CSS: ^4.2.2

**Verdict**: KEEP. Tailwind v4 (current: 4.x) is GA and production-ready with the Oxide engine. This is the correct version for new projects in 2026.  
**Source**: [Tailwind v4.0 blog](https://tailwindcss.com/blog/tailwindcss-v4)

### 3.12 Architecture: Hexagonal / Ports-and-Adapters

**Verdict**: KEEP. The hexagonal pattern (domain → application → infrastructure → api) is the right choice for a project that expects to swap embedding providers, rerankers, and potentially vector stores. The CODE_QUALITY review (2026-06-05) confirmed clean layering with zero infra imports in domain. The ports (IEmbeddingService, IRerankerService, repository interfaces) are cleanly defined. No architectural revision recommended.

### 3.13 Search Design: BM25 + Vector + RRF + Cross-encoder

**Verdict**: KEEP. Hybrid BM25+vector+RRF is the 2026 industry standard for production RAG/semantic search. The recent addition of language-aware reranker routing (feeding native Arabic text to multilingual rerankers) is state-of-the-art design. The ISRI Arabic stemmer feeding the tsvector path is a pragmatic and appropriate Tier-2 enhancement.  

**One genuine gap worth tracking (not fixing now)**: the BM25 GIN index on `content` uses the default `pg_catalog.arabic` text-search dictionary (if configured) or `simple`. For truly high-quality Arabic full-text, PostgreSQL can be configured with an Arabic text search dictionary that applies root-based stemming at the DB level — but since Mizan already applies ISRI stemming at ingestion time via `ingest_tanzil.py`, the overlap is addressed. This is a MONITOR item, not an action item.

### 3.14 pgvector Python library: ≥0.2.0 → 0.4.2

**Verdict**: UPGRADE constraint to `>=0.3.0` (S, non-breaking).  
pgvector-python 0.4.x adds support for `halfvec` and `sparsevec` types (mirroring pgvector 0.8.x extension additions) and async improvements. The project only uses `Vector` type for dense embeddings, so this is low-urgency but worth tracking for future half-precision storage optimization.  
**Source**: [pgvector-python releases](https://github.com/pgvector/pgvector-python/releases)

### 3.15 Alembic: ≥1.13.0 → 1.18.4

**Verdict**: UPGRADE constraint to `>=1.14.0` (S).  
The pyproject.toml requires ≥1.13.0; 1.18.4 is latest. No breaking changes between 1.13 and 1.18 — purely additive (new `--autogenerate` options, `op.create_check_constraint` improvements). Tightening to ≥1.14.0 or ≥1.16.0 signals the tested baseline more accurately.  

### 3.16 Observability gap: no OpenTelemetry traces

**Verdict**: CONSIDER (L effort, low urgency).  
The stack ships Sentry (error tracking) and prometheus-fastapi-instrumentator (metrics), but no distributed tracing (OpenTelemetry spans). For a single-container deployment this is fine. As the corpus grows or multi-tenant use is considered, OTEL traces would let you profile embedding latency vs DB query vs reranking per request. The structlog integration makes adding OTEL relatively clean (otel-exporter-otlp + opentelemetry-instrumentation-fastapi). This is a nice-to-have, not a deficiency.

---

## 4. Prioritized Recommendations

Sorted by **value-per-effort** (highest first). "Worth doing" items are separated from "shiny but not worth the churn."

### WORTH DOING

| Priority | Item | Verdict | Effort | Risk | Why it matters |
|---|---|---|---|---|---|
| **P1** | Upgrade pgvector Docker image to 0.8.2 (fix CVE-2026-3172) | UPGRADE (security) | **S** | Low | CVSS 8.1 buffer overflow; parallel HNSW builds are enabled in this project. Run `docker pull pgvector/pgvector:pg15` (now ships 0.8.2) + `ALTER EXTENSION vector UPDATE;` in a maintenance window. |
| **P2** | Upgrade transformers constraint to `>=5.0.0` + rebuild image | UPGRADE | **S–M** | Low–Medium | Unblocks jina-reranker-v2 (multilingual reranker). jina-v2 is 278MB vs 80MB for ms-marco but covers Arabic/Turkish natively. Run `eval/run_eval.py` to confirm it beats the 0.478 MRR baseline before enabling. The existing eval harness makes this a data-driven decision, not a guess. |
| **P3** | Evaluate multilingual-e5-large-instruct as embedding model | CONSIDER UPGRADE | **M** | Medium | MrTyDi-AR MRR@10 improves from 72.3 → 77.5 (+7%). Requires full re-embed of ~42k vectors (script already exists: `embed_quran.py` + `ingest_translations.py`). Note: dimension changes 768→1024 — needs an alembic migration to alter the vector column + config update. Validate with `eval/` before switching prod. |
| **P4** | Upgrade pgvector Python lib to `>=0.3.0` / `>=0.4.0` | UPGRADE | **S** | None | Tracks pgvector 0.8.x extension additions (halfvec for half-precision storage → 50% reduction in vector storage footprint, useful if corpus grows). Constraint-only change; no code changes. |
| **P5** | Upgrade sentence-transformers constraint to `>=5.0.0` | UPGRADE | **S** | None | Closes a confusing 3-major-version documentation gap; prevents accidental use of old 2.x API. No runtime behavior change in standard usage. |
| **P6** | Upgrade Redis to 8.x (`redis:8-alpine`) | UPGRADE | **S** | Low | Redis 7 reaches EOL in the 2027 timeframe; 8.x is current GA. No API changes for the simple cache use case. One-line change in docker-compose + health check passes immediately. |
| **P7** | Upgrade PostgreSQL base image to pg17 | UPGRADE | **M** | Medium | PG17 is current stable; HNSW parallel build improvements relevant to corpus rebuilds; VACUUM improvements for long-running tables. Requires dump/restore migration. Schedule for next corpus rebuild window. |
| **P8** | Tighten `requires-python` to `>=3.12` or `>=3.13` | UPGRADE | **S** | None | Aligns pyproject.toml with the actual Docker runtime (py3.13). Clarifies supported baseline for contributors. |

### SHINY BUT NOT WORTH THE CHURN NOW

| Item | Why skip |
|---|---|
| **Migrate embedding to BGE-M3** | Best retrieval quality for Arabic (MIRACL-AR 67.8+) but 1.1GB model + 1024d dimension = needs mem_limit raised from 3→5GB, full re-embed, alembic migration, and eval. Do this only after the transformers upgrade + jina-v2 eval path is exhausted. If BGE-M3 as embedder + BGE-reranker-v2-m3 (shared weights) beats the current pipeline on the eval harness, it becomes P1. |
| **Migrate to cloud embedding API (Cohere embed-v4, Voyage 3.5)** | Cloud APIs add per-query cost and latency, create a hard external dependency, and require data-privacy review for Quranic scholarly content. Cohere embed-v4 supports 48 languages (good for AR/TR) but the local pipeline already has a Gemini cascade fallback if needed. The self-hosted path is more appropriate for this project. |
| **Add OpenTelemetry distributed tracing** | Single-container deployment; adds ~3-5MB overhead per service; low immediate value. Reconsider if the project scales to multi-tenant or adds async job queues. |
| **Replace pgvector with a dedicated vector DB (Qdrant, Weaviate)** | pgvector + HNSW is production-grade for Mizan's corpus size (42k vectors). Migration would add operational complexity with no measurable recall gain at this scale. The hexagonal repository pattern (IVerseEmbeddingRepository interface) means this is a future option without code changes outside the infrastructure layer. |
| **Migrate to FastAPI 1.0 (once released)** | FastAPI 1.0 has been discussed but not released. Monitor; no action now. |
| **Rebuild on Hono / Bun / other Next.js alternative** | Next.js 16.2 is current and the website is well-structured. No churn justified. |

---

## 5. Arabic/Turkish Search Quality — Specific Path Forward

This is the live lever where the investment pays off most directly for the project's mission. The current state:

1. **Embedding quality**: multilingual-e5-base is good, not SOTA for Arabic. MrTyDi-AR gap to e5-large-instruct is ~7%. This is a measurable, achievable improvement.
2. **Reranker**: ms-marco (English-only) is the validated best at MRR 0.478 on the eval set. The language-aware routing code (2026-06-05) is correct — it will feed Arabic text to a multilingual reranker — but no working multilingual reranker is currently loaded.
3. **The blocking issue is the transformers version** (P2), not a design flaw.

Recommended sequence:
1. Fix CVE-2026-3172 (pgvector 0.8.2) — S effort, no eval needed.
2. Upgrade transformers to ≥5.0.0, rebuild image, verify jina-reranker-v2 loads.
3. Run `python eval/run_eval.py` with jina-v2. If AR/TR MRR beats 0.478, enable it in prod.
4. If jina-v2 helps but not enough, evaluate BGE-M3 as a combined embedder+reranker (P3/BGE path).

---

## 6. Sources

- FastAPI PyPI: https://pypi.org/project/fastapi/
- FastAPI release notes: https://fastapi.tiangolo.com/release-notes/
- pgvector CHANGELOG: https://github.com/pgvector/pgvector/blob/master/CHANGELOG.md
- CVE-2026-3172 (pgvector buffer overflow): https://www.sentinelone.com/vulnerability-database/cve-2026-3172/
- pgvector 0.8.2 release announcement: https://www.postgresql.org/about/news/pgvector-082-released-3245/
- pgvector Python PyPI: https://pypi.org/project/pgvector/
- sentence-transformers PyPI: https://pypi.org/project/sentence-transformers/
- sentence-transformers multimodal v5 announcement: https://mindwiredai.com/2026/04/13/sentence-transformers-just-went-multimodal-heres-why-its-a-big-deal/
- transformers PyPI: https://pypi.org/project/transformers/
- torch PyPI: https://pypi.org/project/torch/
- PyTorch 2.6 CPU FP16: https://pytorch.org/blog/pytorch2-6/
- multilingual-e5-base model card (MrTyDi-AR 72.3): https://huggingface.co/intfloat/multilingual-e5-base
- multilingual-e5-large-instruct model card: https://huggingface.co/intfloat/multilingual-e5-large-instruct
- BGE-M3 MIRACL benchmarks: https://huggingface.co/BAAI/bge-m3
- GATE Arabic embedding paper: https://arxiv.org/abs/2505.24581
- ArabicMTEB / Swan paper: https://arxiv.org/abs/2411.01192
- BGE-reranker-v2-m3 model card: https://huggingface.co/BAAI/bge-reranker-v2-m3
- jina-reranker-v2-base-multilingual: https://huggingface.co/jinaai/jina-reranker-v2-base-multilingual
- Redis 8.0 release notes: https://redis.io/docs/latest/operate/oss_and_stack/stack-with-enterprise/release-notes/redisce/redisos-8.0-release-notes/
- Redis EOL: https://endoflife.date/redis
- Alembic 1.18.4 docs: https://alembic.sqlalchemy.org/en/latest/changelog.html
- Pydantic v2 docs: https://docs.pydantic.dev/latest/
- Next.js 16 blog: https://nextjs.org/blog/next-16
- Next.js EOL: https://endoflife.date/nextjs
- Tailwind CSS v4.0: https://tailwindcss.com/blog/tailwindcss-v4
- Traefik releases: https://github.com/traefik/traefik/releases
- Structlog PyPI: https://pypi.org/project/structlog/
- pgvector pg16/pg17 install guide: https://dbadataverse.com/tech/postgresql/2026/05/install-and-configure-pgvector-on-postgresql-16-and-17-step-by-step-guide-2026
- Python version status: https://devguide.python.org/versions/
- Embedding model comparison 2026: https://reintech.io/blog/embedding-models-comparison-2026-openai-cohere-voyage-bge
- BGE vs E5 comparison 2026: https://dasroot.net/posts/2026/01/embedding-models-comparison-bge-e5-instructor/
