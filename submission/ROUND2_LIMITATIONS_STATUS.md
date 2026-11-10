# Round 2 limitations: status after Round 3

All twelve limitations listed in the Round 2 report were rechecked against the code. Results are measured; commands are in `submission/ROUND3_TESTING_NOTES.md`.

| # | Round 2 limitation | Status | What exists now | Evidence |
|---|---|---|---|---|
| 1 | No OCR | ✅ Done | Text read from images, scanned PDFs and video frames (RapidOCR), with clean-up for ₹, letter/digit mix-ups and run-together words | Creative eval 26/26 and 12/12; input library 60/60 |
| 2 | No logo clear-space or placement check | ✅ Done | Creative Inspection finds the registered logo and checks the clear space around it | Creative tests |
| 3 | Guidelines: PDF only | ✅ Done | PDF, DOCX, HTML, Markdown, TXT, CSV and XLSX | 70/70 input files upload |
| 4 | Sparse TF-IDF evidence search | ✅ Done | Hybrid BM25 + TF-IDF + dense embeddings (bge-small, local), fused ranking | Retrieval recall@3 0.675 → 0.825 |
| 5 | No MCP protocol transport | ✅ Done | MCP server (JSON-RPC over stdio) with read-only governance tools | MCP end-to-end test |
| 6 | No internet-wide impersonation monitoring | ⚠️ Still a limit | Analyses submitted URLs, text and screenshots: lookalike domains, phishing requests, wrong prices | Needs external data feeds (domain registrations, ad libraries); out of scope |
| 7 | Lexicon sentiment, small test set | ✅ Done | AI-model sentiment for unrated feedback when a model is configured; improved lexicon as fallback; star ratings still take precedence | See below |
| 8 | Reviewer intelligence limited by demo data | ⚠️ Still a limit | Engine is built and tested; its insight depends on real review history | Improves with real usage only |
| 9 | No email or push notifications | ✅ Done | Email (SMTP), Slack, signed webhooks, and **browser push** (Web Push, works with the tab closed) | RFC 8291 test vector matches; delivery and role-filter tests |
| 10 | Per-process rate limiting | ✅ Done | Limits stored in the database, shared by every server instance; real client IP used behind the proxy | Two-instance test: 5 allowed in total, not 5 each |
| 11 | Visual DNA partly implemented | ✅ Done | Colour and contrast, text inside creatives, logo detection and clear space | Visual and creative tests |
| 12 | No dense retrieval, pgvector or Row-Level Security | ✅ Done | Dense retrieval and pgvector (HNSW index); **PostgreSQL Row-Level Security** on every tenant table | Full suite on PostgreSQL 18 with RLS on; RLS tests |

## Sentiment (item 7), measured

Texts without star ratings, labelled before measuring (`backend/eval/run_sentiment_eval.py`).

| Engine | 120-item set | 45 unseen texts |
|---|---|---|
| Lexicon, before | 79.2% | not measured |
| Lexicon, after improvements | 100% (tuned on this set) | **73.3%** |
| AI model (Groq `gpt-oss-120b`) | 96.7% | **97.8%** |

The lexicon's 100% is not a real score, because it was tuned on that set; 73.3% on unseen text is its honest number. That is why uploads use the AI model when one is configured (up to 300 unrated rows per upload, `REPUTATION_LLM_MAX_ROWS`). Each record stores which engine scored it.

## Notes for deployment

- **Row-Level Security** applies only on PostgreSQL. It also needs the app to connect as a normal role, not a superuser; Neon's default role is fine. On SQLite the application-level filters remain the guard.
- **Push notifications:** each user turns them on in **Settings → Notifications**. Optionally set `VAPID_PRIVATE_KEY` and `VAPID_SUBJECT` (for example `mailto:brand@company.com`). Without them a key is generated once and stored in the database.
- **Email** needs `SMTP_HOST`, `SMTP_FROM` and, if required, `SMTP_USER`/`SMTP_PASSWORD`.
- **Rate limiting** is shared through the database by default. `RATE_LIMIT_BACKEND=memory` uses the old per-process limiter.
