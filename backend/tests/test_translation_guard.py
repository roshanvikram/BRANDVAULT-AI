"""Translation Guard tests — engine behaviour across languages, the optional AI
pass (with a fake provider, no network), and the API (auth, tenant isolation,
persistence).

Run: `python -m unittest backend.tests.test_translation_guard` (repo root).
"""
import json
import unittest
import uuid

from fastapi.testclient import TestClient

from backend.app.services import translation_guard as tg

EN = "The NovaBook AI Pro 16 provides up to 12 hours of battery life. Now at ₹79,999."
CTX = tg.BrandContext(product_names=["NovaBook AI Pro 16"],
                      approved_prices=[(79999.0, "NovaBook AI Pro 16 Launch Price", "Pricing Policy")])


def types(result):
    return {(f["type"], f["severity"]) for f in result["findings"]}


class TestLanguageDetection(unittest.TestCase):
    def test_scripts(self):
        cases = {
            "हमारा लैपटॉप 12 घंटे तक चलता है": "hi",
            "எங்கள் லேப்டாப் 12 மணி நேரம் வரை": "ta",
            "ഞങ്ങളുടെ ലാപ്ടോപ്പ്": "ml",
            "మా ల్యాప్‌టాప్": "te",
            "ನಮ್ಮ ಲ್ಯಾಪ್‌ಟಾಪ್": "kn",
            "NovaBook AI Pro 16は最大12時間": "ja",
            "NovaBook AI Pro 16 电池续航超过12小时": "zh",
            "يوفر عمر بطارية حتى 12 ساعة": "ar",
            "Notre ordinateur offre jusqu'à 12 heures": "fr",
            "Unser Laptop bietet bis zu 12 Stunden": "de",
            "Nuestro portátil ofrece hasta 12 horas": "es",
            "Our laptop gives you up to 12 hours": "en",
        }
        for text, code in cases.items():
            self.assertEqual(tg.detect_language(text)["code"], code, text)


class TestEngine(unittest.TestCase):
    def test_identical_translation_is_consistent(self):
        r = tg.analyze_pair(EN, "en", EN, CTX)
        self.assertEqual(r["verdict"], "Consistent")
        self.assertEqual(r["findings"], [])

    def test_brief_example_hindi_inflates_claim_and_price(self):
        hi = "नोवाबुक एआई प्रो 16 में 12 घंटे से अधिक बैटरी लाइफ मिलती है। अब सिर्फ ₹69,999 में।"
        r = tg.analyze_pair(EN, "en", hi, CTX)
        t = types(r)
        self.assertIn(("qualifier_changed", "CRITICAL"), t)       # up to -> more than
        self.assertIn(("changed_value", "CRITICAL"), t)           # 79,999 -> 69,999
        self.assertIn(("price_contradiction", "CRITICAL"), t)     # vs approved fact
        self.assertIn(("brand_term_changed", "WARNING"), t)       # transliterated name
        self.assertEqual(r["verdict"], "Needs revision")
        self.assertLessEqual(r["overall_score"], 59)
        # "प्रो 16" is part of the product name, not an extra claim
        self.assertNotIn("additional_claim", {f["type"] for f in r["findings"]})

    def test_brief_example_tamil_drops_qualifier(self):
        ta = "NovaBook AI Pro 16 12 மணி நேர பேட்டரி ஆயுளை வழங்குகிறது. இப்போது ₹79,999."
        r = tg.analyze_pair(EN, "en", ta, CTX)
        self.assertEqual(types(r), {("qualifier_changed", "WARNING")})
        self.assertEqual(r["verdict"], "Review recommended")

    def test_postposition_qualifier_matches(self):
        for text in ["NovaBook AI Pro 16 में 12 घंटे तक बैटरी लाइफ मिलती है। अब ₹79,999 में।",
                     "NovaBook AI Pro 16 12 மணி நேரம் வரை பேட்டரி. இப்போது ₹79,999."]:
            self.assertEqual(tg.analyze_pair(EN, "en", text, CTX)["verdict"], "Consistent", text)

    def test_european_number_formats(self):
        fr = "Le NovaBook AI Pro 16 offre jusqu'à 12 heures d'autonomie. Désormais à 79 999 ₹."
        self.assertEqual(tg.analyze_pair(EN, "en", fr, CTX)["verdict"], "Consistent")
        de = "Das NovaBook AI Pro 16 bietet bis zu 12 Stunden Akkulaufzeit. Jetzt für 79.999 ₹."
        self.assertEqual(tg.analyze_pair(EN, "en", de, CTX)["verdict"], "Consistent")

    def test_german_more_than_is_critical(self):
        de = "Das NovaBook AI Pro 16 bietet mehr als 12 Stunden Akkulaufzeit. Jetzt für 79.999 ₹."
        self.assertIn(("qualifier_changed", "CRITICAL"), types(tg.analyze_pair(EN, "en", de, CTX)))

    def test_cjk_qualifiers(self):
        ja = "NovaBook AI Pro 16は最大12時間のバッテリー駆動。今なら₹79,999。"
        self.assertEqual(tg.analyze_pair(EN, "en", ja, CTX)["verdict"], "Consistent")
        zh = "NovaBook AI Pro 16 电池续航超过12小时。现价₹79,999。"
        self.assertIn(("qualifier_changed", "CRITICAL"), types(tg.analyze_pair(EN, "en", zh, CTX)))

    def test_native_digits_are_normalised(self):
        hi = "NovaBook AI Pro 16 में १२ घंटे तक बैटरी लाइफ मिलती है। अब ₹७९,९९९ में।"
        self.assertEqual(tg.analyze_pair(EN, "en", hi, CTX)["verdict"], "Consistent")

    def test_missing_and_additional_figures(self):
        es = "El NovaBook AI Pro 16 ofrece hasta 12 horas de batería y 2 años de garantía."
        t = {f["type"] for f in tg.analyze_pair(EN, "en", es, CTX)["findings"]}
        self.assertIn("missing_information", t)   # price dropped
        self.assertIn("additional_claim", t)      # warranty added

    def test_negation_change_flagged(self):
        es = "El NovaBook AI Pro 16 ofrece hasta 12 horas de batería. No incluye cargador. Ahora a ₹79,999."
        self.assertIn(("negation_changed", "WARNING"), types(tg.analyze_pair(EN, "en", es, CTX)))

    def test_prohibited_term_in_translation(self):
        ctx = tg.BrandContext(product_names=CTX.product_names, approved_prices=CTX.approved_prices,
                              prohibited=[("cheap", "great value")])
        fr = "Le NovaBook AI Pro 16 offre jusqu'à 12 heures. Désormais à 79 999 ₹. Un laptop cheap!"
        self.assertIn(("prohibited_term", "CRITICAL"), types(tg.analyze_pair(EN, "en", fr, ctx)))

    def test_unsupported_language_is_honest(self):
        ml = "NovaBook AI Pro 16 12 മണിക്കൂർ ബാറ്ററി. ₹79,999."
        r = tg.analyze_pair(EN, "en", ml, CTX)
        self.assertFalse(r["qualifier_check_supported"])
        self.assertIsNone(r["scores"]["claim_consistency"])
        self.assertIsNone(r["scores"]["semantic_similarity"])  # no AI here


