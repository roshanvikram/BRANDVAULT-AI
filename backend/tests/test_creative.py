"""Round 3 · Improvement 1 — Creative Inspection (OCR, PDF, video, regions, clear space, settings)."""
import unittest

from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.services import creative, ocr
from backend.main import app
from backend.tests import creative_fixtures as cf
from backend.tests._util import drop_db, make_seeded_db

API = "/api/v1"


class OcrCorrectionUnitTests(unittest.TestCase):
    VOCAB = ocr.brand_vocabulary(["NovaBook AI Pro 16", "NovaSleeve"])

    def test_confusions_fixed_only_against_brand_vocabulary(self):
        fixed, fx = ocr.correct("NovaBook Al Pro 16 Albert", self.VOCAB)
        self.assertEqual(fixed, "NovaBook AI Pro 16 Albert")  # "Albert" untouched
        self.assertEqual(fx[0]["to"], "AI")

    def test_run_together_words_split(self):
        fixed, fx = ocr.correct("NovaBookAlPro16", self.VOCAB)
        self.assertEqual(fixed, "NovaBook AI Pro 16")
        self.assertEqual(fx[0]["reason"], "words run together by OCR")

    def test_currency_restored_only_in_price_context(self):
        self.assertEqual(ocr.restore_currency("Now only 69,999", "₹")[0], "Now only ₹69,999")
        self.assertEqual(ocr.restore_currency("Students: only R69,999", "₹")[0], "Students: only ₹69,999")
        self.assertEqual(ocr.restore_currency("Over 10,000 happy users", "₹")[0], "Over 10,000 happy users")

    def test_clear_space_measurement(self):
        ok = creative.clear_space([100, 100, 200, 100], 600, 400, 0.25, [])
        self.assertTrue(ok["ok"])
        self.assertEqual(ok["required_px"], 25)
        tight = creative.clear_space([10, 100, 200, 100], 600, 400, 0.25, [{"text": "Sale", "box": [100, 210, 80, 20]}])
        self.assertFalse(tight["ok"])
        self.assertIn("left", tight["tight_edges"])
        self.assertEqual(tight["intruding_text"], ["Sale"])


@unittest.skipUnless(ocr.available(), "OCR engine not installed")
class CreativeApiTests(unittest.TestCase):
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
        cls.client = TestClient(app)

        def login(email, pw):
            r = cls.client.post(f"{API}/auth/login", json={"email": email, "password": pw})
            return {"Authorization": f"Bearer {r.json()['access_token']}"}
        cls.creator = login("creator@novatech.demo", "Creator@2026")
        cls.admin = login("admin@novatech.demo", "Admin@2026")
        from backend.app.services.seed import seed_vortexa_brand, seed_demo_users  # noqa: F401
        db = cls.Session()
        seed_vortexa_brand(db)
        db.close()
        cls.vx = login("creator@vortexa.demo", "Creator@2026")

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        drop_db(cls.engine, cls.path)
        settings.LLM_ENABLED, settings.RATE_LIMIT_ENABLED = cls._prev

    def _inspect(self, name, data, headers=None):
        r = self.client.post(f"{API}/creative/inspect", files={"file": (name, data)}, headers=headers or self.creator)
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_banner_price_and_superlative_found_and_located(self):
        out = self._inspect("banner.png", cf.banner(["NovaBook AI Pro 16", "The world's fastest AI laptop!", "Now only ₹69,999"]))
        self.assertEqual(out["kind"], "image")
        cats = {f["category"] for f in out["submission"]["findings"]}
        self.assertIn("Pricing", cats)
        self.assertIn("Contradicted", [c["status"] for c in out["submission"]["claims"]])
        self.assertTrue(any(r["kind"] == "finding" and r["page"] == 0 for r in out["regions"]))
        self.assertTrue(any(c["to"] == "₹69,999" for c in out["corrections"]))
        img = self.client.get(f"{API}/creative/inspections/{out['id']}/pages/0/image", headers=self.creator)
        self.assertEqual(img.status_code, 200)
        self.assertTrue(img.content.startswith(b"\x89PNG"))

    def test_pdf_text_layer_is_used_exactly(self):
        out = self._inspect("deck.pdf", cf.text_pdf([["Cover"], ["10x faster than every competitor", "Launch price Rs. 69,999"]]))
        self.assertEqual(out["kind"], "pdf")
        self.assertEqual([p["source"] for p in out["pages"]], ["pdf-text", "pdf-text"])
        self.assertTrue(any(r["page"] == 1 for r in out["regions"]))

    def test_scanned_pdf_and_video_use_ocr(self):
        scan = self._inspect("scan.pdf", cf.image_pdf(["Pre-order bonus", "complimentary NovaSleeve accessory"]))
        self.assertEqual(scan["pages"][0]["source"], "ocr")
        self.assertIn("Outdated", [c["status"] for c in scan["submission"]["claims"]])
        vid = self._inspect("promo.mp4", cf.video([["NovaBook AI Pro 16"], ["The world's fastest AI laptop"]]))
        self.assertEqual(vid["kind"], "video")
        self.assertGreaterEqual(len(vid["pages"]), 2)
        self.assertIn("note", vid)

    def test_no_text_is_reported_not_invented(self):
        out = self._inspect("blank.png", cf.banner([]))
        self.assertFalse(out["text_found"])
        self.assertIsNone(out["submission_id"])

    def test_unsupported_file_rejected(self):
        r = self.client.post(f"{API}/creative/inspect", files={"file": ("notes.txt", b"hello world")}, headers=self.creator)
        self.assertEqual(r.status_code, 415)

    def test_other_organisations_cannot_see_inspections(self):
        out = self._inspect("x.png", cf.banner(["NovaBook AI Pro 16"]))
        self.assertEqual(self.client.get(f"{API}/creative/inspections/{out['id']}", headers=self.vx).status_code, 404)
        self.assertEqual(self.client.get(f"{API}/creative/inspections/{out['id']}/pages/0/image", headers=self.vx).status_code, 404)
        ids = [i["id"] for i in self.client.get(f"{API}/creative/inspections", headers=self.vx).json()]
        self.assertNotIn(out["id"], ids)

    def test_settings_admin_only_and_validated(self):
        self.assertTrue(self.client.get(f"{API}/workspace/settings", headers=self.admin).json()["editable"])
        self.assertFalse(self.client.get(f"{API}/workspace/settings", headers=self.creator).json()["editable"])
        self.assertEqual(self.client.put(f"{API}/workspace/settings", json={"logo_clear_space_ratio": 0.5},
                                         headers=self.creator).status_code, 403)
        r = self.client.put(f"{API}/workspace/settings", json={"logo_clear_space_ratio": 0.5}, headers=self.admin)
        self.assertEqual(r.json()["settings"]["logo_clear_space_ratio"], 0.5)
        self.assertEqual(self.client.put(f"{API}/workspace/settings", json={"logo_clear_space_ratio": 9},
                                         headers=self.admin).status_code, 422)
        self.assertEqual(self.client.put(f"{API}/workspace/settings", json={"made_up": 1},
                                         headers=self.admin).status_code, 422)
        self.client.put(f"{API}/workspace/settings", json={"logo_clear_space_ratio": 0.25}, headers=self.admin)


if __name__ == "__main__":
    unittest.main()
