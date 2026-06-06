# Mizan — Roadmap

> Last refreshed: 2026-06-06 (post-merge; embedding-backend abstraction + offline A/B shipped)
> Strategic direction. Tactical, executable items live in `TODO.md`.

Mizan Core Engine is a scholarly-grade Quranic text-analysis + semantic-search platform:
high-precision letter/word/Abjad analysis verified against Tanzil standards, plus hybrid
semantic search across Quran, translations, tafsir, and hadith.

- **API:** https://mizan-api.rollingcatsoftware.com — Python 3.11 / FastAPI, async SQLAlchemy, pgvector, Redis
- **Website:** https://mizan.rollingcatsoftware.com — Next.js 16 / React 19 (standalone)
- **Infra:** Hetzner CX43, Docker + Traefik (auto-SSL), shared Postgres 17 (pgvector) + Redis 7.4

---

## Current state (verified)

**Live & healthy.** Both containers up; `/health` → `database:true, cache:true, embedding:true, reranking:true`. NOTE: prod runs the deployed image (2026-04-26) — search-quality + reranker correctness work and the embedding-backend abstraction merged to `master` after that, so **prod lags `master`** until the next manual deploy. The reranker fixes (PR #15) note themselves as live; the embedding-backend abstraction is code-only and behaviour-unchanged at the default, so it is a safe no-op until a model is actually swapped.

What works in production:
- 114 surahs + 6,236 verses ingested; verse text, metadata, Abjad/letter/word analysis.
- Hybrid semantic search: vector (pgvector cosine on verses + translations + library chunks) + BM25 keyword (tsvector/GIN) fused with Reciprocal Rank Fusion across up to ~6 retrieval paths, sequential on one async session.
- EN (Sahih International) + TR translations embedded and surfaced per result.
- **Cross-encoder reranking is ON in prod** (`ENABLE_RERANKING=true`) — note: config *default* is `false`; prod overrides via compose. Reranking only re-scores candidates that have an English translation.
- Morphology endpoints respond (4 routes) but return **null linguistic fields** — no real MASAQ/QAC corpus is loaded; `data/masaq/` is empty.
- Frontend: Playground, Search, Library, Docs, About, legal pages; client-side i18n (en/tr/ar + RTL).
- Ops: rate limiting (slowapi), security headers, global exception handler, Sentry **built but DSN unset**, Prometheus `/metrics` (optional extra), CI (ruff + mypy --strict + pytest, cov-fail-under 50).

Known stale claims corrected this refresh: reranking is **enabled** (not disabled) in prod; the active reranker is **ms-marco (English)**, not the multilingual jina model the code docstring advertises; morphology is **structurally live but data-empty**; "automated daily backups" is not evidenced in-repo (RUNBOOK documents manual `pg_dump` only); deploy workflow does **not** auto-run migrations or ingestion.

## Next up (highest leverage)

1. ✅ **DONE** — Reranking made correct: single-source reranker model, post-rerank `min_similarity` scale bug fixed (PR #15, live), per-request rerank kill-switch, eval harness, and **language-aware reranking** so AR/TR queries get a real rerank signal. A latent reranked-score→candidate index-mapping bug was also fixed. *(was TODO P0)*
2. ✅ **DONE 2026-06-06** — **Pluggable embedding backend + model-aware prefix policy** (`feat/embedding-backend-abstraction`): `EMBEDDING_MODEL` selects the backend and its query/passage prefix convention travels with it (e5 → `query: `/`passage: `; else none). Default unchanged (e5-base). Offline, prod-safe A/B harness (`eval/run_offline_ab.py`) added.
3. ⏳ **Embedding upgrade to e5-large (search-quality frontier)** — the 2026-06-06 offline A/B shows e5-large beats e5-base on the Arabic path by a wide margin (MRR 0.585→**0.854**, nDCG 0.289→**0.452**). Recommended, but **gated**: it is 1024-dim → needs a `vector(768)→vector(1024)` migration + full re-embed + owner sign-off (see Phase 3). Default stays e5-base until then.
4. **Activate the multilingual reranker in prod** — set `RERANKER_MODEL=jina…` (needs image rebuild w/ pinned transformers — the no-rebuild path was falsified 2026-06-05) once it actually beats the ms-marco MRR 0.478 baseline. — *TODO P2 (operator / sign-off)*
5. Turn on observability and document the real deploy/migrate/ingest order. — *TODO P1*

---

## Phase 1 — Trustworthy search (correctness)

**Goal:** the search results users see are provably better with reranking on than off, and no valid result is silently dropped.

Deliverables:
- ✅ Single source of truth for the reranker model; startup log (`reranker_model_loaded`) confirms the loaded model. *(PR #15)*
- ✅ `min_similarity` filtering applied on a meaningful (cosine) scale (removed for fused results; cosine gate stays on the per-path vector scores). *(PR #15 — live; "mercy" went from ~2 to 20 results)*
- ✅ Per-request rerank kill-switch (`rerank: bool|null`) to A/B a query against raw RRF. *(PR #15)*
- ✅ Search-quality eval harness (`eval/`, labelled EN/TR/AR query set, precision@k / recall@k / MRR by language) to gate any ranking change. *(branch `feat/search-quality-2026-06-05`)*
- ✅ Language-aware reranking: native AR/TR candidate text is fed to a multilingual reranker so Arabic/Turkish queries get a real rerank signal (was English-only → AR/TR pinned at RRF floor); English-only reranker is never fed text it cannot score. Latent reranked-score→candidate index-mapping bug fixed. *(branch `feat/search-quality-2026-06-05`)*
- ✅ **Pluggable embedding backend + model-aware prefix policy** (2026-06-06, `feat/embedding-backend-abstraction`): the e5 `query: `/`passage: ` convention is now a property of the chosen backend (`prefix_policy.py`), so `EMBEDDING_MODEL` swaps the model *and* its prefixing safely; default unchanged. Plus an offline, prod-safe A/B harness (`eval/run_offline_ab.py`, MRR/nDCG/recall@k) that proves an embedding change before any re-embed.
- ⏳ **Activate** the multilingual reranker in prod — needs an image rebuild with pinned transformers for jina (the "no rebuild" path was falsified 2026-06-05) and an eval that beats ms-marco MRR 0.478. *(operator / sign-off — TODO P2)*

## Phase 2 — Production hardening & observability

**Goal:** failures are visible, deploys are repeatable, dependencies are current.

Deliverables:
- Sentry DSN wired in prod; `sentry-sdk` + Prometheus instrumentator confirmed installed in the image; one test error captured.
- Documented post-deploy runbook: `alembic upgrade head` → ingest → embed → verify; deploy workflow runs (or explicitly defers) migrations.
- Dependabot PR #14 (Next.js) and future bumps merged on a cadence; CI coverage gate aligned to the project's 75% target.
- Legacy `fly.toml` / `railway.toml` removed or clearly marked unused.

## Phase 3 — Morphology & corpus depth

**Goal:** morphology is real, and the library spans more authoritative sources.

Deliverables:
- Real Quranic Arabic Corpus ingested so roots/lemmas/patterns are populated (or endpoints/UI clearly labelled "preview").
- Additional tafsir/translation corpora ingested + embedded and verified in search results.
- **Embedding-model upgrade to `intfloat/multilingual-e5-large` (1024-dim)** — the
  offline A/B (`docs/EMBEDDING_AB_2026-06-06.md`) already shows it beats e5-base on
  the Arabic path (MRR +0.269, nDCG +0.163). The pluggable backend + prefix policy
  is in place, so the remaining work is the **breaking** part: a
  `vector(768)→vector(1024)` Alembic migration, `EMBEDDING_DIMENSION=1024`, a full
  re-embed of all verses/translations/chunks, and a live `eval/run_eval.py` re-check
  for EN/TR before cutover. Flag-gated (`EMBEDDING_MODEL`), owner-signed-off rollout.
  (`BAAI/bge-m3`, also 1024-dim, remains an alternative candidate to A/B the same way.)

## Phase 4 — Product features

**Goal:** richer scholarly exploration on top of the verified engine.

Deliverables:
- Comparative translation view (multiple meals side by side; translations already stored per-language).
- Concept/graph view (verse → similar verses → tafsir → hadith) on existing `/similar` + `search_similar_to_verse` endpoints.
- Thematic tagging via embedding clustering; word-by-word morphology UI once Phase 3 data lands.

---

## Code Quality & Professionalization

> From the 2026-06-05 code-quality review (`docs/CODE_QUALITY_2026-06-05.md`, grade **A−**).
> Two small fixes (Abjad `max_length`, a bad `type: ignore` cast) already shipped on
> `quality/2026-06-05`. The items below are behavior-changing or cross-cutting and are
> intentionally **not** auto-applied:

- ✅ **[P1] Make the test suite hermetic + the rate limiter effective** *(done 2026-06-05,
  `feat/search-quality-baseline-2026-06-05`)*. Added `Settings.init_db_on_startup`
  (default `True`; test conftest forces `False`) — eliminates the 22-ERROR mode when no
  local Postgres is present. Added `Limiter(default_limits=["120/minute"])` so
  `SlowAPIMiddleware` enforces a ceiling on every route, not just the one decorated
  `/search/semantic` route. 3 new rate-limit integration tests; full suite now 225 tests
  (all green).
- **[P2] De-duplicate `SemanticSearchService.search()` retrieval paths** — extract a
  `_safe_retrieve(path_name, coro)` helper; the six try/except blocks differ only by the
  `path=` log label (~50 lines removed).
- **[P2] Replace deprecated naive `datetime.utcnow()`** (~9 sites) with
  `datetime.now(timezone.utc)`; currently hidden because `filterwarnings` ignores
  `DeprecationWarning`. Touches stored-timestamp tz semantics — do deliberately.
- **[P3] Tighten integration asserts** that accept `status_code in (200, 500)` once the
  suite is hermetic; collapse the duplicated `get_async_session`/`get_session_context`;
  swap `asyncio.get_event_loop()` → `get_running_loop()` in the two ML adapters.

---

## Notes & gotchas

- AsyncSession runs all search DB queries **sequentially** (no concurrent queries on one session) — keep this in mind for latency work.
- Embedding (e5-base ~280MB) and reranker models load **lazily on first request** after a restart — the first post-restart query is slow; consider pre-warming.
- `data/masaq/` and `data/embeddings/` are empty in-repo (`.gitkeep` only); `quran/` + `data/tanzil/` carry the source text.
- `.env.prod` is correctly gitignored and untracked.
- Deploy: `infra/deploy.sh [build|restart|logs] mizan` on the self-hosted Hetzner runner; trigger via `.github/workflows/deploy-hetzner.yml`.