class _FakeProvider:
    name = "fake"
    model = "fake-1"
    available = True

    def __init__(self, raw):
        self.raw = raw
        self.calls = []

    def analyze(self, system, user):
        self.calls.append((system, user))
        return self.raw


class TestAIPass(unittest.TestCase):
    def test_ai_result_is_labelled_and_merged(self):
        raw = "```json\n" + json.dumps({
            "meaning_score": 72,
            "differences": [{"type": "meaning_change", "severity": "critical", "explanation": "Battery claim inflated."},
                            {"bad": "item"}],
            "corrected_translation": "corrected text",
            "cultural_notes": ["Fine for the region."],
        }) + "\n```"
        p = _FakeProvider(raw)
        hi = "NovaBook AI Pro 16 में 12 घंटे से अधिक बैटरी लाइफ मिलती है। अब ₹79,999 में।"
        r = tg.analyze_pair(EN, "en", hi, CTX, provider=p, brand_brief="BRAND: NOVA")
        self.assertEqual(r["engine"], "deterministic+llm:fake")
        self.assertEqual(r["scores"]["semantic_similarity"], 72)
        self.assertEqual(r["corrected_translation"], "corrected text")
        ai = [f for f in r["findings"] if f["engine"] == "llm:fake"]
        self.assertEqual(len(ai), 1)              # the malformed item is dropped
        self.assertEqual(ai[0]["severity"], "CRITICAL")
        self.assertIn("untrusted", p.calls[0][0])  # prompt-injection guard present

    def test_ai_duplicate_of_rule_finding_becomes_confirmation(self):
        raw = json.dumps({"meaning_score": 30, "differences": [
            {"severity": "CRITICAL", "explanation": "Price changed from ₹79,999 to ₹69,999."},
            {"severity": "WARNING", "explanation": "Tone is more casual than the source."}]})
        hi = "NovaBook AI Pro 16 में 12 घंटे तक बैटरी लाइफ मिलती है। अब ₹69,999 में।"
        r = tg.analyze_pair(EN, "en", hi, CTX, provider=_FakeProvider(raw))
        price = [f for f in r["findings"] if f["type"] == "changed_value"][0]
        self.assertTrue(price["confirmed_by_ai"])
        ai = [f for f in r["findings"] if f["engine"].startswith("llm")]
        self.assertEqual([f["explanation"] for f in ai], ["Tone is more casual than the source."])

    def test_unusable_ai_output_falls_back(self):
        r = tg.analyze_pair(EN, "en", EN, CTX, provider=_FakeProvider("not json at all"))
        self.assertEqual(r["engine"], "deterministic")
        self.assertIsNone(r["scores"]["semantic_similarity"])


class TestApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from backend.main import app
        from backend.app.core.config import settings
        from backend.app.core import security
        from backend.app.db.session import get_db
        from backend.app.models.brand import Organization
        from backend.app.models.user import User, ROLE_CREATOR
        from backend.tests._util import make_seeded_db

        cls.app, cls.settings, cls.get_db = app, settings, get_db
        cls._prev = (settings.LLM_ENABLED, settings.RATE_LIMIT_ENABLED)
        settings.LLM_ENABLED = False
        settings.RATE_LIMIT_ENABLED = False
        cls.engine, cls.Session, cls.path = make_seeded_db()
        db = cls.Session()
        db.add(Organization(id="tg-beta", name="BETA", slug="tg-beta"))
        salt, h = security.hash_password("Beta@2026")
        db.add(User(id=str(uuid.uuid4()), email="c@tgbeta.test", full_name="Beta Creator", role=ROLE_CREATOR,
                    org_id="tg-beta", salt=salt, password_hash=h))
        db.commit()
        db.close()

        def _override():
            d = cls.Session()
            try:
                yield d
            finally:
                d.close()

        app.dependency_overrides[get_db] = _override
        cls.client = TestClient(app)
        cls.nova = cls._hdr("creator@novatech.demo", "Creator@2026")
        cls.beta = cls._hdr("c@tgbeta.test", "Beta@2026")

    @classmethod
    def tearDownClass(cls):
        from backend.tests._util import drop_db
        cls.settings.LLM_ENABLED, cls.settings.RATE_LIMIT_ENABLED = cls._prev
        cls.app.dependency_overrides.clear()
        drop_db(cls.engine, cls.path)

    @classmethod
    def _hdr(cls, email, pw):
        r = cls.client.post("/api/v1/auth/login", json={"email": email, "password": pw})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    def _run(self, headers):
        body = {"title": "Battery launch", "source_text": EN, "translations": [
            {"label": "Tamil", "text": "NovaBook AI Pro 16 12 மணி நேர பேட்டரி ஆயுளை வழங்குகிறது. இப்போது ₹79,999."},
            {"label": "Hindi", "text": "नोवाबुक एआई प्रो 16 में 12 घंटे से अधिक बैटरी लाइफ मिलती है। अब सिर्फ ₹69,999 में।"},
        ]}
        return self.client.post("/api/v1/translation-guard/analyze", headers=headers, json=body)

    def test_requires_login(self):
        self.assertEqual(self.client.post("/api/v1/translation-guard/analyze", json={}).status_code, 401)
        self.assertEqual(self.client.get("/api/v1/translation-guard/campaigns").status_code, 401)

    def test_analyze_uses_org_brand_dna_and_persists(self):
        r = self._run(self.nova)
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["source_lang"], "en")
        self.assertEqual(body["verdict"], "Needs revision")
        self.assertEqual(body["engine"], "deterministic")  # LLM disabled in tests
        langs = [t["detected_lang"] for t in body["translations"]]
        self.assertEqual(langs, ["ta", "hi"])
        hindi = body["translations"][1]
        price = [f for f in hindi["findings"] if f["type"] == "price_contradiction"]
        self.assertTrue(price and "Pricing Policy" in price[0]["evidence"])  # evidence from the real fact
        # persisted + listed + retrievable
        listed = self.client.get("/api/v1/translation-guard/campaigns", headers=self.nova).json()
        self.assertIn(body["id"], [c["id"] for c in listed])
        again = self.client.get(f"/api/v1/translation-guard/campaigns/{body['id']}", headers=self.nova).json()
        self.assertEqual(again["translations"][1]["findings"], hindi["findings"])
        runs = self.client.get("/api/v1/agent/runs", headers=self.nova).json()
        self.assertTrue(any(x["agent_name"] == "Translation Guard Agent" for x in runs))

    def test_tenant_isolation(self):
        cid = self._run(self.nova).json()["id"]
        self.assertEqual(self.client.get(f"/api/v1/translation-guard/campaigns/{cid}", headers=self.beta).status_code, 404)
        self.assertNotIn(cid, [c["id"] for c in self.client.get("/api/v1/translation-guard/campaigns", headers=self.beta).json()])
        r = self.client.post("/api/v1/translation-guard/analyze", headers=self.beta,
                             json={"source_text": EN, "translations": [{"text": EN}], "org_id": "nova-tech-org-001"})
        self.assertEqual(r.status_code, 403)

    def test_validation_limits(self):
        r = self.client.post("/api/v1/translation-guard/analyze", headers=self.nova,
                             json={"source_text": EN, "translations": []})
        self.assertEqual(r.status_code, 422)
        r = self.client.post("/api/v1/translation-guard/analyze", headers=self.nova,
                             json={"source_text": "x" * 5001, "translations": [{"text": "y"}]})
        self.assertEqual(r.status_code, 422)

    def test_languages_endpoint(self):
        body = self.client.get("/api/v1/translation-guard/languages").json()
        self.assertIn("hi", [x["code"] for x in body["qualifier_and_negation_checks"]])
        self.assertFalse(body["ai_available"])


if __name__ == "__main__":
    unittest.main()
