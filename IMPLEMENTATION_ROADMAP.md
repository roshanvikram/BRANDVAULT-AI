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
- **F1.** ✅ DONE — Visual DNA: `services/visual.py` (pure-Python PNG/BMP decode, no OpenCV/Pillow available) + **measured** colour palette, chromatic/monochrome fraction, and contrast; `POST /visual/analyze` persists a Visual submission with findings; frontend shows measured metrics (faked data removed). Verified by tests + live check. Limits: JPEG/WebP/SVG → 415; OCR is an unavailable provider seam (no Tesseract) — a real neural/Tesseract OCR and logo-matching remain future work.
- **F2.** Live updates (SSE/polling) for analysis progress and the review queue.
- **F3.** MCP server auth + audit logging; re-verify tools.

## Milestone G — Deployment  ✅ DONE (config/docs; live deploy to execute on host)
*Delivered: env-driven config + hardened CORS (computed origins, no `*`, `allow_credentials=False` for the stateless-token API), `DATABASE_URL` Postgres support with portable ORM types (test-verified), Alembic scaffold (`backend/alembic.ini` + `migrations/`), `Dockerfile`, `Procfile`, `render.yaml` (web + managed Postgres), `.env.example` prod vars, and `DEPLOYMENT.md` (runbook, security checklist, incognito acceptance checklist, demo accounts). Verified locally: full suite (41 tests) green and the app boots under production-style env (health + login 200). Not verified: a live cloud deploy and a real Postgres migration — no hosting/network/driver in this environment; execute the runbook on the target host.*
- **G1.** Postgres migration (SQLAlchemy models are portable; add Alembic).
- **G2.** Deploy frontend (Vercel) + backend (Render/Fly) + managed Postgres; configure CORS and server-side secrets.
- **G3.** Seeded demo workspace + documented demo account; verify in a private/incognito session. `DEPLOYMENT.md`.

---

# ROUND 2 — "Ultimate Product Evolution" (added 2026-11-05)

Maps the Round 2 vision onto bounded milestones. **Rule unchanged:** the Level‑1
core (A–G) must keep working and nothing is marked done until tested. Each R2
milestone is independently shippable, uses real persisted data, keeps the AI
explainable, and keeps consequential decisions human‑controlled.

### What already exists and must be preserved (do NOT rebuild)
Auth + RBAC + tenant isolation • Brand DNA (rules/facts/terminology, confirm) •
Content Intelligence 3‑panel + apply‑correction • ClaimDNA 5‑status + real
evidence • TF‑IDF RAG retrieval • Visual DNA (measured colour/contrast) •
Agent Control (real `agent_runs`) • Human Approval (gated) • Brand Passport
(SHA‑256) • Risk Radar (real aggregates) • real dashboard data • sign‑up /
sign‑in / Google OAuth • /guide with audio + video walkthrough • 47 tests + eval.

### R2 milestones (proposed order — value-to-risk, Level 1 protected)

