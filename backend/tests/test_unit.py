"""E1 unit tests — security, RAG, analyzer logic, passport hashing.

Runnable with stdlib: `python -m unittest backend.tests.test_unit` (from repo
root), or with pytest if installed. No network / no API key required.
"""
import unittest

from backend.app.core import security
from backend.app.core.config import settings
from backend.app.services import llm as llm_mod
from backend.app.services.analyzer import ContentAnalyzerService
from backend.app.services.passport_service import PassportService
from backend.app.services.rag import RagRetriever, TfidfEmbedder, cosine
from backend.app.services.seed import NOVA_ORG_ID
from backend.tests._util import make_seeded_db, drop_db


class TestSecurity(unittest.TestCase):
    def test_password_hash_roundtrip(self):
        salt, h = security.hash_password("S3cret!")
        self.assertTrue(security.verify_password("S3cret!", salt, h))
        self.assertFalse(security.verify_password("wrong", salt, h))

    def test_token_sign_verify_tamper_expiry(self):
        tok = security.create_token({"sub": "u1", "role": "Reviewer"}, settings.SECRET_KEY, ttl_seconds=60)
        payload = security.decode_token(tok, settings.SECRET_KEY)
        self.assertEqual(payload["sub"], "u1")
        self.assertIsNone(security.decode_token(tok + "x", settings.SECRET_KEY))      # tampered sig
        self.assertIsNone(security.decode_token(tok, "other-secret"))                # wrong key
        expired = security.create_token({"sub": "u1"}, settings.SECRET_KEY, ttl_seconds=-1)
        self.assertIsNone(security.decode_token(expired, settings.SECRET_KEY))        # expired


class TestRag(unittest.TestCase):
    def test_cosine_self_similarity(self):
        e = TfidfEmbedder()
        v = e.embed("launch price strictly 79999", {})
        self.assertAlmostEqual(cosine(v, v), 1.0, places=6)

    def test_embedder_empty(self):
        self.assertEqual(TfidfEmbedder().embed("", {}), {})


class _DbTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.Session, cls.path = make_seeded_db()

    @classmethod
    def tearDownClass(cls):
        drop_db(cls.engine, cls.path)

    def setUp(self):
        self.db = self.Session()
        # Deterministic: force heuristic-only (no LLM) for stable assertions.
        self.svc = ContentAnalyzerService(self.db, llm_provider=llm_mod.NullProvider())

    def tearDown(self):
        self.db.close()

    def _analyze(self, content, title="t"):
        return self.svc.analyze_submission(NOVA_ORG_ID, title, content)


class TestRagRanking(_DbTestCase):
    def test_price_query_ranks_pricing_page(self):
        r = RagRetriever(self.db)
        hit = r.best(NOVA_ORG_ID, "official launch price")
        self.assertIsNotNone(hit)
        self.assertEqual(hit["page"], 3)

    def test_org_isolation_returns_nothing_foreign(self):
        r = RagRetriever(self.db)
        # A term that only exists in NOVA chunks should never surface for an unknown org.
        self.assertEqual(r.search("no-such-org", "launch price"), [])


class TestAnalyzerFindings(_DbTestCase):
    def test_price_contradiction(self):
        sub = self._analyze("Buy the NovaBook AI Pro 16 now for only ₹69,999!")
        pricing = [c for c in sub.claim_verifications if c.category == "Pricing"]
        self.assertTrue(any(c.status == "Contradicted" for c in pricing))
        self.assertTrue(any(f.issue_category == "Pricing" for f in sub.findings))

    def test_price_supported(self):
        sub = self._analyze("The NovaBook AI Pro 16 is available at ₹79,999.")
        pricing = [c for c in sub.claim_verifications if c.category == "Pricing"]
        self.assertTrue(any(c.status == "Supported" for c in pricing))

    def test_terminology_flagged(self):
        sub = self._analyze("This is the world's fastest laptop.")
        self.assertTrue(any(f.issue_category == "Terminology" for f in sub.findings))

    def test_superlative_unsupported(self):
        sub = self._analyze("The world's fastest AI laptop has arrived.")
        self.assertTrue(any(c.status == "Unsupported" and c.category == "Performance"
                            for c in sub.claim_verifications))

    def test_comparative_unsupported(self):
        sub = self._analyze("It is 10x faster than every competitor.")
        self.assertTrue(any(c.status == "Unsupported" and c.category == "Comparative"
                            for c in sub.claim_verifications))

    def test_ambiguous_needs_human_review(self):
        sub = self._analyze("A revolutionary, industry-leading machine.")
        self.assertTrue(any(c.status == "Needs Human Review" for c in sub.claim_verifications))

    def test_outdated_fact(self):
        sub = self._analyze("Get the complimentary pre-order bonus NovaSleeve accessory.")
        self.assertTrue(any(c.status == "Outdated" for c in sub.claim_verifications))

    def test_evidence_cites_real_page(self):
        sub = self._analyze("Now only ₹69,999!")
        pricing_finding = [f for f in sub.findings if f.issue_category == "Pricing"][0]
        self.assertIn("Page", pricing_finding.evidence_source)

    def test_findings_labeled_heuristic(self):
        sub = self._analyze("The world's fastest laptop, only ₹69,999!")
        self.assertTrue(sub.findings)
        self.assertTrue(all(f.analysis_engine == "heuristic" for f in sub.findings))


class TestScore(_DbTestCase):
    def test_clean_content_scores_full(self):
        sub = self._analyze("The NovaBook AI Pro 16 is available at ₹79,999.")
        self.assertEqual(len(sub.findings), 0)
        self.assertEqual(sub.overall_score, 100)

    def test_violations_reduce_and_floor(self):
        sub = self._analyze("World's fastest! 10x faster than every competitor! Only ₹69,999! Cheap!")
        self.assertLess(sub.overall_score, 100)
        self.assertGreaterEqual(sub.overall_score, 5)


class TestPassportHash(_DbTestCase):
    def test_passport_hash_and_idempotency(self):
        from backend.app.models.passport import BrandPassport
        sub = self._analyze("The NovaBook AI Pro 16 at ₹79,999.")
        svc = PassportService(self.db)
        updated = svc.submit_review_decision(sub.id, "Approved", "ok", "NOVA Reviewer", "Reviewer")
        p1 = self.db.query(BrandPassport).filter_by(submission_id=updated.id).first()
        self.assertIsNotNone(p1)
        self.assertTrue(p1.passport_number.startswith("BV-2026-"))
        self.assertEqual(len(p1.content_hash), 64)  # SHA-256 hex
        # Idempotent: a second approve does not mint a second passport.
        svc.generate_brand_passport(updated, "NOVA Reviewer")
        self.assertEqual(self.db.query(BrandPassport).filter_by(submission_id=updated.id).count(), 1)


if __name__ == "__main__":
    unittest.main()
