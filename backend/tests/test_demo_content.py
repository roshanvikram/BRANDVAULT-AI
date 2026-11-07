"""Demo campaign seed for fresh deployments (services/demo_content.py)."""
import unittest

from backend.app.core.config import settings
from backend.app.models.submission import ApprovalRecord, Submission
from backend.app.services.demo_content import CAMPAIGNS, DEMO_NOTE, seed_demo_campaigns
from backend.app.services.seed import NOVA_ORG_ID
from backend.tests._util import drop_db, make_seeded_db


class DemoContentSeedTests(unittest.TestCase):
    def setUp(self):
        self._llm = settings.LLM_ENABLED
        settings.LLM_ENABLED = False
        self.engine, self.Session, self.path = make_seeded_db()
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        drop_db(self.engine, self.path)
        settings.LLM_ENABLED = self._llm

    def _subs(self):
        return {s.title: s for s in self.db.query(Submission).filter(Submission.org_id == NOVA_ORG_ID).all()}

    def test_seeds_every_campaign_once(self):
        self.assertEqual(seed_demo_campaigns(self.db), len(CAMPAIGNS))
        self.assertEqual(seed_demo_campaigns(self.db), 0)  # idempotent
        self.assertEqual(len(self._subs()), len(CAMPAIGNS))

    def test_never_touches_a_workspace_that_has_campaigns(self):
        from backend.app.services.analyzer import ContentAnalyzerService
        from backend.app.services.llm import NullProvider
        ContentAnalyzerService(self.db, llm_provider=NullProvider()).analyze_submission(NOVA_ORG_ID, "Real campaign", "Hello world.")
        self.assertEqual(seed_demo_campaigns(self.db), 0)
        self.assertEqual(list(self._subs()), ["Real campaign"])

    def test_findings_come_from_the_real_engine(self):
        seed_demo_campaigns(self.db)
        subs = self._subs()
        launch = subs["NovaBook AI Pro 16 — Launch Announcement"]
        hero = subs["NovaBook AI Pro 16 — Product Page Hero"]
        self.assertIn("Contradicted", [c.status for c in launch.claim_verifications])  # ₹69,999 vs ₹79,999
        self.assertLess(launch.overall_score, 50)
        self.assertGreaterEqual(hero.overall_score, 90)
        self.assertIn("Outdated", [c.status for c in subs["Retail Partner Email — Pre-order Bonus"].claim_verifications])
        self.assertTrue(all(s.department for s in subs.values()))

    def test_demo_decisions_are_labelled_and_issue_a_passport(self):
        seed_demo_campaigns(self.db)
        subs = self._subs()
        hero = subs["NovaBook AI Pro 16 — Product Page Hero"]
        self.assertEqual(hero.status, "Approved")
        self.assertIsNotNone(hero.passport)
        self.assertEqual(subs["NovaBook AI Pro 16 — Launch Announcement"].status, "Revision Requested")
        records = self.db.query(ApprovalRecord).all()
        self.assertEqual(len(records), 2)
        for r in records:
            self.assertEqual(r.comments, DEMO_NOTE)
            self.assertIn("demo", r.reviewer_name.lower())

    def test_seed_makes_no_ai_calls(self):
        seed_demo_campaigns(self.db)
        engines = {f.analysis_engine or "heuristic" for s in self._subs().values() for f in s.findings}
        self.assertFalse(any(e.startswith("llm") for e in engines))


if __name__ == "__main__":
    unittest.main()
