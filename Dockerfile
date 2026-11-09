# BRANDVAULT AI — backend container (FastAPI).
# Build context is the repo root. The frontend deploys separately (e.g. Vercel).
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

# OpenCV (pulled in by the OCR engine) needs these shared libraries on slim images.
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Bake the embedding model into the image so restarts never re-download it,
# and warm the OCR models once at build time.
ENV EMBEDDING_CACHE_DIR=/app/models
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-en-v1.5', cache_dir='/app/models')" \
    && python -c "from rapidocr_onnxruntime import RapidOCR; RapidOCR()"

COPY backend ./backend

EXPOSE 8000
# PORT is provided by most PaaS platforms (Render, Fly, Cloud Run).
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
