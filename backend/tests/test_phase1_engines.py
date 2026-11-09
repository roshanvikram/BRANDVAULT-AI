"""12-engines Phase 1 tests: Product Truth, Knowledge Gap Detector, Campaign
DNA Fingerprint and Brand Asset Forensics — engine behaviour, permissions,
tenant isolation, evidence correctness and append-only history.

Run: `python -m unittest backend.tests.test_phase1_engines` (repo root).
"""
import io
import json
import os
import shutil
import tempfile
import unittest
import uuid

from fastapi.testclient import TestClient

from backend.app.services import forensics as fx
from backend.tests import forensics_fixtures as ff

API = "/api/v1"
NOVA_ORG = "nova-tech-org-001"
VORTEXA_ORG = "vortexa-tech-org-002"


# =============================================================================
#  Forensics engine (pure computer vision, no DB)
# =============================================================================
def _ref(img, ver, status, current, kind="logo", name="Vortexa logo"):
    data = ff.png_bytes(img)
    rgb, _, alpha = fx.load_image(data)
    fp = fx.fingerprints(data)
    return dict(id=ver, name=name, kind=kind, version_label=ver, status=status, current=current, rgb=rgb, alpha=alpha,
                sha256=fp["sha256"], phash=fp["phash"], dhash=fp["dhash"], replacement=None)


class TestForensicsEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v2, cls.v1 = ff.make_logo("v2"), ff.make_logo("v1")
        cls.refs = [_ref(cls.v2, "v2", "active", True), _ref(cls.v1, "v1", "superseded", False)]

    def _types(self, img, jpeg=False):
        r = fx.investigate(ff.jpeg_bytes(img) if jpeg else ff.png_bytes(img), self.refs)
        return r, {(m["version_label"], f["type"]) for m in r["matches"] for f in m["findings"]}

    def test_clean_official_logo(self):
        r, t = self._types(ff.compose(self.v2))
        self.assertEqual(t, {("v2", "official_logo")})
        self.assertEqual(r["risk"], "low")

    def test_stretched_logo(self):
        r, t = self._types(ff.compose(self.v2, size=(540, 160)))
        self.assertEqual(t, {("v2", "stretched")})
        lm = r["matches"][0]["logo_match"]
        self.assertAlmostEqual(lm["scale_x"] / lm["scale_y"], 1.5, delta=0.1)

    def test_rotated_logo(self):
        r, t = self._types(ff.compose(self.v2, rotate=25))
        self.assertEqual(t, {("v2", "rotated")})
        self.assertAlmostEqual(abs(r["matches"][0]["logo_match"]["rotation_deg"]), 25, delta=2)

    def test_recoloured_logo(self):
        r, t = self._types(ff.compose(ff.recolour(self.v2)))
        self.assertEqual(t, {("v2", "recoloured")})
        self.assertEqual(r["risk"], "high")

    def test_cropped_logo(self):
        _, t = self._types(ff.compose(self.v2, at=(780, 200)))
        self.assertEqual(t, {("v2", "cropped")})

    def test_outdated_logo_version(self):
        r, t = self._types(ff.compose(self.v1))
        self.assertEqual(t, {("v1", "outdated_logo")})  # the current v2 is not also reported

    def test_small_jpeg_still_official(self):
        _, t = self._types(ff.compose(self.v2, size=(180, 80)), jpeg=True)
        self.assertEqual(t, {("v2", "official_logo")})

    def test_no_logo_in_unrelated_image(self):
        r, t = self._types(ff.scene(seed=3))
        self.assertEqual(t, set())
        self.assertEqual(r["risk"], "none")

    def test_identical_and_near_duplicate_creative(self):
        creative = ff.compose(self.v2)
        ref = _ref(creative, "c1", "active", True, kind="creative", name="Diwali banner")
        same = fx.investigate(ff.png_bytes(creative), [ref])
        self.assertEqual({f["type"] for f in same["matches"][0]["findings"]}, {"identical_official"})
        resaved = fx.investigate(ff.jpeg_bytes(creative, q=70), [ref])
        self.assertIn("near_duplicate", {f["type"] for f in resaved["matches"][0]["findings"]})
        other = fx.investigate(ff.png_bytes(ff.scene(seed=9)), [ref])
        self.assertFalse(any(f["type"] == "near_duplicate" for m in other["matches"] for f in m["findings"]))

    def test_rejects_non_images(self):
        with self.assertRaises(ValueError):
            fx.load_image(b"%PDF-1.4 not an image")


