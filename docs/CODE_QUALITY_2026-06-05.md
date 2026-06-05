# Mizan — Code Quality & Architecture Review (2026-06-05)

> Reviewer: senior code-quality / architecture pass over `master` HEAD `e383572`.
> Scope: Python 3.11 / FastAPI hexagonal backend (`src/mizan`, 87 modules, ~12k LOC).
> Baseline: `ruff check src/` ✅ clean · `mypy --strict src/` ✅ clean (87 files) ·
> `pytest tests/unit` ✅ 200 passed · `pytest tests/integration` ⚠️ 22 errors (needs a live DB — see F2).
>
> This is primarily a **review + document** pass. Two small, clearly-safe fixes were
> applied on branch `quality/2026-06-05` (see "Fixes applied"). Larger items are
> documented here and queued in `ROADMAP.md` → "Code Quality & Professionalization".

## Overall grade: **A−**

A genuinely well-engineered codebase: clean hexagonal layering, mypy `--strict`
passing with almost no `type: ignore`, disciplined defensive error handling on the
ML/search paths, and unusually honest docstrings/ADR-style comments that explain
*why* (RRF scale, reranker language routing, index-mapping bug). It loses points
mostly on **operability of the test suite** (integration tests can't run without a
real DB), a **rate limiter that is wired but effectively inert**, and a handful of
consistency nits (`datetime.utcnow()`, one unbounded input). None of these are
load-bearing security holes; the SQL layer in particular is parameterised correctly.

---

## Per-dimension scores (1–5)

| Dimension | Score | One-line justification |
|---|---:|---|
| SOLID & hexagonal boundaries | **5** | Domain has zero infra imports; ports (`IEmbeddingService`, `IRerankerService`, repo interfaces) are clean; adapters injected via FastAPI deps. 
| DRY / duplication / dead code | **4** | No dead code, no TODO/FIXME debt. Two real duplications: `search()`'s 6 try/except retrieval blocks; `get_async_session`/`get_session_context` are near-identical. |
| Error handling | **5** | No silently swallowed errors. Every broad `except` either re-raises (db, indexing) or logs + degrades intentionally (reranker OOM, per-path search). |
| Type safety (mypy strict) | **5** | `--strict` passes; only 9 `type: ignore` repo-wide, each justified; the 2 `cast()` are `isinstance`-guarded. (One bad cast removed in this pass.) |
| Naming / readability / size | **4** | Names are excellent. `SemanticSearchService.search()` (~180 lines) and `library_repositories.py` (1103 lines, 4 repos) are the only real size/complexity hotspots. |
| Test quality (critical-path) | **3** | Unit tests assert real behavior (RRF, rerank index-mapping, language routing). But integration suite is **non-hermetic** and several tests accept `status in (200, 500)`. |
| Security hygiene | **4** | Input validation strong; raw SQL is fully parameterised (`# nosec` justified); API-key auth uses `hmac.compare_digest`; Sentry strips secrets. Loses a point for the inert rate limiter + one unbounded input (now fixed). |
| CLAUDE.md consistency | **5** | Code matches the documented reranker single-source-of-truth, min_similarity-scale, and morphology-preview conventions precisely. |

---

## Prioritized findings

### P0 — security / correctness bug
*(none found)*

### P1 — should fix soon

**F1 — Rate limiter is wired but effectively inert.**
`SlowAPIMiddleware` is installed (`api/main.py:170`) and a shared `Limiter` exists
(`api/limiters.py:22`), but **only one route** actually carries a limit decorator
(`api/routers/semantic_search.py:109 @limiter.limit("30/minute")`). slowapi's
middleware does **not** apply a global default limit — undecorated routes are
unthrottled. So the abuse-prone arbitrary-text analysis endpoints
(`/api/v1/analysis/*`, `/api/v1/analyze`) and the library mutation endpoints are
not rate-limited at all. *Fix:* add a default limit (slowapi supports
`Limiter(..., default_limits=["60/minute"])`) or decorate the analysis + library
routers. Larger than a one-liner because each decorated endpoint must take
`request: Request` — documented for the roadmap, not auto-applied.

**F2 — Integration test suite cannot run without a live PostgreSQL (non-hermetic).**
`api/main.py:104-105` calls `await init_db()` in the lifespan whenever
`settings.is_production` is False. Under `TestClient`, `is_production` is False
(no `.env` overriding `debug`/`secret_key` → `config.py:215-218`), so app startup
opens a real DB connection and **fails before any dependency override takes effect**
(`tests/integration/conftest.py` mocks `get_db_session`/`get_redis_cache`, but the
lifespan bypasses them). Result: all 22 integration tests `ERROR` locally/CI without
a DB. *Fix options:* gate `init_db()` behind an explicit `MIZAN_AUTO_CREATE_TABLES`
flag (default off in tests), or have the integration `app` fixture set
`debug=False, secret_key=<non-default>` so `is_production` is True and the lifespan
skips `init_db()`. Not auto-applied because it changes startup behavior and needs a
deliberate choice; queued for the roadmap.

### P2 — quality / robustness

**F3 — Unbounded text input on the Abjad endpoint (DoS bound inconsistency).** *(FIXED)*
`api/routers/analysis.py:121` — `calculate_abjad`'s `text` Query param had no
`max_length`, while the two sibling count endpoints cap at 10000 (lines 58, 94) and
`UnifiedAnalysisRequest.text` caps at 5000. Added `max_length=10000` to match.

