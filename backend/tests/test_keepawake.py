"""Keep-awake scheduling for free hosting, and the storage flag in /capabilities."""
import datetime
import os
import unittest
from unittest import mock

from backend.app.services import keepawake as ka

IST = ka.IST


class KeepAwakeTests(unittest.TestCase):
    def test_window_in_ist(self):
        at = lambda h, m: datetime.datetime(2026, 11, 10, h, m, tzinfo=IST)
        with mock.patch.dict(os.environ, {"KEEP_AWAKE_WINDOW": "09:00-20:30"}):
            self.assertTrue(ka.in_window(at(9, 0)))
            self.assertTrue(ka.in_window(at(20, 30)))
            self.assertFalse(ka.in_window(at(8, 59)))
            self.assertFalse(ka.in_window(at(23, 0)))
            # 03:30 UTC is 09:00 IST
            self.assertTrue(ka.in_window(datetime.datetime(2026, 11, 10, 3, 30, tzinfo=datetime.timezone.utc)))

    def test_targets_from_render_and_cors(self):
        env = {"RENDER_EXTERNAL_URL": "https://api.example.onrender.com", "KEEP_AWAKE_URLS": ""}
        with mock.patch.dict(os.environ, env):
            t = ka.targets(["http://localhost:3000", "https://web.example.onrender.com"])
        self.assertEqual(t, ["https://api.example.onrender.com/api/v1/health", "https://web.example.onrender.com/"])

    def test_off_outside_render(self):
        with mock.patch.dict(os.environ, {"RENDER": "", "KEEP_AWAKE_URLS": ""}):
            self.assertFalse(ka.enabled())
        with mock.patch.dict(os.environ, {"RENDER": "true", "KEEP_AWAKE": "off"}):
            self.assertFalse(ka.enabled())
        with mock.patch.dict(os.environ, {"RENDER": "true", "KEEP_AWAKE": ""}):
            self.assertTrue(ka.enabled())


class StorageFlagTests(unittest.TestCase):
    def test_sqlite_on_render_is_temporary(self):
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.app.db.session import get_db
        from backend.main import app
        # Never touch the developer's real database (it may be Neon/PostgreSQL).
        Session = sessionmaker(bind=create_engine("sqlite://"))

        def _db():
            d = Session()
            try:
                yield d
            finally:
                d.close()
        app.dependency_overrides[get_db] = _db
        try:
            c = TestClient(app)
            with mock.patch.dict(os.environ, {"RENDER": "true", "STORAGE_PERSISTENT": ""}):
                j = c.get("/api/v1/capabilities").json()
            self.assertEqual(j["database"], "sqlite")
            self.assertFalse(j["persistent_storage"])
            with mock.patch.dict(os.environ, {"RENDER": ""}):
                self.assertTrue(c.get("/api/v1/capabilities").json()["persistent_storage"])
        finally:
            app.dependency_overrides.pop(get_db, None)


if __name__ == "__main__":
    unittest.main()