# =============================================================================
#  API tests (seeded throwaway DB, both demo organisations)
# =============================================================================
class _ApiBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from backend.main import app
        from backend.app.core.config import settings
        from backend.app.db.session import get_db
        from backend.app.services.seed import seed_vortexa_brand
        from backend.app.api.v1 import assets as assets_api
        from backend.tests._util import make_seeded_db

        cls.app, cls.settings, cls.assets_api = app, settings, assets_api
        cls._prev = (settings.LLM_ENABLED, settings.RATE_LIMIT_ENABLED, assets_api.STORAGE_ROOT)
        settings.LLM_ENABLED = False
        settings.RATE_LIMIT_ENABLED = False
        cls.storage = tempfile.mkdtemp(prefix="bv_storage_")
        assets_api.STORAGE_ROOT = cls.storage
        cls.engine, cls.Session, cls.path = make_seeded_db()
        db = cls.Session()
        seed_vortexa_brand(db)
        from backend.app.services.rag import RagRetriever
        RagRetriever(db).index_org(VORTEXA_ORG)  # the app indexes every org at startup
        db.close()

        def _override():
            d = cls.Session()
            try:
                yield d
            finally:
                d.close()

        app.dependency_overrides[get_db] = _override
        cls.client = TestClient(app)
        cls.nova_admin = cls._hdr("admin@novatech.demo", "Admin@2026")
        cls.nova_creator = cls._hdr("creator@novatech.demo", "Creator@2026")
        cls.nova_reviewer = cls._hdr("reviewer@novatech.demo", "Reviewer@2026")
        cls.vx_admin = cls._hdr("admin@vortexa.demo", "Admin@2026")
        cls.vx_creator = cls._hdr("creator@vortexa.demo", "Creator@2026")

    @classmethod
    def tearDownClass(cls):
        from backend.tests._util import drop_db
        cls.settings.LLM_ENABLED, cls.settings.RATE_LIMIT_ENABLED, cls.assets_api.STORAGE_ROOT = cls._prev
        cls.app.dependency_overrides.clear()
        drop_db(cls.engine, cls.path)
        shutil.rmtree(cls.storage, ignore_errors=True)

    @classmethod
    def _hdr(cls, email, pw):
        r = cls.client.post(f"{API}/auth/login", json={"email": email, "password": pw})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}


