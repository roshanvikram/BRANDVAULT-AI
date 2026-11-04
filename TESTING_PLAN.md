# TESTING_PLAN.md — BRANDVAULT AI

**Date:** 2026-11-04. This plan separates **what has actually been executed** from **what is planned**. No test is marked passed unless it was run.

---

## Automated suite (Milestone E) — EXECUTED, results below

A real `unittest` suite (also pytest-compatible) and a labelled evaluation runner now ship in the repo. Run from the repo root:
```bash
backend/venv/Scripts/python -m unittest backend.tests.test_unit backend.tests.test_integration
backend/venv/Scripts/python backend/eval/run_eval.py
```

**Unit + integration (`backend/tests/`): 28 tests, all passing.**
- Unit (E1): PBKDF2 verify; token sign/verify/tamper/expiry; TF-IDF cosine self-similarity; price-contradiction / supported-price; terminology; superlative/comparative Unsupported; ambiguous→Needs-Human-Review; expired-fact→Outdated; evidence cites a real page; findings labeled `heuristic`; clean copy scores 100; violations floor at ≥5; passport SHA-256 (64 hex) + idempotency.
- Integration (E2, TestClient): health; workspaces; analyze→fetch→apply-correction; `/rag/search`; upload type validation; `/approval/decide` 401 no-token, 403 creator-approve, 200 creator-submit, 200 reviewer-approve with forged-name ignored + passport issued, 403 cross-tenant; persistence.

**Evaluation (E4): 36 labelled cases, `backend/eval/dataset.json`.** Measured on the deterministic (LLM-free) engine:

| Metric | Value |
|---|---|
| Workflow completion | 36 / 36 |
| Micro **Precision** | **1.000** |
| Micro **Recall** | **0.860** |
| Micro **F1** | **0.925** |
| TP / FP / FN | 37 / 0 / 6 |
| Exact per-case tag match | 30 / 36 (83%) |

The 6 false negatives are honest out-of-scope limitations: reworded superlatives ("most powerful ever", "best in the universe"), an open-ended comparative ("faster than anything"), a non-price fact conflict (18-month vs approved 2-year warranty), and 2 visual cases — none detectable by the current rule engine. **The eval also surfaced and we fixed two real bugs**: a price regex matching "rs" inside words (e.g. "delive**rs** 45") and over-loose fact-keyword matching (generic words like "launch"/"offer"); precision rose from 0.925 to 1.000 after the fixes.

## 0. Earlier manual verification (live backend)

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
