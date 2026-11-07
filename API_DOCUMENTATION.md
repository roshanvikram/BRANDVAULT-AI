# API_DOCUMENTATION.md — BRANDVAULT AI

**Generated from the live FastAPI app** (`app.openapi()`) on 2026-11-04. This is the **actual** contract, which differs from the aspirational endpoint list in the master brief (PART 18). Interactive docs: `http://127.0.0.1:8000/docs`.

- **Base URL:** `http://127.0.0.1:8000`
- **API prefix:** `/api/v1`
- **Auth (Phase 1a, 2026-11-07):** every organisation-scoped endpoint requires `Authorization: Bearer <token>` from `/auth/login` (401 without it). Public: `/auth/login`, `/auth/register`, `/auth/google/*`, `/health`, `/copy-studio/status`, `/twin/suggestions`.
- **Tenant scope:** the organisation comes from the token. `org_id` parameters are optional; if sent and different from the caller's org the API returns **403**. Other orgs' submissions, jobs and passports return 403/404.
- **Roles:** Brand DNA writes (`POST /brand/rules`, `POST /brand/facts`, `PATCH /brand/rules/{id}/confirm`, `POST /brand/guidelines/upload`, `POST /brand/workspaces`) and `POST /memory/apply-terminology` are **Administrator-only** and audit-logged. Approve/Reject/Revision on `/approval/decide` need Reviewer or Administrator.
- **Version-locked approvals:** `/approval/decide` accepts `expected_version`; a stale version returns **409**. Any content change creates a new version, resets status to `Analysed`, and marks an existing passport `SUPERSEDED`. Approval records store `submission_version` + `content_hash`.
- **Async jobs:** `POST /content/analyze-async` (optional `Idempotency-Key` header) → `GET /content/jobs/{id}` → `POST /content/jobs/{id}/cancel` (queued only, else 409). Status values: `queued`, `processing`, `completed`, `failed`, `cancelled`; state is stored in the `jobs` table.
- **Rate limits:** `/auth/login` + `/auth/register` (`RATE_LIMIT_AUTH_PER_MIN`, default 20/min/IP) and `/content/analyze*`, `/copy-studio/rewrite`, `/twin/ask` (`RATE_LIMIT_AI_PER_MIN`, default 30/min/IP) → 429 with `Retry-After`.
- **Demo orgs:** `nova-tech-org-001` (NOVA TECH) and `vortexa-tech-org-002` (VORTEXA), seeded on startup; each demo user belongs to one.
- **Demo accounts** (judging workspace only, not production): `admin@novatech.demo` / `Admin@2026` (Administrator), `creator@novatech.demo` / `Creator@2026` (Creator), `reviewer@novatech.demo` / `Reviewer@2026` (Reviewer).

## Authentication
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/auth/login` | `{email, password}` → `{access_token, token_type, user}` |
| GET | `/api/v1/auth/me` | Current user (requires bearer token) |

---

## Root & health
| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Product/team metadata, status banner |
| GET | `/api/v1/health` | Liveness + DB connectivity |

## Brand DNA
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/brand/workspaces` | List organisations (with counts) |
| POST | `/api/v1/brand/workspaces` | Create an organisation |
| GET | `/api/v1/brand/guidelines?org_id=` | List uploaded guideline documents |
| POST | `/api/v1/brand/guidelines/upload` | Upload a guideline (multipart: `org_id`, `file`) — PDF parsed via pypdf |
| GET | `/api/v1/brand/rules?org_id=&category=` | List brand rules |
| POST | `/api/v1/brand/rules` | Create a brand rule |
| PATCH | `/api/v1/brand/rules/{rule_id}/confirm` | Admin-confirm an extracted rule |
| GET | `/api/v1/brand/facts?org_id=` | List approved facts |
| POST | `/api/v1/brand/facts` | Create an approved fact |
| GET | `/api/v1/brand/terms?org_id=` | List terminology rules |

