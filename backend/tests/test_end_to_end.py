"""Round 3 — the complete product workflow in one test, through the public HTTP API.

guideline upload (Word) -> admin confirms an extracted rule -> creator submits copy ->
creative banner inspected -> launch readiness -> reviewer approves -> Brand Passport ->
passport verification -> publishing gate (API key) -> notifications + signed webhook.
"""
import unittest

from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.services import events, ocr
from backend.main import app
from backend.tests import creative_fixtures as cf
from backend.tests._util import drop_db, make_seeded_db
from backend.tests.test_retrieval import make_docx

API = "/api/v1"


class EndToEndWorkflowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._prev = (settings.LLM_ENABLED, settings.RATE_LIMIT_ENABLED, events.SYNC, events.sender, events.session_factory)
        settings.LLM_ENABLED = False
        settings.RATE_LIMIT_ENABLED = False
        cls.engine, cls.Session, cls.path = make_seeded_db()
        events.SYNC, events.session_factory = True, cls.Session
        cls.sent = []
        events.sender = lambda url, body, headers: (cls.sent.append(headers["X-BrandVault-Event"]) or (200, "ok"))

        def _override():
            d = cls.Session()
            try:
                yield d
            finally:
                d.close()

        app.dependency_overrides[get_db] = _override
        cls.c = TestClient(app)

        def login(email, pw):
            return {"Authorization": f"Bearer {cls.c.post(f'{API}/auth/login', json={'email': email, 'password': pw}).json()['access_token']}"}
        cls.admin = login("admin@novatech.demo", "Admin@2026")
        cls.creator = login("creator@novatech.demo", "Creator@2026")
        cls.reviewer = login("reviewer@novatech.demo", "Reviewer@2026")

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        drop_db(cls.engine, cls.path)
        settings.LLM_ENABLED, settings.RATE_LIMIT_ENABLED, events.SYNC, events.sender, events.session_factory = cls._prev

    def test_full_workflow(self):
        c = self.c
        # 1. Admin uploads a Word guideline; extracted rules wait for confirmation (human gate #1).
        self.assertEqual(c.post(f"{API}/integrations/webhooks", json={"url": "http://localhost:9000/h", "events": ["*"]}, headers=self.admin).status_code, 200)
        g = c.post(f"{API}/brand/guidelines/upload", headers=self.admin, files={"file": ("Social_Policy.docx", make_docx([
            ("Heading1", "Social Media"), (None, "Every post with a price must strictly include T&C apply after the price.")]))})
        self.assertEqual(g.status_code, 200, g.text)
        rules = c.get(f"{API}/brand/rules", headers=self.admin).json()
        new_rule = next(r for r in rules if r["source_document"] == "Social_Policy.docx")
        self.assertFalse(new_rule["is_confirmed"])
        self.assertEqual(c.patch(f"{API}/brand/rules/{new_rule['id']}/confirm", headers=self.creator).status_code, 403)
        self.assertEqual(c.patch(f"{API}/brand/rules/{new_rule['id']}/confirm", headers=self.admin).status_code, 200)

        # 2. Creator submits a draft with a wrong price -> contradicted, reviewers notified.
        bad = c.post(f"{API}/content/analyze", headers=self.creator,
                     json={"title": "Diwali post", "content": "NovaBook AI Pro 16 now only ₹69,999! T&C apply."}).json()
        self.assertIn("Contradicted", [x["status"] for x in bad["claim_verifications"]])
        self.assertTrue(any(n["event"] == "analysis.completed" for n in c.get(f"{API}/notifications", headers=self.reviewer).json()["items"]))

        # 3. The same price inside a banner image is caught by Creative Inspection.
        if ocr.available():
            insp = c.post(f"{API}/creative/inspect", headers=self.creator,
                          files={"file": ("banner.png", cf.banner(["NovaBook AI Pro 16", "Now only ₹69,999"]))}).json()
            self.assertIn("Pricing", [f["category"] for f in insp["submission"]["findings"]])

        # 4. Corrected copy -> launch readiness -> reviewer approves -> Brand Passport.
        good_text = "NovaBook AI Pro 16 is available at ₹79,999. T&C apply. Up to 18 hours mixed productivity workload."
        good = c.post(f"{API}/content/analyze", headers=self.creator, json={"title": "Diwali post v2", "content": good_text}).json()
        ready = c.post(f"{API}/launch/{good['id']}/check", headers=self.reviewer)
        self.assertEqual(ready.status_code, 200, ready.text)
        self.assertNotEqual(ready.json()["state"], "Approved for Launch")  # not approved yet: readiness never approves
        self.assertEqual(c.post(f"{API}/approval/decide", headers=self.creator,
                                json={"submission_id": good["id"], "decision": "Approved", "comments": "self-approve"}).status_code, 403)
        ok = c.post(f"{API}/approval/decide", headers=self.reviewer,
                    json={"submission_id": good["id"], "decision": "Approved", "comments": "Checked", "expected_version": good["version"]})
        self.assertEqual(ok.status_code, 200, ok.text)

        # 5. Passport verification by hand and through the publishing gate.
        v = c.post(f"{API}/passport/verify", headers=self.creator, data={"text": good_text}).json()
        self.assertEqual(v["result"], "Verified Match")
        key = c.post(f"{API}/integrations/api-keys", headers=self.admin, json={"name": "CMS", "scopes": ["gate"]}).json()["key"]
        self.assertTrue(c.post(f"{API}/public/gate", headers={"X-API-Key": key}, json={"text": good_text}).json()["allowed"])
        self.assertFalse(c.post(f"{API}/public/gate", headers={"X-API-Key": key},
                                json={"text": good_text.replace("18 hours", "20 hours")}).json()["allowed"])

        # 6. Every step was announced to the webhook.
        for e in ("analysis.completed", "review.decided", "passport.issued", "publish_gate.blocked"):
            self.assertIn(e, self.sent)


if __name__ == "__main__":
    unittest.main()