class TestProductTruthApi(_ApiBase):
    def _verify(self, h, text):
        r = self.client.post(f"{API}/products/verify", headers=h, json={"text": text})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_brief_example_price_contradicted_with_evidence(self):
        r = self._verify(self.vx_creator, "Get VortexBook AI Pro 16 today for ₹69,999.")
        self.assertEqual(r["verdict"], "Contradicted")
        c = r["claims"][0]
        self.assertEqual((c["status"], c["attribute"], c["submitted_value"], c["approved_value"]),
                         ("Contradicted", "price", "₹69,999", "₹79,999"))
        self.assertIn("VT-BG-2026-001", c["source_document"])   # the real approved-fact source
        self.assertEqual(c["page_reference"], 2)
        self.assertIn("79,999", c["evidence_excerpt"] or "")     # evidence actually states the value
        self.assertIn("₹79,999", c["suggestion"])

    def test_missing_battery_is_unsupported_not_invented(self):
        r = self._verify(self.vx_creator, "VortexBook AI Pro 16 gives 15 hours of battery.")
        c = r["claims"][0]
        self.assertEqual((c["status"], c["attribute"], c["approved_value"]), ("Unsupported", "battery", None))

    def test_qualifier_rules(self):
        st = lambda t: [c["status"] for c in self._verify(self.nova_creator, t)["claims"]]
        self.assertEqual(st("NovaBook AI Pro 16 lasts up to 18 hours."), ["Supported"])
        self.assertEqual(st("NovaBook AI Pro 16 lasts 18 hours."), ["Needs Human Review"])   # drops "up to"
        self.assertEqual(st("NovaBook AI Pro 16 lasts more than 18 hours."), ["Contradicted"])
        self.assertEqual(st("NovaBook AI Pro 16 lasts 20 hours."), ["Contradicted"])
        self.assertEqual(st("NovaBook AI Pro 16 has a 2-year warranty."), ["Supported"])

    def test_admin_only_writes_and_supersession_makes_old_price_outdated(self):
        # Own product, so other tests keep the seeded VortexBook facts.
        self.assertEqual(self.client.post(f"{API}/products", headers=self.vx_creator, json={"name": "Vortex Phone X"}).status_code, 403)
        pid = self.client.post(f"{API}/products", headers=self.vx_admin, json={"name": "Vortex Phone X"}).json()["id"]
        body = {"attribute": "price", "value_text": "₹24,999", "source_document": "Launch price list", "page_reference": 1}
        self.assertEqual(self.client.post(f"{API}/products/{pid}/facts", headers=self.vx_creator, json=body).status_code, 403)
        self.assertEqual(self.client.post(f"{API}/products/{pid}/facts", headers=self.vx_admin, json=body).status_code, 200)
        body2 = dict(body, value_text="₹21,999", source_document="Price revision memo")
        self.assertEqual(self.client.post(f"{API}/products/{pid}/facts", headers=self.vx_admin, json=body2).status_code, 200)
        prod = [p for p in self.client.get(f"{API}/products", headers=self.vx_admin).json()["products"] if p["id"] == pid][0]
        prices = {f["value_text"]: f["status"] for f in prod["facts"] if f["attribute"] == "price"}
        self.assertEqual(prices, {"₹21,999": "approved", "₹24,999": "superseded"})
        old = self._verify(self.vx_creator, "Vortex Phone X now ₹24,999.")["claims"][0]
        self.assertEqual((old["status"], old["approved_value"]), ("Outdated", "₹21,999"))
        new = self._verify(self.vx_creator, "Vortex Phone X now ₹21,999.")["claims"][0]
        self.assertEqual(new["status"], "Supported")

    def test_tenant_isolation(self):
        nova = self.client.get(f"{API}/products", headers=self.nova_creator).json()["products"]
        vx = self.client.get(f"{API}/products", headers=self.vx_creator).json()["products"]
        self.assertEqual({p["name"] for p in nova}, {"NovaBook AI Pro 16"})
        vx_names = {p["name"] for p in vx}
        self.assertIn("VortexBook AI Pro 16", vx_names)
        self.assertFalse(any(n.startswith("Nova") for n in vx_names))
        fid = nova[0]["facts"][0]["id"]
        self.assertEqual(self.client.post(f"{API}/products/facts/{fid}/approve", headers=self.vx_admin).status_code, 404)
        self.assertEqual(self.client.post(f"{API}/products/{nova[0]['id']}/facts", headers=self.vx_admin,
                                          json={"attribute": "price", "value_text": "₹1", "source_document": "xx"}).status_code, 404)
        self.assertEqual(self.client.get(f"{API}/products", headers={}).status_code, 401)

    def test_extract_reports_blocker_without_ai(self):
        r = self.client.post(f"{API}/products/extract", headers=self.nova_admin)
        self.assertEqual(r.status_code, 503)
        self.assertIn("No AI model", r.json()["detail"])

    def test_ai_extraction_rejects_unverifiable_evidence(self):
        from backend.app.services import product_truth as pt
        from backend.app.models.product import ProductFact

        class Fake:
            name, model, available = "fake", "fake-1", True

            def analyze(self, system, user):
                return json.dumps({"facts": [
                    {"product": "NovaBook AI Pro 16", "attribute": "price", "value_text": "₹79,999", "page": 1,
                     "excerpt": "official launch price is strictly ₹79,999"},      # really in the guideline
                    {"product": "NovaBook AI Pro 16", "attribute": "battery", "value_text": "30 hours", "page": 1,
                     "excerpt": "battery lasts an amazing 30 hours"},               # invented
                    {"product": "NovaBook AI Pro 16", "attribute": "colour", "value_text": "blue", "excerpt": "blue body"},
                ]})

        db = self.Session()
        try:
            res = pt.extract_from_documents(db, NOVA_ORG, Fake(), actor="test")
            self.assertEqual(res["rejected_unverifiable"], 2 * res["batches"] if res["batches"] else 2)
            pending = db.query(ProductFact).filter(ProductFact.org_id == NOVA_ORG, ProductFact.status == "pending").all()
            self.assertTrue(all("30 hours" not in f.value_text for f in pending))
        finally:
            db.close()


