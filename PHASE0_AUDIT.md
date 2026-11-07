# PHASE 0 — Repository Audit & Upgrade Plan

**Date:** 2026-11-07 · **Branch:** `master` · **Scope:** audit only, no product code changed.

Everything below was checked against the code in this session, not taken from the older docs.
Test baseline: **64/64 backend tests pass** (`python -m unittest discover -s backend/tests -t .`).

---

## 1. Existing architecture

| Layer | What is there |
|---|---|
| Frontend | Next.js 14.2 (App Router), React 18, TypeScript, Tailwind 3, lucide icons. No chart, graph, upload or test libraries. One API client: `frontend/src/lib/api.ts` (638 lines). Auth context: `src/lib/auth.tsx`. Shell: `components/layout/*`. |
| Backend | FastAPI + SQLAlchemy 2 (typed `Mapped` models), Pydantic v2, single router tree `backend/app/api/v1/*`. |
| Database | SQLite file `brandvault.db`. Tables come from `create_all` plus an additive column shim (`app/db/migrations.py`). Alembic is scaffolded (`backend/migrations/`) with **no version files**, and alembic is **not installed** in the venv. |
| AI | `services/llm.py`: provider interface with HTTP Anthropic and Groq drivers (Groq key is set in `.env`, Anthropic key is empty). The heuristic analyzer is the default and the fallback. |
| Retrieval | `services/rag.py`: TF-IDF vectors stored as JSON on `document_chunks`, cosine + keyword hybrid, filtered by org. |
| Vision | `services/visual.py`: pure-Python PNG/BMP decoder, measured palette / chromatic fraction / contrast. OCR is a null provider. |
| Jobs | **Uncommitted work in progress:** `services/jobs.py` (in-memory thread job store) and `POST /content/analyze-async` + `GET /content/jobs/{id}`. Lost on restart, so it does not yet meet the "refresh-safe job state" requirement. |
| Auth | PBKDF2 passwords, HMAC bearer tokens, roles Creator / Reviewer / Administrator, Google OAuth routes. |
| MCP | `backend/mcp_server.py` (183 lines), not re-verified. |
| Environment | Python 3.13.2. **Installable via pip now:** Pillow, numpy (dry-run confirmed). **Not present:** OpenCV, Tesseract binary, ffmpeg, langdetect, sentence-transformers. |

## 2. Existing feature inventory (verified against code)

| Requested module | Exists? | Where | State |
|---|---|---|---|
| Command Center | Yes | `app/dashboard` | Real data |
| Brand DNA Studio | Yes | `app/brand-dna`, `api/v1/brand.py` | PDF/TXT/MD ingestion, rules/facts/terms, admin confirm |
| Content Intelligence | Yes | `app/content-intelligence`, `services/analyzer.py` | Findings + evidence + apply-correction + re-analysis |
| ClaimDNA | Yes | `app/claim-dna`, `api/v1/claim.py` | 5-status model, evidence map |
| Visual DNA | Partial | `app/visual-dna`, `services/visual.py` | Colour/contrast only on PNG/BMP; no logo, OCR, typography or layout |
| Knowledge Graph | Yes | `services/graph.py` | Built from real records |
| Brand Digital Twin | Yes | `app/assistant`, `services/twin.py` | Grounded Q&A, LLM phrasing only |
| AI Creative Studio | Partial | `app/copy-studio` | Text rewrite only |
| Brand Memory | Yes | `services/memory.py` | Learns terminology from history, admin-only apply |
| Risk Radar | Yes | `services/risk.py` | 5 explained rule-based indicators |
| Agent Control Center | Yes | `app/agent-control` | Real persisted `agent_runs` |
| Approval Hub | Yes | `api/v1/approval.py` | Auth-gated decide; 3 decisions only |
| Brand Passport | Yes | `services/passport_service.py` | SHA-256 of content |
| Onboarding / Settings | Yes | `app/onboarding`, `app/settings` | — |
| Evaluation | Partial | `backend/eval/` | 36 labelled text cases, P=1.00 R=0.86 (text analyzer only) |

## 3. Missing feature inventory

