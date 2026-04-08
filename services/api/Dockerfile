FROM python:3.12-slim AS base

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    PATH="/root/.local/bin:$PATH"

# UV — hızlı Python package manager
RUN pip install uv --no-cache-dir

# Bağımlılıkları önce kopyala (layer cache optimizasyonu)
COPY pyproject.toml .

# ── Development ─────────────────────────────────────────────────
FROM base AS development
RUN uv pip install -e ".[dev]" --system
COPY src/ ./src/
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "info"]

# ── Production ───────────────────────────────────────────────────
FROM base AS production
RUN uv pip install . --system
COPY src/ ./src/
EXPOSE 8000
CMD ["gunicorn", "src.main:app", \
     "-w", "4", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--graceful-timeout", "30"]
