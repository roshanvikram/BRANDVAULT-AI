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
| Command Center | `/` | 🟡 | Live metrics + sample test trigger |
| Brand DNA Studio | `/brand-dna` | 🟠 | Rules/facts/terms display + confirm; PDF upload path present, DOCX/TXT not fully supported |
| Content Intelligence | `/content-intelligence` | ✅ | 3-panel editor/findings/evidence, verified via API |
| ClaimDNA | `/claim-dna` | ✅ | Sample test + claim statuses |
| Visual DNA Inspector | `/visual-dna` | ⛔ | **UI only** — no backend route, no OCR/CV |
| Agent Control Center | `/agent-control` | ✅ | Real persisted `agent_runs` + stats |
| Approval Hub | `/approval-hub` | 🟡 | Decision flow works; no auth gate |
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
| Visual DNA Agent | ⛔ | Not implemented |

## Infrastructure / cross-cutting (PARTS 11, 13, 17, 20, 21, 24)

| Capability | Status | Notes |
|---|---|---|
| RAG / embeddings / vector search | 🟠 | **Evidence now retrieved from `document_chunks`** (lexical token-overlap, Milestone A) with real page citations — no more hardcoded citation strings. Still no embeddings/vector search (Milestone C) |
| PostgreSQL / pgvector | ⛔ | SQLite only |
| LLM provider integration | 🔒 | Config slots exist; no calls; no keys |
| Authentication / RBAC | ⛔ | Roles are string fields; approval is forgeable |
| Tenant isolation | 🟠 | `org_id` filter only, no auth enforcement |
| Secure file upload validation | 🟠 | Upload exists; size/type hardening unverified |
| DOCX / OCR ingestion | ⛔ | pypdf only |
| Automated tests (unit/integration/E2E) | ⛔ | None present |
| Labelled evaluation dataset (PART 21E) | ⛔ | Not created |
| WebSocket/SSE live updates | ⛔ | Synchronous request/response |
| MCP server | 🟡 | File present; not re-verified this session |
| Public deployment | ⛔ | Local only |

## Data model vs PART 17 spec

Present: `organizations, brand_guidelines, document_chunks, brand_rules, approved_facts, terminology_rules, submissions, findings, claim_verifications, approval_records, revisions, brand_passports, agent_runs, audit_logs`.
Missing vs spec: `users, memberships, brand_assets, evidence_links, suggestions, tool_audit_logs, governance_insights`.
