# BRANDVAULT AI — backend container (FastAPI).
# Build context is the repo root. The frontend deploys separately (e.g. Vercel).
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend

EXPOSE 8000
# PORT is provided by most PaaS platforms (Render, Fly, Cloud Run).
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
