# IMPLEMENTATION_ROADMAP.md — BRANDVAULT AI

**Date:** 2026-11-04. Ordered by value-to-risk. The guiding rule (from the brief): **never compromise the working core to add optional features**, and **never fake** a capability — ship a clean abstraction with honest fallback instead.

---

## Milestone A — Integrity of the current claims (do first, low risk)
Goal: make what already works fully honest and defensible to a judge.

- **A1. Retrieve evidence from `document_chunks`** instead of hardcoded citation strings in `analyzer.py`. Match the triggering rule/fact to its chunk and surface the real `page_number` + `content`. *Removes the only genuine "fabricated citation" risk.*
- **A2. Fix `average_latency_ms`** (currently rounds to 0) — measure in microseconds or accumulate.
- **A3. Add Outdated & Needs-Human-Review paths** to ClaimDNA using a `valid_until`/freshness field on facts, so all 5 statuses are reachable, not just defined.
- **A4. Author `API_DOCUMENTATION.md`** from the live OpenAPI (`/docs`) and reconcile the README's aspirational endpoints with reality.

## Milestone B — Real (optional) LLM layer with graceful fallback  ✅ DONE
Goal: satisfy "real AI" without breaking the deterministic guarantee.
*Delivered: `services/llm.py` (Anthropic driver via official SDK, default `claude-opus-5-5`; OpenAI/Gemini honest stubs); Pydantic-validated, per-item-safe output; findings labeled `llm:<provider>` and dedup-merged with heuristics; retrieved (not model-invented) citations; `/health` LLM status; UI engine badge. Verified: validation, merge, dedupe, fallback, labeling. Live HTTP call unverified without an API key.*

- **B1. Provider abstraction** (`services/llm.py`) with OpenAI/Anthropic/Gemini drivers behind one interface; **heuristic engine stays the default** and the automatic fallback when no key is configured or a call fails/times out.
- **B2. LLM-assisted findings** validated against **Pydantic schemas** before persistence; reject/flag invalid model output (never silently pass fabricated results).
- **B3. Clearly label** in the UI whether a finding came from the heuristic engine or the LLM.

## Milestone C — Real RAG  ✅ DONE
*Delivered: `services/rag.py` — `Embedder` interface + `TfidfEmbedder` (L2-normalized TF-IDF), `cosine`, and `RagRetriever` with hybrid (cosine + keyword) ranking and org/guideline-status isolation. Embeddings persisted to `document_chunks.embedding_json` (backfilled at startup, indexed on upload). Analyzer evidence now comes from RAG with lexical fallback. New `POST /rag/search`. Verified: page-ranking, org isolation, persistence, cosine sanity. Limit: TF-IDF (not neural) + brute-force SQLite; interfaces are swap-ready for sentence-transformers / pgvector.*
- **C1.** Add embeddings (local `sentence-transformers` or provider embeddings) + a vector column. On SQLite use a brute-force cosine search; design the interface so a Postgres+pgvector swap is config-only.
- **C2.** Ingestion pipeline: extract → chunk (with page/section metadata) → embed → store, for uploaded PDFs (extend to DOCX/TXT).
- **C3.** Hybrid retrieval (semantic + keyword) with org + approval-status + version filtering; feed retrieved chunks to findings as true evidence.

## Milestone D — Security & multi-user  ✅ DONE (D1–D2; D3 partial)
*Delivered: `core/security.py` (PBKDF2 passwords + HMAC bearer tokens, stdlib), `models/user.py` (`users` table, 3 roles), `api/deps.py` (`get_current_user`, `require_roles`, `ensure_same_org`), `api/v1/auth.py` (`/auth/login`, `/auth/me`), seeded demo accounts. `/approval/decide` gated: Reviewer/Administrator-only for authoritative decisions, authenticated attribution (forged names ignored), cross-tenant 403. Frontend signs in as demo Creator/Reviewer for the submit/approve flows. D3: upload type+size validation. Verified by tests (login, RBAC, forged + cross-tenant approval denied, passport on approve). Remaining D3: rate limiting, broader input sanitisation.*
- **D1.** Minimal auth (session or JWT) + three roles (Administrator/Creator/Reviewer). **Gate `/approval/decide`** so approval cannot be forged.
- **D2.** Enforce tenant isolation at the auth layer, then add a cross-tenant access test.
- **D3.** Harden uploads (size/type validation, private storage path), input sanitisation, rate limiting, safe error envelopes.

## Milestone E — Testing & evaluation (make QA claims real)  ✅ DONE (E1/E2/E4; E3 TODO)
*Delivered: `backend/tests/` — 28 unittest tests (unit + TestClient integration), all passing; `backend/eval/dataset.json` (36 labelled cases) + `run_eval.py` reporting P=1.000 / R=0.860 / F1=0.925 (6 honest out-of-scope FNs). The eval surfaced and we fixed two real analyzer bugs (price regex word boundary; over-loose fact-keyword matching). Run: `python -m unittest backend.tests.test_unit backend.tests.test_integration` and `python backend/eval/run_eval.py`. Remaining: E3 Playwright browser E2E.*
- **E1.** `pytest` unit tests: price parsing, term matching, claim classification, score calc, passport hash.
- **E2.** Integration tests over the FastAPI app (`httpx`/`TestClient`) covering the 9 integration flows in `TESTING_PLAN.md`.
- **E3.** Playwright E2E for the 10 browser scenarios.
- **E4.** A labelled eval set (30–50 cases) + a script reporting precision/recall/FP/FN. Report **measured** numbers only.

## Milestone F — Optional modules
- **F1.** Visual DNA: real OCR (Tesseract) + deterministic colour-palette extraction (OpenCV/Pillow); label measured vs interpreted results. Add the missing `/analyse/image` route.
- **F2.** Live updates (SSE/polling) for analysis progress and the review queue.
- **F3.** MCP server auth + audit logging; re-verify tools.

## Milestone G — Deployment
- **G1.** Postgres migration (SQLAlchemy models are portable; add Alembic).
- **G2.** Deploy frontend (Vercel) + backend (Render/Fly) + managed Postgres; configure CORS and server-side secrets.
- **G3.** Seeded demo workspace + documented demo account; verify in a private/incognito session. `DEPLOYMENT.md`.

---

### Explicitly deferred to Round 3 (do not claim as done)
Brand Drift Intelligence • Advanced Multimodal (video) Governance • Enterprise MCP Integration Hub (Figma/Slack/CMS connectors).
