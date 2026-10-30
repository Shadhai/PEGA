
# FROM python:3.11-slim@sha256:9534e5a8e315485d4061ed659af0fd78a284c015f9b73661b41d6bab25604534

# ENV PYTHONDONTWRITEBYTECODE=1 \
#     PYTHONUNBUFFERED=1 \
#     PIP_NO_CACHE_DIR=1

# WORKDIR /app

# RUN groupadd --system appuser && useradd --system --gid appuser appuser

# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# COPY src ./src
# COPY webapp ./webapp
# COPY data/extracted ./data/extracted
# COPY data/experience.db ./data/experience.db

# # Copy machine learning models
# COPY models/minilm ./models/minilm
# COPY models/qwen2.5-1.5b ./models/qwen2.5-1.5b

# COPY logs ./logs

# RUN mkdir -p data/graph_db logs/evidence logs/benchmarks
# RUN chown -R appuser:appuser /app

# USER appuser

# EXPOSE 8000

# HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
#     CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/', timeout=3)"

# CMD ["uvicorn", "webapp.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --system appuser && \
    useradd --system --gid appuser appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser src ./src
COPY --chown=appuser:appuser webapp ./webapp
COPY --chown=appuser:appuser data/extracted ./data/extracted
COPY --chown=appuser:appuser data/experience.db ./data/experience.db
COPY --chown=appuser:appuser logs ./logs

RUN mkdir -p /app/data/graph_db \
    /app/logs/evidence \
    /app/logs/benchmarks && \
    chown appuser:appuser /app/data \
    /app/data/graph_db /app/logs \
    /app/logs/evidence /app/logs/benchmarks

USER appuser

EXPOSE 10000

CMD ["sh", "-c", "uvicorn webapp.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
