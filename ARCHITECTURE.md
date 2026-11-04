# ARCHITECTURE.md — BRANDVAULT AI

**Date:** 2026-11-04. Describes the system **as built**.

## 1. Shape

A **modular monolith**: a Next.js frontend talking over REST to a single FastAPI backend, which owns all business logic and a SQLite database. This is the right choice for the hackathon scope — no microservices overhead.

```
┌─────────────────────────────┐        HTTP/JSON        ┌──────────────────────────────┐
│  Next.js 14 (App Router)    │  ───────────────────▶   │  FastAPI backend (modular)     │
│  frontend/src/app/*         │   NEXT_PUBLIC_API_URL    │  backend/app/api/v1/*          │
│  lib/api.ts (typed client)  │  ◀───────────────────   │  services/ analyzer, passport  │
└─────────────────────────────┘                         │  models/ (SQLAlchemy ORM)      │
                                                         │  SQLite: brandvault.db         │
                                                         └──────────────────────────────┘
                                                                        │
                                                         backend/mcp_server.py (MCP tools)
```

## 2. Backend layering

- `backend/main.py` — app factory, CORS, lifespan hook that **creates tables and seeds NOVA TECH** on startup.
- `app/core/config.py` — Pydantic settings (DB URL, CORS, optional AI keys).
- `app/db/` — `base.py` (declarative Base), `session.py` (engine, `get_db` dependency).
- `app/models/` — `brand.py`, `submission.py`, `passport.py` (ORM tables).
- `app/schemas/` — Pydantic request/response models (validation boundary).
- `app/api/v1/` — 8 routers: `health, brand, content, claim, approval, passport, agent, radar`.
- `app/services/` — `analyzer.py` (the analysis engine), `passport_service.py`, `seed.py`.

## 3. The analysis engine (`services/analyzer.py`)

This is the product's core. It is a **deterministic, explainable rule engine**, executed as a sequence of named "agents" that each persist an `AgentRun` event:

1. **Terminology Agent** — regex match of stored prohibited terms → CRITICAL findings with the stored preferred term as the correction.
2. **Brand Voice Agent** — exclamation-mark density heuristic → tone WARNING.
3. **ClaimDNA Agent** — extracts prices (`₹/Rs/INR`) and compares to the approved pricing fact (CONTRADICTED on mismatch, SUPPORTED on match); regex-detects superlative and comparative claims → UNSUPPORTED.
4. **Suggestion Agent / Orchestrator** — computes a deterministic brand-health score (`100 − weighted deductions`, floored at 5), attaches findings/claims, writes an `AuditLog`, commits.

**Design honesty:** the output is reproducible and every finding carries a `rule_reference`, `evidence_source`, and `confidence`. The weakness is that some `evidence_source`/`rule_reference` strings are **hardcoded literals** rather than read from the matched `DocumentChunk`. The seeded chunks' page numbers are consistent with those literals, so citations are *grounded* but not *dynamically retrieved*. Fixing this (retrieve from chunks) is the top RAG task.

## 4. Data flow — content analysis

```
POST /content/analyze {org_id,title,content}
  → ContentAnalyzerService.analyze_submission
      → load org + active rules/facts/terms + chunks
      → run agents, build Finding[] + ClaimVerification[]
      → persist Submission, Findings, Claims, AgentRuns, AuditLog
  ← SubmissionResponse (findings, claims, score)
```

Approval → passport:
```
POST /approval/decide → persist approval_records + revision
  → if approved/conditionally passed → passport_service builds SHA-256 hash → brand_passports row
GET /passport/by-submission/{id} → report page
```

## 5. Frontend

App Router pages under `frontend/src/app/<module>/page.tsx`, shared layout in `components/layout/` (Sidebar, Header, RightActivityPanel) implementing the three-column enterprise shell. All server data flows through the typed client in `lib/api.ts`. The design system is the strict monochrome palette in `tailwind.config.ts` + `globals.css`.

## 6. Known architectural gaps

- No auth/session layer → no real RBAC or tenant isolation (only `org_id` query filtering).
- No async job queue → analysis is synchronous (fine at current latencies; blocks on a real LLM).
- No embedding/vector store → retrieval is rule-based.
- SQLite → single-writer; migrate to Postgres for concurrency + pgvector.

## 7. Intended production target (not yet built)

Vercel (frontend) + Render/Fly (backend) + managed Postgres w/ pgvector + object storage for uploads. See `DEPLOYMENT.md` (to be authored) and `IMPLEMENTATION_ROADMAP.md`.
