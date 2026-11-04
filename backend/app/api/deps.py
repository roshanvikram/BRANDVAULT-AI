"""Authentication / RBAC dependencies."""
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import decode_token
from backend.app.db.session import get_db
from backend.app.models.user import User


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail,
                         headers={"WWW-Authenticate": "Bearer"})


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the bearer token to an active User, or raise 401."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _unauthorized("Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_token(token, settings.SECRET_KEY)
    if not payload or "sub" not in payload:
        raise _unauthorized("Invalid or expired token")
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or not user.is_active:
        raise _unauthorized("User not found or inactive")
    return user


def require_roles(*roles: str):
    """Dependency factory: require the current user to hold one of `roles`."""
    allowed = set(roles)

    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' is not permitted this action (requires: {', '.join(sorted(allowed))}).",
            )
        return user

    return _checker


def ensure_same_org(user: User, resource_org_id: str) -> None:
    """Tenant isolation: block cross-organisation access."""
    if user.org_id != resource_org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-organisation access is not permitted.",
        )
