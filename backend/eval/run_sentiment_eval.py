"""Measure feedback sentiment on labelled customer texts (no star ratings).

Run from the repo root:
    backend/venv/Scripts/python backend/eval/run_sentiment_eval.py                         # 120-item set
    backend/venv/Scripts/python backend/eval/run_sentiment_eval.py sentiment_holdout.json  # 40-item hold-out
    add --llm to use the configured language model (as on the live site)
"""
import json
import os
import sys
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.services import reputation  # noqa: E402

LABELS = ["positive", "negative", "neutral"]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    name = args[0] if args else "sentiment_dataset.json"
    with open(os.path.join(os.path.dirname(__file__), name), encoding="utf-8") as fh:
        items = json.load(fh)["items"]
    provider = None
    if "--llm" in sys.argv:
        from backend.app.core.config import settings
        from backend.app.services.llm import get_llm_provider
        provider = get_llm_provider(settings)
        if not provider.available:
            print("No LLM is configured.")
            return 1
    texts = [t for t, _ in items]
    if provider:
        preds = [p[0] for p in reputation.score_batch(texts, provider)]
    else:
        preds = [reputation.score_sentiment(t, None)[0] for t in texts]
    conf = Counter((gold, pred) for (_, gold), pred in zip(items, preds))
    correct = sum(conf[(l, l)] for l in LABELS)
    print("=" * 64)
    print(f"Sentiment evaluation ({name}) — engine: {'LLM ' + provider.model if provider else 'lexicon'}")
    print("=" * 64)
    print(f"Items: {len(items)}   Accuracy: {correct}/{len(items)} = {correct / len(items):.1%}")
    f1s = []
    for l in LABELS:
        tp = conf[(l, l)]
        fp = sum(conf[(g, l)] for g in LABELS if g != l)
        fn = sum(conf[(l, p)] for p in LABELS if p != l)
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        f1s.append(f1)
        print(f"{l:<9} precision {p:.2f}  recall {r:.2f}  F1 {f1:.2f}")
    print(f"Macro F1: {sum(f1s) / 3:.3f}")
    print("-" * 64)
    print("gold \\ predicted   " + "  ".join(f"{l[:3]:>4}" for l in LABELS))
    for g in LABELS:
        print(f"{g:<18} " + "  ".join(f"{conf[(g, p)]:>4}" for p in LABELS))
    wrong = [(t, g, p) for (t, g), p in zip(items, preds) if g != p]
    if wrong:
        print("-" * 64)
        for t, g, p in wrong:
            print(f"  [{g} -> {p}] {t}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
