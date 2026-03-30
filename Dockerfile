# ============================================
# TradeOS V2 — Production Dockerfile
# Multi-stage build for FastAPI backend
# ============================================
FROM python:3.12-slim AS base

# Security: non-root user
RUN groupadd -r tradeos && useradd -r -g tradeos -d /app -s /sbin/nologin tradeos

WORKDIR /app

# Install system deps for ML libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ gfortran libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Dependencies ──
COPY v2/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn uvicorn[standard] certifi

# ── Application ──
COPY .env.example ./.env.example
COPY v2/ ./v2/

# Create storage dirs
RUN mkdir -p /app/v2/storage/models /app/v2/storage/cache && \
    chown -R tradeos:tradeos /app

USER tradeos

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/health')" || exit 1

EXPOSE 8080

# Production server with gunicorn + uvicorn workers
CMD ["gunicorn", "v2.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "2", \
     "--bind", "0.0.0.0:8080", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
