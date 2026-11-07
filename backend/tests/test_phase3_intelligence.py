"""12-engines Phase 3 tests: Campaign Stress Testing, Content Similarity,
Brand Fraud Intelligence and Reputation Early Warning (incl. a labelled
sentiment set whose measured accuracy is asserted, not assumed).

Run: `python -m unittest backend.tests.test_phase3_intelligence` (repo root).
"""
import datetime
import io
import json
import shutil
import tempfile
import unittest
import uuid

from fastapi.testclient import TestClient

from backend.app.services import fraud, reputation
from backend.tests import forensics_fixtures as ff

API = "/api/v1"
NOVA_ORG = "nova-tech-org-001"
LAUNCH = "NovaBook AI Pro 16 lasts up to 18 hours. Now ₹79,999. *Inclusive of taxes."

# Labelled feedback (text, rating or None, expected sentiment)
LABELLED = [
    ("Battery easily lasts all day, really impressed", None, "positive"),
    ("Fast, smooth and the display is crisp. Love it", None, "positive"),
    ("Great value, would recommend to friends", None, "positive"),
    ("Support was helpful and quick", None, "positive"),
    ("Excellent build quality and solid keyboard", None, "positive"),
    ("Battery drains in 4 hours, not 18 as advertised", None, "negative"),
    ("Laptop overheats and the fan is noisy", None, "negative"),
    ("Screen flickering after a week, very disappointed", None, "negative"),
    ("Delivery was late and support was rude", None, "negative"),
    ("Not good at all, it crashed twice on day one", None, "negative"),
    ("Arrived on Tuesday in a brown box", None, "neutral"),
    ("I use it for spreadsheets at work", None, "neutral"),
    ("It is okay", 3, "neutral"),
    ("Honestly the worst purchase", 1, "negative"),
    ("Works as described", 5, "positive"),
    ("Not bad for the price", None, "positive"),
]


class TestUnits(unittest.TestCase):
    def test_sentiment_accuracy_on_labelled_set(self):
        correct = sum(reputation.score_sentiment(t, r)[0] == y for t, r, y in LABELLED)
        acc = correct / len(LABELLED)
        print(f"\n[measured] lexicon sentiment accuracy on {len(LABELLED)} labelled items: {acc:.2%}")
        self.assertGreaterEqual(acc, 0.8)

    def test_negation_and_rating_precedence(self):
        self.assertEqual(reputation.score_sentiment("not good", None)[0], "negative")
        self.assertEqual(reputation.score_sentiment("terrible", 5)[0], "positive")   # rating wins, engine says so
        self.assertEqual(reputation.score_sentiment("terrible", 5)[2], "rating")

    def test_categories(self):
        self.assertIn("Battery", reputation.categorise("battery drains fast"))
        self.assertIn("Advertising claims", reputation.categorise("not as advertised"))

    def test_domain_signals(self):
        off, toks = ["novatech.in"], ["novabook", "nova"]
        t = lambda h: {f["type"] for f in fraud.analyse_domain(h, off, toks)}
        self.assertEqual(t("novatech.in"), {"official_domain"})
        self.assertEqual(t("shop.novatech.in"), {"official_domain"})
        self.assertIn("typosquat", t("novatecb.in"))
        self.assertIn("homoglyph", t("n0vatech.in"))
        self.assertIn("brand_in_domain", t("novabook-offers.shop"))
        self.assertIn("brand_in_subdomain", t("novatech.in.secure-login.xyz"))
        self.assertIn("punycode", t("xn--novatch-1ya.in"))
        self.assertEqual(t("unrelated-store.com"), set())

    def test_fetch_refuses_private_hosts(self):
        text, note = fraud.fetch_page("http://127.0.0.1:9/")
        self.assertIsNone(text)
        self.assertIn("not a public", note)
        self.assertIsNone(fraud.fetch_page("file:///etc/passwd")[0])

    def test_upload_parsing(self):
        csv = "text,rating,date,channel\nBattery dies fast,2,2026-10-01,Amazon\n,4,2026-10-02,x\nLove it,5,02/10/2026,Flipkart\n"
        rows, problems = reputation.parse_upload("f.csv", csv.encode())
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["rating"], 2.0)
        self.assertEqual(rows[0]["date"], datetime.datetime(2026, 10, 1))
        self.assertTrue(problems)
        self.assertEqual(reputation.parse_upload("f.json", b"{not json")[0], [])


