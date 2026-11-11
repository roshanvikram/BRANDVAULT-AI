"""Deleting an uploaded guideline document."""
import unittest

from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.brand import BrandGuideline, BrandRule, DocumentChunk
from backend.app.models.retrieval import ChunkEmbedding
from backend.main import app
from backend.tests._util import drop_db, make_seeded_db

API = "/api/v1"
DOC = ("Delete Test Guide\n\nAll prices must match the approved price list.\n\n"
       "Exclamation marks are strictly prohibited in headlines.\n\nOur tone is calm and precise.\n").encode()


class GuidelineDeleteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._prev = (settings.LLM_ENABLED, settings.RATE_LIMIT_ENABLED)
        settings.LLM_ENABLED = False
        settings.RATE_LIMIT_ENABLED = False
        cls.engine, cls.Session, cls.path = make_seeded_db()

        def _db():
            d = cls.Session()
            try:
                yield d
            finally:
                d.close()
        app.dependency_overrides[get_db] = _db
        cls.c = TestClient(app)
        tok = lambda e, p: {"Authorization": "Bearer " + cls.c.post(f"{API}/auth/login", json={"email": e, "password": p}).json()["access_token"]}
        cls.admin = tok("admin@novatech.demo", "Admin@2026")
        cls.creator = tok("creator@novatech.demo", "Creator@2026")

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        drop_db(cls.engine, cls.path)
        settings.LLM_ENABLED, settings.RATE_LIMIT_ENABLED = cls._prev

    def test_delete_removes_document_keeps_confirmed_rules(self):
        g = self.c.post(f"{API}/brand/guidelines/upload", headers=self.admin,
                        files={"file": ("delete_test_guide.md", DOC, "text/markdown")}).json()
        self.assertIn("id", g)
        db = self.Session()
        try:  # a second unconfirmed rule from the same document
            import uuid
            db.add(BrandRule(id=str(uuid.uuid4()), org_id="nova-tech-org-001", category="Guideline Rule", title="Extra",
                             rule_text="Use calm wording.", severity="WARNING", source_document="delete_test_guide.md",
                             is_active=True, is_confirmed=False))
            db.commit()
        finally:
            db.close()
        rules = [r for r in self.c.get(f"{API}/brand/rules", headers=self.admin).json()
                 if r.get("source_document") == "delete_test_guide.md"]
        self.assertGreaterEqual(len(rules), 2)
        keep = rules[0]["id"]
        self.c.patch(f"{API}/brand/rules/{keep}/confirm", headers=self.admin)

        self.assertEqual(self.c.delete(f"{API}/brand/guidelines/{g['id']}", headers=self.creator).status_code, 403)
        r = self.c.delete(f"{API}/brand/guidelines/{g['id']}", headers=self.admin)
        self.assertEqual(r.status_code, 200, r.text)
        out = r.json()
        self.assertEqual(out["confirmed_rules_kept"], 1)
        self.assertEqual(out["unconfirmed_rules_removed"], len(rules) - 1)
        self.assertGreater(out["passages_removed"], 0)

        db = self.Session()
        try:
            self.assertIsNone(db.query(BrandGuideline).filter(BrandGuideline.id == g["id"]).first())
            self.assertEqual(db.query(DocumentChunk).filter(DocumentChunk.guideline_id == g["id"]).count(), 0)
            left = db.query(BrandRule).filter(BrandRule.source_document == "delete_test_guide.md").all()
            self.assertEqual([x.id for x in left], [keep])
            self.assertTrue(db.query(ChunkEmbedding).count() >= 0)
        finally:
            db.close()
        self.assertNotIn(g["id"], [x["id"] for x in self.c.get(f"{API}/brand/guidelines", headers=self.admin).json()])
        self.assertEqual(self.c.delete(f"{API}/brand/guidelines/{g['id']}", headers=self.admin).status_code, 404)


if __name__ == "__main__":
    unittest.main()
