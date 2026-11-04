"""E2 integration tests — exercise the real FastAPI routes end-to-end over a
seeded throwaway DB (TestClient, no lifespan). Covers the brief's integration
flows: analyse, evidence, apply-correction, RAG, auth gating, approval, passport,
persistence, tenant isolation.

Run: `python -m unittest backend.tests.test_integration` (repo root).
"""
import unittest
import uuid

from fastapi.testclient import TestClient

from backend.main import app
from backend.app.db.session import get_db
from backend.app.services.seed import NOVA_ORG_ID
from backend.app.core import security
from backend.app.models.brand import Organization
from backend.app.models.user import User, ROLE_REVIEWER
from backend.app.models.submission import Submission
from backend.tests._util import make_seeded_db, drop_db

NOVA_CONTENT = "Introducing the world's fastest AI laptop! 10x faster than every competitor. Now only ₹69,999!"


class TestApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.Session, cls.path = make_seeded_db()
        # Second org + reviewer + submission for cross-tenant checks.
        db = cls.Session()
        cls.beta_org = "beta-org-test"
        db.add(Organization(id=cls.beta_org, name="BETA CO", slug="beta-co-test"))
        salt, h = security.hash_password("Beta@2026")
        db.add(User(id=str(uuid.uuid4()), email="rev@beta.test", full_name="Beta Reviewer",
                    role=ROLE_REVIEWER, org_id=cls.beta_org, salt=salt, password_hash=h))
        beta_sub = Submission(id=str(uuid.uuid4()), org_id=cls.beta_org, title="Beta", content="y",
                              status="Pending Review")
        db.add(beta_sub)
        db.commit()
        cls.beta_sub_id = beta_sub.id
        db.close()

        def _override():
            d = cls.Session()
            try:
                yield d
            finally:
                d.close()

        app.dependency_overrides[get_db] = _override
        cls.client = TestClient(app)  # not a context manager -> lifespan not run

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        drop_db(cls.engine, cls.path)

    def _token(self, email, pw):
        r = self.client.post("/api/v1/auth/login", json={"email": email, "password": pw})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()["access_token"]

    # ---- basic surface ----
    def test_health(self):
        r = self.client.get("/api/v1/health")
        self.assertEqual(r.status_code, 200)
        self.assertIn("llm", r.json())

    def test_workspaces(self):
        r = self.client.get("/api/v1/brand/workspaces")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(any(o["id"] == NOVA_ORG_ID for o in r.json()))

    # ---- analysis flow ----
    def test_analyze_then_fetch_and_correct(self):
        r = self.client.post("/api/v1/content/analyze",
                             json={"org_id": NOVA_ORG_ID, "title": "camp", "content": NOVA_CONTENT})
        self.assertEqual(r.status_code, 200, r.text)
        sub = r.json()
        self.assertGreater(len(sub["findings"]), 0)
        self.assertTrue(all("Page" in f["evidence_source"] or "retrieved" in f["evidence_source"]
                            for f in sub["findings"]))
        # fetch detail
        d = self.client.get(f"/api/v1/content/submissions/{sub['id']}")
        self.assertEqual(d.status_code, 200)
        # apply a correction -> re-analysis returns a submission
        finding = sub["findings"][0]
        c = self.client.post("/api/v1/content/apply-correction", json={
            "submission_id": sub["id"], "finding_id": finding["id"],
            "target_text": finding["original_text"], "replacement_text": finding["suggested_correction"],
        })
        self.assertEqual(c.status_code, 200, c.text)

    def test_rag_search(self):
        r = self.client.post("/api/v1/rag/search",
                             json={"query": "launch price", "org_id": NOVA_ORG_ID, "top_k": 3})
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["embedder"], "tfidf")
        self.assertGreaterEqual(body["count"], 1)

    def test_upload_type_validation(self):
        bad = self.client.post("/api/v1/brand/guidelines/upload",
                               data={"org_id": NOVA_ORG_ID},
                               files={"file": ("x.exe", b"nope", "application/octet-stream")})
        self.assertEqual(bad.status_code, 400)
        ok = self.client.post("/api/v1/brand/guidelines/upload",
                              data={"org_id": NOVA_ORG_ID},
                              files={"file": ("policy.txt", b"Prohibited: never say cheap.\n\nPrices must be exact.", "text/plain")})
        self.assertEqual(ok.status_code, 200, ok.text)

    # ---- auth + approval gating ----
    def test_decide_requires_auth(self):
        sub = self.client.post("/api/v1/content/analyze",
                               json={"org_id": NOVA_ORG_ID, "title": "a", "content": NOVA_CONTENT}).json()
        r = self.client.post("/api/v1/approval/decide",
                             json={"submission_id": sub["id"], "decision": "Approved", "comments": "c"})
        self.assertEqual(r.status_code, 401)

    def test_creator_cannot_approve_but_can_submit(self):
        tok = self._token("creator@novatech.demo", "Creator@2026")
        sub = self.client.post("/api/v1/content/analyze",
                               json={"org_id": NOVA_ORG_ID, "title": "b", "content": NOVA_CONTENT}).json()
        h = {"Authorization": f"Bearer {tok}"}
        approve = self.client.post("/api/v1/approval/decide", headers=h,
                                   json={"submission_id": sub["id"], "decision": "Approved", "comments": "c"})
        self.assertEqual(approve.status_code, 403)
        submit = self.client.post("/api/v1/approval/decide", headers=h,
                                  json={"submission_id": sub["id"], "decision": "Pending Review", "comments": "review pls"})
        self.assertEqual(submit.status_code, 200, submit.text)

    def test_reviewer_approves_issues_passport_and_attribution(self):
        tok = self._token("reviewer@novatech.demo", "Reviewer@2026")
        sub = self.client.post("/api/v1/content/analyze",
                               json={"org_id": NOVA_ORG_ID, "title": "c", "content": "Clean copy at ₹79,999."}).json()
        h = {"Authorization": f"Bearer {tok}"}
        r = self.client.post("/api/v1/approval/decide", headers=h,
                             json={"submission_id": sub["id"], "decision": "Approved", "comments": "ok",
                                   "reviewer_name": "FORGED", "reviewer_role": "Administrator"})
        self.assertEqual(r.status_code, 200, r.text)
        hist = self.client.get(f"/api/v1/approval/history/{sub['id']}").json()
        self.assertEqual(hist[0]["reviewer_name"], "NOVA Reviewer")  # forged name ignored
        pp = self.client.get(f"/api/v1/passport/by-submission/{sub['id']}")
        self.assertEqual(pp.status_code, 200)

    def test_cross_tenant_denied(self):
        tok = self._token("reviewer@novatech.demo", "Reviewer@2026")
        r = self.client.post("/api/v1/approval/decide",
                             headers={"Authorization": f"Bearer {tok}"},
                             json={"submission_id": self.beta_sub_id, "decision": "Approved", "comments": "x"})
        self.assertEqual(r.status_code, 403)

    # ---- persistence ----
    def test_persistence(self):
        sub = self.client.post("/api/v1/content/analyze",
                               json={"org_id": NOVA_ORG_ID, "title": "persist", "content": NOVA_CONTENT}).json()
        again = self.client.get(f"/api/v1/content/submissions/{sub['id']}")
        self.assertEqual(again.status_code, 200)
        self.assertEqual(again.json()["id"], sub["id"])


if __name__ == "__main__":
    unittest.main()