class TestKnowledgeGapsApi(_ApiBase):
    def _gaps(self, h):
        r = self.client.get(f"{API}/products/knowledge-gaps", headers=h)
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_vortexa_missing_specs_are_reported(self):
        g = self._gaps(self.vx_creator)
        missing = {i["label"] for i in g["items"] if i["status"] == "missing"}
        for attr in ("Battery", "Processor", "Approved performance claim"):
            self.assertIn(f"VortexBook AI Pro 16 — {attr}", missing)
        self.assertNotIn("VortexBook AI Pro 16 — Approved price", missing)   # price exists
        self.assertTrue(0 <= g["completeness"] < 100)
        self.assertTrue(g["recommended_documents"])

    def test_adding_a_fact_closes_the_gap(self):
        before = self._gaps(self.vx_admin)
        pid = before["products"][0]["product_id"]
        r = self.client.post(f"{API}/products/{pid}/facts", headers=self.vx_admin,
                             json={"attribute": "warranty", "value_text": "1-Year Limited Warranty", "source_document": "Warranty terms"})
        self.assertEqual(r.status_code, 200, r.text)
        after = self._gaps(self.vx_admin)
        missing = {i["label"] for i in after["items"] if i["status"] == "missing"}
        self.assertNotIn("VortexBook AI Pro 16 — Warranty", missing)
        self.assertGreater(after["completeness"], before["completeness"])

    def test_conflicting_price_in_guideline_detected(self):
        from backend.app.models.brand import BrandRule
        db = self.Session()
        try:
            db.add(BrandRule(id=str(uuid.uuid4()), org_id=NOVA_ORG, category="Pricing", title="Old price memo",
                             rule_text="The NovaBook launch price is ₹84,999 for all channels.", severity="WARNING",
                             source_document="Old memo", is_active=True, is_confirmed=True))
            db.commit()
        finally:
            db.close()
        conflicts = [i for i in self._gaps(self.nova_creator)["items"] if i["status"] == "conflict"]
        self.assertTrue(any("84,999" in i["detail"] and i["evidence"]["source"] == "Old memo" for i in conflicts))

    def test_guideline_pages_come_from_page_markers(self):
        """Regression: chunks used (paragraph index // 3) + 1 as their page."""
        from backend.app.models.brand import DocumentChunk, BrandGuideline
        doc = ("--- Page 1 ---\nIntro paragraph about the brand and its values in general.\n\n"
               "--- Page 2 ---\nPricing: the launch price must always be quoted exactly as approved.\n\n"
               "Second paragraph on page two about discounts which must be approved first.\n\n"
               "--- Page 5 ---\nWarranty statements must cite the official warranty document.")
        r = self.client.post(f"{API}/brand/guidelines/upload", headers=self.nova_admin,
                             files={"file": ("paged.txt", doc.encode("utf-8"), "text/plain")})
        self.assertEqual(r.status_code, 200, r.text)
        db = self.Session()
        try:
            chunks = (db.query(DocumentChunk).join(BrandGuideline, DocumentChunk.guideline_id == BrandGuideline.id)
                      .filter(BrandGuideline.filename == "paged.txt").order_by(DocumentChunk.chunk_index).all())
            # Round 3 chunking merges short paragraphs of the same page into one passage.
            self.assertEqual(sorted({c.page_number for c in chunks}), [1, 2, 5])
            by_page = {c.page_number: c.content for c in chunks}
            self.assertIn("discounts", by_page[2])
            self.assertIn("Warranty", by_page[5])
            self.assertEqual(chunks[0].section_label, "Page 1")
        finally:
            db.close()

    def test_isolation(self):
        vx = {i["label"] for i in self._gaps(self.vx_creator)["items"]}
        self.assertFalse(any("NovaBook" in x for x in vx))
        self.assertEqual(self.client.get(f"{API}/products/knowledge-gaps", headers=self.vx_creator,
                                         params={"org_id": NOVA_ORG}).status_code, 403)


