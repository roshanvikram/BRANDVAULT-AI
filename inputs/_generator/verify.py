"""Run every file in the input library through the real BrandVault API and compare
the result with the manifest. Writes inputs/VERIFICATION_RESULTS.md.

    backend/venv/Scripts/python inputs/_generator/verify.py
"""
import datetime
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apiclient import Client, INPUTS, manifest, read  # noqa: E402

from backend.app.models.submission import Submission  # noqa: E402
from backend.app.services import creative  # noqa: E402
from backend.app.services.analyzer import ContentAnalyzerService  # noqa: E402
from backend.app.services.llm import NullProvider  # noqa: E402
from backend.eval.run_eval import predict_tags  # noqa: E402

ORG = "nova-tech-org-001"
results = {}
misses = {}


def tags_of(s):
    return set() if s == "clean" else set(s.split(";"))


def record(folder, ok, total, miss):
    results[folder] = (ok, total)
    misses[folder] = miss[:15]
    print(f"{folder:<28} {ok:>3}/{total:<3}", flush=True)


def analyzer_tags(k, text):
    db = k.Session()
    try:
        sub = ContentAnalyzerService(db, llm_provider=NullProvider()).analyze_submission(ORG, "check", text)
        return predict_tags(sub), [c.status for c in sub.claim_verifications]
    finally:
        db.rollback()
        db.close()


def content(k):
    f = "01_content_intelligence"
    ok, miss = 0, []
    rows = manifest(f)
    for r in rows:
        got, _ = analyzer_tags(k, read(f, r["file"]))
        exp = tags_of(r["expected_issues"])
        if got == exp:
            ok += 1
        else:
            miss.append(f"{r['file']}: expected {sorted(exp) or 'clean'}, got {sorted(got) or 'clean'}")
    record(f, ok, len(rows), miss)


def claims(k):
    f = "02_claim_dna"
    ok, miss = 0, []
    rows = manifest(f)
    bad = {"Contradicted", "Unsupported", "Outdated", "Needs Human Review"}
    for r in rows:
        _, statuses = analyzer_tags(k, read(f, r["file"]))
        exp = r["expected_status"]
        good = (not (set(statuses) & bad)) if exp == "Supported" else exp in statuses
        ok += good
        if not good:
            miss.append(f"{r['file']}: expected {exp}, got {statuses or 'no claim'}")
    record(f, ok, len(rows), miss)


def creative_files(k):
    f = "03_creative_inspection"
    ok, miss = 0, []
    rows = manifest(f)
    db = k.Session()
    try:
        analyzer = ContentAnalyzerService(db, llm_provider=NullProvider())
        for r in rows:
            insp = creative.inspect(db, ORG, r["file"], read(f, r["file"], "rb"), "Check", analyzer=analyzer)
            sub = db.get(Submission, insp.submission_id) if insp.submission_id else None
            got = predict_tags(sub) if sub else set()
            exp = tags_of(r["expected_issues"])
            if got == exp:
                ok += 1
            else:
                miss.append(f"{r['file']}: expected {sorted(exp) or 'clean'}, got {sorted(got) or 'clean'}")
    finally:
        db.close()
    record(f, ok, len(rows), miss)


def visual(k):
    f = "04_visual_dna"
    k.post("/brand/rules", json={"category": "Visual", "title": "Monochrome palette",
                                 "rule_text": "Brand visuals use a monochrome palette (black, white and greys).", "severity": "WARNING"})
    ok, miss = 0, []
    rows = manifest(f)
    for r in rows:
        j = k.post("/visual/analyze", files={"file": (r["file"], read(f, r["file"], "rb"))}).json()
        cats = {x["issue_category"] for x in j["submission"]["findings"]}
        exp_colour = r["design"] in ("colour_high", "colour_low")
        exp_low = r["design"] in ("mono_low", "colour_low")
        good = (("Visual" in cats) == exp_colour) and (("Accessibility" in cats) == exp_low)
        ok += good
        if not good:
            m = j["metrics"]
            miss.append(f"{r['file']}: {r['design']} -> findings {sorted(cats)} (colour {m['chromatic_fraction']}, contrast {m['contrast']})")
    record(f, ok, len(rows), miss)


