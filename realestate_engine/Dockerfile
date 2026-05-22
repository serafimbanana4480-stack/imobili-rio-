# Stage 1: Builder
FROM python:3.10-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e ".[cv,nlp,ai]"

# Stage 2: Runtime
FROM python:3.10-slim as runtime

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

RUN mkdir -p data/db data/backups data/cache data/logs && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///data/db/realestate.db
ENV LOG_LEVEL=INFO

EXPOSE 8501 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["streamlit", "run", "dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