class _Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from backend.main import app
        from backend.app.core.config import settings
        from backend.app.db.session import get_db
        from backend.app.services.seed import seed_vortexa_brand
        from backend.app.api.v1 import assets as assets_api
        from backend.tests._util import make_seeded_db

        cls.app, cls.settings, cls.assets_api = app, settings, assets_api
        cls._prev = (settings.LLM_ENABLED, settings.RATE_LIMIT_ENABLED, assets_api.STORAGE_ROOT, settings.FRAUD_URL_FETCH_ENABLED)
        settings.LLM_ENABLED = False
        settings.RATE_LIMIT_ENABLED = False
        settings.FRAUD_URL_FETCH_ENABLED = False
        cls.storage = tempfile.mkdtemp(prefix="bv_p3_")
        assets_api.STORAGE_ROOT = cls.storage
        cls.engine, cls.Session, cls.path = make_seeded_db()
        db = cls.Session()
        seed_vortexa_brand(db)
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
        (cls.settings.LLM_ENABLED, cls.settings.RATE_LIMIT_ENABLED, cls.assets_api.STORAGE_ROOT,
         cls.settings.FRAUD_URL_FETCH_ENABLED) = cls._prev
        cls.app.dependency_overrides.clear()
        drop_db(cls.engine, cls.path)
        shutil.rmtree(cls.storage, ignore_errors=True)

    def analyze(self, content, title="Campaign"):
        r = self.client.post(f"{API}/content/analyze", headers=self.creator, json={"title": title, "content": content})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()


class TestStressTesting(_Base):
    def _run(self, sub, scenario, **params):
        return self.client.post(f"{API}/simulation/run", headers=self.creator,
                                json={"submission_id": sub["id"], "scenario": scenario, "params": params})

    def test_price_change_introduces_contradiction_without_touching_campaign(self):
        sub = self.analyze(LAUNCH, "Sim launch")
        from backend.app.models.submission import Submission, Finding
        db = self.Session()
        try:
            before = (db.query(Submission).count(), db.query(Finding).count())
        finally:
            db.close()
        r = self._run(sub, "price_change", new_price="69999")
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body["hypothetical"])
        self.assertIn("₹69,999", body["simulated"]["text"])
        self.assertTrue(any(c["status"] == "Contradicted" for c in body["product_truth_changes"]))
        self.assertLess(body["score_delta"], 0)
        db = self.Session()
        try:
            after = (db.query(Submission).count(), db.query(Finding).count())
            real = db.query(Submission).filter(Submission.id == sub["id"]).first()
            self.assertEqual(real.content, LAUNCH)          # never modified
            self.assertEqual(real.version, sub["version"])
        finally:
            db.close()
        self.assertEqual(before, after)                     # dry-run wrote nothing
        runs = self.client.get(f"{API}/simulation/runs", headers=self.creator, params={"submission_id": sub["id"]}).json()
        self.assertEqual(runs[0]["scenario"], "price_change")

    def test_scenarios(self):
        sub = self.analyze(LAUNCH, "Sim scenarios")
        tag = self._run(sub, "tagline_change", find="up to 18 hours", replace="more than 20 hours").json()
        self.assertTrue(any(c["status"] == "Contradicted" for c in tag["product_truth_changes"]))
        disc = self._run(sub, "product_discontinued").json()
        self.assertTrue(any(f["category"] == "Product" for f in disc["introduced"]))
        self.assertLess(disc["score_delta"], 0)
        rem = self._run(sub, "remove_disclaimer").json()
        self.assertNotIn("*Inclusive", rem["simulated"]["text"])
        for scenario, params, needle in [("older_guideline", {}, "older guideline"), ("translate", {"language": "Hindi"}, "AI model"),
                                         ("logo_change", {}, "image"), ("price_change", {"new_price": "abc"}, "number")]:
            r = self._run(sub, scenario, **params)
            self.assertEqual(r.status_code, 422, (scenario, r.text))
            self.assertIn(needle, r.json()["detail"])

    def test_isolation(self):
        sub = self.analyze(LAUNCH, "Sim iso")
        r = self.client.post(f"{API}/simulation/run", headers=self.vx,
                             json={"submission_id": sub["id"], "scenario": "remove_disclaimer", "params": {}})
        self.assertEqual(r.status_code, 403)