- **R2‑1 — UX foundation: smart empty states, progressive disclosure, Simple/Advanced mode, guided onboarding wizard.  🟠 PARTIAL** Highest "independently usable" value (PART 04, 16), low risk, no backend fabrication. *Delivered: `GET /onboarding/status` (`api/v1/onboarding.py`) computes **real** setup completion from persisted records (guidelines, confirmed rules, facts, terminology, reviewers, submissions, passports) — never a hardcoded "done"; `/onboarding` guided wizard renders genuine ✓/pending per step with live counts, a completion %, a clearly-labelled demo-data banner, and per-step module links; a dashboard "Workspace setup" progress card; a reusable `EmptyState` (what the page does / why it matters / next action / example) wired into the dashboard's empty submissions state; sidebar "Setup Guide". Verified: 2 onboarding tests in the 51-test suite, `tsc` clean, live walkthrough (100% real completion on the demo + dashboard card). **Remaining R2-1:** Simple/Advanced experience-mode toggle and broader progressive-disclosure/empty-state rollout across every module.*
- **R2‑2 — Brand Knowledge Graph + Brand Intelligence Map.  ✅ DONE** A relational knowledge graph over existing records with an interactive SVG graph explorer; clicking a node opens its real detail (PART 02.2, 06). *Delivered: `services/graph.py` (`build_brand_graph`) assembles nodes/edges purely from real records — Brand→{Guidelines→Evidence, Rules, Facts, Terminology, Campaigns→{Findings, Claims, Passport}} — plus real `finding→rule` cross-links resolved by `rule_reference`↔rule‑title match (no fabricated links). `GET /graph/brand`. New `/knowledge-graph` page: weighted radial‑tree SVG layout with expand/collapse, auto‑fit viewBox, a detail panel showing each node's real fields + "Open in module", and a legend. Verified: endpoint consistency tests (every edge/parent resolves to a real node; 404 on unknown org) in the 49‑test suite, `tsc` clean, and a live browser walkthrough (brand → categories → campaign → findings/claims, real detail panel). No graph DB — relational queries suffice.*
- **R2‑3 — Brand Digital Twin Q&A (grounded).  ✅ DONE** Natural‑language questions answered *only* from approved org data, with citations. *Delivered: `services/twin.py` + `POST /twin/ask` — deterministic keyword intent‑routing (pricing, most‑violated‑rules from real finding history, approved facts/claims, terminology, brand voice, rules) assembling answers from real records with citations; a retrieval fallback over guideline chunks gated by a **content‑word relevance check** so off‑topic questions (e.g. "capital of France") are honestly returned as "not in approved data" instead of answered with an irrelevant passage. Org‑scoped, read‑only, no fabrication; LLM phrasing is a noted optional seam. New `/assistant` chat page: glass UI, suggestion chips, grounded/ungrounded badges, and clickable source citations. Verified: 4 twin tests in the 55‑test suite, `tsc` clean, and a live walkthrough (grounded price answer with citation + honest off‑topic refusal). Never bypasses permissions (PART 02.1, 04).*
- **R2‑4 — Brand Memory Engine.  ✅ DONE** *Delivered: `services/memory.py` + `GET /memory/insights` — learns from real history (accepted corrections via `is_applied`, recurring violations, repeated contradictions) and derives PROPOSALS (a new terminology entry for a recurring flagged word‑phrase not yet formalised; pricing/descriptive flags excluded). `POST /memory/apply-terminology` lets an **Administrator** (RBAC‑gated via `require_roles`, tenant‑isolated, idempotent) explicitly accept a proposal, which creates a real `TerminologyRule` — the system NEVER edits Brand DNA automatically. New `/brand-memory` page (glass): summary, insight cards with counts, and proposals with an admin‑only "Add to terminology" action. Verified: 3 tests in the 64‑test suite (insights, creator→403/no‑token→401, admin creates + idempotent), `tsc` clean, and a live end‑to‑end apply (terminology went 3→4). (PART 02.4)*
- **R2‑5 — Predictive Brand Risk Intelligence.  ✅ DONE** *Delivered: `services/risk.py` + `GET /radar/intelligence` — five explained indicators (Content / Claim / Guideline Conflict / Governance Process / Visual) as transparent, rules‑based indices over real records, each with a `rationale`, the real `drivers` (the exact counts behind the score), a `level`, and a `recommendation`, plus an overall governance‑risk score. Explicitly labelled descriptive indices over history, NOT machine‑learned forecasts. Rebuilt the Risk Radar page in glass with per‑indicator score bars, drivers and recommendations (keeping the recurring‑violations + claim‑distribution detail). Verified: 2 tests in the 60‑test suite, `tsc` clean, live walkthrough (Content 79/High, Claim 93/High, each with real rationale). (PART 02.5)*
- **R2‑6 — Content Intelligence comparison mode + live job state.** Original‑vs‑suggested diff without mutating the submission; real analysis‑job status via SSE/polling (no simulated progress) (PART 07, 10).
- **R2‑7 — ClaimDNA intelligence upgrade.  ✅ DONE** *Delivered: `GET /claim/evidence-map` — org‑wide claim→evidence relationships, each with an evidence_state that distinguishes **missing** (unsupported — no approved evidence) from **contradicted** (conflicts with an approved fact), plus source reliability and evidence freshness (Current/Outdated), derived from the real 5‑status verifications. New **Evidence Integrity Map** on the ClaimDNA page (glass): a state‑distribution bar + claim→evidence relationship rows with reliability/freshness chips and the page reference; the missing‑vs‑contradicted distinction is stated explicitly and never conflated. Verified: 1 test in the 61‑test suite, `tsc` clean, live walkthrough (1 supported, 14 contradicted, 26 missing on the demo). (PART 02.3)*
- **R2‑8 — "Monochrome Organic Glass" visual system.  🟠 PARTIAL** Glassmorphism/organic depth, strictly monochrome, accessibility‑preserving. *Delivered: the foundation + flagship — a subtle monochrome "organic glass" background layer in the authenticated shell, and a fully rebuilt **Command Center** in frosted glass matching the premium reference layout, all from real data: a Getting Started checklist (real onboarding), a Governance Pulse arc gauge (real policy coverage + Active/Draft rule list), KPI cards with real monthly sparklines, a Claim Verification Distribution segmented bar (real claim statuses), and a Live Agent Runs table (real `agent_runs`). No colour, no fabricated series/forecast. `tsc` clean + live‑verified; other pages unaffected by the background. Glass then rolled out to the **persistent chrome** (Sidebar, Header, command search bar, workspace pill) and the **contextual menus** (workspace / notifications / help / search dropdowns) — frosted translucent surfaces over the organic background on every page. Per PART 05, long‑form content and evidence panels (Brand DNA rules, Content Intelligence, ClaimDNA, etc.) are intentionally kept on **solid** surfaces for readability, not glassed. **Remaining (optional):** deeper per‑module glass accents and modal styling where it doesn't hurt legibility.*

