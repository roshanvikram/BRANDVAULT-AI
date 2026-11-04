"""F — Visual DNA tests. Builds BMP images in pure Python (no imaging deps) to
verify deterministic colour metrics, persisted findings, and the unsupported-
format path.
"""
import struct
import unittest

from fastapi.testclient import TestClient

from backend.main import app
from backend.app.db.session import get_db
from backend.app.services import visual
from backend.app.services.analyzer import ContentAnalyzerService  # noqa: F401 (import sanity)
from backend.app.services.seed import NOVA_ORG_ID
from backend.tests._util import make_seeded_db, drop_db


def make_bmp(rows):
    """rows: top-to-bottom list of rows, each a list of (r,g,b). Returns 24-bit BMP bytes."""
    h = len(rows)
    w = len(rows[0])
    row_size = ((24 * w + 31) // 32) * 4
    pad = row_size - w * 3
    pixel_data = bytearray()
    for y in range(h - 1, -1, -1):  # BMP is bottom-up
        for (r, g, b) in rows[y]:
            pixel_data += bytes((b, g, r))
        pixel_data += b"\x00" * pad
    dib = struct.pack("<IiiHHIIiiII", 40, w, h, 1, 24, 0, len(pixel_data), 2835, 2835, 0, 0)
    header = b"BM" + struct.pack("<IHHI", 54 + len(pixel_data), 0, 0, 54)
    return header + dib + bytes(pixel_data)


def solid(w, h, color):
    return [[color] * w for _ in range(h)]


def checker_bw(w, h):
    return [[(0, 0, 0) if (x + y) % 2 else (255, 255, 255) for x in range(w)] for y in range(h)]


class TestVisualDecodeMetrics(unittest.TestCase):
    def test_bmp_decode(self):
        img = visual.decode_image(make_bmp(solid(8, 8, (10, 20, 30))))
        self.assertIsNotNone(img)
        self.assertEqual(img["format"], "bmp")
        self.assertEqual((img["width"], img["height"]), (8, 8))

    def test_monochrome_metrics(self):
        m = visual.compute_metrics(visual.decode_image(make_bmp(checker_bw(16, 16)))["pixels"])
        self.assertLess(m["chromatic_fraction"], 0.05)   # black/white = not chromatic
        self.assertGreater(m["contrast"], 0.8)           # strong luminance spread

    def test_colourful_metrics(self):
        m = visual.compute_metrics(visual.decode_image(make_bmp(solid(16, 16, (220, 20, 20))))["pixels"])
        self.assertGreater(m["chromatic_fraction"], 0.9)  # saturated red

    def test_unsupported_format_returns_none(self):
        self.assertIsNone(visual.decode_image(b"\xff\xd8\xff\xe0 jpeg-ish bytes"))

    def test_ocr_is_unavailable_not_faked(self):
        ocr = visual.get_ocr_provider()
        self.assertFalse(ocr.available)
        self.assertIsNone(ocr.extract_text(b"anything"))


class TestVisualApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.Session, cls.path = make_seeded_db()

        def _override():
            d = cls.Session()
            try:
                yield d
            finally:
                d.close()

        app.dependency_overrides[get_db] = _override
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        drop_db(cls.engine, cls.path)

    def test_colourful_image_flags_visual_finding(self):
        bmp = make_bmp(solid(16, 16, (220, 20, 20)))
        r = self.client.post("/api/v1/visual/analyze",
                             data={"org_id": NOVA_ORG_ID},
                             files={"file": ("ad.bmp", bmp, "image/bmp")})
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertGreater(body["metrics"]["chromatic_fraction"], 0.9)
        cats = [f["issue_category"] for f in body["submission"]["findings"]]
        self.assertIn("Visual", cats)
        self.assertFalse(body["ocr"]["available"])  # honest: OCR not faked

    def test_monochrome_image_no_visual_finding(self):
        bmp = make_bmp(checker_bw(16, 16))
        r = self.client.post("/api/v1/visual/analyze",
                             data={"org_id": NOVA_ORG_ID},
                             files={"file": ("logo.bmp", bmp, "image/bmp")})
        self.assertEqual(r.status_code, 200, r.text)
        cats = [f["issue_category"] for f in r.json()["submission"]["findings"]]
        self.assertNotIn("Visual", cats)

    def test_unsupported_format_415(self):
        r = self.client.post("/api/v1/visual/analyze",
                             data={"org_id": NOVA_ORG_ID},
                             files={"file": ("photo.jpg", b"\xff\xd8\xff\xe0jpeg", "image/jpeg")})
        self.assertEqual(r.status_code, 415)


if __name__ == "__main__":
    unittest.main()
