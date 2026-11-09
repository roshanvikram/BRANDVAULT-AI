"""E4 evaluation runner — measures the heuristic analyzer against a labelled
dataset and reports precision / recall / F1 / FP / FN and workflow completion.

Run from the repo root:
    backend/venv/Scripts/python backend/eval/run_eval.py                      # original 36-case set
    backend/venv/Scripts/python backend/eval/run_eval.py realworld_dataset.json  # 50 held-out real-world inputs

Reports MEASURED results only. The engine is deterministic and LLM-free here, so
numbers are reproducible. Out-of-scope ground-truth tags (visual, fact_conflict)
appear only as false negatives — an honest reflection of current limitations.
"""
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Allow running as a plain script from the repo root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.services.analyzer import ContentAnalyzerService
from backend.app.services import llm as llm_mod
from backend.tests._util import make_seeded_db, drop_db

VIOLATION_TAGS = ["price_conflict", "superlative", "comparative", "terminology", "tone", "outdated", "needs_review", "fact_conflict"]


def predict_tags(sub) -> set:
    tags = set()
    for c in sub.claim_verifications:
        if c.status == "Contradicted" and c.category == "Pricing":
            tags.add("price_conflict")
        elif c.status == "Contradicted":
            tags.add("fact_conflict")
        if c.status == "Unsupported" and c.category == "Performance":
            tags.add("superlative")
        if c.status == "Unsupported" and c.category == "Comparative":
            tags.add("comparative")
        if c.status == "Outdated":
            tags.add("outdated")
        if c.status == "Needs Human Review":
            tags.add("needs_review")
    for f in sub.findings:
        if f.issue_category == "Terminology":
            tags.add("terminology")
        if f.issue_category == "Tone & Voice":
            tags.add("tone")
    return tags


def main():
    here = os.path.dirname(__file__)
    name = sys.argv[1] if len(sys.argv) > 1 else "dataset.json"
    with open(os.path.join(here, name), encoding="utf-8") as fh:
        data = json.load(fh)
    org_id = data["org_id"]
    cases = data["cases"]

    engine, Session, path = make_seeded_db()
    db = Session()
    svc = ContentAnalyzerService(db, llm_provider=llm_mod.NullProvider())

    TP = FP = FN = 0
    per_tag = {t: {"tp": 0, "fp": 0, "fn": 0} for t in VIOLATION_TAGS}
    oos_fn = {}  # out-of-scope expected tags the engine never predicts
    exact = 0
    clean_total = clean_ok = 0
    misses = []
    completed = 0
    errors = []

    for case in cases:
        try:
            sub = svc.analyze_submission(org_id, case["id"], case["content"])
            completed += 1
        except Exception as e:  # pragma: no cover
            errors.append((case["id"], str(e)))
            continue
        exp = set(case["expected"]) - {"clean"}
        pred = predict_tags(sub)

        for t in (pred & exp):
            TP += 1
            if t in per_tag:
                per_tag[t]["tp"] += 1
        for t in (pred - exp):
            FP += 1
            if t in per_tag:
                per_tag[t]["fp"] += 1
        for t in (exp - pred):
            FN += 1
            if t in per_tag:
                per_tag[t]["fn"] += 1
            else:
                oos_fn[t] = oos_fn.get(t, 0) + 1
        if pred == exp:
            exact += 1
        else:
            misses.append((case["id"], sorted(exp - pred), sorted(pred - exp), case["content"]))
        if not exp:
            clean_total += 1
            clean_ok += not pred

    db.close()
    drop_db(engine, path)

    precision = TP / (TP + FP) if (TP + FP) else 0.0
    recall = TP / (TP + FN) if (TP + FN) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    print("=" * 64)
    print(f"BRANDVAULT AI — Heuristic Analyzer Evaluation ({name})")
    print("=" * 64)
    print(f"Cases: {len(cases)}   Workflow completion: {completed}/{len(cases)}")
    if errors:
        print(f"Errors: {errors}")
    print(f"Exact per-case tag match: {exact}/{len(cases)} ({exact/len(cases):.0%})")
    if clean_total:
        print(f"Clean copy passed with no false flag: {clean_ok}/{clean_total}")
    print("-" * 64)
    print(f"Micro Precision: {precision:.3f}")
    print(f"Micro Recall:    {recall:.3f}")
    print(f"Micro F1:        {f1:.3f}")
    print(f"TP={TP}  FP={FP}  FN={FN}")
    print("-" * 64)
    print(f"{'tag':<16}{'TP':>5}{'FP':>5}{'FN':>5}{'prec':>8}{'rec':>8}")
    for t in VIOLATION_TAGS:
        d = per_tag[t]
        p = d["tp"] / (d["tp"] + d["fp"]) if (d["tp"] + d["fp"]) else 0.0
        r = d["tp"] / (d["tp"] + d["fn"]) if (d["tp"] + d["fn"]) else 0.0
        print(f"{t:<16}{d['tp']:>5}{d['fp']:>5}{d['fn']:>5}{p:>8.2f}{r:>8.2f}")
    if oos_fn:
        print("-" * 64)
        print("Out-of-scope ground-truth tags (not detectable by the current rule")
        print("engine — counted as false negatives above):")
        for t, n in sorted(oos_fn.items()):
            print(f"  {t}: {n} missed")
    if misses:
        print("-" * 64)
        print("Cases not matched exactly (missed / wrongly flagged):")
        for cid, missed, extra, text in misses:
            print(f"  {cid}: missed={missed} extra={extra} | {text[:70]}")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
