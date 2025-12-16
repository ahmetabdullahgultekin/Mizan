FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir build && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels -e .

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user for security
RUN groupadd -r mizan && useradd -r -g mizan mizan

# Install runtime dependencies only
COPY --from=builder /app/wheels /app/wheels
RUN pip install --no-cache-dir --no-index --find-links=/app/wheels mizan && \
    rm -rf /app/wheels

# Copy application code
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

# Copy data directory (read-only at runtime)
COPY data/ data/

# Set PYTHONPATH to include src directory
ENV PYTHONPATH=/app/src

# Set ownership
RUN chown -R mizan:mizan /app

USER mizan

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

# Default command
CMD ["uvicorn", "mizan.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