| Area | Missing |
|---|---|
| Brand Asset Library | Whole module: assets, versions, approval states, effective dates, similarity search |
| Visual Intelligence | Logo detection/matching, JPEG/WebP support, OCR, typography, layout, product images, bounding boxes |
| Visual Correction | Whole module: previews, revisions of images, before/after, re-analysis |
| Multilingual | Whole module: language ID, sentence alignment, number/unit/qualifier/negation comparison, terminology checks |
| Creative Studio | Multi-format generation, campaign briefs, auto-run of governance checks |
| Brand Drift | Time-series snapshots and trend comparison |
| Counterfactual Simulator | Whole module |
| Video / Audio | Whole module (needs ffmpeg + speech-to-text) |
| Brand Protection | Whole module (needs real source integrations) |
| Approval Hub | Conditional approval, multi-level/parallel routing, risk-based routing, version-locked approvals |
| Impact Analyser, Workflow Automation, Connector Hub, Public API keys/webhooks, AI Evaluation Centre | Not started |
| Infrastructure | Durable job queue, object storage for media, real migrations, rate limiting, Playwright E2E |

## 4. Security gap analysis (most severe first)

1. **Critical — unauthenticated reads and writes across tenants.** Only 3 routes check a login (`/approval/decide`, `/memory/apply-terminology`, `/auth/me`). Every other route accepts `org_id` from the query/body. That means anyone who can reach the API can, without a token:
   - create rules and facts for any org (`POST /brand/rules`, `POST /brand/facts`),
   - confirm rules (`PATCH /brand/rules/{id}/confirm`), which changes official Brand DNA,
   - upload guidelines, create workspaces, run analyses, apply corrections,
   - read any org's rules, facts, submissions, graph, risk, RAG results and passports.
   This undermines the "Administrator must approve Brand DNA changes" rule.
2. **High — hardcoded fallback `SECRET_KEY`** in `core/config.py`. If the env var is unset, anyone can forge tokens.
3. **Low — `/auth/register` puts every new account in the default (NOVA) org.** The role is fixed to Creator, so it cannot approve or edit Brand DNA, but a new account can still read that org's data. Multi-org sign-up needs an invite or a new-workspace flow.
4. **Medium — no rate limiting** on login, uploads or LLM-backed routes (cost exposure on the Groq key).
5. **Medium — uploads:** image route has no MIME sniffing beyond decoders; no storage outside the DB; no size cap verified for `/visual/analyze`.
6. **Medium — prompt injection:** guideline text and submission text go into LLM prompts; needs explicit "untrusted data" delimiting and output validation (findings are already Pydantic-validated, which helps).
7. **Low — approval not version-locked:** an `ApprovalRecord` does not store which `version` was approved, so an edited submission can keep an earlier approval.
8. **Low — in-memory job store** loses state on restart and has no org scoping on `GET /content/jobs/{id}`.

## 5. Database change plan

Additive only, so existing rows stay intact. Each table carries `org_id` (indexed, FK to `organizations`).

| Phase | New tables | Changed tables |
|---|---|---|
| 1 Security | `jobs` (durable state: queued/processing/completed/failed/cancelled, idempotency key, attempts) | `approval_records` + `submission_version`; `submissions` + `content_hash` |
| 1 Assets | `brand_assets`, `asset_versions` (file stored on disk/object storage, DB keeps path + sha256 + perceptual hash + palette) | `brand_rules` + optional `asset_id` link |
| 2 Visual | `visual_analyses`, `visual_findings` (bbox, detected vs reference, confidence, status `confirmed`/`needs_review`) | — |
| 3 Correction | `corrected_creatives` (parent image, revision no., applied corrections, user, timestamp, re-analysis id) | — |
| 4 Multilingual | `multilingual_campaigns`, `campaign_translations`, `translation_findings` | — |
| 6 Memory/Drift | `ai_feedback`, `brand_policy_proposals`, `brand_drift_snapshots` | — |
| 7 Video/Audio | `media_analyses`, `media_segments` (time-coded) | — |
| 8 Agents | `agent_workflows` (parent run + steps) | `agent_runs` + `workflow_id`, `org_id` |

Migration approach: keep the SQLite additive shim for local dev, and start real Alembic revisions from Phase 1 so Postgres deployment works. This needs `alembic` installed in the venv.

## 6. API change plan

