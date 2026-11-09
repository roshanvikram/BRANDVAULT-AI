# BRANDVAULT AI — Real-World Input Test (50 cases)

**Goal:** measure how well BrandVault catches brand problems in copy written the way marketing teams really write it, then fix what it misses.

**Inputs:** 50 messages across 20 channels: Instagram, WhatsApp, email, SMS, store banners, billboards, press releases, retailer listings, festival ads, spec sheets and Google ads.
- **Problem copy (36 cases):** wrong prices, unapproved discounts, superlatives, competitor comparisons, wrong specifications, an expired offer, banned words, hype and shouting, and vague claims.
- **Clean copy (14 cases):** it must pass with no false alarm.

The labels were written before the first run.

**Brand truth used:**
- Price ₹79,999.
- 45 TOPS.
- Up to 18 hours of battery.
- 2-year warranty.
- The NovaSleeve pre-order bonus expired in 2024.
- Banned words: "world's fastest", "10x faster than every competitor" and "cheap". The naming rule also bans "budget laptop" and "cheap AI device".

## How to run

```
backend/venv/Scripts/python backend/eval/run_eval.py realworld_dataset.json
backend/venv/Scripts/python backend/eval/run_eval.py realworld_holdout.json
backend/venv/Scripts/python backend/eval/run_eval.py               # original 36-case set
```

The analyzer runs without an LLM here, so results are the same on every run.

## Results

| | Precision | Recall | F1 | Exact case match | Clean copy passed |
|---|---|---|---|---|---|
| **Before** fixes (first run) | 0.923 | 0.545 | 0.686 | 29/50 (58%) | 13/14 |
| **After** fixes | 1.000 | 1.000 | 1.000 | 50/50 (100%) | 14/14 |
| Fresh 20-case hold-out (scored once, no changes) | 1.000 | 1.000 | 1.000 | 20/20 | 5/5 |
| Original 36-case set (was 0.925 F1) | 1.000 | 0.953 | 0.976 | 34/36 | 12/12 |

### What the first run missed (recall per issue type, before → after)

| Issue | Before | After | Example it missed before |
|---|---|---|---|
| Wrong specification | 0/5 | 5/5 | "Up to 24 hours of battery life." (approved: 18) |
| Competitor comparison | 1/6 | 6/6 | "2x faster than the MacBook Air M3" |
| Superlative | 3/8 | 8/8 | "India's #1 AI laptop." |
| Banned words | 3/5 | 5/5 | "World’s fastest" with a curly apostrophe; "budget laptop" |
| Tone | 3/5 | 5/5 | "OMG this laptop is INSANE 🔥🔥" |
| Vague claim / financing | 3/4 | 4/4 | "No-cost EMI from ₹6,667/month" |
| Price conflict | 8/8 | 8/8 | Two of those hits were luck (see below) |
| Expired offer | 3/3 | 3/3 | — |

It also raised two false price alarms: on an EMI amount (₹6,667/month) and on an accessory price (NovaSleeve ₹2,499).

## What was fixed

All the new checks are in `backend/app/services/claim_patterns.py` and covered by `backend/tests/test_claim_patterns.py`.

1. **Wrong specifications are now caught.**
   - Battery hours, TOPS and warranty length are compared with the approved facts.
   - "3-year warranty" and "18-month warranty" are both checked against the approved 2 years.
   - Charging times ("80% in 1 hour") are not mistaken for battery life.
   - Before, a wrong number was even marked *Supported* just because the word "battery" appeared. That is fixed.
2. **Prices read the way people write them.**
   - Formats now read: "Rs.74,990/-", "69999 rs" and "₹79,999.00".
   - EMI and monthly amounts go to human review as financing terms instead of being called a wrong price.
   - Accessory prices are not compared with the laptop price.
   - A latent bug made "rs," with no number count as a price. It no longer does.
3. **Superlatives and comparisons are caught in any wording.**
   - Superlatives: "fastest / most powerful / best / #1 … laptop", "best … ever" and "unbeatable".
   - Comparisons: "Nx faster", "faster than any(thing) / every / named rival", "beats / outperforms …" and "leaves the competition behind".
4. **Banned words:**
   - Curly apostrophes are normalised.
   - Words that a confirmed brand rule says "do not use" are enforced even if they are not in the terminology register yet.
5. **Tone:** besides 2+ exclamation marks, it now flags hype slang (OMG, insane, crazy, 🔥) and shouting in capitals. Brand names and acronyms such as GST, MRP and TOPS are ignored.

## Checks that nothing else broke

- **Full test suite:** 230 tests pass, including 7 new ones (1 skipped: the PostgreSQL-only test).
- **Creative Inspection eval:** still 26/26. It sends text read from images through the same analyzer.

## Limits

- **The 50 cases became tuning data.** After the fixes they are no longer an independent test. The 20-case hold-out was written afterwards and scored once without changes, but the same team wrote it. Copy from people outside the team would be a stronger test.
- **The rules are tied to this brand's facts.** The spec check covers battery hours, TOPS and warranty length. Other numbers (weight, screen size, RAM) are not compared yet.
- **Images are tested separately.** Visual issues such as logo colour are covered by Creative Inspection and Visual DNA, not by this text test.
