"""Company readiness: workspaces, invitations, lockout, two-step sign-in, session
revocation, data export and erasure, operations, domain watch, AI fallback, backups."""
import io
import json
import os
import tempfile
import time
import unittest
import uuid
import zipfile

from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.core import observability
from backend.app.core.config import settings
from backend.app.core.security import password_problem, totp_code, verify_totp
from backend.app.db.session import get_db
from backend.app.models.account import DomainWatchHit, ErrorEvent, SecurityEvent
from backend.app.models.brand import Organization
from backend.app.models.intelligence import OfficialDomain
from backend.app.models.user import User
from backend.app.services import ctwatch, llm
from backend.main import app
from backend.tests._util import drop_db, make_seeded_db

API = "/api/v1"


class TotpAndPasswordTests(unittest.TestCase):
    def test_rfc6238_vector(self):
        # RFC 6238 Appendix B, SHA-1 secret "12345678901234567890" at T=59 s -> 94287082 (last 6 digits).
        secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        self.assertEqual(totp_code(secret, at=59), "287082")
        self.assertEqual(totp_code(secret, at=1111111109), "081804")
        self.assertTrue(verify_totp(secret, "287082", at=59 + 25))   # one step of drift is fine
        self.assertFalse(verify_totp(secret, "287082", at=59 + 95))  # three steps later is not
        self.assertFalse(verify_totp(secret, "12345", at=59))

    def test_password_rules(self):
        self.assertIsNotNone(password_problem("short1", "", 10))
        self.assertIsNotNone(password_problem("onlyletterslong", "", 10))
        self.assertIsNotNone(password_problem("password123", "", 10))
        self.assertIsNotNone(password_problem("priya2026secure", "priya@acme.com", 10))
        self.assertIsNone(password_problem("Blue-River-2026", "priya@acme.com", 10))


