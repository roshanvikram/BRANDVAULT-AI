"""
Authentication primitives for BRANDVAULT AI (Milestone D).

Dependency-free and offline: PBKDF2-HMAC-SHA256 password hashing and
HMAC-SHA256-signed bearer tokens (a compact JWT-style token) using the app
SECRET_KEY. This is real, verifiable auth — constant-time comparisons, per-user
salt, token expiry — implemented with the standard library rather than pulling
in PyJWT/passlib (not installable in this offline environment). For production
these map cleanly onto PyJWT + argon2/bcrypt without changing callers.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional, Tuple

_PBKDF2_ROUNDS = 200_000


# ----------------------------- passwords ----------------------------------- #
def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Return (salt_hex, hash_hex). Generates a random salt if none supplied."""
    salt = salt or os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), _PBKDF2_ROUNDS)
    return salt, dk.hex()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    try:
        _, got = hash_password(password, salt)
    except Exception:
        return False
    return hmac.compare_digest(got, expected_hash)


# ----------------------------- tokens --------------------------------------- #
def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _sign(body_b64: str, secret: str) -> str:
    sig = hmac.new(secret.encode("utf-8"), body_b64.encode("ascii"), hashlib.sha256).digest()
    return _b64url_encode(sig)


def create_token(payload: dict, secret: str, ttl_seconds: int = 86_400) -> str:
    body = dict(payload)
    body["iat"] = int(time.time())
    body["exp"] = int(time.time()) + ttl_seconds
    body_b64 = _b64url_encode(json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    return f"{body_b64}.{_sign(body_b64, secret)}"


def decode_token(token: str, secret: str) -> Optional[dict]:
    """Return the payload if the signature is valid and not expired, else None."""
    if not token or token.count(".") != 1:
        return None
    body_b64, sig = token.split(".", 1)
    expected = _sign(body_b64, secret)
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        payload = json.loads(_b64url_decode(body_b64))
    except Exception:
        return None
    if int(payload.get("exp", 0)) < int(time.time()):
        return None
    return payload
