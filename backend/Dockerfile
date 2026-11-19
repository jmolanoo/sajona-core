FROM python:3.12.7-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd --gid 1001 sajona && \
    useradd --uid 1001 --gid sajona --create-home sajona && \
    apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
RUN pip install --upgrade pip && pip install . && \
    mkdir -p /app/audit_logs && chown -R sajona:sajona /app

USER sajona

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=5 \
  CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "sajona_core.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
