"""Round 3 · Improvement 2 — API keys, public Check API, publishing gate, webhooks, notifications,
channel/disclaimer agents and the MCP server."""
import hashlib
import hmac
import json
import os
import sys
import unittest

from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.integration import ApiKey, WebhookDelivery
from backend.app.models.submission import Submission
from backend.app.services import channels, events
from backend.app.services.seed import NOVA_ORG_ID, seed_vortexa_brand
from backend.main import app
from backend.tests._util import drop_db, make_seeded_db

API = "/api/v1"


class ChannelAgentUnitTests(unittest.TestCase):
    CH = {"x": {"label": "X", "max_chars": 20, "aspect_ratios": ["16:9"], "required": ["#ad"]}}

    def test_limits_required_elements_and_aspect(self):
        r = channels.check_channels("A long post that is over twenty characters", self.CH, ["x"], 1000, 1000)[0]
        self.assertFalse(r["ok"])
        self.assertEqual(len(r["issues"]), 3)
        ok = channels.check_channels("Short #ad", self.CH, ["x"], 1600, 900)[0]
        self.assertTrue(ok["ok"], ok)

    def test_disclaimers_only_when_triggered(self):
        rules = [{"id": "p", "label": "Price", "trigger": r"₹\s*\d", "region": "IN", "required_any": ["T&C apply"]}]
        self.assertEqual(channels.check_disclaimers("No price here", rules, "IN"), [])
        self.assertFalse(channels.check_disclaimers("Only ₹79,999", rules, "IN")[0]["ok"])
        self.assertTrue(channels.check_disclaimers("Only ₹79,999. T&C apply", rules, "IN")[0]["ok"])
        self.assertEqual(channels.check_disclaimers("Only ₹79,999", rules, "US"), [])


class WebhookUrlTests(unittest.TestCase):
    def test_url_rules(self):
        self.assertFalse(events.url_allowed("ftp://example.com/x")[0])
        self.assertFalse(events.url_allowed("http://10.0.0.5/hook")[0])
        self.assertTrue(events.url_allowed("http://localhost:9000/hook")[0])  # allowed outside production only
        prev = settings.ENVIRONMENT
        settings.ENVIRONMENT = "production"
        try:
            self.assertFalse(events.url_allowed("http://localhost:9000/hook")[0])
        finally:
            settings.ENVIRONMENT = prev


class IntegrationApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._prev = (settings.LLM_ENABLED, settings.RATE_LIMIT_ENABLED, events.SYNC, events.sender, events.session_factory, events.RETRY_DELAYS)
        settings.LLM_ENABLED = False
        settings.RATE_LIMIT_ENABLED = False
        cls.engine, cls.Session, cls.path = make_seeded_db()
        db = cls.Session()
        seed_vortexa_brand(db)
        db.close()
        events.SYNC = True
        events.session_factory = cls.Session
        events.RETRY_DELAYS = (0.0, 0.0, 0.0)
        cls.sent = []
        events.sender = lambda url, body, headers: (cls.sent.append((url, body, headers)) or (cls.status, "ok"))
        cls.status = 200

        def _override():
            d = cls.Session()
            try:
                yield d
            finally:
                d.close()

        app.dependency_overrides[get_db] = _override
        cls.client = TestClient(app)

        def login(email, pw):
            r = cls.client.post(f"{API}/auth/login", json={"email": email, "password": pw})
            return {"Authorization": f"Bearer {r.json()['access_token']}"}
        cls.admin = login("admin@novatech.demo", "Admin@2026")
        cls.creator = login("creator@novatech.demo", "Creator@2026")
        cls.reviewer = login("reviewer@novatech.demo", "Reviewer@2026")
        cls.vx_admin = login("admin@vortexa.demo", "Admin@2026")

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        drop_db(cls.engine, cls.path)
        (settings.LLM_ENABLED, settings.RATE_LIMIT_ENABLED, events.SYNC, events.sender,
         events.session_factory, events.RETRY_DELAYS) = cls._prev

    def _key(self, headers=None, scopes=("check", "gate", "read")):
        r = self.client.post(f"{API}/integrations/api-keys", json={"name": "CI", "scopes": list(scopes)}, headers=headers or self.admin)
        self.assertEqual(r.status_code, 200, r.text)
        return {"X-API-Key": r.json()["key"]}, r.json()["api_key"]["id"]

    def test_api_keys_admin_only_hashed_and_revocable(self):
        self.assertEqual(self.client.post(f"{API}/integrations/api-keys", json={"name": "x"}, headers=self.creator).status_code, 403)
        key, kid = self._key()
        db = self.Session()
        row = db.get(ApiKey, kid)
        self.assertEqual(row.key_hash, hashlib.sha256(key["X-API-Key"].encode()).hexdigest())
        db.close()
        listed = self.client.get(f"{API}/integrations/api-keys", headers=self.admin).json()["keys"]
        self.assertNotIn(key["X-API-Key"], json.dumps(listed))
        self.assertEqual(self.client.get(f"{API}/public/brand", headers=key).status_code, 200)
        self.client.delete(f"{API}/integrations/api-keys/{kid}", headers=self.admin)
        self.assertEqual(self.client.get(f"{API}/public/brand", headers=key).status_code, 401)
        self.assertEqual(self.client.get(f"{API}/public/brand").status_code, 401)

    def test_scopes_enforced(self):
        key, _ = self._key(scopes=("read",))
        self.assertEqual(self.client.post(f"{API}/public/check", json={"text": "Hello world"}, headers=key).status_code, 403)
        self.assertEqual(self.client.post(f"{API}/public/gate", json={"text": "Hello"}, headers=key).status_code, 403)

    def test_check_api_dry_run_saves_nothing_persist_notifies(self):
        key, _ = self._key()
        db = self.Session()
        before = db.query(Submission).count()
        db.close()  # never hold a transaction open across an API call
        r = self.client.post(f"{API}/public/check", json={"text": "Now only ₹69,999!", "channels": ["x"], "region": "IN"}, headers=key)
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertIsNone(body["submission_id"])
        self.assertIn("Pricing", [f["category"] for f in body["findings"]])
        self.assertFalse(body["publishable"])
        self.assertTrue(any(d["id"] == "price-tc" and not d["ok"] for d in body["disclaimers"]))
        db = self.Session()
        self.assertEqual(db.query(Submission).count(), before)
        db.close()
        r = self.client.post(f"{API}/public/check", json={"text": "NovaBook AI Pro 16 at ₹79,999", "persist": True, "title": "CMS draft"}, headers=key)
        self.assertIsNotNone(r.json()["submission_id"])
        db.close()
        rev = self.client.get(f"{API}/notifications", headers=self.reviewer).json()
        self.assertTrue(any(n["event"] == "analysis.completed" and "CMS draft" in n["title"] for n in rev["items"]))
        cre = self.client.get(f"{API}/notifications", headers=self.creator).json()
        self.assertFalse(any(n["event"] == "analysis.completed" for n in cre["items"]))  # reviewers' task only

    def test_publish_gate_end_to_end_and_webhook_signature(self):
        hook = self.client.post(f"{API}/integrations/webhooks", json={"url": "http://localhost:9999/hook", "events": ["*"]}, headers=self.admin).json()
        secret = hook["secret"]
        key, _ = self._key()
        text = "Meet NovaBook AI Pro 16. Available at ₹79,999 with a 2-Year On-Site Limited Hardware Warranty."
        self.assertFalse(self.client.post(f"{API}/public/gate", json={"text": text}, headers=key).json()["allowed"])
        sub_id = self.client.post(f"{API}/public/check", json={"text": text, "persist": True, "title": "Gate test"}, headers=key).json()["submission_id"]
        r = self.client.post(f"{API}/approval/decide", json={"submission_id": sub_id, "decision": "Approved", "comments": "ok"}, headers=self.reviewer)
        self.assertEqual(r.status_code, 200, r.text)
        gate = self.client.post(f"{API}/public/gate", json={"text": text}, headers=key).json()
        self.assertTrue(gate["allowed"], gate)
        self.assertTrue(gate["passport_number"])
        edited = self.client.post(f"{API}/public/gate", json={"text": text.replace("2-Year", "3-Year")}, headers=key).json()
        self.assertFalse(edited["allowed"])
        self.assertEqual(edited["result"], "Modified After Approval")
        evs = [h["X-BrandVault-Event"] for _, _, h in self.sent]
        for e in ("analysis.completed", "review.decided", "passport.issued", "publish_gate.blocked"):
            self.assertIn(e, evs)
        url, body, headers = self.sent[-1]
        expected = "sha256=" + hmac.new(secret.encode(), headers["X-BrandVault-Timestamp"].encode() + b"." + body, hashlib.sha256).hexdigest()
        self.assertEqual(headers["X-BrandVault-Signature"], expected)
        self.client.delete(f"{API}/integrations/webhooks/{hook['webhook']['id']}", headers=self.admin)

    def test_failed_webhook_retried_and_logged(self):
        hook = self.client.post(f"{API}/integrations/webhooks", json={"url": "http://localhost:9998/hook", "events": ["review.decided"]}, headers=self.admin).json()
        type(self).status = 500
        try:
            self.client.post(f"{API}/integrations/webhooks/{hook['webhook']['id']}/test", headers=self.admin)
        finally:
            type(self).status = 200
        d = self.client.get(f"{API}/integrations/deliveries", headers=self.admin).json()[0]
        self.assertEqual((d["status"], d["attempts"], d["status_code"]), ("failed", 3, 500))
        self.client.delete(f"{API}/integrations/webhooks/{hook['webhook']['id']}", headers=self.admin)

    def test_webhook_validation_and_admin_only(self):
        self.assertEqual(self.client.post(f"{API}/integrations/webhooks", json={"url": "http://10.1.2.3/x"}, headers=self.admin).status_code, 422)
        self.assertEqual(self.client.post(f"{API}/integrations/webhooks", json={"url": "http://localhost:1/x", "events": ["nope"]}, headers=self.admin).status_code, 422)
        self.assertEqual(self.client.get(f"{API}/integrations/webhooks", headers=self.creator).status_code, 403)

    def test_tenant_isolation_for_keys_and_submissions(self):
        key, _ = self._key()
        sub_id = self.client.post(f"{API}/public/check", json={"text": "NovaBook AI Pro 16", "persist": True}, headers=key).json()["submission_id"]
        vx_key, _ = self._key(headers=self.vx_admin)
        self.assertEqual(self.client.get(f"{API}/public/submissions/{sub_id}", headers=vx_key).status_code, 404)
        self.assertEqual(self.client.get(f"{API}/public/brand", headers=vx_key).json()["organization"], "VORTEXA TECHNOLOGIES")
        self.assertNotIn("CI", [k["name"] for k in self.client.get(f"{API}/integrations/api-keys", headers=self.vx_admin).json()["keys"]
                                if k["prefix"] == key["X-API-Key"][:10]])

    def test_notifications_mark_read(self):
        n = self.client.get(f"{API}/notifications", headers=self.reviewer).json()
        if n["items"]:
            self.client.post(f"{API}/notifications/read", json=[n["items"][0]["id"]], headers=self.reviewer)
            again = self.client.get(f"{API}/notifications", headers=self.reviewer).json()
            self.assertTrue(again["items"][0]["read"])
        self.client.post(f"{API}/notifications/read", headers=self.reviewer)
        self.assertEqual(self.client.get(f"{API}/notifications", headers=self.reviewer).json()["unread"], 0)

    def test_channel_check_endpoint(self):
        r = self.client.post(f"{API}/channels/check", json={"text": "x" * 300, "channels": ["x"]}, headers=self.creator).json()
        self.assertFalse(r["channels"][0]["ok"])
        self.assertIn("x", r["available_channels"])


class McpServerTests(unittest.TestCase):
    def test_tools_are_read_only_and_cannot_approve(self):
        try:
            import mcp  # noqa: F401
        except ImportError:
            self.skipTest("mcp SDK not installed")
        import asyncio
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        import mcp_server
        tools = asyncio.run(mcp_server.build_server().list_tools())
        names = {t.name for t in tools}
        self.assertEqual(names, {"get_brand_profile", "search_brand_guidelines", "check_copy", "check_publish_gate", "get_review_status"})
        self.assertTrue(all(t.annotations.read_only_hint for t in tools))
        self.assertFalse(any("approve" in n or "publish" == n for n in names))


if __name__ == "__main__":
    unittest.main()