class TestCampaignFingerprintApi(_ApiBase):
    def _approved_campaign(self, text):
        sub = self.client.post(f"{API}/content/analyze", headers=self.nova_creator,
                               json={"title": "Fingerprint test", "content": text}).json()
        r = self.client.post(f"{API}/approval/decide", headers=self.nova_reviewer,
                             json={"submission_id": sub["id"], "decision": "Approved", "comments": "ok",
                                   "expected_version": sub["version"]})
        self.assertEqual(r.status_code, 200, r.text)
        return sub

    def _verify(self, h, text=None, file=None):
        files = {"file": file} if file else None
        data = {"text": text} if text is not None else {}
        r = self.client.post(f"{API}/passport/verify", headers=h, data=data, files=files)
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_full_lifecycle(self):
        text = "NovaBook AI Pro 16. Engineered for 45 TOPS sustained AI performance. Now ₹79,999."
        sub = self._approved_campaign(text)
        pp = self.client.get(f"{API}/passport/by-submission/{sub['id']}", headers=self.nova_creator).json()
        fp = pp["passport_data"]["fingerprint"]
        for key in ("campaign_id", "brand_id", "content_sha256", "approved_version", "guideline_version",
                    "approval_reference", "approver", "timestamp", "revision_number"):
            self.assertIn(key, fp)
        self.assertNotEqual(pp["guideline_version"], "v2.4")          # real document, not a placeholder
        self.assertIn("NOVA_TECH", pp["guideline_version"])

        self.assertEqual(self._verify(self.nova_creator, text)["result"], "Verified Match")
        self.assertEqual(self._verify(self.nova_creator, "  " + text.replace(" ", "\n  ", 2) + "\n")["result"],
                         "Verified Match")                                # whitespace is not a change
        edited = self._verify(self.nova_creator, text.replace("₹79,999", "₹69,999"))
        self.assertEqual(edited["result"], "Modified After Approval")
        self.assertIn({"change": "replace", "approved": "₹79,999.", "submitted": "₹69,999."}, edited["details"]["diff"])
        self.assertEqual(self._verify(self.nova_creator, "Completely different autumn sale copy for headphones.")["result"],
                         "New Unapproved Campaign")
        f = self._verify(self.nova_creator, file=("ad.txt", text.encode("utf-8"), "text/plain"))
        self.assertEqual(f["result"], "Verified Match")
        img = self._verify(self.nova_creator, file=("ad.png", ff.png_bytes(ff.scene()), "image/png"))
        self.assertEqual(img["result"], "Unable to Verify")

        # edit the approved campaign -> its old text is now a superseded version
        self.client.post(f"{API}/content/analyze", headers=self.nova_creator,
                         json={"title": "Fingerprint test", "content": text + " Limited stock.", "submission_id": sub["id"]})
        self.assertEqual(self._verify(self.nova_creator, text)["result"], "Unknown Version")

        log = self.client.get(f"{API}/passport/integrity-checks", headers=self.nova_creator).json()
        self.assertGreaterEqual(len(log), 7)                              # every check was appended

    def test_unapproved_known_version(self):
        sub = self.client.post(f"{API}/content/analyze", headers=self.nova_creator,
                               json={"title": "Draft only", "content": "Draft-only copy for the spring launch event."}).json()
        r = self._verify(self.nova_creator, "Draft-only copy for the spring launch event.")
        self.assertEqual((r["result"], r["matched_submission_id"]), ("Unknown Version", sub["id"]))

    def test_isolation_and_append_only(self):
        text = "Isolation check copy for NOVA only, approved."
        self._approved_campaign(text)
        self.assertEqual(self._verify(self.vx_creator, text)["result"], "New Unapproved Campaign")  # no leak
        vx_log = self.client.get(f"{API}/passport/integrity-checks", headers=self.vx_creator).json()
        self.assertTrue(all(c["checked_by"].startswith("VORTEXA") for c in vx_log))
        from backend.app.api.v1 import api_router
        routes = [r for inc in api_router.routes for r in inc.original_router.routes]
        paths = {r.path for r in routes}
        methods = {(m, r.path) for r in routes for m in getattr(r, "methods", [])}
        self.assertFalse(any(p.startswith("/passport/integrity-checks") and m in ("PUT", "PATCH", "DELETE")
                             for m, p in methods))
        self.assertIn("/passport/integrity-checks", paths)


