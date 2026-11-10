# BRANDVAULT AI — Round 3 Testing Notes

All numbers below were measured on the final code. Commands are run from the repository root.

## 1. Automated test suite — 244 tests

```
backend/venv/Scripts/python -m unittest discover -s backend/tests -t .
```

| Area | Tests |
|---|---|
| Integration (end-to-end API, RBAC) | 33 |
| Phase 1 engines (Product Truth, gaps, fingerprint, forensics) | 29 |
| Translation Guard | 21 |
| Phase 3 intelligence (stress test, similarity, fraud, reputation) | 20 |
| Phase 2 governance | 19 |
| Phase 1a security (tenancy, versions, durable jobs) | 19 |
| Unit (analyzer, claims, hashing, retrieval) | 18 |
| Claim detectors (prices, superlatives, comparisons, specs, tone) | 7 |
| Fixes found by the input library (OCR digits, Hindi negation, language labels, copy rewrite) | 8 |
| **Round 3 · Improvement 3** — ingestion, ranking, dense, pgvector, versions, gap agent | 14 |
| **Round 3 · Improvement 2** — API keys, Check API, gate, webhooks, notifications, channels, MCP | 13 |
| **Round 3 · Improvement 1** — OCR fixes, clear space, image/PDF/video, isolation, settings | 11 |
| Visual DNA | 10 |
| **Round 3 foundation** — file store, migrations, demo-account switch | 5 |
| Demo content seed | 5 |
| Configuration | 5 |
| **Round 3 end-to-end workflow** (one test, every step) | 1 |
| Keep-awake, storage flag, AI suggestions and retry | 6 |
| **Total** | **244** |

Results:
- **SQLite:** 244 run, all pass (1 skipped: the pgvector-only test).
- **PostgreSQL 18 + pgvector** (`BV_TEST_DATABASE_URL=postgresql://…`): 223 run, all pass (the pgvector test runs here too). Measured before the 21 newest tests were added; those are pure text tests with no database.

The end-to-end test walks the whole product:
1. A Word guideline is uploaded and an admin confirms the extracted rule.
2. The creator's copy with a wrong price is flagged as contradicted.
3. The same wrong price inside a banner image is caught.
4. Readiness never approves on its own; the creator cannot approve their own copy.
5. A reviewer approves and a Brand Passport is issued.
6. The passport verifies, and the publishing gate allows the exact copy and blocks an edited copy.
7. Every step fires a signed webhook.

## 2. Analyzer evaluation (text) — tested on 50 real-world inputs

Full write-up: `submission/REALWORLD_TEST_RESULTS.md`.

| Dataset | Cases | Precision | Recall | F1 | Exact match |
|---|---|---|---|---|---|
| Real-world set, **before** fixes (`realworld_dataset.json`) | 50 | 0.923 | 0.545 | 0.686 | 29/50 |
| Real-world set, after fixes | 50 | 1.000 | 1.000 | 1.000 | 50/50 |
| Fresh hold-out, scored once (`realworld_holdout.json`) | 20 | 1.000 | 1.000 | 1.000 | 20/20 |
| Original set (`dataset.json`) | 36 | 1.000 | 0.953 | 0.976 | 34/36 |

The only remaining misses on the original set are its 2 "visual" cases (logo colour, packaging). These are image checks that Creative Inspection and Visual DNA handle, and this harness only feeds text.

## 2b. Input library — 893 files through the real API

`inputs/` holds 893 realistic files, at least 50 per feature, across 14 folders: copy, claims, banners/PDFs/videos, images, guideline documents, translations, rewrites, questions, feedback exports, fraud reports, channel payloads, logo assets, passport checks and similarity texts. Each folder's `manifest.csv` states the expected result. `inputs/_generator/verify.py` runs every file through the HTTP API.

| Folder | First run | After fixes |
|---|---|---|
| Copy Studio (rules mode) | 7/60 | 60/60 |
| Translation Guard | 54/75 | 75/75 |
| Brand Assistant | 48/60 | 60/60 |
| Fraud Intelligence | 48/60 | 60/60 |
| Creative Inspection | 54/60 | 60/60 |
| The other 9 folders | all matched | all matched |
| **All 14 folders** | | **893/893** |

The text and creative evaluations were re-run afterwards and are unchanged: real-world text 50/50, hold-out 20/20, creatives 26/26 and 12/12.

Product problems found and fixed:
- **Translation Guard:**
  - Hindi words containing "मत" or ending in "न" were read as negations.
  - Short French text was detected as Spanish; the translation's language label is now used.
  - Renamed model names ("NovaCore N10" → "Nova Core N1") were not caught.
