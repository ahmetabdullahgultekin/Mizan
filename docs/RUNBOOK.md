# Mizan Operational Runbook

Operational reference for the Mizan Core Engine (MCE). Use this document to diagnose and resolve production incidents.

---

## Table of Contents

0. [Deployment & Post-Deploy Checklist](#0-deployment--post-deploy-checklist)
1. [Service Health Checks](#1-service-health-checks)
2. [Common Failure Scenarios](#2-common-failure-scenarios)
3. [Embedding Service Troubleshooting](#3-embedding-service-troubleshooting)
4. [Database Operations](#4-database-operations)
5. [Restarting Services](#5-restarting-services)
6. [Log Inspection](#6-log-inspection)
7. [Backup and Restore](#7-backup-and-restore)
8. [Incident Response Checklist](#8-incident-response-checklist)

---

## 0. Deployment & Post-Deploy Checklist

### What the CI deploy actually does

`.github/workflows/deploy-hetzner.yml` (push to `master`, paths `src/ website/
Dockerfile* docker-compose.prod.yml requirements*.txt alembic/`) runs, over SSH
on the Hetzner host:

```bash
cd /opt/projects/Mizan
git pull origin master
cd /opt/projects
./infra/deploy.sh build mizan      # docker compose build (prod image)
./infra/deploy.sh restart mizan    # recreate the mizan containers
# then a /health curl with retries + a website 200 check
```

> ⚠️ **The deploy workflow does NOT run database migrations or any
> ingest/embed script.** `alembic upgrade head` and all `scripts/ingest_*` /
> `scripts/embed_*` runs are **manual** steps. A push that only changes code
> deploys fine; a push that adds an Alembic migration or needs new/changed data
> will deploy a container that is out of sync with the schema/data until you run
> the steps below by hand.

### Post-deploy order (run on the Hetzner host after a deploy)

Run these from inside the running API container (it has the app + scripts +
prod DB/Redis env). Substitute the real container name (`mizan-api`).

```bash
# 1. MIGRATE — only if this deploy added/changed an Alembic migration
docker exec -it mizan-api alembic upgrade head
docker exec -it mizan-api alembic current        # confirm head

# 2. INGEST — only if Quran text / sources changed (normally one-time, idempotent)
docker exec -it mizan-api python scripts/ingest_tanzil.py
docker exec -it mizan-api python scripts/ingest_translations.py   # EN + TR
# optional library corpora:
# docker exec -it mizan-api python scripts/ingest_tafsir.py
# docker exec -it mizan-api python scripts/ingest_hadith.py

# 3. EMBED — only if verses/translations were (re)ingested or the model changed
docker exec -it mizan-api python scripts/embed_quran.py --skip-existing

# 4. VERIFY
curl -s https://mizan-api.rollingcatsoftware.com/health | python -m json.tool
curl -s https://mizan-api.rollingcatsoftware.com/api/v1/search/verses/embeddings/stats \
  | python -m json.tool   # total_embeddings should be 6236
```

### Decision guide — what to run for a given change

| Change in the deploy | Migrate | Ingest | Embed |
|----------------------|:-------:|:------:|:-----:|
| Code only (`src/`, `website/`) | no | no | no |
| New Alembic migration (`alembic/`) | **yes** | only if it adds data columns to backfill | only if embeddings affected |
| New/changed translation or corpus source | no | **yes** | **yes** (`--skip-existing`) |
| Embedding model or dimension change | **yes** (vector column) | no | **yes** (full re-embed, NOT `--skip-existing`) |

> A model/dimension change is the dangerous one: it requires an Alembic
> migration to change the `vector(N)` column **and** a full re-embed; mixing
> dimensions breaks pgvector search (see Section 3). Gate it behind a backup
> (Section 7) and the eval harness before flipping prod.

---

## 1. Service Health Checks

### Full stack health
```bash
curl -s http://localhost:8000/health | python -m json.tool
```

Expected response when healthy:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": true,
  "cache": true,
  "embedding": true,
  "timestamp": "2026-03-11T12:00:00Z"
}
```

| Field | `true` | `false` | `null` |
|-------|--------|---------|--------|
| `database` | DB reachable | DB unreachable | — |
| `cache` | Redis reachable | Redis unreachable | — |
| `embedding` | Embedding service OK | Embedding service down | Semantic search disabled |

### PostgreSQL
```bash
docker compose exec db pg_isready -U mizan -d mizan
# → "mizan:5432 - accepting connections"
```

### Redis
```bash
docker compose exec redis redis-cli ping
# → PONG
```

### Frontend (Next.js)
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# → 200
```

---

## 2. Common Failure Scenarios

### API returns 503 / health shows `database: false`

**Cause:** PostgreSQL container is down or connection pool exhausted.

```bash
# Check container status
docker compose ps db

# Restart DB
docker compose restart db

# Check API logs for connection errors
docker compose logs api --tail=50 | grep -i "connection\|error"
```

### API returns 503 / health shows `cache: false`

**Cause:** Redis is down. The API degrades gracefully (cache miss), but performance suffers.

```bash
docker compose restart redis
```

### Semantic search returns no results (`total_results: 0`)

**Possible causes:**
1. No text sources have been indexed (status ≠ INDEXED)
2. The query similarity threshold is too high
3. Verse embeddings haven't been generated

**Diagnose:**
```bash
# Check how many verse embeddings exist
curl -s http://localhost:8000/api/v1/search/verses/embeddings/stats | python -m json.tool

# Check text source status
curl -s http://localhost:8000/api/v1/library/spaces | python -m json.tool
```

**Fix:**
```bash
# Re-generate verse embeddings (resumable)
python scripts/embed_quran.py --skip-existing

# Re-index a specific text source
# Use POST /api/v1/library/spaces/{id}/sources
```

### API returns 422 on all requests

**Cause:** Pydantic validation error — usually malformed request body or changed schema.

Check the response `detail` array for field-level errors:
```bash
curl -s -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}' | python -m json.tool
```

### Rate limiting — 429 Too Many Requests

The semantic search endpoint is limited to **30 requests/minute** per IP.

```bash
# Check if a specific IP is hitting the limit
docker compose logs api --tail=100 | grep "429\|rate_limit"
```

Wait 60 seconds or adjust the limit in `src/mizan/api/routers/semantic_search.py`.

---

## 3. Embedding Service Troubleshooting

### Check current embedding configuration
```bash
curl -s http://localhost:8000/health | python -m json.tool
# Look at the "embedding" field
```

More detail:
```bash
curl -s http://localhost:8000/api/v1/search/verses/embeddings/stats | python -m json.tool
```

### Embedding service returns errors

**Local model (sentence-transformers):**
```bash
# Verify model is cached
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-base')"
```

**Gemini API:**
```bash
# Verify API key
echo $GEMINI_API_KEY

# Test a direct embed call
python -c "
import google.generativeai as genai
genai.configure(api_key='$GEMINI_API_KEY')
result = genai.embed_content(model='models/text-embedding-004', content='test')
print(len(result['embedding']), 'dimensions')
"
```

### Dimension mismatch error at startup

```
ValueError: Embedding dimension mismatch: primary model 'X' has dimension 768,
but fallback model 'Y' has dimension 1024.
```

**Fix:** Ensure `EMBEDDING_MODEL` and `EMBEDDING_FALLBACK_MODEL` produce the same dimension. The default `intfloat/multilingual-e5-base` uses 768 dimensions.

### Embedding run interrupted — checkpoint/resume

If `embed_quran.py` was interrupted, resume from where it left off:
```bash
python scripts/embed_quran.py --skip-existing
```

Check progress:
```bash
curl -s "http://localhost:8000/api/v1/search/verses/embeddings/stats" | python -m json.tool
# total_embeddings should increase toward 6236
```

---

## 4. Database Operations

### Apply pending migrations
```bash
alembic upgrade head
```

### Check migration status
```bash
alembic current
alembic history --verbose
```

### Rollback last migration
```bash
alembic downgrade -1
```

### Connect to the database directly
```bash
docker compose exec db psql -U mizan -d mizan
```

### Useful diagnostic queries
```sql
-- Count verses
SELECT COUNT(*) FROM verses;

-- Count indexed chunks per source
SELECT ts.title_arabic, ts.status, ts.indexed_chunks, ts.total_chunks
FROM text_sources ts
ORDER BY ts.created_at DESC;

-- Count verse embeddings by model
SELECT model_name, COUNT(*) FROM verse_embeddings GROUP BY model_name;

-- Find failed indexing jobs
SELECT id, title_arabic, status, updated_at
FROM text_sources WHERE status = 'FAILED';
```

---

## 5. Restarting Services

### Restart everything
```bash
docker compose restart
```

### Restart individual services
```bash
docker compose restart api
docker compose restart db
docker compose restart redis
docker compose restart website
```

### Full reset (WARNING: destroys data)
```bash
docker compose down -v  # removes volumes
docker compose up -d
alembic upgrade head
python scripts/ingest_tanzil.py
python scripts/embed_quran.py
```

---

## 6. Log Inspection

### API logs (structured JSON)
```bash
docker compose logs api -f --tail=100
```

### Filter by log level
```bash
docker compose logs api --tail=500 | grep '"level":"error"'
```

### Filter by request ID (X-Request-ID header)
```bash
# Get the request ID from the API response header, then:
docker compose logs api --tail=1000 | grep "abc12345"
```

### Database slow queries
```bash
docker compose exec db psql -U mizan -d mizan -c "
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state != 'idle' AND now() - query_start > interval '5 seconds'
ORDER BY duration DESC;
"
```

---

## 7. Backup and Restore

### Backup PostgreSQL database
```bash
docker compose exec db pg_dump -U mizan -d mizan -Fc > backups/mizan_$(date +%Y%m%d_%H%M%S).dump
```

### Restore from backup
```bash
docker compose exec -T db pg_restore -U mizan -d mizan -c < backups/mizan_20260311_120000.dump
```

### Backup verse embeddings only (large — pgvector data)
```bash
docker compose exec db psql -U mizan -d mizan -c "\COPY verse_embeddings TO '/tmp/verse_embeddings.csv' CSV HEADER"
docker compose cp db:/tmp/verse_embeddings.csv backups/
```

---

## 8. Incident Response Checklist

### Service degraded (non-zero error rate)

1. [ ] Check `/health` endpoint — identify which component is `false`
2. [ ] Check `docker compose ps` — confirm all containers are running
3. [ ] Check `docker compose logs api --tail=100` for error details
4. [ ] Check Sentry (if configured) for exception traces
5. [ ] Restart the affected container: `docker compose restart <service>`
6. [ ] If DB is involved, check disk space: `df -h`
7. [ ] If embedding is involved, check `embeddings/stats` endpoint

### Complete service outage

1. [ ] `docker compose ps` — identify stopped containers
2. [ ] `docker compose up -d` — bring all services up
3. [ ] `alembic upgrade head` — ensure migrations are applied
4. [ ] `curl http://localhost:8000/health` — verify recovery
5. [ ] Monitor logs for 5 minutes: `docker compose logs -f --tail=50`

### Data corruption suspected

1. [ ] **Do not restart** — take a backup first
2. [ ] `pg_dump` as described in Section 7
3. [ ] Run integrity check: `python scripts/ingest_tanzil.py --verify-only` (if supported)
4. [ ] Compare verse count: `SELECT COUNT(*) FROM verses;` should be **6236**
5. [ ] If corrupted, restore from most recent clean backup
