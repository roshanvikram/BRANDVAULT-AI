# FEATURE_STATUS.md — BRANDVAULT AI

**Date:** 2026-11-04. Status legend:
- ✅ **Implemented & tested** (I ran it this session)
- 🟡 **Implemented, not independently tested**
- 🟠 **Partially implemented** (works for the seeded/demo path, gaps remain)
- ⛔ **Not implemented**
- 🔒 **Blocked by external dependency** (key/service/infra not configured)

---

## Core workflow (PART 27 acceptance scenario)

| Capability | Status | Notes |
|---|---|---|
| Seed demo org (NOVA TECH) on startup | ✅ | `seed.py`, idempotent |
| Brand rules / facts / terminology stored per org | ✅ | Queried live during analysis |
| Content submission → analysis job | ✅ | `POST /content/analyze`, synchronous |
| Findings with category/severity/evidence/confidence | ✅ | Persisted `findings` table |
| ClaimDNA 5-status verification | ✅ | **All 5 reachable** (Milestone A): Contradicted (price), Unsupported (superlative/comparative), Outdated (expired fact), Needs Human Review (ambiguous superlative / price with no approved record), Supported |
| Pricing contradiction detection | ✅ | ₹69,999 vs ₹79,999 verified |
| Apply correction + re-analyse | ✅ | `POST /content/apply-correction` |
| Human approval decision | ✅ | `POST /approval/decide`, persisted |
| Brand Passport (SHA-256) | ✅ | `BV-2026-52ED8A` generated & verified |
| Dashboard reflects real data | ✅ | Reads live endpoints |
| Persistence across restart | ✅ | SQLite file, pre-existing rows |

## Modules (UI routes)

| Module | Route | Status | Notes |
|---|---|---|---|
| Command Center | `/dashboard` | ✅ | **R2-8:** rebuilt in "Monochrome Organic Glass" — glass cards over a subtle organic background. Real data: Getting Started (onboarding), Governance Pulse gauge (policy coverage), KPI sparklines, Claim Verification Distribution, Live Agent Runs. Live-verified |
| Brand DNA Studio | `/brand-dna` | 🟠 | Rules/facts/terms display + confirm; PDF upload path present, DOCX/TXT not fully supported |
| Knowledge Graph | `/knowledge-graph` | ✅ | **R2-2:** interactive SVG graph explorer over **real** records (`GET /graph/brand`, `services/graph.py`). Brand→categories→entities→findings/claims/passport + real finding→rule cross-links. Expand/collapse, auto-fit, detail panel with module links. Verified by tests + live walkthrough |
| AI Copy Studio | `/copy-studio` | ✅ | **R2-AI:** generative brand-compliant rewrite (`POST /copy-studio/rewrite`, `services/copystudio.py`). Uses the LLM when configured (labelled `llm:<provider>`+model), else a deterministic rules-based rewrite from real terminology+pricing (labelled `heuristic`). No-SDK HTTP Anthropic driver added so it works offline/without the SDK; goes fully generative on `ANTHROPIC_API_KEY`. Honest AI/heuristic badge. Verified by tests + live |
| Brand Assistant (Digital Twin Q&A) | `/assistant` | ✅ | **R2-3:** grounded NL Q&A (`POST /twin/ask`, `services/twin.py`). Deterministic intent-routing + cited answers from real records; content-word relevance gate → honest "not in approved data" for off-topic. Glass chat UI with source links. Verified by tests + live |
| Setup Guide (Onboarding) | `/onboarding` | 🟠 | **R2-1:** guided wizard driven by `GET /onboarding/status` — **real** completion from persisted config (confirmed rules, facts, reviewers, submissions…), per-step counts + module links, demo-data banner, dashboard progress card, reusable `EmptyState`. Verified by tests + live. Remaining R2-1: Simple/Advanced mode + broader empty-state rollout |
| Content Intelligence | `/content-intelligence` | ✅ | 3-panel editor/findings/evidence, verified via API |
| ClaimDNA | `/claim-dna` | ✅ | Sample test + claim statuses |
| Visual DNA Inspector | `/visual-dna` | 🟠 | **Milestone F:** real `POST /visual/analyze` — pure-Python PNG/BMP decode + **measured** colour palette, chromatic/monochrome fraction, contrast; persists a Visual submission with findings. UI shows measured metrics (replaced the old faked setTimeout). **Limits:** JPEG/WebP/SVG → 415 (not faked); OCR unavailable (honest seam, no Tesseract) |
| Agent Control Center | `/agent-control` | ✅ | Real persisted `agent_runs` + stats |
| Approval Hub | `/approval-hub` | ✅ | Decision flow works and is **auth-gated** (Milestone D); UI signs in as demo Reviewer before deciding |
| Brand Passport | `/brand-passport` | ✅ | List + SHA-256; PDF export = print view |
| Brand Risk Radar | `/risk-radar` | 🟡 | Aggregates real records |
| Settings | `/settings` | 🟡 | Config + roadmap display |