class TestAssetForensicsApi(_ApiBase):
    def _upload(self, h, img, name="Vortexa logo", version="v1", supersedes=None, kind="logo"):
        data = {"name": name, "kind": kind, "version_label": version}
        if supersedes:
            data["supersedes_id"] = supersedes
        return self.client.post(f"{API}/assets", headers=h, data=data,
                                files={"file": (f"{version}.png", ff.png_bytes(img), "image/png")})

    def test_library_supersession_and_investigation(self):
        self.assertEqual(self._upload(self.vx_creator, ff.make_logo("v1")).status_code, 403)   # admin only
        v1 = self._upload(self.vx_admin, ff.make_logo("v1"), version="v1").json()
        v2 = self._upload(self.vx_admin, ff.make_logo("v2"), version="v2", supersedes=v1["id"]).json()
        lib = {a["version_label"]: a for a in self.client.get(f"{API}/assets", headers=self.vx_creator).json()}
        self.assertEqual((lib["v1"]["status"], lib["v1"]["current"]), ("superseded", False))
        self.assertEqual(lib["v1"]["replacement"]["id"], v2["id"])        # only a current asset is recommended
        self.assertIsNone(lib["v2"]["replacement"])

        r = self.client.post(f"{API}/assets/investigate", headers=self.vx_creator,
                             files={"file": ("old-ad.png", ff.png_bytes(ff.compose(ff.make_logo("v1"))), "image/png")})
        self.assertEqual(r.status_code, 200, r.text)
        inv = r.json()
        top = inv["matches"][0]
        self.assertEqual(inv["risk"], "high")
        self.assertEqual((top["version_label"], top["findings"][0]["type"]), ("v1", "outdated_logo"))
        self.assertEqual(top["replacement"]["version_label"], "v2")
        self.assertEqual(len(top["logo_match"]["bbox"]), 4)
        # evidence preserved and retrievable by the same org only
        self.assertEqual(self.client.get(f"{API}/assets/investigations/{inv['id']}/file", headers=self.vx_creator).status_code, 200)
        self.assertEqual(self.client.get(f"{API}/assets/investigations/{inv['id']}/file", headers=self.nova_creator).status_code, 404)
        self.assertEqual(self.client.get(f"{API}/assets/{v2['id']}/file", headers=self.nova_creator).status_code, 404)
        runs = self.client.get(f"{API}/agent/runs", headers=self.vx_creator).json()
        self.assertTrue(any(x["agent_name"] == "Asset Forensics Agent" for x in runs))

    def test_invalid_upload_rejected(self):
        r = self.client.post(f"{API}/assets/investigate", headers=self.nova_creator,
                             files={"file": ("x.png", b"not an image at all", "image/png")})
        self.assertEqual(r.status_code, 415)

    def test_empty_library_is_honest(self):
        r = self.client.post(f"{API}/assets/investigate", headers=self.nova_creator,
                             files={"file": ("ad.png", ff.png_bytes(ff.scene()), "image/png")}).json()
        self.assertEqual(r["compared"], 0)
        self.assertIn("No official assets", r["summary"])

    def test_knowledge_gaps_see_the_logo_library(self):
        before = {i["key"]: i["status"] for i in
                  self.client.get(f"{API}/products/knowledge-gaps", headers=self.nova_admin).json()["items"]}
        self.assertEqual(before["assets_logo"], "missing")
        self._upload(self.nova_admin, ff.make_logo("v2"), name="NOVA logo", version="v1")
        after = {i["key"]: i["status"] for i in
                 self.client.get(f"{API}/products/knowledge-gaps", headers=self.nova_admin).json()["items"]}
        self.assertEqual(after["assets_logo"], "ok")


if __name__ == "__main__":
    unittest.main()
