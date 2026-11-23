FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    ANONYMIZED_TELEMETRY=False \
    EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2 \
    FASTEMBED_CACHE_PATH=/opt/fastembed \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Bake the embedding model into the image so startup never needs a download
RUN python -c "import os; from fastembed import TextEmbedding; TextEmbedding(os.environ['EMBED_MODEL'])" \
    && chmod -R a+rX /opt/fastembed

COPY app ./app
COPY static ./static
COPY data/sample_menu.json ./data/sample_menu.json

RUN useradd -m appuser && mkdir -p /app/data/chroma && chown -R appuser /app/data
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]