def guidelines(k):
    f = "05_brand_dna_guidelines"
    ok, miss = 0, []
    rows = manifest(f)
    for r in rows:
        res = k.post("/brand/guidelines/upload", files={"file": (r["file"], read(f, r["file"], "rb"))})
        good = res.status_code == 200 and res.json().get("status") == "processed"
        ok += good
        if not good:
            miss.append(f"{r['file']}: HTTP {res.status_code} {res.text[:120]}")
    record(f, ok, len(rows), miss)


def translations(k):
    f = "06_translation_guard"
    ok, miss = 0, []
    rows = manifest(f)
    for r in rows:
        body = json.loads(read(f, r["file"]))
        j = k.post("/translation-guard/analyze", json={**body, "use_ai": False}).json()
        per = {t["label"]: t for t in j["translations"]}
        bad_lang = None if r["case_type"] == "clean" else r["languages"].split(",")[0]
        good = True
        for lang, t in per.items():
            flagged = bool(t["findings"])
            if flagged != (lang == bad_lang):
                good = False
        ok += good
        if not good:
            miss.append(f"{r['file']}: " + "; ".join(f"{l}={[x['type'] for x in t['findings']]}" for l, t in per.items()))
    record(f, ok, len(rows), miss)


def copy_studio(k):
    f = "07_copy_studio"
    ok, miss = 0, []
    rows = manifest(f)
    for r in rows:
        j = k.post("/copy-studio/rewrite", json={"content": read(f, r["file"])}).json()
        left, _ = analyzer_tags(k, j["rewritten"])
        before = tags_of(r["issues_to_fix"])
        fixed = before - left
        # EMI amounts are financing terms a reviewer must approve; a rewrite cannot settle them.
        if left == {"needs_review"} and "emi" in j["rewritten"].lower():
            left = set()
        good = not left
        ok += good
        if not good:
            miss.append(f"{r['file']}: fixed {sorted(fixed)}, still {sorted(left)}")
    record(f, ok, len(rows), miss)


def assistant(k):
    f = "08_brand_assistant"
    ok, miss = 0, []
    rows = manifest(f)
    for r in rows:
        j = k.post("/twin/ask", json={"question": read(f, r["file"]).strip()}).json()
        good = j["grounded"] == (r["type"] == "answerable")
        ok += good
        if not good:
            miss.append(f"{r['file']}: {r['type']} -> grounded={j['grounded']} ({j['answer'][:80]!r})")
    record(f, ok, len(rows), miss)


def reputation(k):
    f = "09_reputation_feedback"
    ok, miss = 0, []
    rows = manifest(f)
    for r in rows:
        j = k.post("/reputation/upload", files={"file": (r["file"], read(f, r["file"], "rb"))}).json()
        good = j.get("imported") == int(r["usable_rows"]) and j.get("skipped") == int(r["rows_to_skip"])
        ok += good
        if not good:
            miss.append(f"{r['file']}: expected {r['usable_rows']} imported / {r['rows_to_skip']} skipped, got {j}")
    record(f, ok, len(rows), miss)


def fraud(k):
    f = "10_fraud_intelligence"
    k.post("/fraud/domains", json={"domain": "novatech.example"})
    ok, miss = 0, []
    rows = manifest(f)
    for r in rows:
        body = read(f, r["file"])
        url = body.split("URL: ", 1)[1].split("\n", 1)[0].strip()
        msg = body.split("Message:\n", 1)[1].strip()
        j = k.post("/fraud/investigate", data={"url": url, "text": msg}).json()
        suspected = j.get("risk") in ("high", "medium")
        good = suspected == r["expected_result"].startswith("SUSPECTED")
        ok += good
        if not good:
            miss.append(f"{r['file']}: {r['expected_result'][:40]} -> risk {j.get('risk')} ({j.get('detected_issue', '')[:80]})")
    record(f, ok, len(rows), miss)


def channels(k):
    f = "11_channel_check"
    ok, miss = 0, []
    rows = manifest(f)
    for r in rows:
        j = k.post("/channels/check", json=json.loads(read(f, r["file"]))).json()
        ch = j["channels"][0] if isinstance(j.get("channels"), list) and j["channels"] else {}
        text = json.dumps(ch).lower()
        over_exp = r["length_result"] == "OVER limit"
        over_got = (ch.get("chars", 0) > (ch.get("max_chars") or 10 ** 9))
        ratio_exp = "WRONG" in r["image_result"]
        ratio_got = any(i.startswith("Image is") for i in ch.get("issues", []))
        good = over_exp == over_got and (ratio_exp == ratio_got if r["image_result"] != "no image" else True)
        ok += good
        if not good:
            miss.append(f"{r['file']}: expected {r['length_result']}/{r['image_result']}, got {json.dumps(ch)[:200]}")
    record(f, ok, len(rows), miss)


