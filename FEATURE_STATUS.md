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
| Brand Memory | `/brand-memory` | ✅ | **R2-4:** learns from real history (`GET /memory/insights`, `services/memory.py`) — accepted corrections, recurring violations, contradictions — and proposes new terminology. `POST /memory/apply-terminology` is **Administrator-only** (RBAC + tenant isolation, idempotent) and creates a real rule; never auto-edits Brand DNA. Glass page with admin-gated apply. Verified by tests + live apply |
| Knowledge Graph | `/knowledge-graph` | ✅ | **R2-2:** interactive SVG graph explorer over **real** records (`GET /graph/brand`, `services/graph.py`). Brand→categories→entities→findings/claims/passport + real finding→rule cross-links. Expand/collapse, auto-fit, detail panel with module links. Verified by tests + live walkthrough |
| AI Copy Studio | `/copy-studio` | ✅ | **R2-AI:** generative brand-compliant rewrite (`POST /copy-studio/rewrite`, `services/copystudio.py`). Uses the LLM when configured (labelled `llm:<provider>`+model), else a deterministic rules-based rewrite from real terminology+pricing (labelled `heuristic`). No-SDK HTTP drivers for **Anthropic** (`ANTHROPIC_API_KEY`) and **Groq** (`GROQ_API_KEY`, OpenAI-compatible — e.g. `openai/gpt-oss-120b`; sends a real User-Agent to pass Cloudflare). Honest AI/heuristic badge. **Verified live generative** (Groq `openai/gpt-oss-120b` produced grounded brand-compliant prose) + tests |
| Brand Assistant (Digital Twin Q&A) | `/assistant` | ✅ | **R2-3:** grounded NL Q&A (`POST /twin/ask`, `services/twin.py`). Deterministic intent-routing + cited answers from real records; content-word relevance gate → honest "not in approved data" for off-topic. **When an LLM key is configured it rephrases the grounded answer naturally (labelled `phrased_by: llm:<provider>` + an "AI · model" badge) — strictly no new facts; the deterministic answer + citations stay authoritative and are the fallback.** Glass chat UI with source links. Verified by tests + live (Groq phrasing) |
| Setup Guide (Onboarding) | `/onboarding` | 🟠 | **R2-1:** guided wizard driven by `GET /onboarding/status` — **real** completion from persisted config (confirmed rules, facts, reviewers, submissions…), per-step counts + module links, demo-data banner, dashboard progress card, reusable `EmptyState`. Verified by tests + live. Remaining R2-1: Simple/Advanced mode + broader empty-state rollout |
| Content Intelligence | `/content-intelligence` | ✅ | 3-panel editor/findings/evidence, verified via API |
| ClaimDNA | `/claim-dna` | ✅ | Sample test + claim statuses. **R2-7 Evidence Integrity Map:** `GET /claim/evidence-map` → claim→evidence relationships with source reliability + freshness and an explicit **missing-vs-contradicted** distinction; glass visualization with a state-distribution bar. Verified by tests + live |
| Visual DNA Inspector | `/visual-dna` | 🟠 | **Milestone F:** real `POST /visual/analyze` — pure-Python PNG/BMP decode + **measured** colour palette, chromatic/monochrome fraction, contrast; persists a Visual submission with findings. UI shows measured metrics (replaced the old faked setTimeout). **Limits:** JPEG/WebP/SVG → 415 (not faked); OCR unavailable (honest seam, no Tesseract) |
| **Product Truth Engine** (12-engines Phase 1) | `/brand-dna/products` | ✅ | Structured `products` + `product_facts` (source document, page, verbatim excerpt, status pending/approved/rejected/superseded, validity dates). Bootstrapped from existing approved facts. Verifies prices, battery hours, TOPS, GHz, GB/TB (RAM vs storage), display, weight, warranty years with qualifier rules -> Supported / Contradicted / Outdated / Unsupported / Needs Human Review. Missing facts are Unsupported, never guessed. Admin-only writes with supersession history. **AI extraction** (durable job) proposes pending facts and discards any whose quoted evidence is not verbatim in the document — live-verified with Groq (3 proposed, duplicates caught) |
| **Knowledge Gap Detector** | `/brand-dna/knowledge-gaps` | ✅ | Completeness score + prioritised list of missing / conflicting / outdated / weakly-sourced Brand DNA: per-product attribute matrix, colour/logo/typography/disclaimer/regional/benchmark coverage, price conflicts between sources, recurring unsupported claims, unconfirmed rules, effective dates, stale documents and expired facts; recommended documents to upload; action links. Policy ownership is reported as not tracked yet |
| **Campaign DNA Fingerprint** | `/brand-passport/verify` | ✅ | Passports now record a fingerprint (campaign, brand, content SHA-256, version-bound hash, approved version, **real guideline version** — replaced the hardcoded "v2.4", approval reference, approver, timestamp, revision). Verify pasted text or .txt/.md: Verified Match / Modified After Approval (word diff) / Unknown Version / New Unapproved Campaign / Unable to Verify. Images are routed to Asset Forensics (byte hash ≠ visual identity). Append-only `campaign_integrity_checks` log (no update/delete routes) |
| **Brand Asset Library + Forensics** | `/visual-dna/forensics` | ✅ | Admin-uploaded official assets (validated images on disk under `backend/storage/`, SHA-256, DCT pHash + dHash, dominant colours, versions with supersession; only current assets are recommended as replacements). Investigation: identical file, near-duplicate, logo localisation (ORB + RANSAC homography, edge-template fallback) with outline-agreement verification (calibrated: true ≥ 0.71, false ≤ 0.48, threshold 0.6) and one-version-per-region arbitration; measures stretch, rotation, crop, recolour (median CIE76 ΔE), outdated version. 10 labelled synthetic cases all correct; evidence preserved. **Limits:** logo search is per-asset feature matching (not a trained detector); no OCR; synchronous (~0.3–1.6 s) rather than a background job |
| Guideline ingestion fix | Brand DNA upload | ✅ | Chunk pages now come from the PDF's `--- Page N ---` markers (previously paragraph index ÷ 3, which mis-cited pages); startup data fix corrected 6 stored chunks. Upload now keeps up to 200 paragraphs (was 10) |
| **Translation Guard** (new, 2026-11-07) | `/translation-guard` | ✅ | Compares translated campaigns with the source. **Deterministic:** language ID by Unicode script (+ stop-words for Latin), numbers/units/prices with native-digit and European-format normalisation, qualifiers (up to / more than / about) with pre/post-position lexicons for en, hi, ta, fr, de, es, ja, zh, ar, negations, approved product names, prohibited terms, prices vs approved facts. **AI (when configured):** meaning score, extra differences, corrected translation, cultural notes — labelled, and merged as "Confirmed by AI" when it repeats a rule finding. Persisted (`multilingual_campaigns`, `campaign_translations`), tenant-scoped, rate-limited, Markdown report download. 21 tests; live-verified with Groq `openai/gpt-oss-120b` on the brief's 12-hour example. **Limits:** ml/te/kn/bn/gu/pa get number, price and brand-term checks only; no OCR or subtitle-file upload yet |
| Agent Control Center | `/agent-control` | ✅ | Real persisted `agent_runs` + stats |
| Approval Hub | `/approval-hub` | ✅ | Decision flow works and is **auth-gated** (Milestone D); UI signs in as demo Reviewer before deciding |
| Brand Passport | `/brand-passport` | ✅ | List + SHA-256; PDF export = print view |
| Brand Risk Radar | `/risk-radar` | ✅ | **R2-5 Predictive Risk Intelligence:** `GET /radar/intelligence` (`services/risk.py`) → 5 explained indicators (Content/Claim/Guideline/Process/Visual) with rationale + real drivers + recommendation + overall score, transparent rules over history (not ML forecasts). Glass page with score bars. Verified by tests + live |
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
| **Phase 1a security foundation (2026-11-07)** | ✅ | Login required on every org-scoped route (route audit: only auth, health and two static info routes are public); org taken from the token, mismatched `org_id` → 403; Brand DNA writes Administrator-only + audit-logged; cross-org submission overwrite blocked; agent runs carry `org_id` (137 legacy runs without an org are hidden); passports scoped by org; version-locked approvals + passport supersede/re-issue; no default `SECRET_KEY`; per-IP rate limits; durable `jobs` table (idempotency, retries, cancel-while-queued, restart recovery). 19 tests in `tests/test_phase1a.py`; live-verified as VORTEXA admin and NOVA reviewer |
| Authentication / RBAC | ✅ | **Milestone D:** `users` table, PBKDF2 passwords, HMAC bearer tokens, `/auth/login` + `/auth/me`, 3 roles. `/approval/decide` is gated — only Reviewer/Administrator may approve/reject/request-revision, attribution comes from the authenticated identity (forged names ignored), and tokenless callers (AI agents) cannot approve. Verified by tests |
| Tenant isolation | ✅ | **Phase 1a:** enforced on all reads and writes from the token (was approval-only). Frontend no longer hardcodes the NOVA org id, so VORTEXA users now see VORTEXA data |
| Secure file upload validation | 🟠 | **Milestone D3:** type allowlist (pdf/txt/md) + 15 MB + empty-file checks. Upload now Administrator-only. No content sniffing / malware scan yet |
| Rate limiting | 🟠 | **Phase 1a:** in-process per-IP limits on auth + AI routes (not shared across instances) |
| DOCX / OCR ingestion | ⛔ | pypdf only; OCR is an unavailable provider seam (Milestone F), never faked |
| Automated tests (unit + integration) | ✅ | **83 tests passing as of Phase 1a.** Originally **Milestone E:** 28 `unittest` tests (also pytest-compatible) in `backend/tests/`, all passing — security, RAG, analyzer, auth/RBAC, approval gating, persistence. **Playwright E2E still TODO** (needs a browser runtime) |
| Labelled evaluation dataset (PART 21E) | ✅ | **Milestone E:** 36 labelled cases (`backend/eval/dataset.json`) + `run_eval.py`. Measured: **P=1.000, R=0.860, F1=0.925** (6 honest out-of-scope FNs). Surfaced & fixed 2 analyzer bugs |
| Background jobs | ✅ | **Phase 1a:** durable `jobs` table; daemon-thread worker (swap for RQ/Celery in production). Only content analysis uses it so far |
| WebSocket/SSE live updates | ⛔ | Synchronous request/response; jobs are polled |
| MCP server | 🟡 | File present; not re-verified this session |
| Public deployment | 🟠 | **Milestone G:** deployment config shipped — `Dockerfile`, `render.yaml` (web + managed Postgres), `Procfile`, `DEPLOYMENT.md` (runbook + incognito checklist + demo accounts). Authored, not live-deployed from here (no hosting/network) |

## Data model vs PART 17 spec

Present: `organizations, users, brand_guidelines, document_chunks, brand_rules, approved_facts, terminology_rules, submissions, findings, claim_verifications, approval_records, revisions, brand_passports, agent_runs, audit_logs`.
Missing vs spec: `memberships, brand_assets, evidence_links, suggestions, tool_audit_logs, governance_insights`. (`users` added in Milestone D — single org per user covers RBAC + tenant isolation; `memberships` for multi-org users is future work.)