- **Copy Studio (rules mode)** fixed only 7/60 off-brand texts. It now corrects specs, superlatives, comparisons, expired offers, vague claims and hype: 60/60.
- **Brand Assistant** answered off-topic questions (stock price, next year's plans) with loosely related passages. It now declines them.
- **Fraud Intelligence:**
  - The official shop's accessory price was flagged as a wrong laptop price.
  - "We never ask for your OTP" was flagged as an OTP request.
- **Creative Inspection OCR:**
  - "1ox" was read in place of "10x", which hid a banned claim.
  - "75,0o0" hid a price.
  - A ₹ symbol was dropped after "alert:".

## 2c. With the AI model on (as on the live site)

`run_eval.py realworld_dataset.json --llm` uses the configured model (Groq, `openai/gpt-oss-120b`).
- **First run:** recall 1.00, precision 0.92. 4 clean texts were flagged by the model, for example "Hi Priya, thanks…" for tone. Many calls also failed with HTTP 429 (free-tier rate limit) and fell back to rules only.
- **Fixes:**
  - AI-only findings are now *suggestions for the reviewer* (severity SUGGESTION, small score effect).
  - Findings whose quote is not in the copy are dropped.
  - Groq 429/503 replies are retried up to twice, waiting at most 8 s.
- **After fixes:** 50/50 exact, precision 1.00, recall 1.00, 14/14 clean texts pass, 0 failed calls.

## 3. Creative Inspection evaluation (Improvement 1)

`backend/eval/run_creative_eval.py` (dataset `creative_dataset.json`) and `run_creative_eval.py creative_holdout.json`.

| Set | Creatives | Issue precision | Issue recall | F1 | Exact issue set | OCR character accuracy |
|---|---|---|---|---|---|---|
| Main | 26 (9 PNG, 5 JPEG, 3 WebP, 3 text PDF, 3 scanned PDF, 3 video) | 1.000 | 1.000 | 1.000 | 26/26 | 0.997 |
| Held-out | 12 | 1.000 | 1.000 | 1.000 | 12/12 | 0.995 |

Average time per creative: image 2.6–3.6 s, text PDF 0.1–0.2 s, scanned PDF about 3.2 s, video about 12 s, on a laptop CPU.

**Read this honestly:**
- **Synthetic set:** all creatives are generated (clean rendered text on plain backgrounds), so real photos, busy backgrounds or stylised fonts will score lower.
- **Tuning:** the OCR fixes (2× upscaling of small images, ₹ restoration, word splitting) were tuned on the main set. That is why a separate held-out set was written afterwards and run once without changes.
- **First-run problems:** before these fixes, the main set scored recall 0.86. The missed cases had a dropped ₹ symbol and run-together words.

## 4. Retrieval evaluation (Improvement 3)

`backend/eval/run_retrieval_eval.py` — an authored guideline corpus of 36 passages and 40 labelled queries (9 exact-term, 31 paraphrase).

| Method | Recall@1 | Recall@3 | MRR | Paraphrase R@3 | Exact R@3 |
|---|---|---|---|---|---|
| Round 2 (TF-IDF + keyword) | 0.500 | 0.675 | 0.575 | 0.581 | 1.000 |
| Hybrid, no dense (BM25 + TF-IDF) | 0.500 | 0.675 | 0.575 | 0.581 | 1.000 |
| **Hybrid with dense (BGE-small)** | **0.625** | **0.825** | **0.717** | **0.774** | **1.000** |

How these numbers were reached:
- **Dense threshold (cosine ≥ 0.62):** set from 12 unrelated queries (highest similarity 0.603), not from the labelled queries.
- **Fusion design:** first measured as three equal votes (R@3 0.775), then changed to lexical-vs-dense on principle (TF-IDF and BM25 are correlated), which gave 0.825.
- **Remaining misses:** 7 paraphrases, e.g. "how much does the laptop cost", "release date".

## 5. Manual checks in the browser
- **Creative Inspection:** a banner drawn on a canvas and uploaded through the real API. The price contradiction, the superlative, the "Al"→"AI" fix and the restored ₹ were all shown, and the boxes landed on the right lines.
- **Settings:** engine status (SQLite, OCR on, BGE-small hybrid on, email not configured, demo sign-ins on), API keys (create/revoke) and webhook UI.
- **Publishing page:** a 231-character post was checked against X and Instagram. It fit both channels, flagged the missing price T&C and EMI disclosure, and accepted the battery wording.
- **Notification bell:** showed the real "Publishing blocked: New Unapproved Campaign" event from the MCP test.
- **MCP:** a real stdio session with the official MCP client listed 5 tools. `check_copy` found 5 issues without saving anything, `check_publish_gate` blocked unapproved copy, and `get_brand_profile` returned NOVA TECH. The test key was revoked afterwards.
- **Builds:** the production frontend build passed (37 pages), and the TypeScript check is clean.
- **Memory:** about 300 MB with the app, OCR and the embedding model loaded (Render free plan limit is 512 MB).

## 6. Known gaps (not hidden)
- **Cross-encoder reranker:** not built (memory budget).
- **PostgreSQL row-level security:** not added; tenant isolation is app-level and tested.
- **Live site still on SQLite:** it switches to persistent PostgreSQL when the team adds a Neon `DATABASE_URL` (steps in `DEPLOYMENT.md` §9).
- **Email notifications:** need SMTP settings.
- **Creative accuracy:** measured on synthetic creatives only.
- **PostgreSQL test run:** PostgreSQL test runs use PGlite (PostgreSQL 18 compiled to WebAssembly) locally, which multiplexes connections into one session. Two fixes came from this: a test no longer holds a session open across an API call, and synchronous (test-mode) webhook delivery reuses the caller's session. In production, deliveries run on their own thread and session, which is normal on real PostgreSQL.
- **Final PostgreSQL result:** 223/223 pass. One earlier full run showed a single set-up error in the Visual DNA tests (a table missing at sign-in); it did not reproduce in isolation or in the next full run, and is attributed to state left in the shared test database by an interrupted run.
