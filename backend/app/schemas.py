from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str
    version: str
    analyzer: Literal["llm", "mock-fallback"]


class LoginRequest(BaseModel):
    nickname: str = Field(min_length=2, max_length=80)


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=128)


class AuthUser(BaseModel):
    id: int
    nickname: str
    role: Literal["user", "admin"]


class AuthResponse(BaseModel):
    token: str
    user: AuthUser


class TrackOut(BaseModel):
    id: str
    title: str
    artist: str
    file: str
    quadrant: str


class MusicOut(TrackOut):
    pass


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=4, max_length=200)


class CapsuleOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    capsule_id: str = Field(alias="capsuleId")
    created_at: datetime = Field(alias="createdAt")
    input: str
    emotions: dict[str, int]
    valence: float
    arousal: float
    keywords: list[str]
    fine_labels: list[str] = Field(alias="fineLabels")
    quadrant: str
    music: MusicOut | None
    comment: str


class CapsuleListResponse(BaseModel):
    items: list[CapsuleOut]
    total: int
    limit: int
    offset: int