class TestSimilarity(_Base):
    def test_exact_near_sentence_and_unrelated(self):
        a = self.analyze("Meet NovaBook AI Pro 16. Engineered for creators who never stop. Now ₹79,999.", "Original")
        r = self.client.post(f"{API}/similarity/check", headers=self.creator, json={"text": a["content"]}).json()
        self.assertEqual(r["matches"][0]["label"], "Exact duplicate")
        near = self.client.post(f"{API}/similarity/check", headers=self.creator,
                                json={"text": "Meet NovaBook AI Pro 16. Engineered for creators who never stop. Now ₹74,999."}).json()
        self.assertEqual(near["matches"][0]["label"], "Near-duplicate")
        tag = self.client.post(f"{API}/similarity/check", headers=self.creator,
                               json={"text": "Autumn sale. Engineered for creators who never stop. Visit a store today."}).json()
        self.assertTrue(any(m["label"] == "Reused tagline or sentence" for m in tag["matches"]))
        none = self.client.post(f"{API}/similarity/check", headers=self.creator,
                                json={"text": "Our headphones deliver crisp sound for commuters and students."}).json()
        self.assertFalse(any(m["title"] == "Original" for m in none["matches"]))
        self.assertIn("not a copyright", none["note"])

    def test_submission_mode_excludes_itself_and_clusters(self):
        a = self.analyze("Unique spring campaign for the NovaBook with calm confident copy.", "Spring A")
        self.analyze("Unique spring campaign for the NovaBook with calm confident copy.", "Spring B")
        r = self.client.post(f"{API}/similarity/check", headers=self.creator, json={"submission_id": a["id"]}).json()
        self.assertNotIn(f"submission:{a['id']}", [m["ref"] for m in r["matches"]])
        self.assertTrue(any(m["title"] == "Spring B" for m in r["matches"]))
        cl = self.client.get(f"{API}/similarity/clusters", headers=self.creator).json()["clusters"]
        self.assertTrue(any({"Spring A", "Spring B"} <= {m["title"] for m in c["members"]} for c in cl))

    def test_dismiss_false_positive_and_restore(self):
        self.analyze("Weekend workshop for creators using the NovaBook in Chennai.", "Workshop")
        text = "Weekend workshop for creators using the NovaBook in Chennai."
        m = self.client.post(f"{API}/similarity/check", headers=self.creator, json={"text": text}).json()["matches"][0]
        body = {"pair_key": m["pair_key"], "reason": "Intentional reuse for the same event"}
        self.assertEqual(self.client.post(f"{API}/similarity/dismiss", headers=self.creator, json=body).status_code, 200)
        after = self.client.post(f"{API}/similarity/check", headers=self.creator, json={"text": text}).json()
        self.assertNotIn(m["pair_key"], [x["pair_key"] for x in after["matches"]])
        shown = self.client.post(f"{API}/similarity/check", headers=self.creator, json={"text": text, "include_dismissed": True}).json()
        self.assertTrue([x for x in shown["matches"] if x["pair_key"] == m["pair_key"] and x["dismissed"]])
        self.client.post(f"{API}/similarity/restore", headers=self.creator, json=body)
        back = self.client.post(f"{API}/similarity/check", headers=self.creator, json={"text": text}).json()
        self.assertIn(m["pair_key"], [x["pair_key"] for x in back["matches"]])

    def test_image_near_duplicate_and_isolation(self):
        creative = ff.compose(ff.make_logo("v2"))
        self.client.post(f"{API}/assets", headers=self.admin, data={"name": "Banner", "kind": "creative", "version_label": "v1"},
                         files={"file": ("b.png", ff.png_bytes(creative), "image/png")})
        r = self.client.post(f"{API}/similarity/image", headers=self.creator,
                             files={"file": ("b.jpg", ff.jpeg_bytes(creative, 70), "image/jpeg")}).json()
        self.assertEqual(r["matches"][0]["label"], "Near-duplicate image")
        vx = self.client.post(f"{API}/similarity/image", headers=self.vx,
                              files={"file": ("b.jpg", ff.jpeg_bytes(creative, 70), "image/jpeg")}).json()
        self.assertEqual(vx["matches"], [])
        txt = self.client.post(f"{API}/similarity/check", headers=self.vx, json={"text": LAUNCH}).json()
        self.assertFalse(any("Sim" in m["title"] for m in txt["matches"]))


