# BRANDVAULT AI — Technical Details (Round 3, final)

## Links
- **Live app:** https://brandvault-ai-1.onrender.com (frontend) · https://brandvault-ai.onrender.com (API)
- **Source code:** https://github.com/roshanvikram/BRANDVAULT-AI
- Free hosting sleeps after 15 idle minutes, so the first visit can take up to a minute. The app shows a "waking up" banner.

## Architecture
| Tier | Technology | Round 3 additions |
|---|---|---|
| Presentation | Next.js 14, React 18, TypeScript, Tailwind | Creative Inspection, Publishing Gate, rebuilt Settings, notification centre, cold-start banner (37 pages) |
| API & orchestration | FastAPI, Pydantic v2, SQLAlchemy 2.1, Python 3.12/3.13 | Public API (API keys), webhooks, event hub, capabilities endpoint (124 endpoints) |
| Intelligence | Deterministic engines first; Groq / Anthropic LLM optional and labelled | OCR (RapidOCR/ONNX), dense embeddings (BGE-small via fastembed), BM25, RRF fusion, Channel Adapter, Disclaimer agent, Guideline Gap Agent |
| Data | SQLite (local) or PostgreSQL 16+ with pgvector | Database file store, chunk embeddings, pgvector + HNSW, portable migrations (38 tables, plus a native pgvector table on PostgreSQL) |
| Integrations | — | MCP server (official SDK 2.x, stdio, read-only), HMAC-signed webhooks, Slack/email |

## Round 3 modules
| Module | Files |
|---|---|
| OCR + brand-vocabulary correction | `backend/app/services/ocr.py` |
| Creative pipeline (image / PDF / video, regions, clear space) | `backend/app/services/creative.py`, `backend/app/api/v1/creative.py`, `frontend/src/app/visual-dna/creative/page.tsx` |
| Organisation settings | `backend/app/services/org_settings.py`, `frontend/src/app/settings/page.tsx` |
| Event hub, webhooks, notifications | `backend/app/services/events.py`, `backend/app/models/integration.py` |
| API keys, public API, channel checks | `backend/app/api/v1/integrations.py`, `backend/app/services/channels.py`, `frontend/src/app/approval-hub/publishing/page.tsx` |
| MCP server | `backend/mcp_server.py` |
| Ingestion (PDF, DOCX, HTML, MD/TXT, CSV, XLSX) | `backend/app/services/ingest.py` |
| Embeddings + hybrid retrieval + pgvector | `backend/app/services/embeddings.py`, `backend/app/services/rag.py`, `backend/app/models/retrieval.py` |
| Guideline Gap Agent | `guideline_conflicts()` in `backend/app/services/knowledge_gaps.py` |
| Durable file storage | `backend/app/services/filestore.py`, `backend/app/models/storage.py` |

## Key design decisions
- **Deterministic first, AI labelled.** OCR fixes, prices, channel limits, disclaimers, clear space, gate decisions and conflict detection are all rule-based and explainable. LLM output stays optional and labelled.
- **No agent can approve or publish.** API keys and MCP tools can check and read only. Approval needs a Reviewer or Administrator.
- **Honest degradation.** When OCR or embeddings are missing, `/capabilities` and the UI say so. Retrieval falls back to BM25 + TF-IDF, and text is never invented.
- **Meaning-only evidence needs a calibrated threshold** (cosine ≥ 0.62, above the highest similarity seen for unrelated queries), so unrelated passages are never cited.
- **Fusion:** TF-IDF and BM25 are fused first, then combined with the dense ranking. Correlated lexical methods therefore don't outvote meaning.
- **Webhooks:** HMAC-SHA256 over `timestamp.body`, three attempts and a delivery log. Only public HTTPS URLs are allowed in production (SSRF guard).
- **API keys:** stored as SHA-256 hashes, shown once, scoped (`check`, `gate`, `read`) and revocable.
- **Files:** stored in the database, so they survive restarts and move with the database to PostgreSQL.

## Configuration (new in Round 3)
`DATABASE_URL` (PostgreSQL for persistence), `DEMO_ACCOUNTS_ENABLED`, `SEED_DEMO_CONTENT`, `EMBEDDING_PROVIDER` / `EMBEDDING_MODEL` / `EMBEDDING_BASE_URL` / `EMBEDDING_API_KEY` / `EMBEDDING_CACHE_DIR`, `RAG_MODE`, `SMTP_*`. See `.env.example` and `DEPLOYMENT.md` §9.

## Resource use
About 300 MB RAM with the app, OCR and the embedding model loaded (Render free plan limit is 512 MB). The Docker image bakes in the embedding and OCR models.

## API reference
`API_DOCUMENTATION.md` → "Round 3 endpoints". Live interactive docs are at `<API>/docs`.