## Content Intelligence
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/content/analyze` | Analyse content → findings + claim verifications + score |
| POST | `/api/v1/content/apply-correction` | Apply a suggested fix and re-analyse |
| GET | `/api/v1/content/submissions?org_id=` | List submissions |
| GET | `/api/v1/content/submissions/{submission_id}` | Submission detail |

**`POST /content/analyze`** request:
```json
{ "org_id": "nova-tech-org-001", "title": "Launch copy", "content": "…", "author_name": "Creator", "submission_id": null }
```
Returns a `Submission` with `findings[]` (category, severity, original_text, explanation, `rule_reference`, `evidence_source`, confidence, suggested_correction) and `claim_verifications[]`.

## ClaimDNA
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/claim/test-sample` | Run the built-in NOVA TECH acceptance case |
| GET | `/api/v1/claim/verifications?submission_id=` | Claim verifications for a submission |

**Claim statuses** (all reachable): `Supported`, `Unsupported`, `Contradicted`, `Outdated`, `Needs Human Review`.
- `Contradicted` — approved evidence conflicts (e.g. wrong price).
- `Unsupported` — no approved evidence (e.g. "world's fastest").
- `Outdated` — the matched approved fact has a `valid_until` in the past.
- `Needs Human Review` — ambiguous marketing language, or a price with no approved pricing record.
Each verification carries `evidence_text` + `source_reference` **retrieved from `document_chunks`** (real page citation), or `null` when no passage was retrieved.

## Approval (human-in-the-loop)
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/approval/decide` | **Requires bearer token.** Record Approved / Rejected / Revision Requested (+ comments). On approval, generates a Brand Passport |
| GET | `/api/v1/approval/history/{submission_id}` | Decision history |
| GET | `/api/v1/approval/revisions/{submission_id}` | Revision history |

> 🔒 **Gated (Milestone D).** `/approval/decide` needs a valid token. Only **Reviewer/Administrator** may issue authoritative decisions (Approved/Rejected/Revision Requested); **Creator** may only submit for review (`Pending Review`). The decision is attributed to the authenticated user (client-supplied names ignored), and the caller's org must match the submission's (cross-tenant → 403). No token → 401.

## Brand Passport
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/passport/list` | All issued passports |
| GET | `/api/v1/passport/by-submission/{submission_id}` | Passport for a submission |
| GET | `/api/v1/passport/{passport_number}` | Passport by number (e.g. `BV-2026-52ED8A`) |

## Agent Control Center
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/agent/runs?limit=` | Persisted agent execution events |
| GET | `/api/v1/agent/stats` | Totals + `average_latency_ms` (µs-precision) + per-agent distribution |

## Visual DNA
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/visual/analyze` | Multipart (`org_id`, `file`). Measured colour-palette/contrast analysis of a PNG/BMP; persists a Visual submission with findings |

Returns `{submission, format, dimensions, metrics, ocr}`. `metrics` are measured (chromatic/monochrome fraction, contrast, dominant palette). JPEG/WebP/SVG → **415** (not analysed here). `ocr.available` is `false` — OCR is an unavailable seam, never fabricated.

## RAG Retrieval
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/rag/search` | Hybrid (TF-IDF cosine + keyword) retrieval over org-isolated guideline chunks |

**`POST /rag/search`** request: `{ "query": "launch price", "org_id": "nova-tech-org-001", "top_k": 3 }`
Returns ranked passages with real page citations and `score`/`cosine`/`keyword` components, plus the `embedder` name (`tfidf`). Statistical embedding, not neural — see FEATURE_STATUS.md.

## Risk Radar
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/radar/metrics?org_id=` | Aggregated governance analytics from stored records |

---

## Reconciliation with PART 18 (brief) — honesty note
The brief lists endpoints like `/api/analyse/text`, `/api/copilot/chat`, and review routes under `/api/reviews/...`. Those paths **do not exist**; the equivalent real capabilities are `/content/analyze`, no copilot chat, and approval under `/approval/decide`. RAG is now exposed at `/api/v1/rag/search` (Milestone C) and is also used internally by analysis. Visual analysis is at `/api/v1/visual/analyze` (Milestone F) rather than `/analyse/image`. These gaps are tracked in FEATURE_STATUS.md.
