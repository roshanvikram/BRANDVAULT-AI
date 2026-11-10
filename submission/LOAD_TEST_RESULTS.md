# Load test and productivity results

How BrandVault behaves with a lot of data, what was slow, what was fixed, and the new time-saving features.

## How it was tested

`backend/eval/run_load_test.py` fills a fresh database with **1,000 campaigns** checked by the real analyzer (rule engine, evidence retrieval, claim checks). They come from the 302 realistic texts in `inputs/` and the eval sets. It then records 600 reviewer decisions, calls **all 60 list pages** of the API as an administrator, and opens the dashboard 30 times with 10 people at once.

```bash
python -m backend.eval.run_load_test --campaigns 1000
```

All numbers below are from one laptop, one server process and SQLite. PostgreSQL gives the same results in the test suite.

## What happened at 1,000 campaigns

| Measure | Before | After |
|---|---|---|
| Checking one piece of copy (median) | 51 ms | 55 ms (unchanged: this was already fast) |
| Failed analyses | 0 of 1,000 | 0 of 1,000 |
| Recording a review decision | 14 ms | 12 ms |
| Asset lifecycle page | **6.5 s** | **0.24 s** |
| Knowledge graph | 1.5 s | 0.29 s |
| Consistency analytics | 1.4 s | 0.16 s |
| Reviewer intelligence | 1.0 s | 0.10 s |
| Similarity clusters | 0.86 s | 0.17 s |
| Campaign list | 1.0 s | 0.15 s |
| Data the dashboard downloads | 1.9 MB | 0.44 MB (and about 10x less on the wire with compression) |
| Dashboard, 10 people at once | **21.3 s** | **4.5 s** |
| Server errors on any page | 0 | 0 |

### Causes and fixes
1. **One database query per campaign** (the "N+1" problem): pages that showed campaigns fetched each campaign's findings, claims and approvals separately, up to 3,000 queries per page. They now load in a few batched queries.
2. **Asset lifecycle re-synced the product catalogue for every campaign**, and that sync also made every campaign already loaded be read again. It now syncs once, first, and reuses the catalogue: 16 queries instead of about 3,000. Output is byte-for-byte identical to before.
3. **Similarity compared every campaign with every other** (about 500,000 comparisons). It now uses prefix filtering, which only compares campaigns that share rare phrases. The pairs found are identical to the full comparison at every threshold (tested).
4. **No compression**: responses are now gzip-compressed.
5. **The dashboard downloaded every campaign's full text and findings**. It now uses a light list with a 160-character preview and finding severities only.

The remaining dashboard time with 10 people at once comes from one Python process doing the work. A paid server with 2 or more workers (`uvicorn --workers 2`) would divide it.

## New time-saving features

| Feature | Where | What it saves |
|---|---|---|
| **Bulk check** | Content Intelligence → Bulk check | Paste many pieces separated by `---`, or upload CSV, Excel, Word, PDF or text files (up to 200 per batch). They are checked in the background; the job survives restarts and continues where it stopped. Results show score and critical findings per piece, with CSV export. |
| **Fix all** | Content Intelligence → Findings → Fix all | Applies every suggested word replacement at once and re-checks once (one new version). Advice-only findings, such as "too many exclamation marks", are listed for a manual edit. Example: score 21 → 98 in one click. |
| **Bulk review** | Approval Hub → Bulk review | A fast paged list (50 per page) with status filters, search and sorting. Select many items and approve, request revision or reject them with one comment. Safety rules stay: only Reviewers and Administrators decide, each decision is recorded separately under their name, and anything with an open critical finding or changed since it was listed is skipped with the reason. |
| **CSV export** | Bulk review → Export all | Every review with status, score and finding counts, for reports. |

## Quality fixes found on the way
- **Suggestions borrowed NOVA TECH's figures.** The suggested replacement for any "fastest/best" claim was always NOVA's "45 TOPS" wording, which was wrong for any other company. It is now built from the claim's own words plus the company's **own** approved facts: "The world's fastest AI laptop" → "The high-performance AI laptop (45 TOPS NPU …)" for NOVA, and "The high-performance AI laptop" for a company without such a fact.
- **Grammar after a fix.** Replacements now correct "a/an" and keep a capital letter at the start of a sentence: "Unbeatable performance at an unbeatable price" → "Strong performance at a competitive price".
- **Page headers** no longer squeeze the title when a page has several buttons.

## Checks
- Automated tests: **288 pass on SQLite and 288 on PostgreSQL** (with Row-Level Security), including 12 new tests for these features.
- Real-world eval: **50/50**, unchanged. The older 36-case set: 34/36, unchanged; the 2 misses are colour words in plain text, which the text checker does not treat as visual issues.
- Browser: Bulk check of 4 pieces, Fix all, and bulk approval (3 approved with passports, 1 skipped for critical findings) all checked on a local server.
