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

## Round 3 endpoints
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/capabilities` | Which optional engines are live (OCR, embeddings, pgvector, email) |
| GET | `/api/v1/creative/status` | OCR engine status and limits |
| POST | `/api/v1/creative/inspect` | Multipart `file` (image/PDF/video), optional `department` → pages, OCR lines, corrections, regions, logo clear space, submission with findings |
| GET | `/api/v1/creative/inspections[/{id}]` · `/creative/inspections/{id}/pages/{n}/image` | History, detail, page image for the overlay |
| GET / PUT | `/api/v1/workspace/settings` | Org settings (clear-space ratio, channels, disclaimers, notifications); PUT is Admin-only and validated |
| GET / POST / DELETE | `/api/v1/integrations/api-keys[/{id}]` | Admin: list, create (key shown once), revoke |
| GET / POST / DELETE | `/api/v1/integrations/webhooks[/{id}]` · POST `/{id}/test` · GET `/integrations/deliveries` | Admin: signed webhooks and the delivery log |
| GET | `/api/v1/notifications` · POST `/notifications/read` | In-app notifications for the user's role; mark read |
| POST | `/api/v1/channels/check` | `{text, channels[], region?, width?, height?}` → Channel Adapter + Disclaimer agent |
| POST | `/api/v1/public/check` | `X-API-Key` (scope `check`): brand checks; `persist:false` saves nothing |
| POST | `/api/v1/public/gate` | `X-API-Key` (scope `gate`): `{allowed}` only for copy identical to a current Brand Passport |
| GET / POST | `/api/v1/public/brand` · `/public/search` · `/public/submissions/{id}` | `X-API-Key` (scope `read`): brand facts, evidence search, review status |
| POST | `/api/v1/brand/guidelines/upload` | Now accepts .pdf .docx .html .md .txt .csv .xlsx; optional `replaces` (older guideline id) |

Webhook signature: `X-BrandVault-Signature: sha256=HMAC_SHA256(secret, X-BrandVault-Timestamp + "." + body)`.

## Advanced intelligence (Phase 3)
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/simulation/scenarios` | Available what-if scenarios |
| POST | `/api/v1/simulation/run` | `{submission_id, scenario, params}` → original vs simulated findings, score change, Product Truth changes, translation check, recommendations (422 when the scenario can't be simulated honestly) |
| GET | `/api/v1/simulation/runs` | Saved hypothetical runs |
| POST | `/api/v1/similarity/check` | `{text}` or `{submission_id}` (excludes itself and its passport) → near-duplicates, similar campaigns, reused sentences |
| GET | `/api/v1/similarity/clusters` | Groups of repeated campaigns |
| POST | `/api/v1/similarity/dismiss` · `/restore` | `{pair_key, reason}`: hide or restore a pair (reason recorded) |
| POST | `/api/v1/similarity/image` | Multipart image → similar official assets (pHash) |
| GET | `/api/v1/fraud/domains` | Official domains; POST / DELETE `/fraud/domains[/{id}]` are Admin-only |
| POST | `/api/v1/fraud/investigate` | Multipart `url`, `text`, `file` → opens an incident with risk, confidence, signals, recommended response |
| GET | `/api/v1/fraud/incidents` · `/fraud/incidents/{id}` · `/fraud/incidents/{id}/evidence` | Incident list, detail, preserved screenshot |
| POST | `/api/v1/fraud/incidents/{id}/status` | Reviewer/Admin: `{status, note}` appended to history |
| POST | `/api/v1/reputation/upload` | Reviewer/Admin: CSV/JSON feedback (≤ 5 MB) |
| POST | `/api/v1/reputation/feedback` | Add one record; GET lists records |
| GET | `/api/v1/reputation/overview?days=` | Sentiment, categories, phrases, products, campaign disputes, trend, early warnings |
| DELETE | `/api/v1/reputation/batches/{id}` | Admin: remove an upload batch |

## Governance intelligence (Phase 2)
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/launch/checks` | The 12 checks, which are mandatory, approval validity |
| PUT | `/api/v1/launch/config` | Admin: `{mandatory: [...], approval_validity_days}` |
| POST | `/api/v1/launch/{submission_id}/check` | Run and persist a readiness report (state, checks with evidence, routing, unresolved findings) |
| GET | `/api/v1/launch/{submission_id}/reports` | Readiness history |
| GET | `/api/v1/governance/lifecycle` | Lifecycle items, counts, alerts, campaigns using outdated information |
| GET | `/api/v1/analytics/consistency` | Filters: `date_from`, `date_to`, `product`, `department`, `category`, `severity` → KPIs, heatmaps, compliance, trends |
| GET | `/api/v1/governance/reviewer-intelligence` | Decision patterns, recommendations, turnaround, queue |
| POST | `/api/v1/governance/reviewer-intelligence/propose` | Admin: create an unconfirmed draft rule |

## Product Truth & Knowledge Gaps
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/products` | Products with facts (status, source, page, excerpt), attribute list, whether AI extraction is available |
| POST | `/api/v1/products/verify` | `{text}` → per-claim status, submitted vs approved value, source document, page, excerpt, suggestion |
| POST | `/api/v1/products` | Admin: create product |
| POST | `/api/v1/products/{id}/facts` | Admin: add an approved fact (supersedes the previous value for that attribute) |
| POST | `/api/v1/products/facts/{id}/approve` · `/reject` | Admin: decide on a pending (AI-proposed) fact |
| POST | `/api/v1/products/extract` → GET `/api/v1/products/extract/{job_id}` | Admin: background AI extraction from guidelines (503 if no AI model) |
| GET | `/api/v1/products/knowledge-gaps` | Completeness, prioritised gap items with evidence and actions, product coverage matrix, recommended documents |

## Campaign integrity
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/passport/verify` | multipart `text` or `file` (.txt/.md; images return Unable to Verify) → result, similarity, word diff, fingerprint |
| GET | `/api/v1/passport/integrity-checks` | Append-only verification log |
| GET | `/api/v1/passport/{number}/fingerprint` | Fingerprint of one passport |

## Brand Asset Library & Forensics
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/assets` | Library with status, current flag, hashes, colours, recommended replacement |
| POST | `/api/v1/assets` | Admin: multipart upload (`file`, `name`, `kind`, `version_label`, optional `supersedes_id`) |
| POST | `/api/v1/assets/{id}/status` | Admin: change status (e.g. archived) |
| GET | `/api/v1/assets/{id}/file` | Official file (same organisation only) |
| POST | `/api/v1/assets/investigate` | multipart `file` → risk, matches, located logo polygon/bbox, measured modifications, findings |
| GET | `/api/v1/assets/investigations[/{id}[/file]]` | Investigation history and preserved evidence |

## Translation Guard
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/translation-guard/languages` | Detected languages, languages with qualifier/negation checks, whether AI is available (public) |
| POST | `/api/v1/translation-guard/analyze` | `{title, source_text, translations:[{label?, text}] (1-8, ≤5000 chars each), use_ai}` → campaign with per-translation verdict, scores, findings, figures table, corrected translation. Auth + AI rate limit |
| GET | `/api/v1/translation-guard/campaigns` | Recent campaigns for the caller's organisation |
| GET | `/api/v1/translation-guard/campaigns/{id}` | One campaign (404 for other organisations) |

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