class TestFraud(_Base):
    def test_lookalike_offer_with_phishing_is_high_risk(self):
        self.client.post(f"{API}/fraud/domains", headers=self.admin, json={"domain": "novatech.in"})
        r = self.client.post(f"{API}/fraud/investigate", headers=self.creator, data={
            "url": "https://novabook-offers.shop/diwali",
            "text": "NovaBook AI Pro 16 mega Diwali offer only ₹19,999! Enter your card number and OTP to claim. Hurry, only today!"})
        self.assertEqual(r.status_code, 200, r.text)
        inc = r.json()
        types = {f["type"] for f in inc["findings"]}
        self.assertTrue({"brand_in_domain", "unauthorised_price", "phishing_request", "urgency"} <= types)
        self.assertEqual(inc["risk"], "high")
        self.assertEqual(inc["status"], "Under Investigation")
        self.assertTrue(inc["number"].startswith("BV-INC-"))
        self.assertTrue(any("not fetched" in f["title"] or "card" in f["title"].lower() for f in inc["findings"]))

    def test_official_domain_with_approved_price_is_low(self):
        self.client.post(f"{API}/fraud/domains", headers=self.admin, json={"domain": "novatech.in"})
        inc = self.client.post(f"{API}/fraud/investigate", headers=self.creator, data={
            "url": "https://shop.novatech.in/novabook", "text": "NovaBook AI Pro 16 is available at ₹79,999."}).json()
        self.assertEqual(inc["risk"], "low")
        self.assertIn("official_domain", {f["type"] for f in inc["findings"]})

    def test_screenshot_evidence_preserved_and_logo_detected(self):
        self.client.post(f"{API}/assets", headers=self.admin, data={"name": "NOVA logo", "kind": "logo", "version_label": "v1"},
                         files={"file": ("l.png", ff.png_bytes(ff.make_logo("v2")), "image/png")})
        r = self.client.post(f"{API}/fraud/investigate", headers=self.creator, data={"url": "https://nova-deals.top"},
                             files={"file": ("shot.png", ff.png_bytes(ff.compose(ff.make_logo("v2"))), "image/png")})
        inc = r.json()
        self.assertTrue(any(f["type"] == "logo_use" for f in inc["findings"]))
        self.assertTrue(inc["has_evidence_file"])
        self.assertEqual(self.client.get(f"{API}/fraud/incidents/{inc['id']}/evidence", headers=self.creator).status_code, 200)
        self.assertEqual(self.client.get(f"{API}/fraud/incidents/{inc['id']}/evidence", headers=self.vx).status_code, 404)

    def test_status_workflow_permissions_and_history(self):
        inc = self.client.post(f"{API}/fraud/investigate", headers=self.creator, data={"text": "Win a free NovaBook, verify your account now"}).json()
        url = f"{API}/fraud/incidents/{inc['id']}/status"
        self.assertEqual(self.client.post(url, headers=self.creator, json={"status": "Confirmed"}).status_code, 403)
        self.assertEqual(self.client.post(url, headers=self.reviewer, json={"status": "Deepfake"}).status_code, 400)
        r = self.client.post(url, headers=self.reviewer, json={"status": "Confirmed", "note": "Reported by 3 customers"})
        self.assertEqual(r.status_code, 200, r.text)
        self.client.post(url, headers=self.admin, json={"status": "Resolved", "note": "Page taken down"})
        full = self.client.get(f"{API}/fraud/incidents/{inc['id']}", headers=self.creator).json()
        self.assertEqual([h["status"] for h in full["history"]], ["Under Investigation", "Confirmed", "Resolved"])
        self.assertEqual(self.client.get(f"{API}/fraud/incidents/{inc['id']}", headers=self.vx).status_code, 404)

    def test_domains_admin_only_and_input_required(self):
        self.assertEqual(self.client.post(f"{API}/fraud/domains", headers=self.creator, json={"domain": "x.com"}).status_code, 403)
        self.assertEqual(self.client.post(f"{API}/fraud/investigate", headers=self.creator, data={}).status_code, 400)


