"""12-engines Phase 2 tests: Launch Readiness, Asset Lifecycle, Consistency
Heatmap analytics and AI Reviewer Intelligence — real calculations over
seeded records, permissions, tenant isolation and no side effects.

Run: `python -m unittest backend.tests.test_phase2_governance` (repo root).
"""
import datetime
import shutil
import tempfile
import time
import unittest
import uuid

from fastapi.testclient import TestClient

from backend.tests import forensics_fixtures as ff

API = "/api/v1"
NOVA_ORG = "nova-tech-org-001"
VORTEXA_ORG = "vortexa-tech-org-002"
CLEAN = "NovaBook AI Pro 16 delivers up to 18 hours of battery life. Now ₹79,999."
BAD_PRICE = "NovaBook AI Pro 16 is the world's fastest AI laptop. Now only ₹69,999!"


class _Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from backend.main import app
        from backend.app.core.config import settings
        from backend.app.db.session import get_db
        from backend.app.services.seed import seed_vortexa_brand
        from backend.app.services.rag import RagRetriever
        from backend.app.api.v1 import assets as assets_api
        from backend.tests._util import make_seeded_db

        cls.app, cls.settings, cls.assets_api = app, settings, assets_api
        cls._prev = (settings.LLM_ENABLED, settings.RATE_LIMIT_ENABLED, assets_api.STORAGE_ROOT)
        settings.LLM_ENABLED = False
        settings.RATE_LIMIT_ENABLED = False
        cls.storage = tempfile.mkdtemp(prefix="bv_p2_")
        assets_api.STORAGE_ROOT = cls.storage
        cls.engine, cls.Session, cls.path = make_seeded_db()
        db = cls.Session()
        seed_vortexa_brand(db)
        RagRetriever(db).index_org(VORTEXA_ORG)
        db.close()

        def _override():
            d = cls.Session()
            try:
                yield d
            finally:
                d.close()

        app.dependency_overrides[get_db] = _override
        cls.client = TestClient(app)
        h = lambda e, p: {"Authorization": f"Bearer {cls.client.post(f'{API}/auth/login', json={'email': e, 'password': p}).json()['access_token']}"}
        cls.admin = h("admin@novatech.demo", "Admin@2026")
        cls.creator = h("creator@novatech.demo", "Creator@2026")
        cls.reviewer = h("reviewer@novatech.demo", "Reviewer@2026")
        cls.vx = h("creator@vortexa.demo", "Creator@2026")

    @classmethod
    def tearDownClass(cls):
        from backend.tests._util import drop_db
        cls.settings.LLM_ENABLED, cls.settings.RATE_LIMIT_ENABLED, cls.assets_api.STORAGE_ROOT = cls._prev
        cls.app.dependency_overrides.clear()
        drop_db(cls.engine, cls.path)
        shutil.rmtree(cls.storage, ignore_errors=True)

    def analyze(self, content, title="Campaign", department=None, submission_id=None):
        body = {"title": title, "content": content}
        if department:
            body["department"] = department
        if submission_id:
            body["submission_id"] = submission_id
        r = self.client.post(f"{API}/content/analyze", headers=self.creator, json=body)
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def decide(self, sub, decision, headers=None, comments="ok"):
        r = self.client.post(f"{API}/approval/decide", headers=headers or self.reviewer,
                             json={"submission_id": sub["id"], "decision": decision, "comments": comments,
                                   "expected_version": sub["version"]})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def readiness(self, sub, headers=None):
        r = self.client.post(f"{API}/launch/{sub['id']}/check", headers=headers or self.creator)
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()


