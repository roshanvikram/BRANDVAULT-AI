"""Round 3 evaluation — Creative Inspection (OCR + brand checks on images, PDFs, video).

Run from the repo root:
    backend/venv/Scripts/python backend/eval/run_creative_eval.py

Creatives are generated from creative_dataset.json at run time on a throwaway
database, analysed with the deterministic engine (no AI calls), and scored:
- OCR character accuracy = 1 - character error rate against the known text
- issue precision / recall / F1 using the same tags as run_eval.py
Reports MEASURED results only.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.models.submission import Submission  # noqa: E402
from backend.app.services import creative  # noqa: E402
from backend.app.services.analyzer import ContentAnalyzerService  # noqa: E402
from backend.app.services.llm import NullProvider  # noqa: E402
from backend.eval.run_eval import VIOLATION_TAGS, predict_tags  # noqa: E402
from backend.tests import creative_fixtures as cf  # noqa: E402
from backend.tests._util import drop_db, make_seeded_db  # noqa: E402

STYLES = [((255, 255, 255), (15, 23, 42)), ((15, 23, 42), (255, 255, 255)), ((238, 242, 255), (67, 56, 202)),
          ((255, 247, 237), (154, 52, 18)), ((236, 253, 245), (6, 95, 70)), ((250, 250, 250), (30, 30, 30))]


def build(case) -> tuple:
    fmt, lines, style = case["format"], case["lines"], case["style"]
    if fmt in ("png", "jpeg", "webp"):
        bg, fg = STYLES[style % len(STYLES)]
        return f"{case['id']}.{ 'jpg' if fmt == 'jpeg' else fmt}", cf.banner(lines, bg=bg, fg=fg, variant=style, fmt=fmt.upper())
    if fmt == "pdf-text":
        return f"{case['id']}.pdf", cf.text_pdf([lines])
    if fmt == "pdf-scan":
        return f"{case['id']}.pdf", cf.image_pdf(lines)
    if fmt == "video":
        return f"{case['id']}.mp4", cf.video([[l] for l in lines])
    raise ValueError(fmt)


def _norm(s: str) -> str:
    return " ".join(s.replace("’", "'").split())


def cer(ref: str, hyp: str) -> float:
    a, b = _norm(ref), _norm(hyp)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1] / max(1, len(a))


def main():
    here = os.path.dirname(__file__)
    name = sys.argv[1] if len(sys.argv) > 1 else "creative_dataset.json"
    with open(os.path.join(here, name), encoding="utf-8") as fh:
        data = json.load(fh)
    engine, Session, path = make_seeded_db()
    db = Session()
    analyzer = ContentAnalyzerService(db, llm_provider=NullProvider())
    tp = fp = fn = 0
    per_tag = {t: [0, 0, 0] for t in VIOLATION_TAGS}
    by_format, rows, exact = {}, [], 0
    try:
        for case in data["cases"]:
            name, blob = build(case)
            t0 = time.perf_counter()
            insp = creative.inspect(db, data["org_id"], name, blob, "Eval", analyzer=analyzer)
            secs = time.perf_counter() - t0
            got_lines = creative.unique_lines(insp.pages)  # the same text the analyzer received
            err = cer(" ".join(case["lines"]), " ".join(got_lines))
            sub = db.get(Submission, insp.submission_id) if insp.submission_id else None
            pred = predict_tags(sub) if sub else set()
            exp = set(case["expected"])
            tp += len(pred & exp); fp += len(pred - exp); fn += len(exp - pred)
            for t in VIOLATION_TAGS:
                per_tag[t][0] += t in pred and t in exp
                per_tag[t][1] += t in pred and t not in exp
                per_tag[t][2] += t in exp and t not in pred
            exact += pred == exp
            f = by_format.setdefault(case["format"], {"n": 0, "acc": 0.0, "secs": 0.0})
            f["n"] += 1; f["acc"] += max(0.0, 1 - err); f["secs"] += secs
            rows.append((case["id"], case["format"], round(max(0.0, 1 - err), 3), sorted(exp), sorted(pred), round(secs, 1), len(insp.corrections)))
    finally:
        db.close()
        drop_db(engine, path)

    prec = tp / (tp + fp) if tp + fp else 1.0
    rec = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    n = len(rows)
    print("=" * 72)
    print("BRANDVAULT AI — Creative Inspection Evaluation (measured)")
    print("=" * 72)
    print(f"Creatives: {n}   Exact issue-set match: {exact}/{n} ({exact / n:.0%})")
    print(f"OCR character accuracy (mean): {sum(r[2] for r in rows) / n:.3f}")
    print(f"Issue precision: {prec:.3f}   recall: {rec:.3f}   F1: {f1:.3f}   (TP={tp} FP={fp} FN={fn})")
    print("-" * 72)
    print(f"{'format':10} {'n':>3} {'ocr acc':>8} {'avg secs':>9}")
    for k, v in by_format.items():
        print(f"{k:10} {v['n']:>3} {v['acc'] / v['n']:>8.3f} {v['secs'] / v['n']:>9.1f}")
    print("-" * 72)
    print(f"{'tag':16} {'TP':>3} {'FP':>3} {'FN':>3}")
    for t, (a, b, c) in per_tag.items():
        if a or b or c:
            print(f"{t:16} {a:>3} {b:>3} {c:>3}")
    print("-" * 72)
    for r in rows:
        flag = "" if r[3] == r[4] else "   <-- differs"
        print(f"{r[0]} {r[1]:9} ocr={r[2]:.3f} expected={r[3]} got={r[4]} {r[5]}s fixes={r[6]}{flag}")
    print("=" * 72)
    return {"cases": n, "precision": prec, "recall": rec, "f1": f1, "exact": exact,
            "ocr_accuracy": sum(r[2] for r in rows) / n}


if __name__ == "__main__":
    main()