**F4 — `_source_to_response` used `object` + a `type: ignore[assignment]` cast.** *(FIXED)*
`api/routers/library.py:149-152` typed the param as `object`, then reassigned to a
`TextSource` with `# type: ignore[assignment]`. All three callers (lines ~214, 228,
244) provably pass a narrowed `TextSource`. Retyped the parameter as `TextSource`
(via a `TYPE_CHECKING` import to keep the deferred-import pattern) and dropped the
cast and the ignore.

**F5 — `search()` retrieval paths are 6× duplicated try/except blocks.**
`application/services/semantic_search_service.py:142-198` — six near-identical
`try: result_lists.append(await <repo>.<call>(...)); except Exception as e:
logger.warning("search_path_failed", path=..., error=str(e))` blocks. Extracting a
`_safe_retrieve(path_name, coro)` helper would cut ~50 lines and remove the
copy-paste risk (the `path=` label is the only thing that varies). Behavior-changing
refactor of the hottest method → roadmap, not auto-applied.

**F6 — `datetime.utcnow()` (deprecated, naive) used in ~9 places.**
e.g. `domain/entities/library.py:45,98,174`, `application/dtos/responses.py:27,122`,
`infrastructure/persistence/quran_repository.py:287`,
`infrastructure/persistence/library_repositories.py:218`. Deprecated in 3.12 and
returns a **naive** datetime; should be `datetime.now(timezone.utc)`. The deprecation
is currently invisible because `pyproject.toml` `filterwarnings` ignores
`DeprecationWarning`. Mechanical but cross-cutting (and touches timezone semantics on
stored timestamps) → roadmap.

### P3 — nits

**F7 — `get_async_session` / `get_session_context` are duplicated.**
`infrastructure/persistence/database.py:63-98` — identical `factory(); try: yield;
commit; except: rollback; raise` bodies. The context-manager form could wrap the
generator form.

**F8 — `asyncio.get_event_loop()` inside async functions.**
`infrastructure/reranking/cross_encoder_service.py:177` and
`infrastructure/embeddings/sentence_transformer_service.py:71`. `get_running_loop()`
is the correct call inside a running coroutine (`get_event_loop()` is soft-deprecated
for this use).

**F9 — Integration tests assert `status_code in (200, 500)`.**
`tests/integration/test_api_search.py:51,97` — a test that passes on a 500 provides
no signal that the endpoint works. Tighten to the expected success/validation code
once F2 makes the suite hermetic.

**F10 — `DomainException.to_dict()` typed `dict[str, str]` but exceptions carry
structured fields.** `domain/exceptions.py:40` only serialises `error`/`message`;
subclasses store richer context (`location`, `surah`, `reason`, …) that never reaches
the API response. Optional enhancement, not a bug.

---

## Strengths (honest, not padding)

- **Hexagonal discipline is real, not cosmetic.** `domain/` imports nothing from
  `infrastructure/` or `api/`; ports live in `domain/services` + `domain/repositories`
  and are injected through FastAPI `Depends`. This is the cleanest layer separation of
  the reviewed repos.
- **mypy `--strict` actually passes** on all 87 files with only 9 `type: ignore`
  (each justified) and 2 guarded `cast()`s — rare for an ML-adjacent FastAPI codebase.
- **Defensive ML/search error handling is exemplary.** The reranker degrades
  gracefully on `MemoryError` and any load/predict failure to identity ordering, all
  logged with context (`cross_encoder_service.py:109-125,192-213`); search treats each
  retrieval path as independently fallible (`semantic_search_service.py:142-198`).
- **Comments explain *why*, and document past bugs.** The min_similarity-scale note
  (`semantic_search_service.py:250-263`), the reranked-score→candidate index-mapping
  fix (`:357-374`), and the reranker single-source-of-truth design are genuine ADRs in
  code. CLAUDE.md and ROADMAP.md match the code precisely.
- **SQL is safe.** Every user-supplied value (`query`, variants, source-type filters)
  is bound via `:params`; f-strings only interpolate internally-derived placeholder
  names / computed floats, and the author flagged each with a justified `# nosec B608`.
- **Strong input validation at the edge** — Pydantic `Field(ge=/le=/min_length=/
  max_length=/pattern=)` on every request DTO and query param; API-key check uses
  `hmac.compare_digest`; Sentry `before_send` strips `authorization`/`cookie`/`x-api-key`.

---

## Fixes applied on `quality/2026-06-05`

| # | File:line | Change | Verified |
|---|---|---|---|
| F3 | `api/routers/analysis.py:121` | Added `max_length=10000` to `calculate_abjad` `text` param (matches siblings) | ruff + mypy + 200 unit tests green |
| F4 | `api/routers/library.py:149` | Removed `object`-typing + `type: ignore[assignment]` bad cast; typed param as `TextSource` via `TYPE_CHECKING` import | ruff + mypy + 200 unit tests green |

Everything else above is **documented only** (behavior-changing or cross-cutting) and
added to `ROADMAP.md` → "Code Quality & Professionalization".

## Biggest single refactor recommended for the roadmap

**Make the test suite hermetic and the rate limiter effective (F1 + F2 together).**
Today the integration suite is the project's weakest quality gate: it can't run in CI
without a live DB (F2) and what does run tolerates 500s (F9), while the rate limiter
that *looks* deployed protects exactly one route (F1). Decouple `init_db()` from
request-time startup (explicit flag / test fixture), tighten the integration asserts,
and apply a `default_limits` policy — turning two pieces of "wired but inert"
infrastructure into real, enforced guarantees.
