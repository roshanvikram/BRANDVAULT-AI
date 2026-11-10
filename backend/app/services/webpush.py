"""Standard Web Push (works in Chrome, Edge, Firefox and Safari 16.4+).

Implements what browsers require, with the `cryptography` library only:
  * VAPID (RFC 8292): a P-256 key pair identifies this server to the browser's
    push service; each request carries a short-lived ES256 JWT.
  * Message encryption (RFC 8291 + RFC 8188, "aes128gcm"): the payload is
    encrypted for the subscriber's browser key, so the push service cannot read it.

The VAPID key comes from VAPID_PRIVATE_KEY (base64url, 32 bytes) or is generated
once and stored in the database. Notifications reach a browser even when the
BrandVault tab is closed, once the user has turned them on.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import time
from typing import Optional, Tuple
from urllib.parse import urlparse

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF, HKDFExpand
from sqlalchemy.orm import Session

log = logging.getLogger("brandvault.webpush")


def b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def unb64u(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _raw_public(pub: ec.EllipticCurvePublicKey) -> bytes:
    return pub.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)


def _private_from_raw(raw: bytes) -> ec.EllipticCurvePrivateKey:
    return ec.derive_private_key(int.from_bytes(raw, "big"), ec.SECP256R1())


# ------------------------------------------------------------------ VAPID ----
def vapid_key(db: Session) -> ec.EllipticCurvePrivateKey:
    env = os.getenv("VAPID_PRIVATE_KEY", "").strip()
    if env:
        return _private_from_raw(unb64u(env))
    from backend.app.models.push import ServerSetting
    row = db.get(ServerSetting, "vapid_private_key")
    if row is None:
        key = ec.generate_private_key(ec.SECP256R1())
        raw = key.private_numbers().private_value.to_bytes(32, "big")
        row = ServerSetting(key="vapid_private_key", value=b64u(raw))
        db.add(row)
        db.commit()
    return _private_from_raw(unb64u(row.value))


def public_key(db: Session) -> str:
    """The applicationServerKey browsers subscribe with (base64url, uncompressed point)."""
    return b64u(_raw_public(vapid_key(db).public_key()))


def vapid_header(key: ec.EllipticCurvePrivateKey, endpoint: str, subject: str) -> str:
    u = urlparse(endpoint)
    header = b64u(json.dumps({"typ": "JWT", "alg": "ES256"}, separators=(",", ":")).encode())
    claims = b64u(json.dumps({"aud": f"{u.scheme}://{u.netloc}", "exp": int(time.time()) + 12 * 3600, "sub": subject},
                             separators=(",", ":")).encode())
    signing_input = f"{header}.{claims}".encode()
    r, s = decode_dss_signature(key.sign(signing_input, ec.ECDSA(hashes.SHA256())))
    sig = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    return f"vapid t={header}.{claims}.{b64u(sig)}, k={b64u(_raw_public(key.public_key()))}"


# ------------------------------------------------------------- encryption ----
def _hkdf(salt: bytes, ikm: bytes, info: bytes, length: int) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=length, salt=salt, info=info).derive(ikm)


def encrypt(payload: bytes, ua_public_b64: str, auth_b64: str, *, salt: Optional[bytes] = None,
            as_private: Optional[ec.EllipticCurvePrivateKey] = None, record_size: int = 4096) -> bytes:
    """RFC 8291 aes128gcm body for one subscriber. `salt`/`as_private` are fixed only in tests."""
    ua_public = unb64u(ua_public_b64)
    auth = unb64u(auth_b64)
    as_private = as_private or ec.generate_private_key(ec.SECP256R1())
    as_public = _raw_public(as_private.public_key())
    salt = salt or os.urandom(16)
    ua_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), ua_public)
    ecdh = as_private.exchange(ec.ECDH(), ua_key)
    ikm = _hkdf(auth, ecdh, b"WebPush: info\x00" + ua_public + as_public, 32)
    cek = _hkdf(salt, ikm, b"Content-Encoding: aes128gcm\x00", 16)
    nonce = _hkdf(salt, ikm, b"Content-Encoding: nonce\x00", 12)
    ciphertext = AESGCM(cek).encrypt(nonce, payload + b"\x02", None)  # single, final record
    header = salt + record_size.to_bytes(4, "big") + bytes([len(as_public)]) + as_public
    return header + ciphertext


# ------------------------------------------------------------------- send ----
def send(db: Session, sub, payload: dict, poster=None) -> Tuple[int, str]:
    """Send one notification. Returns (HTTP status, text). 404/410 mean the subscription is gone."""
    body = encrypt(json.dumps(payload).encode(), sub.p256dh, sub.auth)
    subject = os.getenv("VAPID_SUBJECT", "mailto:admin@brandvault.invalid")
    headers = {"TTL": "86400", "Urgency": "normal", "Content-Encoding": "aes128gcm",
               "Content-Type": "application/octet-stream",
               "Authorization": vapid_header(vapid_key(db), sub.endpoint, subject)}
    if poster is None:
        import httpx
        r = httpx.post(sub.endpoint, content=body, headers=headers, timeout=8.0)
        return r.status_code, r.text[:200]
    return poster(sub.endpoint, body, headers)
