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


# ----------------------------- two-step sign-in (TOTP) ---------------------- #
def new_totp_secret() -> str:
    """Random 160-bit secret, base32 (what authenticator apps expect)."""
    return base64.b32encode(os.urandom(20)).decode("ascii").rstrip("=")


def totp_code(secret: str, at: Optional[float] = None, step: int = 30, digits: int = 6) -> str:
    """RFC 6238 time-based one-time password (HMAC-SHA1, 30 s, 6 digits)."""
    key = base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)
    counter = int((time.time() if at is None else at) // step)
    mac = hmac.new(key, counter.to_bytes(8, "big"), hashlib.sha1).digest()
    off = mac[-1] & 0x0F
    num = (int.from_bytes(mac[off:off + 4], "big") & 0x7FFFFFFF) % (10 ** digits)
    return str(num).zfill(digits)


def verify_totp(secret: str, code: str, window: int = 1, at: Optional[float] = None) -> bool:
    """Accept the current code and one step either side (clock drift)."""
    code = (code or "").replace(" ", "").strip()
    if not secret or not code.isdigit() or len(code) != 6:
        return False
    now = time.time() if at is None else at
    return any(hmac.compare_digest(totp_code(secret, now + k * 30), code) for k in range(-window, window + 1))


def totp_uri(secret: str, email: str, issuer: str = "BrandVault AI") -> str:
    import urllib.parse
    label = urllib.parse.quote(f"{issuer}:{email}")
    return f"otpauth://totp/{label}?secret={secret}&issuer={urllib.parse.quote(issuer)}&algorithm=SHA1&digits=6&period=30"


# ----------------------------- password rules ------------------------------- #
_COMMON = {"password", "password1", "password123", "123456789", "1234567890", "qwerty123", "letmein",
           "welcome1", "admin123", "iloveyou", "brandvault", "changeme"}


def password_problem(password: str, email: str = "", min_length: int = 10) -> Optional[str]:
    """Return why a password is too weak, or None when it is acceptable."""
    p = password or ""
    if len(p) < min_length:
        return f"Password must be at least {min_length} characters."
    if len(p) > 256:
        return "Password is too long."
    if not any(c.isalpha() for c in p) or not any(c.isdigit() for c in p):
        return "Use both letters and numbers in the password."
    low = p.lower()
    if low in _COMMON or low.rstrip("!@#$%") in _COMMON:
        return "That password is too common. Choose another."
    local = (email or "").split("@")[0].lower()
    if local and len(local) >= 4 and local in low:
        return "The password must not contain your email name."
    return None
