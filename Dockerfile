# Railway-optimized Dockerfile for Mizan API
FROM python:3.11-slim

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

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Expose port (Railway sets PORT env var)
EXPOSE 8000

# Start command (Railway overrides with $PORT)
CMD ["sh", "-c", "uvicorn mizan.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