class _Api(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._prev = (settings.LLM_ENABLED, settings.RATE_LIMIT_ENABLED)
        settings.LLM_ENABLED = False
        settings.RATE_LIMIT_ENABLED = False
        cls.engine, cls.Session, cls.path = make_seeded_db()

        def _override():
            d = cls.Session()
            try:
                yield d
            finally:
                d.close()
        app.dependency_overrides[get_db] = _override
        observability.session_factory = cls.Session
        cls.c = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        observability.session_factory = None
        app.dependency_overrides.clear()
        drop_db(cls.engine, cls.path)
        settings.LLM_ENABLED, settings.RATE_LIMIT_ENABLED = cls._prev

    def login(self, email, password, code=None):
        body = {"email": email, "password": password}
        if code:
            body["mfa_code"] = code
        return self.c.post(f"{API}/auth/login", json=body)

    def auth(self, token):
        return {"Authorization": f"Bearer {token}"}

    def new_company(self, company="Acme Foods"):
        email = f"owner-{uuid.uuid4().hex[:8]}@acme.example"
        r = self.c.post(f"{API}/auth/register", json={"email": email, "password": "Blue-River-2026", "full_name": "Asha Owner",
                                                       "workspace": "new", "company_name": company})
        self.assertEqual(r.status_code, 201, r.text)
        return email, r.json()


class WorkspaceAndTeamTests(_Api):
    def test_new_company_workspace(self):
        email, body = self.new_company("Acme Foods")
        self.assertEqual(body["user"]["role"], "Administrator")
        self.assertNotEqual(body["user"]["org_id"], "nova-tech-org-001")
        h = self.auth(body["access_token"])
        ob = self.c.get(f"{API}/onboarding/status", headers=h).json()
        self.assertEqual(ob["org"]["name"], "Acme Foods")
        self.assertFalse(ob["is_demo"])
        members = self.c.get(f"{API}/team/members", headers=h).json()["members"]
        self.assertEqual([m["email"] for m in members], [email])
        # cannot see the demo company's data
        self.assertEqual(self.c.get(f"{API}/fraud/incidents", headers=h).json(), [])
        self.assertEqual(self.c.post(f"{API}/auth/register", json={"email": "x@y.example", "password": "Blue-River-2026",
                                                                    "full_name": "X", "workspace": "new", "company_name": ""}).status_code, 422)

    def test_invite_flow_and_role(self):
        _, body = self.new_company("Invite Co")
        h = self.auth(body["access_token"])
        r = self.c.post(f"{API}/team/invites", headers=h, json={"email": "rev@invite.example", "role": "Reviewer"})
        self.assertEqual(r.status_code, 200, r.text)
        token = r.json()["link"].split("invite=")[1]
        self.assertEqual(r.json()["invite"]["email_status"], "email not configured")
        info = self.c.get(f"{API}/auth/invite/{token}").json()
        self.assertEqual((info["email"], info["role"], info["workspace"]), ("rev@invite.example", "Reviewer", "Invite Co"))
        wrong = self.c.post(f"{API}/auth/register", json={"email": "other@invite.example", "password": "Blue-River-2026",
                                                           "full_name": "Other", "invite_token": token})
        self.assertEqual(wrong.status_code, 400)
        ok = self.c.post(f"{API}/auth/register", json={"email": "rev@invite.example", "password": "Blue-River-2026",
                                                        "full_name": "Ravi Reviewer", "invite_token": token})
        self.assertEqual(ok.status_code, 201, ok.text)
        self.assertEqual(ok.json()["user"]["role"], "Reviewer")
        self.assertEqual(ok.json()["user"]["org_id"], body["user"]["org_id"])
        again = self.c.post(f"{API}/auth/register", json={"email": "rev2@invite.example", "password": "Blue-River-2026",
                                                           "full_name": "Again", "invite_token": token})
        self.assertEqual(again.status_code, 400)  # used
        # a Reviewer cannot manage the team
        self.assertEqual(self.c.post(f"{API}/team/invites", headers=self.auth(ok.json()["access_token"]),
                                     json={"email": "z@z.example", "role": "Administrator"}).status_code, 403)
        listed = self.c.get(f"{API}/team/invites", headers=h).json()["invites"]
        self.assertEqual(listed[0]["status"], "accepted")

    def test_last_admin_guard_and_role_change_signs_out(self):
        _, body = self.new_company("Guard Co")
        h = self.auth(body["access_token"])
        me = body["user"]["id"]
        r = self.c.patch(f"{API}/team/members/{me}", headers=h, json={"role": "Creator"})
        self.assertEqual(r.status_code, 400)
        tok = self.c.post(f"{API}/team/invites", headers=h, json={"email": "c@guard.example", "role": "Creator"}).json()["link"].split("invite=")[1]
        c = self.c.post(f"{API}/auth/register", json={"email": "c@guard.example", "password": "Blue-River-2026",
                                                       "full_name": "Cara", "invite_token": tok}).json()
        ch = self.auth(c["access_token"])
        self.assertEqual(self.c.get(f"{API}/auth/me", headers=ch).status_code, 200)
        r = self.c.patch(f"{API}/team/members/{c['user']['id']}", headers=h, json={"role": "Reviewer"})
        self.assertEqual(r.json()["role"], "Reviewer")
        self.assertEqual(self.c.get(f"{API}/auth/me", headers=ch).status_code, 401)  # old token is void
        self.assertEqual(self.c.patch(f"{API}/team/members/{c['user']['id']}", headers=h, json={"active": False}).json()["active"], False)
        self.assertEqual(self.login("c@guard.example", "Blue-River-2026").status_code, 403)

    def test_demo_signup_default_unchanged(self):
        r = self.c.post(f"{API}/auth/register", json={"email": f"d-{uuid.uuid4().hex[:6]}@x.example",
                                                       "password": "Blue-River-2026", "full_name": "Demo"})
        self.assertEqual(r.json()["user"]["role"], "Creator")
        self.assertEqual(r.json()["user"]["org_id"], "nova-tech-org-001")
        self.assertEqual(self.c.get(f"{API}/auth/signup-options").json()["new_workspace"], True)


class SignInSecurityTests(_Api):
    def test_lockout_and_unlock(self):
        email, body = self.new_company("Lock Co")
        tok = self.c.post(f"{API}/team/invites", headers=self.auth(body["access_token"]),
                          json={"email": "l@lock.example", "role": "Creator"}).json()["link"].split("invite=")[1]
        u = self.c.post(f"{API}/auth/register", json={"email": "l@lock.example", "password": "Blue-River-2026",
                                                       "full_name": "Lee", "invite_token": tok}).json()["user"]
        codes = [self.login("l@lock.example", "wrong-pass-1").status_code for _ in range(settings.LOGIN_MAX_FAILURES)]
        self.assertEqual(codes, [401] * settings.LOGIN_MAX_FAILURES)
        self.assertEqual(self.login("l@lock.example", "Blue-River-2026").status_code, 423)  # even the right password
        self.c.post(f"{API}/team/members/{u['id']}/unlock", headers=self.auth(body["access_token"]))
        self.assertEqual(self.login("l@lock.example", "Blue-River-2026").status_code, 200)
        actions = [e["action"] for e in self.c.get(f"{API}/team/audit", headers=self.auth(body["access_token"])).json()["events"]]
        self.assertIn("login.locked", actions)
        self.assertIn("member.unlocked", actions)

    def test_two_step_sign_in(self):
        email, body = self.new_company("MFA Co")
        h = self.auth(body["access_token"])
        setup = self.c.post(f"{API}/auth/mfa/setup", headers=h).json()
        self.assertTrue(setup["otpauth_uri"].startswith("otpauth://totp/"))
        self.assertEqual(self.c.post(f"{API}/auth/mfa/enable", headers=h, json={"code": "000000"}).status_code, 400)
        on = self.c.post(f"{API}/auth/mfa/enable", headers=h, json={"code": totp_code(setup["secret"])})
        self.assertEqual(on.status_code, 200, on.text)
        self.assertTrue(on.json()["user"]["mfa_enabled"])
        self.assertEqual(self.c.get(f"{API}/auth/me", headers=h).status_code, 401)  # older sessions end
        r = self.login(email, "Blue-River-2026")
        self.assertEqual((r.status_code, r.json()["detail"]), (401, "mfa_required"))
        self.assertEqual(self.login(email, "Blue-River-2026", "123456").json()["detail"], "mfa_invalid")
        ok = self.login(email, "Blue-River-2026", totp_code(setup["secret"]))
        self.assertEqual(ok.status_code, 200)
        h2 = self.auth(ok.json()["access_token"])
        off = self.c.post(f"{API}/auth/mfa/disable", headers=h2, json={"code": totp_code(setup["secret"]), "password": "Blue-River-2026"})
        self.assertEqual(off.status_code, 200, off.text)
        self.assertEqual(self.login(email, "Blue-River-2026").status_code, 200)

    def test_password_change_revokes_sessions(self):
        email, body = self.new_company("Pw Co")
        h = self.auth(body["access_token"])
        self.assertEqual(self.c.post(f"{API}/auth/password", headers=h, json={"current_password": "nope", "new_password": "Green-Hill-2027"}).status_code, 400)
        self.assertEqual(self.c.post(f"{API}/auth/password", headers=h, json={"current_password": "Blue-River-2026", "new_password": "weak"}).status_code, 422)
        r = self.c.post(f"{API}/auth/password", headers=h, json={"current_password": "Blue-River-2026", "new_password": "Green-Hill-2027"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(self.c.get(f"{API}/auth/me", headers=h).status_code, 401)
        self.assertEqual(self.c.get(f"{API}/auth/me", headers=self.auth(r.json()["access_token"])).status_code, 200)
        self.assertEqual(self.login(email, "Green-Hill-2027").status_code, 200)
        new = self.c.post(f"{API}/auth/logout-all", headers=self.auth(r.json()["access_token"])).json()["access_token"]
        self.assertEqual(self.c.get(f"{API}/auth/me", headers=self.auth(r.json()["access_token"])).status_code, 401)
        self.assertEqual(self.c.get(f"{API}/auth/me", headers=self.auth(new)).status_code, 200)


class PrivacyTests(_Api):
    def test_export_is_scoped_and_has_no_secrets(self):
        _, body = self.new_company("Export Co")
        h = self.auth(body["access_token"])
        self.c.post(f"{API}/fraud/domains", headers=h, json={"domain": "exportco.example"})
        self.c.post(f"{API}/auth/mfa/setup", headers=h)
        r = self.c.get(f"{API}/privacy/export", headers=h)
        self.assertEqual(r.status_code, 200)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        data = json.loads(z.read("data.json"))
        self.assertEqual([o["name"] for o in data["organizations"]], ["Export Co"])
        self.assertEqual([d["domain"] for d in data["official_domains"]], ["exportco.example"])
        self.assertEqual(data["users"][0]["password_hash"], "[removed]")
        self.assertEqual(data["users"][0]["mfa_secret"], "[removed]")
        blob = z.read("data.json").decode()
        self.assertNotIn("novatech.demo", blob)
        self.assertNotIn("nova-tech-org-001", blob)

    def test_workspace_deletion(self):
        email, body = self.new_company("Gone Co")
        h = self.auth(body["access_token"])
        org_id = body["user"]["org_id"]
        self.c.post(f"{API}/fraud/domains", headers=h, json={"domain": "goneco.example"})
        self.assertEqual(self.c.post(f"{API}/privacy/delete-workspace", headers=h, json={"confirm": "wrong", "password": "Blue-River-2026"}).status_code, 400)
        r = self.c.post(f"{API}/privacy/delete-workspace", headers=h, json={"confirm": "Gone Co", "password": "Blue-River-2026"})
        self.assertEqual(r.status_code, 200, r.text)
        db = self.Session()
        try:
            self.assertIsNone(db.query(Organization).filter(Organization.id == org_id).first())
            self.assertEqual(db.query(User).filter(User.org_id == org_id).count(), 0)
            self.assertEqual(db.query(OfficialDomain).filter(OfficialDomain.org_id == org_id).count(), 0)
            self.assertIsNotNone(db.query(Organization).filter(Organization.id == "nova-tech-org-001").first())
            self.assertGreater(db.query(User).filter(User.org_id == "nova-tech-org-001").count(), 0)
            self.assertTrue(db.query(SecurityEvent).filter(SecurityEvent.action == "workspace.deleted").count())
        finally:
            db.close()
        self.assertEqual(self.login(email, "Blue-River-2026").status_code, 401)

    def test_demo_workspace_protected_and_account_deletion(self):
        admin = self.login("admin@novatech.demo", "Admin@2026").json()["access_token"]
        r = self.c.post(f"{API}/privacy/delete-workspace", headers=self.auth(admin), json={"confirm": "NOVA TECH", "password": "Admin@2026"})
        self.assertEqual(r.status_code, 403)
        u = self.c.post(f"{API}/auth/register", json={"email": "leaver@x.example", "password": "Blue-River-2026", "full_name": "Leaver"}).json()
        hh = self.auth(u["access_token"])
        self.assertEqual(self.c.post(f"{API}/privacy/delete-account", headers=hh, json={"confirm": "no", "password": "Blue-River-2026"}).status_code, 400)
        self.assertEqual(self.c.post(f"{API}/privacy/delete-account", headers=hh, json={"confirm": "DELETE", "password": "Blue-River-2026"}).status_code, 200)
        self.assertEqual(self.login("leaver@x.example", "Blue-River-2026").status_code, 401)
        self.assertEqual(self.c.get(f"{API}/auth/me", headers=hh).status_code, 401)


class OperationsTests(_Api):
    def test_request_id_and_security_headers(self):
        r = self.c.get(f"{API}/health", headers={"X-Request-ID": "trace-12345678"})
        self.assertEqual(r.headers["X-Request-ID"], "trace-12345678")
        self.assertEqual(r.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(r.headers["X-Frame-Options"], "DENY")
        self.assertEqual(len(self.c.get(f"{API}/health", headers={"X-Request-ID": "bad id!"}).headers["X-Request-ID"]), 32)
        self.assertEqual(self.c.get(f"{API}/ready").json(), {"ready": True})

    def test_unhandled_error_is_captured(self):
        def boom():
            raise RuntimeError("database exploded")
        app.add_api_route("/__boom", boom)
        try:
            r = self.c.get("/__boom")
            self.assertEqual(r.status_code, 500)
            self.assertNotIn("exploded", r.text)  # no internals to the browser
            rid = r.json()["request_id"]
            self.assertEqual(r.headers["X-Request-ID"], rid)
        finally:
            app.router.routes = [rt for rt in app.router.routes if getattr(rt, "path", "") != "/__boom"]
        db = self.Session()
        try:
            row = db.query(ErrorEvent).filter(ErrorEvent.request_id == rid).first()
            self.assertIsNotNone(row)
            self.assertIn("exploded", row.message)
        finally:
            db.close()

    def test_metrics_and_status(self):
        prev = settings.METRICS_TOKEN
        self.c.get(f"{API}/health")
        try:
            settings.METRICS_TOKEN = ""
            self.assertEqual(self.c.get("/metrics").status_code, 404)
            settings.METRICS_TOKEN = "scrape-token-123"
            self.assertEqual(self.c.get("/metrics", headers={"Authorization": "Bearer nope"}).status_code, 401)
            m = self.c.get("/metrics", headers={"Authorization": "Bearer scrape-token-123"})
            self.assertEqual(m.status_code, 200)
            self.assertIn("brandvault_requests_total{", m.text)
            self.assertIn('brandvault_request_seconds_bucket{route="/api/v1/health",le="+Inf"}', m.text)
        finally:
            settings.METRICS_TOKEN = prev
        admin = self.login("admin@novatech.demo", "Admin@2026").json()["access_token"]
        s = self.c.get(f"{API}/system/status", headers=self.auth(admin)).json()
        self.assertTrue(s["database"]["ok"])
        self.assertGreater(s["traffic"]["requests"], 0)
        creator = self.login("creator@novatech.demo", "Creator@2026").json()["access_token"]
        self.assertEqual(self.c.get(f"{API}/system/status", headers=self.auth(creator)).status_code, 403)


class DomainWatchTests(_Api):
    def test_scan_scores_and_stores_lookalikes(self):
        _, body = self.new_company("Zentrova Labs")
        h = self.auth(body["access_token"])
        org_id = body["user"]["org_id"]
        self.c.post(f"{API}/fraud/domains", headers=h, json={"domain": "zentrova.com"})
        rows = [{"id": 101, "name_value": "zentrova.com\nwww.zentrova.com", "issuer_name": "C=US, O=Let's Encrypt", "not_before": "2026-11-01T00:00:00"},
                {"id": 102, "name_value": "zentrova-offers.shop", "issuer_name": "C=US, O=Let's Encrypt", "not_before": "2026-11-05T10:00:00"},
                {"id": 103, "name_value": "*.zentr0va.com", "issuer_name": "C=US, O=ZeroSSL", "not_before": "2026-11-06T10:00:00"},
                {"id": 104, "name_value": "unrelated.org", "issuer_name": "x", "not_before": None}]
        db = self.Session()
        try:
            out = ctwatch.scan(db, org_id, fetch=lambda term: rows)
            self.assertIn("zentrova", out["terms"])
            hosts = {h.host: h for h in db.query(DomainWatchHit).filter(DomainWatchHit.org_id == org_id)}
            self.assertEqual(set(hosts), {"zentrova-offers.shop", "zentr0va.com"})
            self.assertEqual(hosts["zentrova-offers.shop"].risk, "high")
            self.assertEqual(ctwatch.scan(db, org_id, fetch=lambda term: rows)["new_hits"], 0)  # no duplicates
            failed = ctwatch.scan(db, org_id, fetch=lambda term: (_ for _ in ()).throw(TimeoutError()))
            self.assertTrue(failed["errors"])
        finally:
            db.close()
        listed = self.c.get(f"{API}/fraud/watch", headers=h).json()
        hit = next(x for x in listed["hits"] if x["host"] == "zentrova-offers.shop")
        self.assertEqual(hit["cert_url"], "https://crt.sh/?id=102")
        r = self.c.post(f"{API}/fraud/watch/{hit['id']}", headers=h, json={"status": "incident"}).json()
        self.assertTrue(r["incident_id"])
        self.assertEqual(len(self.c.get(f"{API}/fraud/incidents", headers=h).json()), 1)

    def test_extension_swap_and_subdomain_lures(self):
        from backend.app.services import fraud
        types = lambda h: [f["type"] for f in fraud.analyse_domain(h, ["zentrova.com"], ["zentrova"])]
        self.assertEqual(types("zentrova.cc"), ["tld_swap"])          # was missed before
        self.assertEqual(types("zentrova.co.in"), ["tld_swap"])       # two-part extension, no false subdomain hit
        self.assertEqual(types("shop.zentrova.com"), ["official_domain"])
        self.assertIn("brand_in_subdomain", types("zentrova.login-help.net"))

    def test_background_scan_endpoint(self):
        _, body = self.new_company("Quorvex Labs")
        h = self.auth(body["access_token"])
        self.assertEqual(self.c.post(f"{API}/fraud/watch/scan", headers=h).status_code, 400)  # no official domains yet
        self.c.post(f"{API}/fraud/domains", headers=h, json={"domain": "quorvex.com"})
        asked = []
        prev = (ctwatch._fetch_crtsh, ctwatch.session_factory)
        ctwatch._fetch_crtsh = lambda q: (asked.append(q), [{"id": 7, "name_value": "quorvex-login.top", "issuer_name": "O=Test CA", "not_before": "2026-11-09T00:00:00"}])[1]
        ctwatch.session_factory = self.Session
        try:
            r = self.c.post(f"{API}/fraud/watch/scan", headers=h).json()
            self.assertTrue(r["started"])
            for _ in range(100):
                if not self.c.get(f"{API}/fraud/watch", headers=h).json()["scan"].get("running"):
                    break
                time.sleep(0.1)
            w = self.c.get(f"{API}/fraud/watch", headers=h).json()
            self.assertEqual(w["scan"]["summary"]["new_hits"], 1)
            self.assertEqual([x["host"] for x in w["hits"]], ["quorvex-login.top"])
            self.assertEqual(asked[0], "quorvex")
            self.assertIn("qu0rvex", asked)  # character-swap spelling searched too
        finally:
            ctwatch._fetch_crtsh, ctwatch.session_factory = prev


class FallbackTests(unittest.TestCase):
    class P(llm.LLMProvider):
        def __init__(self, name, reply):
            self.name, self.reply, self.calls = name, reply, 0

        @property
        def available(self):
            return True

        @property
        def model(self):
            return self.name

        def analyze(self, system, user):
            self.calls += 1
            return self.reply

    def test_next_provider_answers_and_cache(self):
        a, b = self.P("groq", None), self.P("openai", '{"findings": []}')
        f = llm.FallbackProvider([a, b], cache_seconds=60)
        msg = f"check {uuid.uuid4()}"
        self.assertEqual(f.analyze("sys", msg), '{"findings": []}')
        self.assertEqual(f.last_used, "openai")
        self.assertEqual(f.analyze("sys", msg), '{"findings": []}')
        self.assertEqual((a.calls, b.calls), (1, 1))  # second call served from the cache
        self.assertIsNone(llm.FallbackProvider([self.P("x", None)]).analyze("s", "u"))

    def test_factory_builds_chain(self):
        class S:
            LLM_ENABLED, LLM_PROVIDER, LLM_FALLBACK, LLM_CACHE_SECONDS = True, "groq", True, 0
            ANTHROPIC_API_KEY, ANTHROPIC_MODEL = "", ""
            GROQ_API_KEY, GROQ_MODEL = "g", "m"
            OPENAI_API_KEY, OPENAI_MODEL = "o", "gpt"
            GEMINI_API_KEY, GEMINI_MODEL = "", ""
            LLM_TIMEOUT_SECONDS, LLM_MAX_TOKENS = 5, 100
        p = llm.get_llm_provider(S)
        self.assertEqual(p.chain, ["groq", "openai"])
        S.LLM_FALLBACK = False
        self.assertEqual(llm.get_llm_provider(S).chain, ["groq"])


class BackupTests(unittest.TestCase):
    def test_round_trip(self):
        from backend.scripts import backup
        engine, Session, path = make_seeded_db()
        if path is None:
            drop_db(engine, path)
            self.skipTest("SQLite-only round trip")
        tmp = tempfile.mkdtemp()
        dump = os.path.join(tmp, "b.json.gz")
        target = os.path.join(tmp, "restored.db")
        try:
            made = backup.create(f"sqlite:///{path}", dump)
            self.assertEqual(backup.verify(dump), made)
            restored = backup.restore(f"sqlite:///{target}", dump)
            self.assertEqual({k: v for k, v in made.items() if v}, restored)
            with self.assertRaises(SystemExit):  # never into a database that has users
                backup.restore(f"sqlite:///{target}", dump)
        finally:
            drop_db(engine, path)


if __name__ == "__main__":
    unittest.main()
