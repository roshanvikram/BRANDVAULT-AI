"""A seeded, in-process BrandVault API client for checking the input library."""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient  # noqa: E402

from backend.app.core.config import settings  # noqa: E402
from backend.app.db.session import get_db  # noqa: E402
from backend.app.services import events  # noqa: E402
from backend.app.services.demo_content import seed_demo_campaigns  # noqa: E402
from backend.main import app  # noqa: E402
from backend.tests._util import drop_db, make_seeded_db  # noqa: E402

API = "/api/v1"
INPUTS = os.path.join(ROOT, "inputs")


class Client:
    def __enter__(self):
        settings.LLM_ENABLED = False
        settings.RATE_LIMIT_ENABLED = False
        self.engine, self.Session, self.path = make_seeded_db()
        events.SYNC, events.session_factory = True, self.Session
        events.sender = lambda url, body, headers: (200, "ok")
        db = self.Session()
        seed_demo_campaigns(db)
        db.commit()
        db.close()

        def _override():
            d = self.Session()
            try:
                yield d
            finally:
                d.close()

        app.dependency_overrides[get_db] = _override
        self.c = TestClient(app)
        tok = lambda e, p: {"Authorization": "Bearer " + self.c.post(f"{API}/auth/login", json={"email": e, "password": p}).json()["access_token"]}
        self.admin = tok("admin@novatech.demo", "Admin@2026")
        self.reviewer = tok("reviewer@novatech.demo", "Reviewer@2026")
        return self

    def __exit__(self, *a):
        app.dependency_overrides.clear()
        drop_db(self.engine, self.path)

    def post(self, path, **kw):
        kw.setdefault("headers", self.admin)
        return self.c.post(API + path, **kw)

    def get(self, path, **kw):
        kw.setdefault("headers", self.admin)
        return self.c.get(API + path, **kw)


def read(folder, name, mode="r"):
    with open(os.path.join(INPUTS, folder, name), mode, **({} if "b" in mode else {"encoding": "utf-8"})) as fh:
        return fh.read()


def manifest(folder):
    import csv
    with open(os.path.join(INPUTS, folder, "manifest.csv"), encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))
