"""AI findings are reviewer suggestions, and only when they quote the copy."""
import json
import unittest

from backend.app.services import llm as llm_mod
from backend.app.services.analyzer import ContentAnalyzerService
from backend.tests._util import drop_db, make_seeded_db

ORG = "nova-tech-org-001"


class FakeProvider(llm_mod.LLMProvider):
    name = "fake"

    @property
    def available(self):
        return True

    @property
    def model(self):
        return "fake-1"

    def analyze(self, system, user):
        return json.dumps({"findings": [
            {"issue_category": "Tone & Voice", "severity": "CRITICAL", "original_text": "Hi Priya",
             "explanation": "Too casual.", "suggested_correction": "Dear Priya", "confidence": 0.9},
            {"issue_category": "Promotional Claim", "severity": "CRITICAL", "original_text": "the best laptop in the galaxy",
             "explanation": "Invented quote.", "suggested_correction": "", "confidence": 0.95},
        ]})


class LlmFindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.Session, cls.path = make_seeded_db()

    @classmethod
    def tearDownClass(cls):
        drop_db(cls.engine, cls.path)

    def test_suggestions_only_and_quotes_checked(self):
        db = self.Session()
        try:
            sub = ContentAnalyzerService(db, llm_provider=FakeProvider()).analyze_submission(
                ORG, "Email", "Hi Priya, thanks for your interest in the NovaBook AI Pro.")
            ai = [f for f in sub.findings if (f.analysis_engine or "").startswith("llm")]
            self.assertEqual([f.original_text for f in ai], ["Hi Priya"])  # invented quote dropped
            self.assertEqual(ai[0].severity, "SUGGESTION")
            self.assertGreaterEqual(sub.overall_score, 92)  # a suggestion only nudges the score
        finally:
            db.close()

    def test_rate_limit_retry_is_bounded(self):
        import urllib.error
        from unittest import mock
        calls = []

        def boom(*a, **k):
            calls.append(1)
            raise urllib.error.HTTPError("u", 429, "Too Many Requests", {"retry-after": "0"}, None)

        p = llm_mod.GroqProvider("key", "m", 5, 100)
        with mock.patch("urllib.request.urlopen", boom), mock.patch("time.sleep"):
            self.assertIsNone(p.analyze("s", "u"))
        self.assertEqual(len(calls), 3)


if __name__ == "__main__":
    unittest.main()
