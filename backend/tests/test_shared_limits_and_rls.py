"""Shared (database-backed) rate limiting and PostgreSQL Row-Level Security."""
import os
import unittest

from sqlalchemy import text

from backend.app.core.ratelimit import _SharedLimiter
from backend.app.db import rls
from backend.tests._util import drop_db, make_seeded_db

NOVA = "nova-tech-org-001"


class SharedRateLimitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.Session, cls.path = make_seeded_db()

    @classmethod
    def tearDownClass(cls):
        drop_db(cls.engine, cls.path)

    def test_two_instances_share_one_limit(self):
        """Two limiter objects stand in for two server processes using the same database."""
        a, b = _SharedLimiter(), _SharedLimiter()
        db1, db2 = self.Session(), self.Session()
        try:
            results = [(a if i % 2 else b).hit("login", "203.0.113.7", 5, 60.0, db=db1 if i % 2 else db2) for i in range(7)]
        finally:
            db1.close()
            db2.close()
        self.assertEqual(results[:5], [None] * 5)          # 5 allowed in total, not 5 each
        self.assertIsNotNone(results[5])
        self.assertIsNotNone(results[6])

    def test_clients_are_separate(self):
        lim = _SharedLimiter()
        db = self.Session()
        try:
            for _ in range(3):
                lim.hit("ai", "198.51.100.1", 3, 60.0, db=db)
            self.assertIsNotNone(lim.hit("ai", "198.51.100.1", 3, 60.0, db=db))
            self.assertIsNone(lim.hit("ai", "198.51.100.2", 3, 60.0, db=db))
        finally:
            db.close()

    def test_falls_back_to_memory_without_a_database(self):
        lim = _SharedLimiter()
        self.assertIsNone(lim.hit("x", "k", 1, 60.0, db=None))
        self.assertIsNotNone(lim.hit("x", "k", 1, 60.0, db=None))


@unittest.skipUnless(os.getenv("BV_TEST_DATABASE_URL", "").startswith("postgres"), "Row-Level Security needs PostgreSQL")
class RowLevelSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.Session, cls.path = make_seeded_db()
        from backend.app.models.brand import BrandRule, Organization
        db = cls.Session()
        db.add(Organization(id="rls-other-org", name="Other Org", slug="rls-other-org"))
        db.flush()
        db.add(BrandRule(id="rls-other-rule", org_id="rls-other-org", category="Tone & Voice", title="Other brand rule",
                         rule_text="Belongs to a different organisation.", severity="WARNING"))
        db.commit()
        db.close()
        with cls.engine.begin() as c:
            c.execute(text("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bv_rls_app') "
                           "THEN CREATE ROLE bv_rls_app NOSUPERUSER; END IF; END $$"))
            c.execute(text("GRANT USAGE ON SCHEMA public TO bv_rls_app"))
            c.execute(text("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO bv_rls_app"))

    @classmethod
    def tearDownClass(cls):
        drop_db(cls.engine, cls.path)

    def _count(self, conn, org):
        conn.execute(text("SELECT set_config('app.org_id', :o, true)"), {"o": org})
        return conn.execute(text("SELECT org_id, count(*) FROM brand_rules GROUP BY org_id")).all()

    def test_policies_hide_other_organisations(self):
        self.assertGreater(len(rls.tenant_tables(self.engine)), 20)
        with self.engine.connect() as c:
            c.execute(text("SET ROLE bv_rls_app"))  # an ordinary role, as in production
            everyone = dict(self._count(c, ""))
            self.assertGreaterEqual(len(everyone), 2)  # system context sees both demo brands
            only_nova = dict(self._count(c, NOVA))
            self.assertEqual(set(only_nova), {NOVA})
            other = next(o for o in everyone if o != NOVA)
            self.assertEqual(set(dict(self._count(c, other))), {other})
            # Writing a row for another organisation is refused by WITH CHECK.
            c.execute(text("SELECT set_config('app.org_id', :o, true)"), {"o": NOVA})
            with self.assertRaises(Exception):
                c.execute(text("INSERT INTO stored_files (id, org_id, folder, mime, size, sha256, data, created_at) "
                               "VALUES ('rls-x', :o, 'x', 'text/plain', 1, 'x', 'x', now())"), {"o": other})
            c.rollback()

    def test_session_keeps_tenant_across_transactions(self):
        db = self.Session()
        try:
            rls.set_tenant(db, NOVA)
            db.commit()  # next statement starts a new transaction on a pooled connection
            self.assertEqual(db.execute(text("SELECT current_setting('app.org_id', true)")).scalar(), NOVA)
        finally:
            db.close()
        fresh = self.Session()
        try:  # the setting never leaks to the next user of the connection
            self.assertIn(fresh.execute(text("SELECT current_setting('app.org_id', true)")).scalar(), (None, ""))
        finally:
            fresh.close()


if __name__ == "__main__":
    unittest.main()
