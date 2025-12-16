#!/bin/sh
# Entrypoint script for Mizan API
# Ensures PORT variable is properly expanded

PORT="${PORT:-8000}"
echo "Starting Mizan API on port $PORT"
exec uvicorn mizan.api.main:app --host 0.0.0.0 --port "$PORT"
