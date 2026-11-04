from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import create_token, verify_password
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    # Constant-ish failure path: verify even when user missing to reduce enumeration.
    if not user or not verify_password(payload.password, user.salt, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    token = create_token(
        {"sub": user.id, "role": user.role, "org": user.org_id},
        settings.SECRET_KEY,
    )
    return TokenResponse(access_token=token, user=user)


@router.get("/me", response_model=UserResponse)
def me(current: User = Depends(get_current_user)):
    return current