# =============================================================================
class TestLaunchReadiness(_Base):
    def _check(self, report, key):
        return next(c for c in report["checks"] if c["key"] == key)

    def test_twelve_checks_and_approved_for_launch(self):
        sub = self.analyze(CLEAN, title="Clean launch")
        r = self.readiness(sub)
        self.assertEqual(len(r["checks"]), 12)
        self.assertEqual(r["state"], "Ready for Review")
        self.assertEqual(self._check(r, "pricing")["status"], "pass")
        self.assertEqual(self._check(r, "approvals")["status"], "pending")
        self.decide(sub, "Approved")
        self.assertEqual(self.readiness(sub)["state"], "Approved for Launch")

    def test_contradicted_price_blocks_with_evidence_and_routing(self):
        sub = self.analyze(BAD_PRICE, title="Bad price")
        r = self.readiness(sub)
        self.assertEqual(r["state"], "Blocked by Critical Issues")
        pricing = self._check(r, "pricing")
        self.assertEqual(pricing["status"], "fail")
        self.assertTrue(any("₹79,999" in e for e in pricing["evidence"]))
        self.assertIn("pricing", r["blocking"])
        self.assertIn("Brand administrator", r["route_to"])
        self.assertTrue(r["unresolved_findings"])
        hist = self.client.get(f"{API}/launch/{sub['id']}/reports", headers=self.creator).json()
        self.assertEqual(hist[0]["state"], "Blocked by Critical Issues")

    def test_never_changes_the_campaign(self):
        sub = self.analyze(BAD_PRICE, title="No side effects")
        self.readiness(sub)
        after = self.client.get(f"{API}/content/submissions/{sub['id']}", headers=self.creator).json()
        self.assertEqual((after["status"], after["version"], after["content"]), (sub["status"], sub["version"], sub["content"]))
        self.assertEqual(self.client.get(f"{API}/approval/history/{sub['id']}", headers=self.creator).json(), [])

    def test_edit_after_approval_is_expired_approval(self):
        sub = self.analyze(CLEAN, title="Edited later")
        self.decide(sub, "Approved")
        edited = self.analyze(CLEAN + " Limited stock.", title="Edited later", submission_id=sub["id"])
        r = self.readiness(edited)
        self.assertEqual(r["state"], "Expired Approval")
        self.assertIn("version 1", self._check(r, "approvals")["detail"])

    def test_pending_approval(self):
        sub = self.analyze(CLEAN, title="Sent for review")
        self.decide(sub, "Pending Review", headers=self.creator, comments="please review")
        self.assertEqual(self.readiness(sub)["state"], "Pending Approval")

    def test_new_guideline_requires_reanalysis(self):
        sub = self.analyze(CLEAN, title="Before new guideline")
        time.sleep(0.01)
        up = self.client.post(f"{API}/brand/guidelines/upload", headers=self.admin,
                              files={"file": ("new-rules.txt", b"All campaigns must quote prices exactly as approved by Finance.", "text/plain")})
        self.assertEqual(up.status_code, 200, up.text)
        r = self.readiness(sub)
        self.assertEqual(r["state"], "Requires Reanalysis")
        self.assertIn("new-rules.txt", self._check(r, "guideline_version")["detail"])

    def test_admin_policy_controls_blocking(self):
        body = {"mandatory": ["approvals"], "approval_validity_days": 30}
        self.assertEqual(self.client.put(f"{API}/launch/config", headers=self.creator, json=body).status_code, 403)
        self.assertEqual(self.client.put(f"{API}/launch/config", headers=self.admin,
                                         json={"mandatory": ["nonsense"]}).status_code, 400)
        r = self.client.put(f"{API}/launch/config", headers=self.admin, json=body)
        self.assertEqual(r.status_code, 200, r.text)
        try:
            sub = self.analyze("NovaBook AI Pro 16 now ₹69,999.", title="Price only")
            rep = self.readiness(sub)
            self.assertEqual(self._check(rep, "pricing")["status"], "fail")
            self.assertFalse(self._check(rep, "pricing")["mandatory"])
            self.assertEqual(rep["state"], "Ready for Review")       # pricing no longer blocks
        finally:
            from backend.app.services.launch_readiness import DEFAULT_MANDATORY
            self.client.put(f"{API}/launch/config", headers=self.admin,
                            json={"mandatory": DEFAULT_MANDATORY, "approval_validity_days": 90})

    def test_translation_and_disclaimer_checks_use_real_records(self):
        sub = self.analyze(CLEAN, title="With translations")
        self.assertEqual(self._check(self.readiness(sub), "translations")["status"], "not_applicable")
        tg = self.client.post(f"{API}/translation-guard/analyze", headers=self.creator, json={
            "title": "t", "source_text": CLEAN, "use_ai": False,
            "translations": [{"text": "NovaBook AI Pro 16 में 18 घंटे से अधिक बैटरी लाइफ। अब ₹79,999."}]})
        self.assertEqual(tg.status_code, 200, tg.text)
        self.assertEqual(self._check(self.readiness(sub), "translations")["status"], "fail")
        self.assertEqual(self._check(self.readiness(sub), "disclaimers")["status"], "unavailable")
        from backend.app.models.brand import BrandRule
        db = self.Session()
        try:
            db.add(BrandRule(id=str(uuid.uuid4()), org_id=NOVA_ORG, category="Legal", title="Pricing disclaimer",
                             rule_text="Every price must carry the disclaimer *Inclusive of taxes.", severity="WARNING",
                             is_active=True, is_confirmed=True))
            db.commit()
        finally:
            db.close()
        self.assertEqual(self._check(self.readiness(sub), "disclaimers")["status"], "fail")
        with_disc = self.analyze(CLEAN + " *Inclusive of taxes.", title="Has disclaimer")
        self.assertEqual(self._check(self.readiness(with_disc), "disclaimers")["status"], "pass")

    def test_isolation(self):
        sub = self.analyze(CLEAN, title="Nova only")
        self.assertEqual(self.client.post(f"{API}/launch/{sub['id']}/check", headers=self.vx).status_code, 403)
        self.assertEqual(self.client.get(f"{API}/launch/{sub['id']}/reports", headers=self.vx).status_code, 403)


