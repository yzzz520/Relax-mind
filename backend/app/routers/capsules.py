import secrets
import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..config import settings
from ..models import Capsule, Track, User
from ..schemas import (
    AnalyzeRequest,
    CapsuleListResponse,
    CapsuleOut,
    MusicOut,
)
from ..services.analyzer import get_analyzer
from ..services.music import get_music_provider
from ..services.vad import quadrant_of


router = APIRouter(prefix="/api/capsules", tags=["capsules"])
CHINA_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")


def track_to_music(track: Track | None) -> MusicOut | None:
    if not track:
        return None
    return MusicOut(
        id=track.id,
        title=track.title,
        artist=track.artist,
        file=track.file_url,
        quadrant=track.quadrant,
    )


def capsule_to_out(capsule: Capsule) -> CapsuleOut:
    created_at = capsule.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=CHINA_TZ)
    else:
        created_at = created_at.astimezone(CHINA_TZ)
    return CapsuleOut(
        capsuleId=capsule.id,
        createdAt=created_at,
        input=capsule.input_text,
        emotions=capsule.emotions,
        valence=capsule.valence,
        arousal=capsule.arousal,
        keywords=capsule.keywords,
        fineLabels=capsule.fine_labels,
        quadrant=capsule.track.quadrant if capsule.track else quadrant_of(
            capsule.valence,
            capsule.arousal,
        ),
        music=track_to_music(capsule.track),
        comment=capsule.comment,
    )


@router.post(
    "/analyze",
    response_model=CapsuleOut,
    summary="Analyze mood with the selected provider",
)
async def analyze_capsule(
    payload: AnalyzeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Analyze input text, pick a stable track, and persist the capsule."""
    analyzer = get_analyzer(settings.mood_analyzer)
    analysis = await analyzer.analyze(payload.text)
    quadrant = quadrant_of(analysis.valence, analysis.arousal)
    provider = get_music_provider(settings.music_provider, db)
    track = await provider.pick(quadrant, payload.text)
    created_at = datetime.now(CHINA_TZ)
    capsule_id = (
        f"cap_{int(time.time() * 1000)}_"
        f"{secrets.token_hex(2)}"
    )

    capsule = Capsule(
        id=capsule_id,
        user_id=user.id,
        input_text=payload.text,
        emotions=analysis.emotions,
        valence=analysis.valence,
        arousal=analysis.arousal,
        keywords=analysis.keywords,
        fine_labels=analysis.fine_labels,
        track_id=track.id if track else None,
        comment=analysis.comment,
        created_at=created_at,
    )
    db.add(capsule)
    db.commit()
    db.refresh(capsule)
    capsule.track = track
    return capsule_to_out(capsule)


@router.get("", response_model=CapsuleListResponse)
def list_capsules(
    limit: int = Query(50, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return the current user's capsule history, newest first."""
    base_query = select(Capsule).where(Capsule.user_id == user.id)
    total = db.scalar(
        select(func.count()).select_from(base_query.subquery())
    ) or 0
    capsules = db.scalars(
        base_query.order_by(Capsule.created_at.desc()).offset(offset).limit(limit)
    ).all()
    return CapsuleListResponse(
        items=[capsule_to_out(item) for item in capsules],
        total=total,
        limit=limit,
        offset=offset,
    )
