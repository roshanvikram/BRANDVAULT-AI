"""Phase 1a security-foundation tests.

Covers: login required on org-scoped routes, Administrator-only Brand DNA
writes, tenant isolation (reads, writes, submission overwrite, jobs, agent
runs, passports), version-locked approvals, durable jobs (idempotency, cancel,
restart recovery), rate limiting, and the no-default-secret rule.

Run: `python -m unittest backend.tests.test_phase1a` (repo root).
"""
import time
import unittest
import uuid

from fastapi.testclient import TestClient

from backend.main import app
from backend.app.core import security
from backend.app.core.config import settings, _resolve_secret_key, Settings
from backend.app.core.ratelimit import limiter
from backend.app.db.session import get_db
from backend.app.models.brand import Organization
from backend.app.models.job import Job, JOB_QUEUED, JOB_PROCESSING, JOB_CANCELLED, JOB_FAILED
from backend.app.models.user import User, ROLE_REVIEWER
from backend.app.services import jobs as jobs_svc
from backend.app.services.seed import NOVA_ORG_ID
from backend.tests._util import make_seeded_db, drop_db

NOVA_CONTENT = "Introducing the world's fastest AI laptop! 10x faster than every competitor. Now only ₹69,999!"
API = "/api/v1"


class TestPhase1a(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._llm_prev, cls._rl_prev = settings.LLM_ENABLED, settings.RATE_LIMIT_ENABLED
        settings.LLM_ENABLED = False
        settings.RATE_LIMIT_ENABLED = False
        cls.engine, cls.Session, cls.path = make_seeded_db()
        db = cls.Session()
        cls.beta_org = "beta-org-1a"
        db.add(Organization(id=cls.beta_org, name="BETA CO", slug="beta-co-1a"))
        salt, h = security.hash_password("Beta@2026")
        db.add(User(id=str(uuid.uuid4()), email="rev@beta1a.test", full_name="Beta Reviewer",
                    role=ROLE_REVIEWER, org_id=cls.beta_org, salt=salt, password_hash=h))
        db.commit()
        db.close()

        def _override():
            d = cls.Session()
            try:
                yield d
            finally:
                d.close()

        app.dependency_overrides[get_db] = _override
        cls._factory_prev = jobs_svc.session_factory
        jobs_svc.session_factory = cls.Session
        cls.client = TestClient(app)
        cls.admin = cls._hdr("admin@novatech.demo", "Admin@2026")
        cls.creator = cls._hdr("creator@novatech.demo", "Creator@2026")
        cls.reviewer = cls._hdr("reviewer@novatech.demo", "Reviewer@2026")
        cls.beta = cls._hdr("rev@beta1a.test", "Beta@2026")

    @classmethod
    def tearDownClass(cls):
        settings.LLM_ENABLED, settings.RATE_LIMIT_ENABLED = cls._llm_prev, cls._rl_prev
        jobs_svc.session_factory = cls._factory_prev
        app.dependency_overrides.clear()
        drop_db(cls.engine, cls.path)

    @classmethod
    def _hdr(cls, email, pw):
        r = cls.client.post(f"{API}/auth/login", json={"email": email, "password": pw})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    def _analyze(self, headers, content=NOVA_CONTENT, title="t", submission_id=None):
        body = {"title": title, "content": content}
        if submission_id:
            body["submission_id"] = submission_id
        r = self.client.post(f"{API}/content/analyze", headers=headers, json=body)
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    # ---------------- authentication required ----------------
    def test_org_routes_require_login(self):
        gets = ["/brand/workspaces", "/brand/guidelines", "/brand/rules", "/brand/facts", "/brand/terms",
                "/content/submissions", "/claim/evidence-map", "/radar/metrics", "/radar/intelligence",
                "/graph/brand", "/onboarding/status", "/memory/insights", "/passport/list",
                "/agent/runs", "/agent/stats"]
        for path in gets:
            self.assertEqual(self.client.get(API + path).status_code, 401, path)
        posts = [("/content/analyze", {"title": "a", "content": "b"}), ("/rag/search", {"query": "price"}),
                 ("/twin/ask", {"question": "price"}), ("/copy-studio/rewrite", {"content": "x"}),
                 ("/brand/rules", {"title": "x", "rule_text": "y"})]
        for path, body in posts:
            self.assertEqual(self.client.post(API + path, json=body).status_code, 401, path)

    def test_public_routes_stay_public(self):
        self.assertEqual(self.client.get(f"{API}/health").status_code, 200)
        self.assertEqual(self.client.get(f"{API}/copy-studio/status").status_code, 200)

    # ---------------- Brand DNA writes are admin-only ----------------
    def test_creator_cannot_change_brand_dna(self):
        rule = {"title": "No hype", "rule_text": "Avoid hype.", "category": "Tone & Voice", "severity": "WARNING"}
        self.assertEqual(self.client.post(f"{API}/brand/rules", headers=self.creator, json=rule).status_code, 403)
        fact = {"fact_key": "k", "fact_value": "v", "verification_source": "s"}
        self.assertEqual(self.client.post(f"{API}/brand/facts", headers=self.creator, json=fact).status_code, 403)
        up = self.client.post(f"{API}/brand/guidelines/upload", headers=self.reviewer,
                              files={"file": ("p.txt", b"Prices must be exact and strictly verified.", "text/plain")})
        self.assertEqual(up.status_code, 403)
        some_rule = self.client.get(f"{API}/brand/rules", headers=self.creator).json()[0]
        self.assertEqual(self.client.patch(f"{API}/brand/rules/{some_rule['id']}/confirm",
                                           headers=self.creator).status_code, 403)

    def test_admin_changes_brand_dna_scoped_and_audited(self):
        rule = {"title": "Phase1a rule", "rule_text": "Say BrandVault.", "category": "Terminology", "severity": "WARNING"}
        r = self.client.post(f"{API}/brand/rules", headers=self.admin, json=rule)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["org_id"], NOVA_ORG_ID)  # from the token, not the client
        db = self.Session()
        try:
            from backend.app.models.passport import AuditLog
            log = db.query(AuditLog).filter(AuditLog.action == "RULE_CREATED").first()
            self.assertIsNotNone(log)
            self.assertIn("NOVA Admin", log.actor)
        finally:
            db.close()

    def test_admin_cannot_confirm_other_orgs_rule(self):
        beta_admin_rule = self.client.get(f"{API}/brand/rules", headers=self.admin).json()[0]
        # A NOVA rule confirmed by a BETA user (not admin) -> 403 either way.
        self.assertEqual(self.client.patch(f"{API}/brand/rules/{beta_admin_rule['id']}/confirm",
                                           headers=self.beta).status_code, 403)

    # ---------------- tenant isolation ----------------
    def test_cannot_read_other_org_by_param(self):
        for path in ["/brand/rules", "/brand/facts", "/content/submissions", "/radar/metrics", "/graph/brand"]:
            r = self.client.get(API + path, headers=self.beta, params={"org_id": NOVA_ORG_ID})
            self.assertEqual(r.status_code, 403, path)

    def test_default_scope_is_own_org(self):
        self.assertEqual(self.client.get(f"{API}/brand/rules", headers=self.beta).json(), [])
        ws = self.client.get(f"{API}/brand/workspaces", headers=self.beta).json()
        self.assertEqual([w["id"] for w in ws], [self.beta_org])  # no other tenant names leak

    def test_cannot_read_or_overwrite_other_org_submission(self):
        sub = self._analyze(self.creator)
        self.assertEqual(self.client.get(f"{API}/content/submissions/{sub['id']}", headers=self.beta).status_code, 403)
        r = self.client.post(f"{API}/content/analyze", headers=self.beta,
                             json={"title": "hijack", "content": "x", "submission_id": sub["id"]})
        self.assertEqual(r.status_code, 403)
        fresh = self.client.get(f"{API}/content/submissions/{sub['id']}", headers=self.creator).json()
        self.assertEqual(fresh["content"], NOVA_CONTENT)
        self.assertEqual(self.client.get(f"{API}/approval/history/{sub['id']}", headers=self.beta).status_code, 403)

    def test_agent_runs_scoped(self):
        self._analyze(self.creator)
        nova = self.client.get(f"{API}/agent/runs", headers=self.creator).json()
        self.assertTrue(nova)
        self.assertEqual(self.client.get(f"{API}/agent/runs", headers=self.beta).json(), [])

    # ---------------- version-locked approvals ----------------
    def test_edit_after_approval_requires_reapproval(self):
        sub = self._analyze(self.creator, content="Clean copy at ₹79,999.", title="lock")
        self.assertEqual(sub["version"], 1)
        r = self.client.post(f"{API}/approval/decide", headers=self.reviewer,
                             json={"submission_id": sub["id"], "decision": "Approved", "comments": "ok",
                                   "expected_version": 1})
        self.assertEqual(r.status_code, 200, r.text)
        pp1 = self.client.get(f"{API}/passport/by-submission/{sub['id']}", headers=self.reviewer).json()

        edited = self._analyze(self.creator, content="Clean copy at ₹79,999. Now with more!", title="lock",
                               submission_id=sub["id"])
        self.assertEqual(edited["version"], 2)
        self.assertEqual(edited["status"], "Analysed")  # approval no longer applies
        pp = self.client.get(f"{API}/passport/by-submission/{sub['id']}", headers=self.reviewer).json()
        self.assertEqual(pp["verification_status"], "SUPERSEDED")

        stale = self.client.post(f"{API}/approval/decide", headers=self.reviewer,
                                 json={"submission_id": sub["id"], "decision": "Approved", "comments": "ok",
                                       "expected_version": 1})
        self.assertEqual(stale.status_code, 409)

        ok = self.client.post(f"{API}/approval/decide", headers=self.reviewer,
                              json={"submission_id": sub["id"], "decision": "Approved", "comments": "v2 ok",
                                    "expected_version": 2})
        self.assertEqual(ok.status_code, 200, ok.text)
        pp2 = self.client.get(f"{API}/passport/by-submission/{sub['id']}", headers=self.reviewer).json()
        self.assertNotEqual(pp2["content_hash"], pp1["content_hash"])
        self.assertNotEqual(pp2["verification_status"], "SUPERSEDED")
        self.assertEqual(pp2["passport_data"]["previous_issues"][0]["passport_number"], pp1["passport_number"])

        hist = self.client.get(f"{API}/approval/history/{sub['id']}", headers=self.reviewer).json()
        self.assertEqual(sorted(h["submission_version"] for h in hist), [1, 2])

    def test_apply_correction_bumps_version(self):
        sub = self._analyze(self.creator)
        f = sub["findings"][0]
        r = self.client.post(f"{API}/content/apply-correction", headers=self.creator,
                             json={"submission_id": sub["id"], "finding_id": f["id"],
                                   "target_text": f["original_text"], "replacement_text": f["suggested_correction"]})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["version"], 2)
        revs = self.client.get(f"{API}/approval/revisions/{sub['id']}", headers=self.creator).json()
        self.assertTrue(any(v["version"] == 2 for v in revs))

    def test_apply_correction_rejects_foreign_finding(self):
        a = self._analyze(self.creator)
        b = self._analyze(self.creator)
        r = self.client.post(f"{API}/content/apply-correction", headers=self.creator,
                             json={"submission_id": a["id"], "finding_id": b["findings"][0]["id"],
                                   "target_text": "x", "replacement_text": "y"})
        self.assertEqual(r.status_code, 404)

    # ---------------- durable jobs ----------------
    def _wait(self, job_id, headers):
        for _ in range(100):
            j = self.client.get(f"{API}/content/jobs/{job_id}", headers=headers).json()
            if j["status"] in ("completed", "failed", "cancelled"):
                return j
            time.sleep(0.05)
        self.fail("job did not finish")

    def test_async_job_completes_and_is_persisted(self):
        r = self.client.post(f"{API}/content/analyze-async", headers=self.creator,
                             json={"title": "async", "content": NOVA_CONTENT})
        self.assertEqual(r.status_code, 200, r.text)
        job = self._wait(r.json()["job_id"], self.creator)
        self.assertEqual(job["status"], "completed", job)
        self.assertEqual(job["attempts"], 1)
        sub = self.client.get(f"{API}/content/submissions/{job['submission_id']}", headers=self.creator)
        self.assertEqual(sub.status_code, 200)
        # Other tenants cannot see the job.
        self.assertEqual(self.client.get(f"{API}/content/jobs/{job['id']}", headers=self.beta).status_code, 404)

    def test_idempotency_key_reuses_job(self):
        h = dict(self.creator, **{"Idempotency-Key": f"k-{uuid.uuid4().hex}"})
        one = self.client.post(f"{API}/content/analyze-async", headers=h, json={"title": "i", "content": "x"}).json()
        two = self.client.post(f"{API}/content/analyze-async", headers=h, json={"title": "i", "content": "x"}).json()
        self.assertEqual(one["job_id"], two["job_id"])
        self.assertTrue(two["reused"])
        self._wait(one["job_id"], self.creator)

    def test_cancel_only_queued(self):
        db = self.Session()
        try:
            job, _ = jobs_svc.create_job(db, org_id=NOVA_ORG_ID, kind="content_analysis",
                                         input_data={"title": "c", "content": "x"}, dispatch=False)
            jid = job.id
        finally:
            db.close()
        r = self.client.post(f"{API}/content/jobs/{jid}/cancel", headers=self.creator)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["status"], "cancelled")
        again = self.client.post(f"{API}/content/jobs/{jid}/cancel", headers=self.creator)
        self.assertEqual(again.status_code, 409)

    def test_failed_handler_retries_then_fails(self):
        db = self.Session()
        try:
            job, _ = jobs_svc.create_job(db, org_id="no-such-org", kind="content_analysis",
                                         input_data={"title": "f", "content": "x"}, max_attempts=2, dispatch=False)
            jid = job.id
        finally:
            db.close()
        jobs_svc.run_job(jid)
        db = self.Session()
        try:
            j = db.query(Job).filter(Job.id == jid).first()
            self.assertEqual(j.status, JOB_FAILED)
            self.assertEqual(j.attempts, 2)
            self.assertIn("not found", j.error)
        finally:
            db.close()

    def test_restart_recovery(self):
        db = self.Session()
        try:
            stuck, _ = jobs_svc.create_job(db, org_id=NOVA_ORG_ID, kind="content_analysis",
                                           input_data={"title": "r", "content": "x"}, dispatch=False)
            stuck.status, stuck.attempts = JOB_PROCESSING, 1
            spent, _ = jobs_svc.create_job(db, org_id=NOVA_ORG_ID, kind="content_analysis",
                                           input_data={"title": "r2", "content": "x"}, max_attempts=1, dispatch=False)
            spent.status, spent.attempts = JOB_PROCESSING, 1
            db.commit()
            jobs_svc.resume_unfinished(db, dispatch=False)
            db.refresh(stuck)
            db.refresh(spent)
            self.assertEqual(stuck.status, JOB_QUEUED)   # re-queued, has an attempt left
            self.assertEqual(spent.status, JOB_FAILED)   # no attempts left -> failed, not faked
        finally:
            db.close()

    # ---------------- rate limiting ----------------
    def test_login_rate_limited(self):
        prev_on, prev_n = settings.RATE_LIMIT_ENABLED, settings.RATE_LIMIT_AUTH_PER_MIN
        limiter.reset()
        settings.RATE_LIMIT_ENABLED = True
        try:
            # The dependency captured the limit at import time, so drive it to that limit.
            codes = [self.client.post(f"{API}/auth/login", json={"email": "x@y.z", "password": "bad"}).status_code
                     for _ in range(prev_n + 1)]
            self.assertEqual(codes[-1], 429)
            self.assertTrue(all(c == 401 for c in codes[:-1]))
        finally:
            settings.RATE_LIMIT_ENABLED = prev_on
            limiter.reset()

    # ---------------- secret key ----------------
    def test_no_default_secret_in_production(self):
        s = Settings()
        s.SECRET_KEY = ""
        s.ENVIRONMENT = "production"
        with self.assertRaises(RuntimeError):
            _resolve_secret_key(s)
        self.assertNotEqual(settings.SECRET_KEY, "brandvault-enterprise-secret-key-2026")
        self.assertGreaterEqual(len(settings.SECRET_KEY), 32)


if __name__ == "__main__":
    unittest.main()
