# Mizan — Roadmap

> Last refreshed: 2026-06-04 (grounded in HEAD `3c44ddb` + live API/container inspection)
> Strategic direction. Tactical, executable items live in `TODO.md`.

Mizan Core Engine is a scholarly-grade Quranic text-analysis + semantic-search platform:
high-precision letter/word/Abjad analysis verified against Tanzil standards, plus hybrid
semantic search across Quran, translations, tafsir, and hadith.

- **API:** https://mizan-api.rollingcatsoftware.com — Python 3.11 / FastAPI, async SQLAlchemy, pgvector, Redis
- **Website:** https://mizan.rollingcatsoftware.com — Next.js 16 / React 19 (standalone)
- **Infra:** Hetzner CX43, Docker + Traefik (auto-SSL), shared Postgres 17 (pgvector) + Redis 7.4

---

## Current state (verified)

**Live & healthy.** Both containers up; `/health` → `database:true, cache:true, embedding:true, reranking:true`. Deployed image (2026-04-26) matches current HEAD; local repo is in sync with `origin/master`.

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

1. Make reranking actually help: pick one reranker model deliberately (multilingual vs English-only) and fix the post-rerank `min_similarity` filter that compares cosine thresholds against non-cosine scores (silently drops valid hits). — *TODO P0*
2. Re-verify the test suite green on HEAD and record the real number behind the "172 passed" badge. — *TODO P0*
3. Turn on observability and document the real deploy/migrate/ingest order. — *TODO P1*

---

## Phase 1 — Trustworthy search (correctness)

**Goal:** the search results users see are provably better with reranking on than off, and no valid result is silently dropped.

Deliverables:
- Single source of truth for the reranker model; `/health` (or startup log) confirms the loaded model.
- `min_similarity` filtering applied on a meaningful (cosine) scale, or removed for fused results.
- Per-request rerank kill-switch / `debug=raw` to A/B a query against raw RRF.
- Search-quality eval harness (labelled query→verse set, recall@k / nDCG) gating any ranking change.

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
- Optional embedding-model upgrade (`BAAI/bge-m3`, 1024-dim) — only if it beats `multilingual-e5-base` on the Phase 1 eval harness; gated behind a `vector(768)→vector(1024)` migration and full re-embed.

## Phase 4 — Product features

**Goal:** richer scholarly exploration on top of the verified engine.

Deliverables:
- Comparative translation view (multiple meals side by side; translations already stored per-language).
- Concept/graph view (verse → similar verses → tafsir → hadith) on existing `/similar` + `search_similar_to_verse` endpoints.
- Thematic tagging via embedding clustering; word-by-word morphology UI once Phase 3 data lands.

---

## Notes & gotchas

- AsyncSession runs all search DB queries **sequentially** (no concurrent queries on one session) — keep this in mind for latency work.
- Embedding (e5-base ~280MB) and reranker models load **lazily on first request** after a restart — the first post-restart query is slow; consider pre-warming.
- `data/masaq/` and `data/embeddings/` are empty in-repo (`.gitkeep` only); `quran/` + `data/tanzil/` carry the source text.
- `.env.prod` is correctly gitignored and untracked.
- Deploy: `infra/deploy.sh [build|restart|logs] mizan` on the self-hosted Hetzner runner; trigger via `.github/workflows/deploy-hetzner.yml`.