- **Phase 1:** add `get_current_user` + `ensure_same_org` to every org-scoped route and derive `org_id` from the token. Writes that change Brand DNA require Administrator. Keep the `org_id` parameter accepted but validated against the token, so existing callers keep working. Add a simple per-IP rate limit on `/auth/*` and LLM routes.
- **Assets:** `/assets` CRUD, `/assets/{id}/versions`, `/assets/{id}/approve`, `/assets/search`, `/assets/similar`, signed file download.
- **Visual:** `POST /visual/analyze` becomes a job → `GET /visual/analyses/{id}` (findings + bboxes); keep the old response shape for the current page.
- **Correction:** `POST /visual/analyses/{id}/corrections/preview`, `.../apply` (new revision, triggers re-analysis), `GET .../revisions`.
- **Multilingual:** `POST /multilingual/campaigns`, `POST .../translations`, `GET .../report`.
- **Jobs:** `GET /jobs/{id}` (org-scoped), `POST /jobs/{id}/cancel`.

## 7. Frontend change plan

- Group the sidebar into sections with progressive disclosure: **Govern** (Brand DNA, Asset Library, Memory), **Analyse** (Content, ClaimDNA, Visual, Multilingual, Media), **Create** (Creative Studio), **Review** (Approval Hub, Passport), **Insight** (Command Center, Risk, Drift, Graph, Twin, Agents), **Admin** (Connectors, Settings).
- Shared components to build once: drag-and-drop upload, job progress (polls the durable job), image annotation with bounding boxes, before/after slider, evidence card, confidence/severity badges.
- Upgrade `visual-dna` into Visual Intelligence in place (same route, no duplicate module).
- Every new screen reads from the backend; anything not live yet carries a "not available" label.
- Add Playwright once the upload → findings → correction flow exists.

## 8. Phased implementation plan

The order below differs slightly from the brief: **security comes first**, because building the Asset Library on top of unauthenticated routes would repeat the biggest gap.

| Phase | Delivers | Real capability available here | Limits to state up front |
|---|---|---|---|
| **1a Security foundation** ✅ done 2026-11-07 | Auth + tenant checks on all routes, admin gate on Brand DNA writes, no fallback secret, durable `jobs` table (finishes the uncommitted async work), version-locked approvals, rate limiting | Fully buildable now | Frontend must send the token on every call; demo pages sign in first |
| **1b Brand Asset Library** | Assets, versions, approval states, effective dates, palette/fonts as structured assets, perceptual hash on upload | Needs Pillow + numpy (installable) | Semantic search over assets = TF-IDF on names/tags, not image embeddings |
| **2 Visual Intelligence** | JPEG/WebP via Pillow; measured palette vs approved HEX with ΔE (CIEDE2000); WCAG contrast; logo match via perceptual hash + template search over approved logo versions; outdated-version detection | Colour, contrast, logo version matching are deterministic and testable | OCR/typography need Tesseract installed **or** a vision-capable LLM key. Font ID will be labelled "estimate" |
| **3 Smart Correction** | Colour remap to nearest approved colour, logo swap by compositing the approved asset into the detected box, revisions, before/after, automatic re-analysis | Deterministic edits with Pillow | No generative image-editing model is configured; generative edits stay "not available" until one is |
| **4 Multilingual** | Script-based language ID, sentence alignment, explicit comparison of numbers, units, qualifiers ("up to" / "more than"), negations, brand terms; LLM semantic pass when the key is set; report export | Deterministic checks catch the 12-hours example without an LLM | Cultural review is LLM-suggested and always marked "needs human review" |
| 5 Creative Studio | Brief → multi-part generation → auto-run through analyzer + ClaimDNA, regenerate a part | Text via Groq | Image generation needs a provider |
| 6 Memory + Drift | Feedback capture on accept/reject, policy proposals, monthly drift snapshots | Builds on `services/memory.py` | Drift trends only appear once real history exists |
| 7 Video / Audio | Frame sampling + per-frame visual checks, transcription, subtitle comparison | Needs ffmpeg (user install) and a speech-to-text provider | Not buildable as "real" until both are configured |
| 8 Agents | Workflow table, orchestrator that runs the specialist services above and records each step | Wraps real services | Agents never approve |
| 9–10 | Simulator, risk forecasting, protection, connectors, public API, observability | Simulator + forecasting from stored data | Protection and connectors need real API credentials per service |

### What I need from you before Phase 1b onward
- OK to install **Pillow** and **numpy** into `backend/venv` (and add them to `requirements.txt`).
- For OCR: install the Tesseract binary, or confirm we use a vision-capable LLM (I'll check which Groq models accept images before relying on one).
- For video/audio later: ffmpeg and a speech-to-text provider.

### Uncommitted changes found
`backend/app/api/v1/content.py` (async analyze routes) and `backend/app/services/jobs.py` are uncommitted. Phase 1a would replace the in-memory store with the durable `jobs` table, keeping the same endpoints.
