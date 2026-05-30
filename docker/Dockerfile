# Build stage
FROM python:3.13-slim AS builder

# Копируем uv из официального образа
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first to leverage Docker cache
COPY pyproject.toml uv.lock ./

# Install runtime dependencies only (no dev group)
RUN uv sync --frozen --no-dev --no-editable

# Final stage
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid app --shell /bin/bash --create-home app

# Copy virtualenv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --chown=app:app . .

# Copy and make entrypoint script executable
COPY --chown=app:app docker/scripts/backend_entrypoint.sh /app/docker/scripts/backend_entrypoint.sh
RUN chmod +x /app/docker/scripts/backend_entrypoint.sh

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/sessions && \
    chown -R app:app /app

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -x "python" || exit 1

# Default command
CMD ["python", "src/main.py"]
