# =============================================================================
# NexusCore Backend — FastAPI + Uvicorn
# Tag convention: jorahone/jnop-backend:latest
# =============================================================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Production stage ─────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create directories and non-root user
RUN mkdir -p /logs /srv/jnop/data /srv/jnop/logs && \
    addgroup --system --gid 1001 jnop && \
    adduser --system --uid 1001 --ingroup jnop --no-create-home jnop && \
    chown -R jnop:jnop /app /logs /srv/jnop

USER jnop

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=5 --start-period=15s \
    CMD python /app/healthcheck.py

LABEL org.opencontainers.image.title="NexusCore Backend" \
      org.opencontainers.image.description="FastAPI backend for J1 NOC Platform" \
      org.opencontainers.image.vendor="JorahOne" \
      org.opencontainers.image.version="11.0.0"
