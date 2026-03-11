#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Mizan Full-Stack Startup Script
#
# Usage:
#   ./scripts/start.sh                  # full stack with embeddings
#   ./scripts/start.sh --skip-embed     # skip embedding generation
#   ./scripts/start.sh --api-only       # backend only (no frontend)
# ---------------------------------------------------------------------------
set -euo pipefail

# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------
SKIP_EMBED=false
API_ONLY=false

for arg in "$@"; do
  case "$arg" in
    --skip-embed)   SKIP_EMBED=true ;;
    --api-only)     API_ONLY=true ;;
    *) echo "Unknown flag: $arg"; exit 1 ;;
  esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

log()  { echo -e "${GREEN}[mizan]${NC} $*"; }
warn() { echo -e "${YELLOW}[mizan]${NC} $*"; }
err()  { echo -e "${RED}[mizan]${NC} $*" >&2; }

wait_for_service() {
  local name="$1"; local url="$2"; local max=30; local i=0
  log "Waiting for $name to be ready…"
  until curl -sf "$url" > /dev/null 2>&1; do
    i=$((i+1))
    if [ "$i" -ge "$max" ]; then
      err "$name did not become ready after ${max}s. Aborting."
      exit 1
    fi
    sleep 1
  done
  log "$name is ready."
}

# ---------------------------------------------------------------------------
# 1. Start infrastructure
# ---------------------------------------------------------------------------
log "Starting Docker Compose services (db + redis)…"
docker compose up -d db redis

# ---------------------------------------------------------------------------
# 2. Wait for PostgreSQL
# ---------------------------------------------------------------------------
log "Waiting for PostgreSQL…"
max_wait=60; waited=0
until docker compose exec -T db pg_isready -U "${POSTGRES_USER:-mizan}" -d "${POSTGRES_DB:-mizan}" > /dev/null 2>&1; do
  waited=$((waited+1))
  if [ "$waited" -ge "$max_wait" ]; then
    err "PostgreSQL did not become ready within ${max_wait}s."
    exit 1
  fi
  sleep 1
done
log "PostgreSQL is ready."

# ---------------------------------------------------------------------------
# 3. Apply database migrations
# ---------------------------------------------------------------------------
log "Applying Alembic migrations…"
alembic upgrade head

# ---------------------------------------------------------------------------
# 4. Ingest Quran data (idempotent — skips if verses already present)
# ---------------------------------------------------------------------------
log "Ingesting Quran text data…"
python scripts/ingest_tanzil.py

# ---------------------------------------------------------------------------
# 5. Generate verse embeddings (optional, resumable)
# ---------------------------------------------------------------------------
if [ "$SKIP_EMBED" = false ]; then
  log "Generating verse embeddings (--skip-existing for checkpoint/resume)…"
  python scripts/embed_quran.py --skip-existing
else
  warn "Skipping verse embedding generation (--skip-embed flag set)."
fi

# ---------------------------------------------------------------------------
# 6. Start the API server
# ---------------------------------------------------------------------------
log "Starting Mizan API server on http://localhost:8000 …"
if [ "$API_ONLY" = true ]; then
  uvicorn mizan.api.main:app --host 0.0.0.0 --port 8000 --reload
  exit 0
fi

# Run API in background when we also need to start the frontend
uvicorn mizan.api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!
log "API server PID: $API_PID"

# ---------------------------------------------------------------------------
# 7. Wait for API to be healthy, then start frontend
# ---------------------------------------------------------------------------
wait_for_service "Mizan API" "http://localhost:8000/health"

log "Starting Next.js frontend on http://localhost:3000 …"
cd website && npm run dev &
FRONTEND_PID=$!
log "Frontend PID: $FRONTEND_PID"

log "All services started. Press Ctrl+C to stop."

# ---------------------------------------------------------------------------
# Graceful shutdown on SIGINT / SIGTERM
# ---------------------------------------------------------------------------
cleanup() {
  warn "Shutting down…"
  kill "$FRONTEND_PID" 2>/dev/null || true
  kill "$API_PID" 2>/dev/null || true
  docker compose stop db redis 2>/dev/null || true
}
trap cleanup INT TERM

wait "$API_PID" "$FRONTEND_PID"
