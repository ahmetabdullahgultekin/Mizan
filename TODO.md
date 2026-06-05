# Mizan — TODO

> Last refreshed: 2026-06-04 (grounded in HEAD `3c44ddb`, live API + prod container inspection)
> Tactical backlog. Strategic sequencing lives in `ROADMAP.md`.

## Verified current state (read before starting)

| Area | Reality on HEAD / prod |
|------|------------------------|
| API + Website | Live & healthy: `mizan-api` + `mizan-website` containers up; `/health` returns `database:true, cache:true, embedding:true, reranking:true`. Deployed image dated 2026-04-26 == current HEAD. |
| Quran data | 114 surahs + 6,236 verses ingested; semantic search returns real results with EN/TR translations. |
| Reranking | **ENABLED in prod** (`ENABLE_RERANKING=true` via `docker-compose.prod.yml` `${ENABLE_RERANKING:-true}`). The config *default* is `false`, but prod overrides it on. CLAUDE.md / old roadmap saying "disabled" are STALE. |
| Reranker model | Prod sets no `RERANKER_MODEL`, so it uses the config default `cross-encoder/ms-marco-MiniLM-L-6-v2` (English-only, ~80MB) — NOT the multilingual jina model the service docstring advertises. |
| Morphology (MASAQ) | Endpoints respond, but `root`/`lemma`/`pattern` are **all null** in prod (2:255 → 116 segments, 0 roots). `data/masaq/` is empty (only `.gitkeep`). Morphology is structurally live but linguistically empty. |
| Tests | 172 backend test functions (README badge "172 passed"); CI runs ruff + mypy --strict + pytest `--cov-fail-under=50`. Not reproducible locally here (no venv) and prod image is slim (no tests/pytest). Treat "172 passed" as CI-asserted, not independently re-verified this session. |
| Secrets | `.env.prod` is gitignored and NOT tracked (good). |

---

## P0 — Blocker / Critical

- [ ] **Reconcile reranker model: prod runs English-only ms-marco, not multilingual jina** — `src/mizan/infrastructure/config.py` (`reranker_model` default), `docker-compose.prod.yml` (no `RERANKER_MODEL` set), `src/mizan/infrastructure/reranking/cross_encoder_service.py` (docstring/default = jina). Why: reranking is ON in prod but only re-scores the *English translation* of each candidate with an English cross-encoder, so Arabic/Turkish queries get no rerank benefit and English-translation bias is amplified. Done when: a single source of truth sets the reranker model, `GET /health` (or a debug log) confirms the model actually loaded matches intent, and the choice (ms-marco vs jina) is documented in CLAUDE.md with its memory/latency cost on the CX43.

- [ ] **Fix post-rerank `min_similarity` filtering against the wrong score scale** — `src/mizan/application/services/semantic_search_service.py` lines ~183-190. Why: after RRF and/or sigmoid reranking, results are filtered with `r.similarity_score >= min_similarity` (default 0.5), but RRF-normalized and sigmoid scores are NOT cosine similarities — the threshold is semantically meaningless and silently drops valid hits (live `mercy` query returned only 2 results). Done when: the final user-facing filter is applied to per-path cosine scores (captured before fusion) OR the threshold is removed/re-scaled for fused results, with a test asserting a broad query returns ≥ expected count.

- [ ] **Verify the test suite actually passes on HEAD and record the real number** — `tests/`, `.github/workflows/ci.yml`. Why: README claims "172 passed"; this session could not reproduce (no local install) and the count is the source of a public badge. Done when: `pip install -e ".[dev,ml]"` then `pytest` is run on HEAD, the green count is recorded in CHANGELOG/README, and any newly-red tests get tickets.

## P1 — High

- [ ] **Document the real prod deploy runbook for migrations + ingestion** — `.github/workflows/deploy-hetzner.yml`, `docs/RUNBOOK.md`, `CLAUDE.md`. Why: the deploy workflow only runs `deploy.sh build/restart mizan` + a health curl; it does NOT run `alembic upgrade head` or any ingest/embed script, so schema/data changes are silent manual steps with no documented order. Done when: RUNBOOK has an explicit "after deploy" checklist (migrate → ingest → embed → verify) and the deploy workflow either runs migrations or explicitly states they are manual.

- [ ] **Decide and document MASAQ morphology: ship real QAC data or label it as preview** — `scripts/ingest_masaq.py`, `data/masaq/` (empty), `src/mizan/api/routers/morphology.py`. Why: 4 morphology endpoints are advertised as "Production" but return null roots/lemmas because no real corpus is loaded; users get empty linguistic fields. Done when: either the Quranic Arabic Corpus is ingested (roots non-null for 2:255) OR the endpoints/UI clearly flag morphology as "preview / data pending" so it isn't mistaken for verified output.

