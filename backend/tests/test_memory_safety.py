"""Guards that keep a small (512 MB) server from running out of memory."""
import datetime
import io
import json
import unittest
from unittest import mock

from backend.app.services import ctwatch, ocr


class OcrStatusTests(unittest.TestCase):
    def test_status_does_not_load_the_engine(self):
        prev = (ocr._engine, ocr._load_error)
        ocr._engine, ocr._load_error = None, None
        try:
            with mock.patch.object(ocr, "_get_engine", side_effect=AssertionError("engine loaded")):
                s = ocr.status()
            self.assertIn("available", s)
            self.assertIs(ocr._engine, None)
        finally:
            ocr._engine, ocr._load_error = prev


class VisualDnaOcrTests(unittest.TestCase):
    def test_visual_dna_skips_ocr_unless_turned_on(self):
        from backend.app.core.config import settings
        from backend.app.services import visual
        prev = settings.VISUAL_DNA_OCR
        try:
            settings.VISUAL_DNA_OCR = False
            p = visual.get_ocr_provider()
            self.assertTrue(p.skipped)
            self.assertFalse(p.available)
            self.assertIsNone(p.extract_text(b"x"))  # never loads the engine
            self.assertIn("Creative Inspection", p.reason)
        finally:
            settings.VISUAL_DNA_OCR = prev

    def test_one_ocr_at_a_time(self):
        self.assertTrue(hasattr(ocr, "_run_lock"))

    def test_child_running_out_of_memory_is_a_clear_error(self):
        from concurrent.futures.process import BrokenProcessPool

        class Dead:
            def __init__(self, *a, **k):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def submit(self, *a, **k):
                raise BrokenProcessPool("killed")

        with mock.patch("concurrent.futures.ProcessPoolExecutor", Dead):
            with self.assertRaises(ocr.OCRUnavailable) as e:
                ocr._run_in_child(b"png")
        self.assertIn("more memory", str(e.exception))


class DomainWatchLimitsTests(unittest.TestCase):
    def _fake(self, body: bytes):
        class R(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False
        return mock.patch("urllib.request.urlopen", return_value=R(body))

    def test_huge_result_is_refused_not_loaded(self):
        with self._fake(b"[" + b" " * (ctwatch.MAX_BYTES + 10) + b"]"):
            with self.assertRaises(ctwatch.TooManyResults):
                ctwatch._fetch_crtsh("nova")

    def test_only_needed_fields_are_kept(self):
        rows = [{"id": 1, "name_value": "a.com", "issuer_name": "x", "not_before": "2026-01-01T00:00:00",
                 "serial_number": "z" * 500, "entry_timestamp": "t"}]
        with self._fake(json.dumps(rows).encode()):
            out = ctwatch._fetch_crtsh("nova")
        self.assertEqual(set(out[0]), {"id", "name_value", "issuer_name", "not_before"})

    def test_restarts_do_not_trigger_extra_searches(self):
        now = datetime.datetime(2026, 11, 11, 3, 0)
        self.assertEqual(ctwatch.seconds_until_due(None, now, 24), 900)  # first run: 15 min after start
        just_ran = ctwatch.seconds_until_due(now - datetime.timedelta(minutes=5), now, 24)
        self.assertGreater(just_ran, 23 * 3600)  # a restart right after a search waits a day
        self.assertEqual(ctwatch.seconds_until_due(now - datetime.timedelta(hours=30), now, 24), 900)


if __name__ == "__main__":
    unittest.main()