## Agents (PART 10)

| Agent | Status | Notes |
|---|---|---|
| Orchestrator | 🟠 | Sequential coordinator, not autonomous/LLM |
| Terminology Agent | ✅ | Regex over stored prohibited terms |
| Brand Voice Agent | 🟠 | Exclamation-density heuristic only |
| ClaimDNA Agent | ✅ | Price + superlative + comparative detection |
| Suggestion Agent | ✅ | Emits stored preferred terms / corrections |
| Guideline Gap Agent | ⛔ | Listed in stats UI; no real gap logic in analyzer |
| Visual DNA Agent | 🟠 | **Milestone F:** real deterministic colour/contrast measurement (pure-Python decode), persisted as an agent run. No OCR/logo-match (honest limit) |

## Infrastructure / cross-cutting (PARTS 11, 13, 17, 20, 21, 24)

| Capability | Status | Notes |
|---|---|---|
| RAG / embeddings / vector search | 🟠 | **Milestone C:** real vector-space retrieval — TF-IDF embeddings (L2-normalized, persisted to `document_chunks.embedding_json`), brute-force **cosine** + keyword **hybrid** ranking, org/status isolation, exposed via `POST /rag/search`; analyzer evidence now comes from it (lexical overlap is the fallback). **Honest limit:** statistical TF-IDF, not a neural/transformer embedding; interface is swap-ready for sentence-transformers or pgvector |
| PostgreSQL / pgvector | 🟠 | **Milestone G:** Postgres-ready — portable ORM types (verified by test), `DATABASE_URL` config, CORS hardened (env-driven, no `*`, `allow_credentials=False`), Alembic scaffold. Not run against a live Postgres here (driver not installable offline). pgvector N/A (retrieval is TF-IDF) |
| LLM provider integration | 🟠 | **Milestone B:** provider abstraction (`services/llm.py`) with a real Anthropic driver (official SDK, default `claude-opus-5-5`). LLM findings are Pydantic-validated, labeled `llm:<provider>`, merged/deduped with heuristics, and carry retrieved (not model-invented) citations. Heuristic engine stays default + automatic fallback on any failure. `/health` exposes live LLM status. **Verified:** validation, merge, dedupe, fallback, labeling. **Not verified here:** a live Anthropic HTTP call (no API key/SDK in this env). OpenAI/Gemini are honest interface stubs (report unavailable) |
| Authentication / RBAC | ✅ | **Milestone D:** `users` table, PBKDF2 passwords, HMAC bearer tokens, `/auth/login` + `/auth/me`, 3 roles. `/approval/decide` is gated — only Reviewer/Administrator may approve/reject/request-revision, attribution comes from the authenticated identity (forged names ignored), and tokenless callers (AI agents) cannot approve. Verified by tests |
| Tenant isolation | ✅ | **Milestone D:** approval enforces caller-org == submission-org; cross-tenant decide → 403 (tested). Reads still use `org_id` filtering |
| Secure file upload validation | 🟠 | **Milestone D3:** type allowlist (pdf/txt/md) + 15 MB + empty-file checks. Rate limiting still TODO |
| DOCX / OCR ingestion | ⛔ | pypdf only; OCR is an unavailable provider seam (Milestone F), never faked |
| Automated tests (unit + integration) | ✅ | **Milestone E:** 28 `unittest` tests (also pytest-compatible) in `backend/tests/`, all passing — security, RAG, analyzer, auth/RBAC, approval gating, persistence. **Playwright E2E still TODO** (needs a browser runtime) |
| Labelled evaluation dataset (PART 21E) | ✅ | **Milestone E:** 36 labelled cases (`backend/eval/dataset.json`) + `run_eval.py`. Measured: **P=1.000, R=0.860, F1=0.925** (6 honest out-of-scope FNs). Surfaced & fixed 2 analyzer bugs |
| WebSocket/SSE live updates | ⛔ | Synchronous request/response |
| MCP server | 🟡 | File present; not re-verified this session |
| Public deployment | 🟠 | **Milestone G:** deployment config shipped — `Dockerfile`, `render.yaml` (web + managed Postgres), `Procfile`, `DEPLOYMENT.md` (runbook + incognito checklist + demo accounts). Authored, not live-deployed from here (no hosting/network) |

## Data model vs PART 17 spec

Present: `organizations, users, brand_guidelines, document_chunks, brand_rules, approved_facts, terminology_rules, submissions, findings, claim_verifications, approval_records, revisions, brand_passports, agent_runs, audit_logs`.
Missing vs spec: `memberships, brand_assets, evidence_links, suggestions, tool_audit_logs, governance_insights`. (`users` added in Milestone D — single org per user covers RBAC + tenant isolation; `memberships` for multi-org users is future work.)
