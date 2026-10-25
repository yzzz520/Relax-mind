from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import create_access_token, hash_password, verify_password
from ..models import Admin, User
from ..schemas import (
    AdminLoginRequest,
    AuthResponse,
    AuthUser,
    LoginRequest,
)


router = APIRouter(prefix="/api/auth", tags=["auth"])
INVALID_ADMIN_CREDENTIALS = "账号或密码错误"


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Log in by nickname, creating the user on first use."""
    nickname = payload.nickname.strip()
    if len(nickname) < 2:
        raise HTTPException(status_code=422, detail="昵称至少需要 2 个字")

    user = db.scalar(select(User).where(User.nickname == nickname))
    if not user:
        user = User(nickname=nickname, role="user")
        db.add(user)
        db.commit()
        db.refresh(user)

    return AuthResponse(
        token=create_access_token(user.id, "user"),
        user=AuthUser(id=user.id, nickname=user.nickname, role="user"),
    )


@router.post("/admin-login", response_model=AuthResponse)
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    """Authenticate an administrator with username and password."""
    admin = db.scalar(select(Admin).where(Admin.username == payload.username))
    if not admin or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_ADMIN_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthResponse(
        token=create_access_token(admin.id, "admin"),
        user=AuthUser(id=admin.id, nickname=admin.username, role="admin"),
    )