# =============================================================================
class TestAssetLifecycle(_Base):
    def _upload(self, img, name, version, supersedes=None, valid_until=None):
        data = {"name": name, "kind": "logo", "version_label": version}
        if supersedes:
            data["supersedes_id"] = supersedes
        if valid_until:
            data["valid_until"] = valid_until
        r = self.client.post(f"{API}/assets", headers=self.admin, data=data,
                             files={"file": (f"{version}.png", ff.png_bytes(img), "image/png")})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def _life(self, h=None):
        r = self.client.get(f"{API}/governance/lifecycle", headers=h or self.creator)
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_states_usage_and_alerts(self):
        soon = (datetime.datetime.utcnow() + datetime.timedelta(days=10)).isoformat()
        v1 = self._upload(ff.make_logo("v1"), "NOVA logo", "v1")
        v2 = self._upload(ff.make_logo("v2"), "NOVA logo", "v2", supersedes=v1["id"], valid_until=soon)
        inv = self.client.post(f"{API}/assets/investigate", headers=self.creator,
                               files={"file": ("old.png", ff.png_bytes(ff.compose(ff.make_logo("v1"))), "image/png")})
        self.assertEqual(inv.status_code, 200, inv.text)
        life = self._life()
        by_id = {i["id"]: i for i in life["items"]}
        self.assertEqual(by_id[v1["id"]]["state"], "Superseded")
        self.assertEqual(by_id[v2["id"]]["state"], "Expiring Soon")
        self.assertEqual(by_id[v1["id"]]["usage"], 1)                       # seen in the investigation
        self.assertTrue(by_id[v1["id"]]["replacement_available"])
        texts = " ".join(a["text"] for a in life["alerts"])
        self.assertIn("expires on", texts)
        self.assertIn("found in 1 investigated image", texts)
        self.assertGreaterEqual(life["counts"]["Superseded"], 1)

    def test_expired_promotion_and_outdated_campaigns(self):
        promo = self.analyze("Pre-order now and get a complimentary NovaSleeve!", title="Old promo")
        life = self._life()
        promo_fact = [i for i in life["items"] if i["kind"] == "approved_fact" and "Pre-Order" in i["name"]][0]
        self.assertEqual(promo_fact["state"], "Superseded")
        self.assertIn(promo["id"], {a["submission_id"] for a in life["affected_campaigns"]})

    def test_approval_superseded_after_edit(self):
        sub = self.analyze(CLEAN, title="Lifecycle approval")
        self.decide(sub, "Approved")
        self.analyze(CLEAN + " New line.", title="Lifecycle approval", submission_id=sub["id"])
        appr = [i for i in self._life()["items"] if i["kind"] == "approval" and i["name"] == "Lifecycle approval"][0]
        self.assertEqual(appr["state"], "Superseded")

    def test_isolation(self):
        names = {i["name"] for i in self._life(self.vx)["items"]}
        self.assertFalse(any("NOVA" in n or "NovaBook" in n for n in names))


