from pydantic import BaseModel, field_validator
import datetime
import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    """Self-service sign-up. New accounts are always provisioned as Creators —
    the least-privileged role that can submit content for review. Elevated
    roles (Reviewer / Administrator), which can authoritatively approve content,
    are granted by an administrator, never self-assigned at sign-up."""
    email: str
    password: str
    full_name: str

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
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
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
