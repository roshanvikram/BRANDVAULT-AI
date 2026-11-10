"""Load test: fill a fresh database with many real analyses, then time every API list page.

    python -m backend.eval.run_load_test --campaigns 1000
    BV_TEST_DATABASE_URL=postgresql+psycopg://... python -m backend.eval.run_load_test   # on PostgreSQL

Uses the real analyzer (rule engine, no AI calls) on the realistic texts in
inputs/ and backend/eval/, records reviewer decisions like a real team would,
then calls every GET endpoint that takes no path parameter as the demo admin and
reports time and response size. Results go to stdout and --out (JSON).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from backend.app.core.config import settings  # noqa: E402

settings.LLM_ENABLED = False
settings.RATE_LIMIT_ENABLED = False

from fastapi.testclient import TestClient  # noqa: E402

from backend.app.db.session import get_db  # noqa: E402
from backend.app.services import events  # noqa: E402
from backend.app.services.analyzer import ContentAnalyzerService  # noqa: E402
from backend.app.services.llm import NullProvider  # noqa: E402
from backend.app.services.passport_service import PassportService  # noqa: E402
from backend.app.services.seed import NOVA_ORG_ID  # noqa: E402
from backend.main import app  # noqa: E402
from backend.tests._util import drop_db, make_seeded_db  # noqa: E402

DEPARTMENTS = ["Marketing", "E-commerce", "Social", "Retail", "Product", "Support", "PR"]
SKIP = {"/metrics", "/api/v1/auth/google/login", "/api/v1/auth/google/callback", "/api/v1/ready"}


def corpus() -> list[tuple[str, str]]:
    """(title, text) pairs from the realistic input library and the eval sets."""
    out = []
    for folder in ("01_content_intelligence", "02_claim_dna", "07_copy_studio", "11_channel_check"):
        for p in sorted(glob.glob(os.path.join(ROOT, "inputs", folder, "*.txt"))):
            text = open(p, encoding="utf-8", errors="ignore").read().strip()
            if 20 < len(text) < 6000:
                out.append((os.path.splitext(os.path.basename(p))[0].replace("_", " "), text))
    for name in ("realworld_dataset.json", "realworld_holdout.json"):
        p = os.path.join(ROOT, "backend", "eval", name)
        if os.path.exists(p):
            for c in json.load(open(p, encoding="utf-8"))["cases"]:
                out.append((f"{c['channel']} {c['id']}", c["content"]))
    return out


def pct(xs, p):
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(p * len(xs)))], 1) if xs else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaigns", type=int, default=1000)
    ap.add_argument("--decide", type=float, default=0.6, help="share of campaigns that get a reviewer decision")
    ap.add_argument("--out", default="")
    ap.add_argument("--keep", action="store_true", help="keep the SQLite database and print its path")
    a = ap.parse_args(argv)
    random.seed(7)

    engine, Session, path = make_seeded_db()
    events.SYNC, events.session_factory = True, Session

    def _db():
        d = Session()
        try:
            yield d
        finally:
            d.close()
    app.dependency_overrides[get_db] = _db
    report: dict = {"database": engine.dialect.name, "campaigns": a.campaigns}
    try:
        texts = corpus()
        report["unique_texts"] = len(texts)
        print(f"[load] {engine.dialect.name}: {len(texts)} unique realistic texts, creating {a.campaigns} campaigns")

        # 1. Real analyses (rule engine + evidence retrieval), one by one like users submitting.
        db = Session()
        times, ids, failures = [], [], 0
        analyzer = ContentAnalyzerService(db, llm_provider=NullProvider())
        t_all = time.perf_counter()
        for i in range(a.campaigns):
            title, text = texts[i % len(texts)]
            t0 = time.perf_counter()
            try:
                sub = analyzer.analyze_submission(NOVA_ORG_ID, f"{title} #{i + 1}", text,
                                                  author_name=random.choice(["Asha", "Ravi", "Meera", "Arjun", "Divya"]))
                sub.department = random.choice(DEPARTMENTS)
                db.commit()
                ids.append(sub.id)
            except Exception as exc:  # noqa: BLE001
                db.rollback()
                failures += 1
                if failures <= 3:
                    print("[load] analysis failed:", type(exc).__name__, exc)
            times.append((time.perf_counter() - t0) * 1000)
            if (i + 1) % 200 == 0:
                print(f"[load]   {i + 1} analysed, median {pct(times, 0.5)} ms")
        report["analysis"] = {"count": len(ids), "failures": failures, "total_s": round(time.perf_counter() - t_all, 1),
                              "p50_ms": pct(times, 0.5), "p95_ms": pct(times, 0.95), "max_ms": pct(times, 1.0)}

        # 2. Reviewer decisions (passports for approvals).
        ps = PassportService(db)
        dec_t = []
        for sid in random.sample(ids, int(len(ids) * a.decide)):
            d = random.choices(["Approved", "Revision Requested", "Rejected"], [0.6, 0.3, 0.1])[0]
            t0 = time.perf_counter()
            ps.submit_review_decision(sid, d, "load test", reviewer_name="NOVA Reviewer", reviewer_role="Reviewer")
            dec_t.append((time.perf_counter() - t0) * 1000)
        db.commit()
        db.close()
        report["decisions"] = {"count": len(dec_t), "p50_ms": pct(dec_t, 0.5), "p95_ms": pct(dec_t, 0.95)}

        # 3. Every GET page with no path parameter, as the demo admin.
        c = TestClient(app)
        tok = c.post("/api/v1/auth/login", json={"email": "admin@novatech.demo", "password": "Admin@2026"}).json()["access_token"]
        h = {"Authorization": f"Bearer {tok}"}
        pages = []
        for p, ops in app.openapi()["paths"].items():  # every documented route
            if "get" in ops and "{" not in p and p.startswith("/api/v1") and p not in SKIP and not p.endswith(".csv"):
                runs = []
                for _ in range(3):
                    t0 = time.perf_counter()
                    resp = c.get(p, headers=h)
                    runs.append((time.perf_counter() - t0) * 1000)
                pages.append({"path": p, "status": resp.status_code, "ms": round(statistics.median(runs), 1),
                              "kb": round(len(resp.content) / 1024, 1)})
        pages.sort(key=lambda x: -x["ms"])
        report["pages"] = pages
        report["errors"] = [x for x in pages if x["status"] >= 500]

        # 4. Ten people loading the dashboard at once.
        dash = ["/api/v1/content/submissions-summary", "/api/v1/brand/rules", "/api/v1/passport/list",
                "/api/v1/agent/runs", "/api/v1/onboarding/status"]

        def one(_):
            t0 = time.perf_counter()
            codes = [c.get(p, headers=h).status_code for p in dash]
            return (time.perf_counter() - t0) * 1000, codes

        with ThreadPoolExecutor(10) as ex:
            res = list(ex.map(one, range(30)))
        report["dashboard_concurrent"] = {"loads": len(res), "p50_ms": pct([r[0] for r in res], 0.5),
                                          "p95_ms": pct([r[0] for r in res], 0.95),
                                          "non_200": sum(1 for r in res for code in r[1] if code != 200)}
    finally:
        app.dependency_overrides.clear()
        if a.keep and path:
            engine.dispose()
            print("[load] kept database:", path)
        else:
            drop_db(engine, path)

    print(json.dumps({k: v for k, v in report.items() if k != "pages"}, indent=1))
    print("\nslowest pages (median of 3):")
    for x in report["pages"][:15]:
        print(f"  {x['ms']:8.1f} ms  {x['kb']:9.1f} KB  {x['status']}  {x['path']}")
    if report["errors"]:
        print("\nSERVER ERRORS:", report["errors"])
    if a.out:
        json.dump(report, open(a.out, "w", encoding="utf-8"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
