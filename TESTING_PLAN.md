# TESTING_PLAN.md — BRANDVAULT AI

**Date:** 2026-11-04. This plan separates **what has actually been executed** from **what is planned**. No test is marked passed unless it was run.

---

## 0. Already executed this session (manual, live backend)

Run against `uvicorn backend.main:app` on a local port:

| # | Test | Result |
|---|---|---|
| M1 | Backend startup + table create + seed | ✅ clean startup |
| M2 | `GET /health` → healthy, db connected | ✅ |
| M3 | `POST /claim/test-sample` (NOVA case) | ✅ 6 findings, score 5/100 |
| M4 | ₹69,999 flagged CONTRADICTED vs ₹79,999 | ✅ |
| M5 | superlative + comparative claims → UNSUPPORTED | ✅ |
| M6 | `GET /passport/list` → SHA-256 passport | ✅ `BV-2026-52ED8A` |
| M7 | `GET /agent/stats` → real execution counts | ✅ 28 runs |
| M8 | `GET /radar/metrics` → aggregates | ✅ |
| M9 | Persistence (rows predate session) | ✅ |

Everything below is **planned and not yet automated** (no pytest/Playwright in the repo yet).

## A. Unit tests (pytest) — planned
- Price extraction & normalisation (`₹79,999` / `Rs. 79999` / `INR 79,999`).
- Prohibited-term matching (case-insensitive, word boundaries).
- Claim classification → correct 5-status label.
- Brand-health score calculation & floor.
- Passport SHA-256 determinism for identical content.
- (After Milestone D) permission check for approval.

## B. Integration tests (httpx / TestClient) — planned
1. Upload guideline → rules extracted/visible.
2. Confirm rules → active in Brand DNA.
3. Submit content → analysed with findings.
4. Analyse → evidence attached from chunks (post Milestone A1).
5. Evidence → ClaimDNA statuses correct.
6. Findings → suggested corrections present.
7. Apply correction → re-analysis reflects change.
8. Submit → approval decision persisted.
9. Approval → passport generated.

## C. End-to-end (Playwright) — planned
Scenarios 1–10 from the brief: create/confirm brand; clean content → no false critical; unsupported claim detected; wrong price → contradiction; apply correction → reanalyse; revision requested → resubmit; approve → passport; refresh → persists; **unauthorised approval rejected** (needs Milestone D); **cross-tenant access denied** (needs Milestone D).

## D. UI testing — planned
Every nav link, button, form, upload, loading/empty/error state, modal, responsive breakpoint, and a zero-console-error check per route.

## E. Evaluation dataset — planned (PART 21E)
30–50 labelled cases across: supported/unsupported/contradicted claims, correct/incorrect prices, outdated facts, tone & terminology violations, conflicting rules, visual violations. Report **measured** precision / recall / FP / FN / evidence-attribution quality / workflow completion. No metric is to be reported before the harness runs.

## How to run (once implemented)
```bash
cd backend && venv/Scripts/python -m pytest        # A, B
cd frontend && npx playwright test                  # C, D
backend/venv/Scripts/python eval/run_eval.py        # E
```
