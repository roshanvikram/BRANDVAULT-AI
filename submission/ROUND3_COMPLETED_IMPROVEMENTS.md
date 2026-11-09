# BRANDVAULT AI — Round 3 Completed Improvements

Team Deal Dynamos · promised in the Round 2 report (section 08) vs delivered.
Every "Delivered" item runs in the product and is covered by automated tests; measured results are in `ROUND3_TESTING_NOTES.md`.

## Improvement 1 — Multimodal Creative Inspection

| Promised in Round 2 | Delivered | Evidence |
|---|---|---|
| OCR with bounding boxes for PNG, JPEG, WebP and PDF pages | ✅ RapidOCR (PaddleOCR models on ONNX Runtime, CPU, pip-only). PDFs use the exact text layer and fall back to OCR for scanned pages | `services/ocr.py`, `services/creative.py`, `tests/test_creative.py` |
| Extracted text flows into ClaimDNA, Product Truth and Terminology | ✅ The recovered text is analysed by the same engine as typed copy and creates a normal submission | Creative Inspection page → "Open in Content Intelligence" |
| Logo clear-space and placement rules | ✅ Logos are located with Asset Forensics; empty margin is measured against an Admin-set ratio, including text intruding into the clear zone | Settings → Workspace; `clear_space()` unit test |
| Region overlays on the creative | ✅ Every finding and claim is boxed on its page; click a finding to highlight it | `/visual-dna/creative` |
| Video and deck support | ✅ Up to 10 PDF pages; 6 key frames sampled from MP4/WebM/MOV | `test_scanned_pdf_and_video_use_ocr` |
| Labelled set of 25+ creatives with measured accuracy | ✅ 26-creative set + 12-creative held-out set | `eval/run_creative_eval.py` |
| Close the 2 visual misses in the Round 2 evaluation | ⚠️ Partly. Visual text is now checked (Creative eval), but the Round 2 text evaluation (`run_eval.py`) still scores its 2 "visual" cases as misses because that harness only feeds text | Stated in testing notes |

Extra (not promised): brand-vocabulary OCR correction (l/I, 0/O, run-together words) and ₹ restoration, each listed for the reviewer; Visual DNA now accepts JPEG/WebP.

## Improvement 2 — Publishing Gate & Channel Integrations

| Promised | Delivered | Evidence |
|---|---|---|
| Public Check API with per-organisation API keys | ✅ Hashed keys with scopes (check, gate, read), shown once, revocable, usage counted | Settings → API keys; `test_integrations.py` |
| Signed webhooks (analysis complete, approved, passport revoked) | ✅ HMAC-SHA256 signed, 3 attempts, delivery log, test button. Events: analysis.completed, review.decided, passport.issued, passport.superseded, publish_gate.blocked, incident.opened | Settings → Webhooks |
| Publishing gate that refuses copy without a valid passport | ✅ `POST /public/gate` allows only copy identical to a current Brand Passport; edits and unapproved copy are blocked, logged and reviewers notified | `test_publish_gate_end_to_end_and_webhook_signature` |
| Channel Adapter agent | ✅ Character limits, aspect ratios and required elements per channel, editable by Admins | `/approval-hub/publishing` |
| Regulatory disclaimer agent | ✅ Region- and trigger-based mandatory wordings (price T&C, EMI disclosure, battery test conditions), editable by Admins | same |
| Full MCP transport | ✅ Real MCP server on the official SDK 2.x (stdio), 5 read-only tools, API-key scoped; verified with a real MCP client session | `backend/mcp_server.py` |
| Slack / email notifications | ✅ In-app notification centre (real events, role-filtered, read state); Slack and email copies when configured — email needs SMTP settings, otherwise labelled "not configured" | Header bell; Settings → Notifications |
| 100% of unauthorised API/MCP calls blocked | ✅ Tested: missing key, revoked key, wrong scope, other organisation's data | `test_scopes_enforced`, `test_tenant_isolation_for_keys_and_submissions` |

## Improvement 3 — Semantic Evidence Engine on PostgreSQL + pgvector

| Promised | Delivered | Evidence |
|---|---|---|
| Dense embeddings in pgvector with HNSW, fused with BM25 via RRF | ✅ BGE-small embeddings (local, no API key; or any OpenAI-compatible API); BM25 + TF-IDF fused, then RRF with dense; native pgvector table + HNSW index on PostgreSQL | `services/rag.py`, `services/embeddings.py`; pgvector test on PostgreSQL 18 |
| Optional cross-encoder reranker | ❌ Not built (memory budget on the free host); listed as a limitation | — |
| New ingestion formats: DOCX, HTML, spreadsheets | ✅ PDF, DOCX, HTML, Markdown/text, CSV, XLSX with page / section / row citations; ~600-character sentence-aligned passages | `services/ingest.py`, `test_retrieval.py` |
| Multi-hop evidence across document versions | ✅ (scoped) Uploading a new version retires the old document: it stays on record but is no longer cited, and facts/rules taken from it are flagged for re-confirmation | `test_replacing_a_document_retires_it_and_flags_conflicts` |
| Guideline Gap Agent made real | ✅ Finds product values that disagree across current documents (negated sentences such as "never advertise ₹69,999" are ignored) | Knowledge Gap Detector |
| Live deployment on managed PostgreSQL with RLS; demo accounts removable | ⚠️ PostgreSQL support built and tested (full suite on PostgreSQL 18); deployment steps for Neon written. Switching the live site to Neon needs the team's Neon connection string. Row-level security not added (tenant isolation remains app-level, tested). Demo sign-ins can be disabled with `DEMO_ACCOUNTS_ENABLED=false` | `DEPLOYMENT.md` §9 |
| Recall above 0.86 with precision near 1.00 | ✅ Analyzer evaluation unchanged at precision 1.00 / recall 0.86 (it does not depend on retrieval ranking); retrieval itself improved — recall@3 0.675 → 0.825 | Testing notes |

## Round 2 bugs and gaps fixed

| Issue | Fix |
|---|---|
| PostgreSQL would have crashed at startup (SQLAlchemy 2.1 needs psycopg 3; requirements shipped psycopg2) | Driver changed; full suite runs on PostgreSQL |
| Brand Passport failed on PostgreSQL (guideline version longer than its 50-character column; SQLite never enforced it) | Column widened |
| Uploaded files lost on every Render restart | Files stored in the database |
| Migrations were SQLite-only | Portable additive migrations |
| Visual DNA flagged colour against a "monochrome rule" no organisation had, and named NOVA TECH for every brand | Colour is judged only against a confirmed palette rule of that organisation |
| Visual DNA rejected JPEG/WebP | Supported |
| PDFs became one passage per page (coarse citations) | Sentence-aligned passages |
| Guideline upload failures were silent in the UI | Error shown |
| Settings page showed "CONNECTED" even when the health call failed | Rebuilt; shows measured engine status |
| Notification bell was derived from submissions, not events | Real event-driven notifications |
| Old MCP script read the database directly and defaulted to the NOVA organisation without any key | Replaced by an API-key-scoped, read-only MCP server |
| Free-plan cold start looked like a broken site | "Waking up the server" banner |
| Malformed .docx crashed the upload (500) | Clear 422 message |
