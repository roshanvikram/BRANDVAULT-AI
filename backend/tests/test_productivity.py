"""Productivity features and the scale fixes behind them: bulk check, Fix all, the paged
review list, bulk decisions, CSV export, the light dashboard list, and the faster
similarity search."""
import io
import os
import time
import random
import unittest

from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.job import Job
from backend.app.services import bulk, events
from backend.app.services import jobs as jobs_svc
from backend.app.services import similarity as sm
from backend.main import app
from backend.tests._util import drop_db, make_seeded_db

API = "/api/v1"
DEMO_COPY = "Introducing the world's fastest AI laptop! 10x faster than every competitor. Now only ₹69,999!"


class BulkParsingTests(unittest.TestCase):
    def test_csv_columns_found_by_name(self):
        data = "Campaign,Team,Ad copy\nDiwali,Social,Buy now for ₹79,999\nEmpty,,\n,PR,No title here at all\n".encode()
        items = bulk.parse_file("ads.csv", data)
        self.assertEqual([i["title"] for i in items], ["Diwali", "No title here at all"])
        self.assertEqual(items[0]["department"], "Social")
        with self.assertRaises(bulk.BulkError):
            bulk.parse_file("bad.csv", b"Name,Owner\nA,B\n")

    def test_text_split_on_separator(self):
        items = bulk.parse_file("batch.txt", "Subject: First\nBody one\n---\nSecond piece\n\n===\nThird".encode())
        self.assertEqual([i["title"] for i in items], ["First", "Second piece", "Third"])
        self.assertEqual(len(bulk.parse_file("one.md", b"Just one piece")), 1)

    def test_limits(self):
        with self.assertRaises(bulk.BulkError):
            bulk.clean([{"content": "x"}] * (bulk.MAX_ITEMS + 1))
        with self.assertRaises(bulk.BulkError):
            bulk.clean([{"content": "   "}])
        self.assertEqual(bulk.clean([{"content": "Hello world", "title": ""}])[0]["title"], "Hello world")


class SuggestionWordingTests(unittest.TestCase):
    def test_superlative_fix_uses_only_own_facts(self):
        from types import SimpleNamespace as N
        from backend.app.services.analyzer import replace_once, superlative_fix
        nova = [N(fact_key="Launch Price", fact_value="₹79,999"),
                N(fact_key="NovaCore N10 AI Engine", fact_value="45 TOPS NPU with sustained 3.8 GHz clock speed")]
        self.assertEqual(superlative_fix("world's fastest AI laptop", []), "high-performance AI laptop")  # no borrowed figures
        self.assertNotIn("TOPS", superlative_fix("world's fastest AI laptop", [N(fact_key="Price", fact_value="₹999")]))
        self.assertEqual(superlative_fix("world's fastest AI laptop", nova),
                         "high-performance AI laptop (45 TOPS NPU with sustained 3.8 GHz clock speed)")
        self.assertEqual(superlative_fix("thinnest laptop ever made", nova), "slim laptop")
        text = "Unbeatable performance at an unbeatable price"
        for q in ("Unbeatable performance", "unbeatable price"):
            text = replace_once(text, q, superlative_fix(q, []))
        self.assertEqual(text, "Strong performance at a competitive price")


class SimilarityPairsTests(unittest.TestCase):
    def test_same_pairs_as_comparing_everything(self):
        random.seed(3)
        words = "fast laptop battery price offer sale new pro display bright light thin".split()
        texts = [" ".join(random.choice(words) for _ in range(random.randint(6, 30))) for _ in range(120)]
        texts += texts[:10]  # exact duplicates
        docs = [{"sha": sm.content_sha256(t), "shingles": sm._shingles(t)} for t in texts]
        for t in (0.3, 0.5, 0.8):
            brute = {(i, j) for i in range(len(docs)) for j in range(i + 1, len(docs))
                     if docs[i]["sha"] == docs[j]["sha"] or sm._jaccard(docs[i]["shingles"], docs[j]["shingles"]) >= t}
            fast = {tuple(sorted(p)) for p in sm._similar_pairs(docs, t)}
            self.assertEqual(brute, fast, t)


class ProductivityApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._prev = (settings.LLM_ENABLED, settings.RATE_LIMIT_ENABLED, events.SYNC, events.session_factory,
                     jobs_svc.session_factory, jobs_svc._dispatch)
        settings.LLM_ENABLED = False
        settings.RATE_LIMIT_ENABLED = False
        cls.engine, cls.Session, cls.path = make_seeded_db()
        events.SYNC, events.session_factory = True, cls.Session
        jobs_svc.session_factory = cls.Session
        # SQLite: run jobs inline. PostgreSQL test server: keep the real background thread
        # (it serves one connection at a time, so an inline job would wait on the request).
        if not os.getenv("BV_TEST_DATABASE_URL"):
            jobs_svc._dispatch = jobs_svc.run_job

        def _db():
            d = cls.Session()
            try:
                yield d
            finally:
                d.close()
        app.dependency_overrides[get_db] = _db
        cls.c = TestClient(app)
        tok = lambda e, p: {"Authorization": "Bearer " + cls.c.post(f"{API}/auth/login", json={"email": e, "password": p}).json()["access_token"]}
        cls.admin = tok("admin@novatech.demo", "Admin@2026")
        cls.creator = tok("creator@novatech.demo", "Creator@2026")

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        drop_db(cls.engine, cls.path)
        (settings.LLM_ENABLED, settings.RATE_LIMIT_ENABLED, events.SYNC, events.session_factory,
         jobs_svc.session_factory, jobs_svc._dispatch) = cls._prev

    def analyse(self, title, text, h=None):
        r = self.c.post(f"{API}/content/analyze", headers=h or self.creator, json={"title": title, "content": text})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_bulk_check_end_to_end(self):
        parsed = self.c.post(f"{API}/content/bulk/parse", headers=self.creator,
                             files=[("files", ("ads.csv", b"Title,Copy\nA,Now only \xe2\x82\xb969,999!\nB,Thin and light for everyday work.\n", "text/csv")),
                                    ("files", ("x.exe", b"MZ", "application/octet-stream"))]).json()
        self.assertEqual(len(parsed["items"]), 2)
        self.assertEqual(len(parsed["errors"]), 1)  # unsupported file reported, not silently dropped
        r = self.c.post(f"{API}/content/bulk", headers=self.creator, json={"items": parsed["items"]}).json()
        for _ in range(300):
            b = self.c.get(f"{API}/content/bulk/{r['job_id']}", headers=self.creator).json()
            if b["status"] not in ("queued", "processing"):
                break
            time.sleep(0.1)
        self.assertEqual(b["status"], "completed")
        self.assertEqual((b["total"], b["done"], b["summary"]["checked"]), (2, 2, 2))
        self.assertGreaterEqual(b["summary"]["with_critical"], 1)  # wrong price
        csv_text = self.c.get(f"{API}/content/bulk/{r['job_id']}/export.csv", headers=self.creator).text
        self.assertTrue(csv_text.startswith("﻿#,Title,Score"))
        self.assertEqual(len(self.c.get(f"{API}/content/bulk", headers=self.creator).json()) >= 1, True)
        self.assertEqual(self.c.post(f"{API}/content/bulk", headers=self.creator, json={"items": [{"content": " "}]}).status_code, 422)

    def test_bulk_resumes_after_restart(self):
        db = self.Session()
        try:
            job, _ = jobs_svc.create_job(db, org_id="nova-tech-org-001", kind="bulk_analysis", dispatch=False,
                                         input_data={"items": [{"title": f"T{i}", "content": f"Plain copy number {i}."} for i in range(3)],
                                                     "results": [{"index": 0, "title": "T0", "submission_id": "x", "score": 100,
                                                                  "critical": 0, "warnings": 0, "findings": 0, "status": "Analysed"}]})
            jid = job.id
        finally:
            db.close()
        jobs_svc.run_job(jid)
        db = self.Session()
        try:
            res = db.query(Job).filter(Job.id == jid).first().input_data["results"]
            self.assertEqual([r["index"] for r in res], [0, 1, 2])  # item 0 not checked twice
            self.assertEqual(res[0]["submission_id"], "x")
        finally:
            db.close()

    def test_fix_all(self):
        sub = self.analyse("Fix me", DEMO_COPY)
        self.assertEqual(self.c.post(f"{API}/content/fix-all", headers=self.creator,
                                     json={"submission_id": sub["id"], "expected_version": sub["version"] + 1}).status_code, 409)
        r = self.c.post(f"{API}/content/fix-all", headers=self.creator,
                        json={"submission_id": sub["id"], "expected_version": sub["version"]}).json()
        new = r["submission"]
        self.assertGreaterEqual(len(r["applied"]), 2)
        self.assertEqual(new["version"], sub["version"] + 1)  # one new version, not one per fix
        self.assertIn("₹79,999", new["content"])
        self.assertNotIn("world's fastest", new["content"])
        self.assertGreater(new["overall_score"], sub["overall_score"])
        self.assertTrue(all(s["reason"] for s in r["skipped"]))  # anything not fixed says why

    def test_queue_paging_filter_search(self):
        for i in range(7):
            self.analyse(f"Queue item {i}", "Thin and light for everyday work.")
        p1 = self.c.get(f"{API}/content/queue?q=Queue item&limit=5&offset=0&sort=oldest", headers=self.admin).json()
        p2 = self.c.get(f"{API}/content/queue?q=Queue item&limit=5&offset=5&sort=oldest", headers=self.admin).json()
        self.assertEqual(p1["total"], 7)
        self.assertEqual([len(p1["items"]), len(p2["items"])], [5, 2])
        self.assertEqual(p1["items"][0]["title"], "Queue item 0")
        self.assertNotIn("content", p1["items"][0])  # light rows
        only = self.c.get(f"{API}/content/queue?status=Approved", headers=self.admin).json()
        self.assertTrue(all(i["status"] == "Approved" for i in only["items"]))

    def test_bulk_decisions_keep_safety_rules(self):
        clean = self.analyse("Bulk clean", "Thin and light for everyday work.")
        risky = self.analyse("Bulk risky", DEMO_COPY)
        stale = self.analyse("Bulk stale", "Designed for creators who travel.")
        items = [{"submission_id": clean["id"], "expected_version": clean["version"]},
                 {"submission_id": risky["id"], "expected_version": risky["version"]},
                 {"submission_id": stale["id"], "expected_version": stale["version"] + 5}]
        self.assertEqual(self.c.post(f"{API}/approval/bulk", headers=self.creator,
                                     json={"items": items, "decision": "Approved", "comments": "looks fine"}).status_code, 403)
        r = self.c.post(f"{API}/approval/bulk", headers=self.admin,
                        json={"items": items, "decision": "Approved", "comments": "Bulk approved"}).json()
        self.assertEqual([d["submission_id"] for d in r["decided"]], [clean["id"]])
        self.assertTrue(r["decided"][0]["passport"])
        reasons = {s["submission_id"]: s["reason"] for s in r["skipped"]}
        self.assertIn("critical", reasons[risky["id"]])
        self.assertIn("version", reasons[stale["id"]])
        hist = self.c.get(f"{API}/approval/history/{clean['id']}", headers=self.admin).json()
        self.assertEqual(hist[0]["reviewer_name"], "NOVA Admin")  # recorded under the real reviewer
        # Creators may still send many items for review at once.
        ok = self.c.post(f"{API}/approval/bulk", headers=self.creator,
                         json={"items": [items[1]], "decision": "Pending Review", "comments": "please review"}).json()
        self.assertEqual(len(ok["decided"]), 1)

    def test_export_and_summary_list(self):
        full = self.c.get(f"{API}/content/submissions", headers=self.admin).json()
        light = self.c.get(f"{API}/content/submissions-summary", headers=self.admin).json()
        self.assertEqual([s["id"] for s in full], [s["id"] for s in light])
        for f, s in zip(full, light):
            self.assertEqual(len(f["findings"]), len(s["findings"]))
            self.assertEqual(sorted(x["severity"] for x in f["findings"]), sorted(x["severity"] for x in s["findings"]))
            self.assertLessEqual(len(s["content"]), 160)
        rows = self.c.get(f"{API}/content/export.csv", headers=self.admin).text.splitlines()
        self.assertTrue(rows[0].lstrip("﻿").startswith("Title,Status,Score"))
        self.assertEqual(len(rows) - 1, len(full))

    def test_responses_are_compressed(self):
        r = self.c.get(f"{API}/content/submissions", headers={**self.admin, "Accept-Encoding": "gzip"})
        self.assertEqual(r.headers.get("content-encoding"), "gzip")


if __name__ == "__main__":
    unittest.main()