- **R2‑AI — AI Copy Studio + no‑SDK live‑LLM path.  ✅ DONE (generative path needs a key)** A genuinely *generative* feature: rewrite marketing copy into a brand‑compliant version grounded in the org's real rules/facts/terminology, preserving intent. *Delivered: `services/copystudio.py` + `POST /copy-studio/rewrite` (+ `/status`). When a provider is configured it uses the LLM and labels the result `llm:<provider>` with the model; otherwise a deterministic rewrite applies the org's real terminology + approved pricing and is labelled `heuristic` — never presented as AI. `services/llm.py` gained a **dependency‑free HTTP Anthropic driver** (`HttpAnthropicProvider`, stdlib urllib) so Claude works even where the `anthropic` SDK can't be installed (offline); the factory uses the SDK when present, else HTTP. New `/copy-studio` page: glass before/after, cited changes, and an honest "AI live · <model>" vs "Heuristic mode — set ANTHROPIC_API_KEY" badge. Verified: 3 tests in the 58‑test suite, `tsc` clean, live walkthrough of the heuristic rewrite (superlative/comparative/price/tone corrections, all cited). **To go fully generative:** set `ANTHROPIC_API_KEY` (the app can reach api.anthropic.com) and restart — the Copy Studio and the Brand Assistant then use real Claude, with the same heuristic fallback on any failure.*

### Level 3 — architecture only, not built (do not claim as done)
Multimodal video/audio & PPTX/DOCX intelligence • Brand Drift Monitoring •
Counterfactual Simulator • Multilingual Governance • Enterprise Connector Hub
(Drive/Slack/Notion/Figma/CMS via permissioned MCP) • public Governance API •
legal/compliance certification claims.
