from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import Admin, User


ALGORITHM = "HS256"
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@dataclass
class Principal:
    subject_id: int
    role: str


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_access_token(subject_id: int, role: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expire_minutes
    )
    payload = {"sub": str(subject_id), "role": role, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def get_current_principal(
    token: str = Depends(oauth2_scheme),
) -> Principal:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="登录已失效，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        subject = int(payload.get("sub", ""))
        role = str(payload.get("role", ""))
    except (JWTError, TypeError, ValueError):
        raise unauthorized

    if role not in {"user", "admin"}:
        raise unauthorized
    return Principal(subject_id=subject, role=role)


def get_current_user(
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> User:
    if principal.role != "user":
        raise HTTPException(status_code=403, detail="仅普通用户可访问")
    user = db.scalar(select(User).where(User.id == principal.subject_id))
    if not user:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    return user


def require_admin(
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> Admin:
    if principal.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    admin = db.scalar(select(Admin).where(Admin.id == principal.subject_id))
    if not admin:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    return admin
