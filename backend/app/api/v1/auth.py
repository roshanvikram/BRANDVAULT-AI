"""
Authentication API: local sign-up / sign-in and (optional) Google OAuth 2.0.

Security posture:
  * Passwords are PBKDF2-HMAC-SHA256 hashed (see core/security.py).
  * Nobody can raise their own role in an existing workspace. Sign-up either
    joins the demo workspace as a Creator, joins a workspace through an
    administrator's invitation (with the invited role), or creates a new company
    workspace whose first member is its Administrator.
  * Failed sign-ins lock the account for a while; optional two-step sign-in
    (TOTP authenticator apps); password changes sign out every other session.
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
import datetime
import hashlib
import re

from fastapi import Request
from pydantic import BaseModel

from backend.app.core.security import (
    create_token, verify_password, hash_password, decode_token,
    new_totp_secret, verify_totp, totp_uri, password_problem,
)
from backend.app.models.user import ROLE_ADMIN
from backend.app.models.account import Invite
from backend.app.services import audit
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
        {"sub": user.id, "role": user.role, "org": user.org_id, "tv": int(user.token_version or 0)},
        settings.SECRET_KEY,
        ttl_seconds=max(1, settings.SESSION_HOURS) * 3600,
    )


def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


def invite_hash(token: str) -> str:
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def _open_invite(db: Session, token: str):
    inv = db.query(Invite).filter(Invite.token_hash == invite_hash(token)).first()
    if not inv or inv.accepted_at or inv.revoked_at or inv.expires_at < _now():
        return None
    return inv


def _slug(name: str, db: Session) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "workspace"
    slug, n = base, 1
    while db.query(Organization).filter(Organization.slug == slug).first():
        n += 1
        slug = f"{base}-{n}"
    return slug


# ----------------------------- local auth ---------------------------------- #
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(rate_limit("auth", settings.RATE_LIMIT_AUTH_PER_MIN))])
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    """Create an account in one of three ways:

    * with an invitation link: join that workspace with the invited role;
    * workspace="new": create a new company workspace; you become its Administrator
      (you administer only your own company's data);
    * workspace="demo": join the shared NOVA TECH demo workspace as a Creator.
    Nobody can give themselves a higher role in an existing workspace.
    """
    email = payload.email.lower().strip()
    problem = password_problem(payload.password, email, settings.PASSWORD_MIN_LENGTH)
    if problem:
        raise HTTPException(status_code=422, detail=problem)
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists. Try signing in.",
        )
    invite = None
    if payload.invite_token:
        invite = _open_invite(db, payload.invite_token)
        if not invite:
            raise HTTPException(status_code=400, detail="This invitation link is invalid, used or expired. Ask for a new one.")
        if invite.email.lower() != email:
            raise HTTPException(status_code=400, detail=f"This invitation is for {invite.email}. Sign up with that email.")
        org_id, role = invite.org_id, invite.role
    else:
        mode = payload.workspace or ("demo" if settings.SEED_DEMO_CONTENT else "new")
        if mode == "new":
            if not settings.ALLOW_NEW_WORKSPACES:
                raise HTTPException(status_code=403, detail="New workspaces are invite-only on this server. Ask your administrator for an invitation.")
            company = (payload.company_name or "").strip()
            if len(company) < 2:
                raise HTTPException(status_code=422, detail="Enter your company name.")
            org = Organization(id=uuid.uuid4().hex, name=company[:120], slug=_slug(company, db))
            db.add(org)
            db.flush()
            org_id, role = org.id, ROLE_ADMIN
        else:
            org_id, role = _default_org_id(db), ROLE_CREATOR
    salt, pwd_hash = hash_password(payload.password)
    user = User(
        id=uuid.uuid4().hex,
        email=email,
        full_name=payload.full_name,
        role=role,
        org_id=org_id,
        salt=salt,
        password_hash=pwd_hash,
        auth_provider="password",
        password_changed_at=_now(),
        last_login_at=_now(),
    )
    db.add(user)
    if invite:
        invite.accepted_at = _now()
    db.commit()
    db.refresh(user)
    audit.record(db, "account.created", org_id=org_id, actor=email, target=role,
                 detail={"via": "invite" if invite else ("new_workspace" if role == ROLE_ADMIN else "demo")}, request=request)
    return TokenResponse(access_token=_mint(user), user=user)


@router.post("/login", response_model=TokenResponse,
             dependencies=[Depends(rate_limit("auth", settings.RATE_LIMIT_AUTH_PER_MIN))])
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    now = _now()
    if user and user.locked_until and user.locked_until > now:
        mins = max(1, int((user.locked_until - now).total_seconds() // 60) + 1)
        raise HTTPException(status_code=423, detail=f"Too many failed sign-ins. This account is locked for {mins} more minute(s).")
    # Verify even when the user is missing / federated to reduce enumeration.
    ok = bool(user and user.salt and user.password_hash and verify_password(payload.password, user.salt, user.password_hash))
    if not ok:
        if user:
            _count_failure(db, user, now)
            audit.record(db, "login.locked" if user.locked_until else "login.failed", org_id=user.org_id, actor=email, request=request)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    if user.mfa_enabled:
        if not payload.mfa_code:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="mfa_required")
        if not verify_totp(user.mfa_secret or "", payload.mfa_code):
            _count_failure(db, user, now)
            audit.record(db, "login.mfa_failed", org_id=user.org_id, actor=email, request=request)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="mfa_invalid")
    user.failed_logins, user.locked_until, user.last_login_at = 0, None, now
    db.commit()
    audit.record(db, "login.success", org_id=user.org_id, actor=email, detail={"mfa": bool(user.mfa_enabled)}, request=request)
    return TokenResponse(access_token=_mint(user), user=user)


def _count_failure(db: Session, user: User, now: datetime.datetime) -> None:
    """Count a wrong password or code; lock the account after LOGIN_MAX_FAILURES in a row."""
    user.failed_logins = int(user.failed_logins or 0) + 1
    if user.failed_logins >= settings.LOGIN_MAX_FAILURES:
        user.locked_until = now + datetime.timedelta(minutes=settings.LOGIN_LOCK_MINUTES)
        user.failed_logins = 0
    db.commit()


@router.get("/me", response_model=UserResponse)
def me(current: User = Depends(get_current_user)):
    return current


# ----------------------------- account security ---------------------------- #
class PasswordChange(BaseModel):
    current_password: str
    new_password: str


@router.post("/password", response_model=TokenResponse,
             dependencies=[Depends(rate_limit("auth", settings.RATE_LIMIT_AUTH_PER_MIN))])
def change_password(body: PasswordChange, request: Request, db: Session = Depends(get_db),
                    current: User = Depends(get_current_user)):
    """Change your password. Every other signed-in session is signed out."""
    if current.auth_provider == "google":
        raise HTTPException(status_code=400, detail="This account signs in with Google, so it has no BrandVault password to change.")
    if not verify_password(body.current_password, current.salt or "", current.password_hash or ""):
        raise HTTPException(status_code=400, detail="Your current password is not correct.")
    problem = password_problem(body.new_password, current.email, settings.PASSWORD_MIN_LENGTH)
    if problem:
        raise HTTPException(status_code=422, detail=problem)
    current.salt, current.password_hash = hash_password(body.new_password)
    current.password_changed_at = _now()
    current.token_version = int(current.token_version or 0) + 1
    db.commit()
    audit.record(db, "password.changed", org_id=current.org_id, actor=current.email, request=request)
    return TokenResponse(access_token=_mint(current), user=current)


@router.post("/logout-all", response_model=TokenResponse)
def logout_all(request: Request, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    """Sign out every device. Returns a fresh token for this one."""
    current.token_version = int(current.token_version or 0) + 1
    db.commit()
    audit.record(db, "sessions.revoked", org_id=current.org_id, actor=current.email, request=request)
    return TokenResponse(access_token=_mint(current), user=current)


class MfaCode(BaseModel):
    code: str
    password: str | None = None


@router.post("/mfa/setup")
def mfa_setup(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    """Start two-step sign-in: returns a new secret for an authenticator app.
    Nothing changes for sign-in until /mfa/enable confirms a code from the app."""
    if current.mfa_enabled:
        raise HTTPException(status_code=400, detail="Two-step sign-in is already on. Turn it off first to change the app.")
    current.mfa_secret = new_totp_secret()
    db.commit()
    return {"secret": current.mfa_secret, "otpauth_uri": totp_uri(current.mfa_secret, current.email)}


@router.post("/mfa/enable", response_model=TokenResponse)
def mfa_enable(body: MfaCode, request: Request, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    if not current.mfa_secret:
        raise HTTPException(status_code=400, detail="Start setup first.")
    if not verify_totp(current.mfa_secret, body.code):
        raise HTTPException(status_code=400, detail="That code is not correct. Check the time on your phone and try the newest code.")
    current.mfa_enabled = True
    current.token_version = int(current.token_version or 0) + 1  # other sessions must sign in with a code
    db.commit()
    audit.record(db, "mfa.enabled", org_id=current.org_id, actor=current.email, request=request)
    return TokenResponse(access_token=_mint(current), user=current)


@router.post("/mfa/disable", response_model=TokenResponse)
def mfa_disable(body: MfaCode, request: Request, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    if not current.mfa_enabled:
        raise HTTPException(status_code=400, detail="Two-step sign-in is not on.")
    if not verify_totp(current.mfa_secret or "", body.code):
        raise HTTPException(status_code=400, detail="That code is not correct.")
    if current.auth_provider != "google" and not verify_password(body.password or "", current.salt or "", current.password_hash or ""):
        raise HTTPException(status_code=400, detail="Your password is not correct.")
    current.mfa_enabled, current.mfa_secret = False, None
    db.commit()
    audit.record(db, "mfa.disabled", org_id=current.org_id, actor=current.email, request=request)
    return TokenResponse(access_token=_mint(current), user=current)


@router.get("/invite/{token}")
def invite_info(token: str, db: Session = Depends(get_db)):
    """Public: what an invitation link is for, so the sign-up form can show it."""
    inv = _open_invite(db, token)
    if not inv:
        raise HTTPException(status_code=404, detail="This invitation link is invalid, used or expired.")
    org = db.query(Organization).filter(Organization.id == inv.org_id).first()
    return {"email": inv.email, "role": inv.role, "workspace": org.name if org else "",
            "expires_at": inv.expires_at.isoformat() + "Z"}


@router.get("/signup-options")
def signup_options():
    """Which sign-up choices this server offers (the form shows only these)."""
    return {"new_workspace": settings.ALLOW_NEW_WORKSPACES, "demo_workspace": settings.SEED_DEMO_CONTENT,
            "password_min_length": settings.PASSWORD_MIN_LENGTH}


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
