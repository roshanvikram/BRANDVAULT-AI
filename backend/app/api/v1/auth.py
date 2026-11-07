"""
Authentication API: local sign-up / sign-in and (optional) Google OAuth 2.0.

Security posture:
  * Passwords are PBKDF2-HMAC-SHA256 hashed (see core/security.py).
  * Self-service sign-up ALWAYS provisions the least-privileged role (Creator).
    Reviewer / Administrator — the roles that can authoritatively approve content
    — are never self-assignable; an admin grants them. This preserves the
    human-in-the-loop guarantee (no account can elevate itself to approver).
  * Google OAuth is a real server-side authorization-code exchange. It is only
    active when GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET are configured; the
    client secret never reaches the browser. When unconfigured the endpoints
    return 503 and the frontend keeps the button disabled.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import create_token, verify_password, hash_password, decode_token
from backend.app.db.session import get_db
from backend.app.models.user import User, ROLE_CREATOR
from backend.app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    GoogleStatusResponse,
)
from backend.app.api.deps import get_current_user
from backend.app.core.ratelimit import rate_limit
from backend.app.services.seed import NOVA_ORG_ID
from backend.app.models.brand import Organization

router = APIRouter(prefix="/auth", tags=["Authentication"])

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def _default_org_id(db: Session) -> str:
    """Workspace that new self-service accounts join. Defaults to the seeded
    NOVA TECH demo org so a fresh account can actually use the product."""
    org = db.query(Organization).filter(Organization.id == NOVA_ORG_ID).first()
    if org:
        return org.id
    first = db.query(Organization).first()
    if not first:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No workspace is provisioned yet. Contact an administrator.",
        )
    return first.id


def _mint(user: User) -> str:
    return create_token(
        {"sub": user.id, "role": user.role, "org": user.org_id},
        settings.SECRET_KEY,
    )


# ----------------------------- local auth ---------------------------------- #
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(rate_limit("auth", settings.RATE_LIMIT_AUTH_PER_MIN))])
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists. Try signing in.",
        )
    salt, pwd_hash = hash_password(payload.password)
    user = User(
        id=uuid.uuid4().hex,
        email=email,
        full_name=payload.full_name,
        role=ROLE_CREATOR,  # never self-assignable beyond Creator
        org_id=_default_org_id(db),
        salt=salt,
        password_hash=pwd_hash,
        auth_provider="password",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=_mint(user), user=user)


@router.post("/login", response_model=TokenResponse,
             dependencies=[Depends(rate_limit("auth", settings.RATE_LIMIT_AUTH_PER_MIN))])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    # Verify even when the user is missing / federated to reduce enumeration.
    if not user or not user.salt or not user.password_hash or not verify_password(
        payload.password, user.salt, user.password_hash
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    return TokenResponse(access_token=_mint(user), user=user)


@router.get("/me", response_model=UserResponse)
def me(current: User = Depends(get_current_user)):
    return current


# ----------------------------- google oauth -------------------------------- #
@router.get("/google/status", response_model=GoogleStatusResponse)
def google_status():
    """Reports whether Google sign-in is configured so the UI can honestly
    enable or disable the button (no fake affordance)."""
    return GoogleStatusResponse(configured=settings.GOOGLE_OAUTH_CONFIGURED)


def _require_google_configured() -> None:
    if not settings.GOOGLE_OAUTH_CONFIGURED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured on this server "
                   "(set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET).",
        )


@router.get("/google/login")
def google_login():
    """Begin the OAuth authorization-code flow: redirect the browser to Google's
    consent screen. `state` is an HMAC-signed nonce (our SECRET_KEY) verified on
    callback to defend against CSRF."""
    _require_google_configured()
    state = create_token({"nonce": os.urandom(8).hex(), "purpose": "google_oauth"},
                         settings.SECRET_KEY, ttl_seconds=600)
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return RedirectResponse(f"{_GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}")


def _frontend_redirect(fragment: str) -> RedirectResponse:
    # Token / error travel in the URL *fragment* (never sent to a server, kept
    # out of logs) — the SPA reads it from window.location.hash.
    return RedirectResponse(f"{settings.FRONTEND_URL}/login#{fragment}")


def _http_post_form(url: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_get_json(url: str, bearer: str) -> dict:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {bearer}"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


@router.get("/google/callback")
def google_callback(db: Session = Depends(get_db), code: str | None = None, state: str | None = None):
    """Google redirects here with an authorization `code`. We exchange it for
    tokens server-side, read the verified profile, find-or-create the user, mint
    our own bearer token and bounce back to the SPA with it in the URL fragment."""
    _require_google_configured()
    if not code:
        return _frontend_redirect("error=google_no_code")
    if not state or not decode_token(state, settings.SECRET_KEY):
        return _frontend_redirect("error=google_bad_state")

    try:
        tokens = _http_post_form(_GOOGLE_TOKEN_URL, {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        })
        access_token = tokens.get("access_token")
        if not access_token:
            return _frontend_redirect("error=google_token_exchange")
        info = _http_get_json(_GOOGLE_USERINFO_URL, access_token)
    except Exception:
        return _frontend_redirect("error=google_unreachable")

    sub = info.get("sub")
    email = (info.get("email") or "").lower().strip()
    if not sub or not email:
        return _frontend_redirect("error=google_profile")
    if info.get("email_verified") is False:
        return _frontend_redirect("error=google_unverified_email")

    name = info.get("name") or email.split("@")[0]

    user = db.query(User).filter(User.google_sub == sub).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()
    if user:
        # Link an existing local account to Google on first federated sign-in.
        if not user.google_sub:
            user.google_sub = sub
            if user.auth_provider == "password" and not user.password_hash:
                user.auth_provider = "google"
            db.commit()
    else:
        # Federated-only account: no usable local password (store unusable values).
        salt, pwd_hash = hash_password(os.urandom(24).hex())
        user = User(
            id=uuid.uuid4().hex,
            email=email,
            full_name=name,
            role=ROLE_CREATOR,
            org_id=_default_org_id(db),
            salt=salt,
            password_hash=pwd_hash,
            auth_provider="google",
            google_sub=sub,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if not user.is_active:
        return _frontend_redirect("error=account_disabled")
    return _frontend_redirect(f"token={_mint(user)}")