# =============================================================================
class TestConsistencyAnalytics(_Base):
    def _get(self, h=None, **params):
        r = self.client.get(f"{API}/analytics/consistency", headers=h or self.creator, params=params)
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_numbers_match_the_database(self):
        self.analyze(BAD_PRICE, title="Retail ad", department="Retail")
        self.analyze(CLEAN, title="Brand ad", department="Brand")
        a = self._get()
        from backend.app.models.submission import Submission
        db = self.Session()
        try:
            subs = db.query(Submission).filter(Submission.org_id == NOVA_ORG).all()
            n_find = sum(len(s.findings) for s in subs)
            n_crit = sum(1 for s in subs for f in s.findings if f.severity == "CRITICAL")
        finally:
            db.close()
        self.assertEqual(a["kpis"]["campaigns"], len(subs))
        self.assertEqual(a["kpis"]["findings"], n_find)
        self.assertEqual(a["kpis"]["critical"], n_crit)
        month = a["heatmaps"]["month"]
        self.assertEqual(sum(sum(r) for r in month["cells"]), n_find)        # heatmap adds up
        self.assertTrue(a["basis"]["demonstration_data"])

    def test_filters(self):
        self.analyze(BAD_PRICE, title="Retail filter ad", department="Retail")
        retail = self._get(department="Retail")
        self.assertTrue(all(c["department"] == "Retail" for c in retail["compliance"]["campaigns"]))
        self.assertIn("Retail", retail["options"]["departments"])
        crit = self._get(severity="CRITICAL")
        self.assertTrue(crit["kpis"]["findings"] == crit["kpis"]["critical"])
        future = self._get(date_from="2999-01-01")
        self.assertEqual(future["kpis"]["campaigns"], 0)
        self.assertIn("No campaigns", future["basis"]["note"])
        prod = self._get(product="NovaBook AI Pro 16")
        self.assertTrue(all("NovaBook AI Pro 16" in c["products"] for c in prod["compliance"]["campaigns"]))
        self.assertEqual(self.client.get(f"{API}/analytics/consistency", headers=self.creator,
                                         params={"date_from": "not-a-date"}).status_code, 400)

    def test_repeated_terminology_and_isolation(self):
        self.analyze(BAD_PRICE, title="Terms 1")
        self.analyze(BAD_PRICE, title="Terms 2")
        terms = {t["term"]: t["count"] for t in self._get()["terminology_repeats"]}
        self.assertGreaterEqual(terms.get("world's fastest", 0), 2)
        vx = self._get(self.vx)
        self.assertFalse(any("Terms" in c["title"] for c in vx["compliance"]["campaigns"]))
        self.assertEqual(self.client.get(f"{API}/analytics/consistency", headers=self.vx,
                                         params={"org_id": NOVA_ORG}).status_code, 403)


# =============================================================================
class TestReviewerIntelligence(_Base):
    def _get(self, h=None):
        r = self.client.get(f"{API}/governance/reviewer-intelligence", headers=h or self.creator)
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_insufficient_data_is_reported(self):
        r = self._get(self.vx)
        self.assertFalse(r["data_sufficient"])
        self.assertIn("human decision", r["data_note"])
        self.assertEqual(r["recommendations"], [])

    def test_patterns_from_real_decisions(self):
        # Reviewers approve the same flagged pricing rule twice -> clarify policy.
        for i in range(2):
            s = self.analyze(BAD_PRICE, title=f"Override {i}")
            self.decide(s, "Approved", comments="Price exception approved by the CMO for this channel.")
        # A rejection of copy the AI scored as clean -> possible rule gap (twice).
        for i in range(2):
            s = self.analyze(CLEAN, title=f"Clean but rejected {i}")
            self.decide(s, "Rejected", comments="Missing the mandatory regional disclaimer.")
        # Two different outcomes on the same rule by different reviewers.
        s = self.analyze(BAD_PRICE, title="Disagreement")
        self.decide(s, "Revision Requested", headers=self.admin, comments="Fix the price.")
        r = self._get()
        self.assertGreaterEqual(r["decisions_analysed"], 5)
        top = r["overridden_findings"][0]
        self.assertGreaterEqual(top["count"], 2)
        self.assertTrue(any("CMO" in c for c in top["comments"]))
        kinds = {x["kind"] for x in r["recommendations"]}
        self.assertIn("clarify_policy", kinds)
        self.assertIn("rule_gap", kinds)
        self.assertTrue(r["disagreements"])
        self.assertTrue(len(r["unanticipated_rejections"]) >= 2)
        self.assertIsNotNone(r["turnaround"]["median_hours"])
        # policy, not people: no per-reviewer scores anywhere in the payload
        def keys(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    yield k
                    yield from keys(v)
            elif isinstance(o, list):
                for v in o:
                    yield from keys(v)
        self.assertFalse([k for k in keys(r) if "rank" in k.lower() or "reviewer_score" in k.lower()])

    def test_proposals_are_drafts_and_admin_only(self):
        body = {"title": "Clarify launch pricing exceptions", "rule_text": "State which channels may show CMO-approved exception prices."}
        self.assertEqual(self.client.post(f"{API}/governance/reviewer-intelligence/propose", headers=self.creator, json=body).status_code, 403)
        r = self.client.post(f"{API}/governance/reviewer-intelligence/propose", headers=self.admin, json=body)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertFalse(r.json()["is_confirmed"])
        rules = self.client.get(f"{API}/brand/rules", headers=self.admin).json()
        draft = [x for x in rules if x["id"] == r.json()["id"]][0]
        self.assertFalse(draft["is_confirmed"])                            # not enforced until confirmed


if __name__ == "__main__":
    unittest.main()
