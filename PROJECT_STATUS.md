# PROJECT_STATUS.md — BRANDVAULT AI

**Inspection date:** 2026-11-04
**Branch:** `master`
**Inspected & verified by:** running the app locally (not a code read-through alone).

---

## 1. Verdict in one line

BRANDVAULT AI is a **genuinely functional modular monolith**, not a static prototype. The end-to-end core workflow (brand DNA → content submission → analysis → findings/claims → correction → human approval → persistent Brand Passport) **actually executes and persists**. The AI layer is a **deterministic heuristic/rule engine**, not an LLM, and there is **no real RAG, no authentication, and no real visual/OCR analysis**. These are the honest limitations below.

## 2. How this was verified (evidence)

All of the following were executed on this machine during inspection, not assumed:

| Check | Result |
|---|---|
| Backend boots (`uvicorn backend.main:app`) | ✅ Startup complete, no errors |
| `GET /api/v1/health` | ✅ `{"status":"healthy","database":"connected"}` |
| `POST /api/v1/claim/test-sample` (NOVA acceptance case) | ✅ 6 findings, score **5/100**, matches spec |
| `GET /api/v1/passport/list` | ✅ `BV-2026-52ED8A`, SHA-256 fingerprint present |
| `GET /api/v1/agent/stats` | ✅ 28 executions, 6 specialist agents, real distribution |
| `GET /api/v1/radar/metrics` | ✅ Aggregates from stored records |
| SQLite `brandvault.db` row counts | ✅ 5 submissions, 23 findings, 13 claims, 20 agent runs, 1 passport, 1 approval |

The NOVA test produced exactly the expected findings: `world's fastest` → terminology/claim violation, `10x faster than every competitor` → claim violation, `₹69,999` → **pricing CONTRADICTED** vs approved `₹79,999`, plus a tone warning for exclamation density.

## 3. Actual technology stack (as built, not as aspired)

- **Frontend:** Next.js 14 App Router, TypeScript, Tailwind CSS, Lucide React. 10 route pages, all wired to the backend via `frontend/src/lib/api.ts`.
- **Backend:** Python 3.13, FastAPI 0.162, Pydantic v2, SQLAlchemy 2.1, Uvicorn. 8 routers.
- **Database:** **SQLite** (`brandvault.db`), persistent, seeded on startup. *Not* PostgreSQL/pgvector (that is aspirational in the README).
- **Document parsing:** `pypdf` only (PDF). No DOCX, no OCR.
- **MCP:** `backend/mcp_server.py` present (self-test entrypoint).
- **AI providers:** config has slots for OpenAI/Anthropic/Gemini keys but **no provider is called** — the analyzer is pure Python heuristics.

## 4. What genuinely works (verified)

- Real content analysis against **stored** brand rules/facts/terminology (per-organisation DB query, not hardcoded UI).
- Findings + claim verifications + deterministic brand-health score, all persisted.
- Agent execution events persisted (`agent_runs`) and surfaced in Agent Control Center.
- Apply-correction mutates stored content and **re-analyses** (revisions preserved via re-run).
- Human approval decision → persisted `approval_records` → Brand Passport with SHA-256 content hash.
- Risk Radar aggregates real historical findings/claims/approvals.
- Data persists across restarts (SQLite file, confirmed by row counts predating this session).

## 5. Honest limitations (see FEATURE_STATUS.md for the full matrix)

1. **LLM optional, off by default** — *(Milestone B added a real Anthropic LLM layer behind the heuristic engine: Pydantic-validated, labeled, dedup-merged findings with graceful fallback; `/health` shows whether it's live.)* With no API key, "AI analysis" is the deterministic regex+rules engine — robust and explainable. The live Anthropic call path is implemented but unverified without a key; OpenAI/Gemini are interface stubs only.
2. **No *semantic* RAG** — no embeddings, no vector search, no pgvector. *(Milestone A fixed the honesty gap: evidence is now **retrieved from `document_chunks`** by lexical token-overlap with real page citations, replacing the previously hardcoded citation strings in `analyzer.py`.)* Retrieval is still lexical, not embedding-based (Milestone C).
3. **No authentication / RBAC** — roles are string fields; **any caller can approve**. No cross-tenant auth gate (only an `org_id` filter).
4. **No real Visual DNA / OCR** — no visual analysis route exists (`/analyse/image` → 404); no OpenCV/Tesseract. The page is UI-only.
5. **No automated tests** — no pytest/Playwright present; QA has been manual.
6. **Not deployed** — local only; no public URL.
7. **API contract differs from the spec** in PART 18 (e.g. `/content/analyze`, not `/api/analyse/text`; no `/rag/search`, no `/copilot/chat`).

## 6. Immediate priorities

See `IMPLEMENTATION_ROADMAP.md`. Highest-value, honesty-preserving next steps: (a) real LLM provider behind the existing heuristic as a clean abstraction with graceful fallback; (b) retrieve evidence from `document_chunks` instead of hardcoded strings; (c) a minimal auth/role gate so approval cannot be forged; (d) an automated test suite + labelled eval set.