- [ ] **Wire Sentry DSN in prod** — `docker-compose.prod.yml`, `.env.prod`, `src/mizan/api/main.py` (`_init_sentry`). Why: Sentry integration is fully built and no-ops without a DSN; prod currently has zero error tracking. Done when: `SENTRY_DSN` + `SENTRY_ENVIRONMENT=production` are set, `sentry-sdk[fastapi]` is installed in the image (it's in the `observability` extra, confirm the Dockerfile installs it), and a forced test error appears in Sentry.

- [ ] **Merge or close open Dependabot PR #14 (Next.js 16.2.3 → 16.2.6)** — `website/package.json`. Why: only open PR; security/bug patch backlog on the framework. Done when: PR #14 is reviewed, website build + e2e pass, and it is merged or closed with a reason. (Note: PR #13 postcss bump already merged onto HEAD.)

- [ ] **Add a per-request rerank kill-switch / debug flag** — `src/mizan/application/dtos/library_requests.py` (`SemanticSearchRequest`), `src/mizan/api/routers/semantic_search.py`. Why: reranking is global-on in prod with no way to A/B a single query against raw RRF, making the P0 score-scale bug hard to diagnose in the field. Done when: an optional `rerank: bool | None` request field (or `?debug=raw`) bypasses the reranker for that call.

## P2 — Medium

- [ ] **Build a search-quality eval harness** — new `eval/` dir + script, reuse `scripts/` patterns. Why: rerank-on, model-choice, and the min_similarity fix all need a metric (e.g. nDCG / recall@k on a labelled query set) to prove they help rather than guessing from one `mercy` query. Done when: a small labelled query→expected-verse set runs in CI or on demand and prints recall@k for {raw RRF, +rerank}.

- [ ] **Cold-start latency: pre-warm the embedding (and reranker) model on startup** — `src/mizan/infrastructure/embeddings/sentence_transformer_service.py` (`_load_model` lazy), `src/mizan/api/main.py` lifespan. Why: both models load lazily on first request; the first user after a restart eats the ~280MB e5 + ms-marco load. Done when: lifespan optionally warms the models (behind a flag) and first-request P99 is measured before/after.

- [ ] **Confirm `sentry-sdk` + `prometheus-fastapi-instrumentator` are in the prod image** — `docker/Dockerfile`, `pyproject.toml` `observability` extra. Why: `/metrics` and Sentry both silently no-op via `except ImportError` if the `observability` extra isn't installed; status is currently unverified. Done when: `docker exec mizan-api python -c "import sentry_sdk, prometheus_fastapi_instrumentator"` succeeds (or the extra is added to the Dockerfile install line).

- [ ] **Remove or clearly mark legacy deploy descriptors** — `fly.toml`, `railway.toml`. Why: project deploys via Hetzner + Traefik; `fly.toml`/`railway.toml` are unused and mislead. Done when: both are deleted or each carries a top comment "LEGACY — not used; prod is Hetzner Docker (see docker-compose.prod.yml)".

- [ ] **Tighten CI coverage gate toward the configured target** — `.github/workflows/ci.yml` (`--cov-fail-under=50`) vs `pyproject.toml` `[tool.coverage.report] fail_under = 75`. Why: the two thresholds disagree; CI only enforces 50% while the project target is 75%. Done when: CI gate is raised to match (or the 75 target is consciously lowered), with the chosen number documented.

## P3 — Nice-to-have

- [ ] **Add more corpora to the library** — `scripts/ingest_library_source.py`, `scripts/ingest_tafsir.py`, `scripts/ingest_hadith.py`. Why: current corpus is Quran + EN/TR translations + (per docs) Ibn Kathir tafsir + Kutub al-Sittah hadith; more tafsir/translation diversity improves cross-lingual recall. Done when: at least one additional source is ingested + embedded and appears in search results.

- [ ] **Comparative translation view (multiple meals side-by-side)** — `website/app/playground`, `website/app/search`, `website/lib/api/client.ts`. Why: long-standing future feature; translations are already stored per-language. Done when: the UI can show ≥2 translations per verse side by side.

- [ ] **Concept/graph view (verse → similar verses → tafsir → hadith)** — `website/app/`, `GET /verses/{s}/{v}/similar`, `search_similar_to_verse`. Why: backend `find_similar_verses` + `search_similar_to_verse` already exist; only a frontend graph is missing. Done when: a basic interactive graph renders from existing endpoints.

- [ ] **Evaluate `BAAI/bge-m3` (1024-dim) for Arabic embedding quality** — `pyproject.toml` `ml`, new alembic migration `vector(768)→vector(1024)`, `scripts/embed_quran.py`, config `embedding_dimension`. Why: potential recall gain for Arabic; large, breaking (re-embed everything). Gate behind the eval harness above. Done when: bge-m3 beats e5-base on the eval set before any migration is written.
