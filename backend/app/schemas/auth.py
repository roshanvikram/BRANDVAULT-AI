from typing import Literal, Optional

from pydantic import BaseModel, field_validator
import datetime
import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LoginRequest(BaseModel):
    email: str
    password: str
    mfa_code: Optional[str] = None  # required only when the account has two-step sign-in on


class RegisterRequest(BaseModel):
    """Self-service sign-up. New accounts are always provisioned as Creators —
    the least-privileged role that can submit content for review. Elevated
    roles (Reviewer / Administrator), which can authoritatively approve content,
    are granted by an administrator, never self-assigned at sign-up."""
    email: str
    password: str
    full_name: str
    # "new": create a company workspace (you become its Administrator).
    # "demo": join the shared NOVA TECH demo workspace as a Creator.
    # Omitted: the server default (demo while demo content is on, otherwise new).
    workspace: Optional[Literal["new", "demo"]] = None
    company_name: Optional[str] = None
    invite_token: Optional[str] = None  # joins the inviting workspace with the invited role

    @field_validator("email")
    @classmethod
    def _email_shape(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("Enter a valid email address.")
        return v

    @field_validator("password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        from backend.app.core.config import settings
        from backend.app.core.security import password_problem
        problem = password_problem(v, "", settings.PASSWORD_MIN_LENGTH)
        if problem:
            raise ValueError(problem)
        return v

    @field_validator("full_name")
    @classmethod
    def _name_present(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Full name is required.")
        return v.strip()


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    org_id: str
    auth_provider: str = "password"
    mfa_enabled: Optional[bool] = False
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class GoogleStatusResponse(BaseModel):
    """Lets the frontend honestly enable/disable the Google button."""
    configured: bool
