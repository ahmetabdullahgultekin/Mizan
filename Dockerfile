# Railway-optimized Dockerfile for Mizan API
# Cache bust: v2
FROM python:3.11-slim

# Build arg to invalidate cache
ARG CACHEBUST=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (for better caching)
COPY pyproject.toml README.md ./

# Install dependencies without building wheel
RUN pip install --no-cache-dir \
    fastapi>=0.109.0 \
    uvicorn[standard]>=0.27.0 \
    pydantic>=2.5.0 \
    pydantic-settings>=2.1.0 \
    httpx>=0.26.0 \
    sqlalchemy[asyncio]>=2.0.25 \
    asyncpg>=0.29.0 \
    alembic>=1.13.0 \
    redis>=5.0.0 \
    structlog>=24.1.0 \
    pyarabic>=0.6.15 \
    regex>=2023.12.0

# Copy application code
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .
COPY data/ data/

# Copy and setup entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Default port (Railway sets PORT env var)
ENV PORT=8000
EXPOSE 8000

# Use entrypoint script for proper variable expansion
ENTRYPOINT ["/entrypoint.sh"]