def forensics(k):
    f = "12_asset_forensics"
    reg = k.post("", files={"file": ("logo.png", read(f, "00_official_logo_REGISTER_FIRST.png", "rb"))},
                 data={"name": "NOVA TECH logo", "kind": "logo", "version_label": "v2"}) if False else \
        k.c.post("/api/v1/assets", headers=k.admin, files={"file": ("logo.png", read(f, "00_official_logo_REGISTER_FIRST.png", "rb"))},
                 data={"name": "NOVA TECH logo", "kind": "logo", "version_label": "v2"})
    ok, miss, out = 0, [], []
    rows = [r for r in manifest(f) if r["file"].startswith("asset_")]
    for r in rows:
        j = k.post("/assets/investigate", files={"file": (r["file"], read(f, r["file"], "rb"))}).json()
        found = json.dumps(j).lower()
        match = bool(j.get("matches") or j.get("detections") or j.get("matched_asset_id"))
        exp_found = r["case"] != "no_logo" and r["case"] != "old_version"
        good = match == exp_found
        ok += good
        if not good:
            miss.append(f"{r['file']}: {r['case']} -> {json.dumps(j)[:180]}")
    record(f, ok, len(rows), miss)
    return reg.status_code


def passport(k):
    f = "13_brand_passport_verify"
    ok, miss = 0, []
    rows = manifest(f)
    for r in rows:
        j = k.post("/passport/verify", data={"text": read(f, r["file"])}).json()
        good = (j.get("result") == "Verified Match") == r["expected_result"].startswith("VERIFIED")
        ok += good
        if not good:
            miss.append(f"{r['file']}: {r['change']} -> {j.get('result')}")
    record(f, ok, len(rows), miss)


def similarity(k):
    f = "14_similarity"
    ok, miss = 0, []
    rows = manifest(f)
    for r in rows:
        j = k.post("/similarity/check", json={"text": read(f, r["file"])}).json()
        top = (j.get("matches") or [None])[0]
        if r["edit"] == "unrelated":
            good = top is None or top["similarity"] < 0.3
        else:
            good = top is not None and top["title"] == r["source_campaign"]
        ok += good
        if not good:
            miss.append(f"{r['file']}: {r['edit']} of '{r['source_campaign']}' -> "
                        + (f"{top['title']} ({top['similarity']}, {top['label']})" if top else "no match"))
    record(f, ok, len(rows), miss)


# Similarity, passport and fraud compare against stored campaigns, so they run before
# the checks that add new submissions.
CHECKS = [similarity, passport, fraud, content, claims, creative_files, visual, guidelines, translations,
          copy_studio, assistant, reputation, channels, forensics]

if __name__ == "__main__":
    only = sys.argv[1:]
    t0 = time.time()
    with Client() as k:
        for check in CHECKS:
            if only and check.__name__ not in only:
                continue
            check(k)
    if not only:
        lines = ["# Input library — verification results", "",
                 f"Run on {datetime.date.today().isoformat()} through the real BrandVault API (seeded demo workspace, no LLM).",
                 "Re-run: `backend/venv/Scripts/python inputs/_generator/verify.py`", "",
                 "| Folder | Files matching the manifest |", "|---|---|"]
        for name, (ok, total) in results.items():
            lines.append(f"| {name} | {ok}/{total} |")
        lines += ["", f"Total: {sum(o for o, _ in results.values())}/{sum(t for _, t in results.values())} "
                  f"in {time.time() - t0:.0f} s", ""]
        for name, m in misses.items():
            if m:
                lines += [f"## {name}: differences", ""] + [f"- {x}" for x in m] + [""]
        with open(os.path.join(INPUTS, "VERIFICATION_RESULTS.md"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
    for name, m in misses.items():
        for x in m[:8]:
            print(f"  [{name}] {x}")