class TestReputation(_Base):
    def _upload(self, rows, name="reviews.json", headers=None):
        return self.client.post(f"{API}/reputation/upload", headers=headers or self.reviewer,
                                files={"file": (name, json.dumps(rows).encode(), "application/json")})

    def test_overview_from_uploaded_feedback(self):
        now = datetime.datetime.utcnow()
        rows = [{"text": t, "rating": r, "date": (now - datetime.timedelta(days=2)).strftime("%Y-%m-%d"), "channel": "Amazon"}
                for t, r, _ in LABELLED]
        rows += [{"text": "NovaBook AI Pro 16 battery lasts 5 hours, not 18 hours as advertised", "date": now.strftime("%Y-%m-%d")}
                 for _ in range(3)]
        r = self._upload(rows)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["imported"], len(rows))
        self.analyze(LAUNCH, "Battery campaign")
        ov = self.client.get(f"{API}/reputation/overview", headers=self.creator).json()
        self.assertEqual(ov["records"], len(rows))
        self.assertGreater(ov["sentiment"]["negative"], 0)
        cats = {c["category"]: c for c in ov["categories"]}
        self.assertGreaterEqual(cats["Battery"]["negative"], 3)
        self.assertTrue(any(p["product"] == "NovaBook AI Pro 16" for p in ov["products"]))
        self.assertTrue(any(c["title"] == "Battery campaign" for c in ov["campaign_related"]))
        self.assertTrue(any(x["theme"] == "Battery" for x in ov["risks"]))
        self.assertIn("not confirmed customer opinion", ov["note"])
        self.assertIsNotNone(ov["trend_note"])            # one week of data -> no trend claimed

    def test_permissions_validation_isolation_and_batch_removal(self):
        self.assertEqual(self._upload([{"text": "ok"}], headers=self.creator).status_code, 403)
        self.assertEqual(self.client.post(f"{API}/reputation/upload", headers=self.reviewer,
                                          files={"file": ("x.txt", b"hello", "text/plain")}).status_code, 400)
        self.assertEqual(self._upload([{"rating": 3}]).status_code, 400)
        r = self._upload([{"text": "Delivery delayed by two weeks", "date": "2026-10-01"}], name="tickets.json").json()
        self.assertEqual(self.client.get(f"{API}/reputation/overview", headers=self.vx).json()["records"], 0)
        ok = self.client.post(f"{API}/reputation/feedback", headers=self.reviewer, json={"text": "Support resolved it fast", "rating": 5})
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(self.client.delete(f"{API}/reputation/batches/{r['batch_id']}", headers=self.reviewer).status_code, 403)
        self.assertEqual(self.client.delete(f"{API}/reputation/batches/{r['batch_id']}", headers=self.admin).json()["removed"], 1)


if __name__ == "__main__":
    unittest.main()
