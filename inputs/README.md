# BrandVault test inputs

893 realistic input files, with at least 50 for every feature, so you can try each part of BrandVault with real-looking material.

Each folder has a `manifest.csv` that says what every file should trigger. The expected results come from how each file was built and were then checked against the real API (see `VERIFICATION_RESULTS.md`).

All content uses the demo brand **NOVA TECH**:
- Price ₹79,999.
- 45 TOPS.
- Up to 18 hours of battery.
- 2-year warranty.
- The NovaSleeve pre-order bonus expired in 2024.
- Banned terms: "world's fastest", "10x faster than every competitor", "cheap" and "budget laptop".

Sign in with the demo admin account (see `DEPLOYMENT.md`).

| Folder | Files | What's inside | Where to use it |
|---|---|---|---|
| `01_content_intelligence` | 110 `.txt` | Marketing copy from Instagram, WhatsApp, email, SMS, banners, press releases and ads. Some is clean, some has 1–3 problems. | **Content Intelligence**: paste the text and analyse |
| `02_claim_dna` | 63 `.txt` | Single claims about price, battery, TOPS and warranty (right and wrong), plus superlatives, the expired offer and vague claims | **Content Intelligence** / **ClaimDNA** |
| `03_creative_inspection` | 60 | 36 banners (PNG/JPG/WebP), 14 PDF decks, 10 MP4 videos with text inside | **Creative Inspection**: upload the file |
| `04_visual_dna` | 60 images | Monochrome and colourful layouts, high and low contrast (PNG/JPG/WebP/BMP) | **Visual DNA**: upload the image |
| `05_brand_dna_guidelines` | 70 | Guidelines as DOCX, PDF, Markdown, TXT and HTML, plus 10 price lists (CSV/XLSX). Some contain deliberate conflicts. | **Brand DNA → Upload guideline** (admin) |
| `06_translation_guard` | 75 `.json` | English source plus Hindi/French/Spanish/German/Tamil translations. Some are clean; others have a changed number, dropped "up to", dropped "no" or an altered product name. | **Translation Guard**: paste the source and translations |
| `07_copy_studio` | 60 `.txt` | Off-brand copy to fix | **AI Copy Studio** |
| `08_brand_assistant` | 60 `.txt` | Questions the brand data can answer, and ones it must decline | **Brand Assistant** |
| `09_reputation_feedback` | 55 CSV/JSON | Customer reviews, support tickets and survey exports (25–120 rows each; some have rows that should be skipped) | **Reputation → Upload feedback** |
| `10_fraud_intelligence` | 60 `.txt` | Reported URL and message: lookalike domains, OTP/card phishing, fake prices, and genuine official pages | **Fraud Intelligence → Investigate**. First add `novatech.example` as an official domain. |
| `11_channel_check` | 60 `.json` | Copy plus channel plus image size: within or over the character limit, right or wrong aspect ratio | **Channel check** (`POST /api/v1/channels/check`) |
| `12_asset_forensics` | 55 images | The official logo placed, scaled, rotated, recoloured or recompressed; the old logo; no logo | **Asset Forensics**. Register `00_official_logo_REGISTER_FIRST.png` first. |
| `13_brand_passport_verify` | 55 `.txt` | The approved "Product Page Hero" copy, exact and with small edits | **Brand Passport → Verify** |
| `14_similarity` | 52 `.txt` | Near-copies, rewrites and trims of existing campaigns, plus unrelated text | **Similarity check** |

## Notes

- **Visual DNA** flags colour only when the brand has a confirmed *monochrome palette* rule. The demo brand doesn't have one, so add it in Brand DNA first, or you will only see the contrast check.
- **Translation Guard:** set each translation's label to its language code (`hi`, `fr`, `es`, `de`, `ta`). Short French and Spanish sentences look alike, and the label tells BrandVault which one it is.
- **Copy Studio without an AI key** uses rules-based rewriting:
  - It corrects prices, specifications and banned words.
  - It softens superlatives and vague claims.
  - It removes competitor comparisons and expired offers.
  - EMI wording is left for a reviewer.
- **Asset Forensics:** the "old logo" files only show as outdated if you register `00_old_logo_2024.png` as a retired version.

## Rebuild or re-check

```
backend/venv/Scripts/python inputs/_generator/generate.py   # rebuild every file (same output each time)
backend/venv/Scripts/python inputs/_generator/verify.py     # run all files through the API, write VERIFICATION_RESULTS.md
```
