"""Round 3 evaluation — evidence retrieval (Improvement 3).

Run from the repo root:
    backend/venv/Scripts/python backend/eval/run_retrieval_eval.py

Loads the authored guideline corpus in retrieval_dataset.json into a throwaway
database and compares, on the same labelled queries:
  1. tfidf            — the Round 2 retriever (TF-IDF cosine + keyword overlap)
  2. hybrid (sparse)  — BM25 + TF-IDF fused with RRF, no dense model
  3. hybrid (dense)   — BM25 + TF-IDF + dense embeddings fused with RRF
Reports recall@1, recall@3 and MRR overall and for exact vs paraphrase queries.
MEASURED results only; mode 3 is skipped (and says so) when no embedding model is available.
"""
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.core.config import settings  # noqa: E402
from backend.app.models.brand import BrandGuideline, DocumentChunk, Organization  # noqa: E402
from backend.app.services import embeddings  # noqa: E402
from backend.app.services.rag import RagRetriever  # noqa: E402
from backend.tests._util import drop_db, make_seeded_db  # noqa: E402

ORG = "retrieval-eval-org"


def load(db, data):
    db.add(Organization(id=ORG, name="Retrieval Eval Org", slug="retrieval-eval"))
    g = BrandGuideline(id=str(uuid.uuid4()), org_id=ORG, filename="NOVA_eval_guidelines.pdf", status="processed",
                       file_path="/eval/NOVA_eval_guidelines.pdf")
    db.add(g)
    for i, p in enumerate(data["passages"]):
        db.add(DocumentChunk(id=str(uuid.uuid4()), guideline_id=g.id, page_number=p["page"], chunk_index=i, content=p["text"]))
    db.commit()


def score(r, queries):
    rows = []
    for q in queries:
        pages = [h["page"] for h in r.search(ORG, q["q"], top_k=3)]
        rank = pages.index(q["gold"]) + 1 if q["gold"] in pages else None
        rows.append((q, rank))

    def agg(subset):
        n = len(subset) or 1
        return (sum(1 for _, k in subset if k == 1) / n, sum(1 for _, k in subset if k) / n,
                sum(1 / k for _, k in subset if k) / n)
    return {"all": agg(rows), "exact": agg([x for x in rows if x[0]["kind"] == "exact"]),
            "paraphrase": agg([x for x in rows if x[0]["kind"] == "paraphrase"]), "rows": rows}


def main():
    here = os.path.dirname(__file__)
    with open(os.path.join(here, "retrieval_dataset.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    engine, Session, path = make_seeded_db()
    db = Session()
    results = {}
    prev = (settings.RAG_MODE, settings.EMBEDDING_PROVIDER)
    try:
        load(db, data)
        # 1) Round 2 baseline
        settings.RAG_MODE = "tfidf"
        r = RagRetriever(db)
        r.index_org(ORG)
        results["tfidf (Round 2)"] = score(r, data["queries"])
        # 2) hybrid without dense
        settings.RAG_MODE, settings.EMBEDDING_PROVIDER = "hybrid", "none"
        embeddings.reset()
        results["hybrid: bm25 + tfidf"] = score(RagRetriever(db), data["queries"])
        # 3) hybrid with dense
        settings.EMBEDDING_PROVIDER = prev[1] if prev[1] != "none" else "auto"
        embeddings.reset()
        st = embeddings.status()
        if st["available"]:
            r = RagRetriever(db)
            r.index_org(ORG)
            results[f"hybrid: bm25 + tfidf + dense ({st['provider']})"] = score(r, data["queries"])
        else:
            print(f"Dense mode skipped: {st['reason']}")
    finally:
        settings.RAG_MODE, settings.EMBEDDING_PROVIDER = prev
        embeddings.reset()
        db.close()
        drop_db(engine, path)

    n = len(data["queries"])
    ex = sum(1 for q in data["queries"] if q["kind"] == "exact")
    print("=" * 84)
    print(f"BRANDVAULT AI — Evidence Retrieval Evaluation (measured) · {len(data['passages'])} passages · "
          f"{n} queries ({ex} exact, {n - ex} paraphrase)")
    print("=" * 84)
    print(f"{'method':48} {'R@1':>6} {'R@3':>6} {'MRR':>6} {'para R@3':>9} {'exact R@3':>10}")
    for name, res in results.items():
        a, p, e = res["all"], res["paraphrase"], res["exact"]
        print(f"{name:48} {a[0]:>6.3f} {a[1]:>6.3f} {a[2]:>6.3f} {p[1]:>9.3f} {e[1]:>10.3f}")
    print("-" * 84)
    last = list(results.values())[-1]["rows"]
    misses = [q["q"] for q, k in last if not k]
    print(f"Misses (top 3) for the last method: {misses or 'none'}")
    print("=" * 84)
    return {k: v["all"] for k, v in results.items()}


if __name__ == "__main__":
    main()
