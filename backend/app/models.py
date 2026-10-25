from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


CHINA_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")


def now_shanghai() -> datetime:
    return datetime.now(CHINA_TZ)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nickname: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(16), default="user")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_shanghai,
    )
    capsules: Mapped[list["Capsule"]] = relationship(back_populates="user")


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_shanghai,
    )


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(160))
    artist: Mapped[str] = mapped_column(String(160), default="待确认")
    file_url: Mapped[str] = mapped_column(String(255))
    quadrant: Mapped[str] = mapped_column(String(24), index=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    license: Mapped[str] = mapped_column(String(32), default="PLACEHOLDER")
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_shanghai,
    )


class Capsule(Base):
    __tablename__ = "capsules"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    input_text: Mapped[str] = mapped_column(Text)
    emotions: Mapped[dict[str, Any]] = mapped_column(JSON)
    valence: Mapped[float] = mapped_column(Float)
    arousal: Mapped[float] = mapped_column(Float)
    keywords: Mapped[list[str]] = mapped_column(JSON)
    fine_labels: Mapped[list[str]] = mapped_column(JSON)
    track_id: Mapped[str | None] = mapped_column(
        ForeignKey("tracks.id"),
        nullable=True,
    )
    comment: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_shanghai,
        index=True,
    )

    user: Mapped[User] = relationship(back_populates="capsules")
    track: Mapped[Track | None] = relationship()
