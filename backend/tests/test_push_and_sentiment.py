"""Web Push (RFC 8291 encryption, VAPID, delivery rules) and model-assisted sentiment."""
import json
import unittest

from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.services import events, reputation
from backend.app.services import webpush as wp
from backend.main import app
from backend.tests._util import drop_db, make_seeded_db

API = "/api/v1"


class EncryptionTests(unittest.TestCase):
    def test_rfc8291_test_vector(self):
        """RFC 8291, Appendix A: same keys and salt must give the exact published message."""
        got = wp.encrypt(b"When I grow up, I want to be a watermelon",
                         "BCVxsr7N_eNgVRqvHtD0zTZsEc6-VV-JvLexhqUzORcxaOzi6-AYWXvTBHm4bjyPjs7Vd8pZGH6SRpkNtoIAiw4",
                         "BTBZMqHH6r4Tts7J_aSIgg", salt=wp.unb64u("DGv6ra1nlYgDCS1FRnbzlw"),
                         as_private=wp._private_from_raw(wp.unb64u("yfWPiYE-n46HLnH0KqZOF1fJJU3MYrct3AELtAQ-oRw")))
        self.assertEqual(wp.b64u(got),
                         "DGv6ra1nlYgDCS1FRnbzlwAAEABBBP4z9KsN6nGRTbVYI_c7VJSPQTBtkgcy27mlmlMoZIIgDll6e3vCYLocInmYWAmS6TlzAC8wEqKK6PBru3jl7A_"
                         "yl95bQpu6cVPTpK4Mqgkf1CXztLVBSt2Ks3oZwbuwXPXLWyouBWLVWGNWQexSgSxsj_Qulcy4a-fN")

    def test_vapid_header_verifies(self):
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
        key = ec.generate_private_key(ec.SECP256R1())
        h = wp.vapid_header(key, "https://fcm.googleapis.com/fcm/send/abc", "mailto:a@b.c")
        token = h.split("t=")[1].split(",")[0]
        head, claims, sig = token.split(".")
        self.assertEqual(json.loads(wp.unb64u(claims))["aud"], "https://fcm.googleapis.com")
        raw = wp.unb64u(sig)
        key.public_key().verify(encode_dss_signature(int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big")),
                                f"{head}.{claims}".encode(), ec.ECDSA(hashes.SHA256()))


class PushApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._prev = (settings.LLM_ENABLED, settings.RATE_LIMIT_ENABLED, events.SYNC, events.session_factory, events.push_poster)
        settings.LLM_ENABLED = False
        settings.RATE_LIMIT_ENABLED = False
        cls.engine, cls.Session, cls.path = make_seeded_db()
        events.SYNC, events.session_factory = True, cls.Session
        cls.sent = []
        events.push_poster = lambda url, body, headers: (cls.sent.append((url, headers)) or ((410, "gone") if "expired" in url else (201, "")))

        def _override():
            d = cls.Session()
            try:
                yield d
            finally:
                d.close()
        app.dependency_overrides[get_db] = _override
        cls.c = TestClient(app)
        tok = lambda e, p: {"Authorization": "Bearer " + cls.c.post(f"{API}/auth/login", json={"email": e, "password": p}).json()["access_token"]}
        cls.admin, cls.creator = tok("admin@novatech.demo", "Admin@2026"), tok("creator@novatech.demo", "Creator@2026")

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        drop_db(cls.engine, cls.path)
        settings.LLM_ENABLED, settings.RATE_LIMIT_ENABLED, events.SYNC, events.session_factory, events.push_poster = cls._prev

    def _sub(self, headers, endpoint):
        ua = ec.generate_private_key(ec.SECP256R1()).public_key()
        from cryptography.hazmat.primitives import serialization
        p256 = wp.b64u(ua.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint))
        r = self.c.post(f"{API}/push/subscribe", headers=headers, json={"endpoint": endpoint, "keys": {"p256dh": p256, "auth": wp.b64u(b"0123456789abcdef")}})
        self.assertEqual(r.status_code, 200, r.text)

    def test_subscribe_deliver_and_cleanup(self):
        key = self.c.get(f"{API}/push/public-key", headers=self.admin).json()["public_key"]
        self.assertEqual(len(wp.unb64u(key)), 65)  # uncompressed P-256 point
        self.assertEqual(self.c.get(f"{API}/push/public-key", headers=self.admin).json()["public_key"], key)  # stable
        self._sub(self.admin, "https://push.example.com/admin-device")
        self._sub(self.admin, "https://push.example.com/expired-device")
        self._sub(self.creator, "https://push.example.com/creator-device")
        self.assertEqual(self.c.post(f"{API}/push/subscribe", headers=self.admin,
                                     json={"endpoint": "http://insecure", "keys": {"p256dh": "x" * 30, "auth": "y" * 10}}).status_code, 400)
        self.sent.clear()
        db = self.Session()
        try:  # a reviewer/admin event: the creator's browser must not get it
            events.emit(db, "nova-tech-org-001", "analysis.completed", {}, title="Ready for review", body="Campaign X")
        finally:
            db.close()
        urls = [u for u, _ in self.sent]
        self.assertIn("https://push.example.com/admin-device", urls)
        self.assertNotIn("https://push.example.com/creator-device", urls)
        self.assertTrue(all(h["Content-Encoding"] == "aes128gcm" and h["Authorization"].startswith("vapid t=") for _, h in self.sent))
        # 410 Gone removed the expired subscription
        self.sent.clear()
        r = self.c.post(f"{API}/push/test", headers=self.admin).json()
        self.assertEqual(r["devices"], 1)
        self.assertEqual(r["sent"], 1)

    def test_test_push_needs_a_subscription(self):
        reviewer = {"Authorization": "Bearer " + self.c.post(f"{API}/auth/login", json={"email": "reviewer@novatech.demo", "password": "Reviewer@2026"}).json()["access_token"]}
        self.assertEqual(self.c.post(f"{API}/push/test", headers=reviewer).status_code, 400)


class SentimentBatchTests(unittest.TestCase):
    class Fake:
        available, name, model = True, "fake", "fake"

        def __init__(self, reply):
            self.reply = reply

        def analyze(self, system, user):
            return self.reply

    def test_model_labels_used_and_fallback(self):
        out = reputation.score_batch(["great", "awful", "a question?"], self.Fake('["positive", "negative", "neutral"]'))
        self.assertEqual([o[0] for o in out], ["positive", "negative", "neutral"])
        self.assertEqual({o[2] for o in out}, {"llm"})
        bad = reputation.score_batch(["I love it", "It arrived broken"], self.Fake("not json"))  # model failed -> lexicon
        self.assertEqual([o[2] for o in bad], ["lexicon", "lexicon"])
        self.assertEqual([o[0] for o in bad], ["positive", "negative"])

    def test_contrast_and_phrases(self):
        self.assertEqual(reputation.score_sentiment("Good screen but the battery is terrible.", None)[0], "negative")
        self.assertEqual(reputation.score_sentiment("Couldn't be happier with this purchase.", None)[0], "positive")
        self.assertEqual(reputation.score_sentiment("Mixed feelings: battery is good, screen is average.", None)[0], "neutral")


if __name__ == "__main__":
    unittest.main()
