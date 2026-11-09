"""Round 3 foundation: durable file storage, portable migrations, demo-account switch."""
import os
import tempfile
import unittest

from sqlalchemy import create_engine, inspect, text

from backend.app.db import migrations
from backend.app.models.user import User
from backend.app.services import filestore
from backend.app.services.seed import DEMO_USERS, NOVA_ORG_ID, VORTEXA_DEMO_USERS, apply_demo_account_policy
from backend.tests._util import drop_db, make_seeded_db


class FileStoreTests(unittest.TestCase):
    def setUp(self):
        self.engine, self.Session, self.path = make_seeded_db()
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        drop_db(self.engine, self.path)

    def test_round_trip_is_stored_in_the_database(self):
        data = b"\x89PNG\r\n\x1a\n" + os.urandom(2048)
        ref = filestore.put(self.db, NOVA_ORG_ID, "assets", data, "image/png")
        self.db.commit()
        self.assertTrue(ref.startswith("db://"))
        self.assertEqual(filestore.read(self.db, ref, NOVA_ORG_ID), data)

    def test_other_organisations_cannot_read_it(self):
        ref = filestore.put(self.db, NOVA_ORG_ID, "assets", b"secret-bytes", "image/png")
        self.db.commit()
        with self.assertRaises(OSError):
            filestore.read(self.db, ref, "vortexa-tech-org-002")

    def test_legacy_disk_paths_still_readable_and_missing_files_raise(self):
        fd, legacy = tempfile.mkstemp()
        os.write(fd, b"old-file")
        os.close(fd)
        try:
            self.assertEqual(filestore.read(self.db, legacy), b"old-file")
        finally:
            os.remove(legacy)
        with self.assertRaises(OSError):
            filestore.read(self.db, legacy)
        with self.assertRaises(OSError):
            filestore.read(self.db, "db://does-not-exist")


class DemoAccountPolicyTests(unittest.TestCase):
    def setUp(self):
        self.engine, self.Session, self.path = make_seeded_db()
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        drop_db(self.engine, self.path)

    def test_disable_and_re_enable(self):
        nova = [u["email"] for u in DEMO_USERS]
        self.assertGreater(apply_demo_account_policy(self.db, False), 0)
        users = self.db.query(User).filter(User.email.in_(nova)).all()
        self.assertTrue(users and all(not u.is_active for u in users))
        self.assertEqual(apply_demo_account_policy(self.db, False), 0)  # idempotent
        apply_demo_account_policy(self.db, True)
        self.assertTrue(all(u.is_active for u in self.db.query(User).filter(User.email.in_(nova)).all()))
        self.assertTrue(VORTEXA_DEMO_USERS)


class MigrationTests(unittest.TestCase):
    def test_adds_missing_columns_without_touching_data(self):
        path = os.path.join(tempfile.gettempdir(), "bv_mig_test.db")
        if os.path.exists(path):
            os.remove(path)
        engine = create_engine(f"sqlite:///{path}")
        try:
            with engine.begin() as conn:
                conn.execute(text("CREATE TABLE submissions (id VARCHAR(36) PRIMARY KEY, title TEXT)"))
                conn.execute(text("INSERT INTO submissions VALUES ('s1', 'kept')"))
            applied = migrations.run_light_migrations(engine)
            self.assertIn("submissions.department", applied)
            self.assertIn("department", {c["name"] for c in inspect(engine).get_columns("submissions")})
            with engine.connect() as conn:
                self.assertEqual(conn.execute(text("SELECT title FROM submissions")).scalar(), "kept")
            self.assertEqual(migrations.run_light_migrations(engine), [])  # idempotent
        finally:
            engine.dispose()
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
