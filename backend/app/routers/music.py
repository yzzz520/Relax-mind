from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Track
from ..schemas import TrackOut


router = APIRouter(prefix="/api/music", tags=["music"])
QUADRANTS = ("melancholic", "anxious", "joyful", "calm")


def track_to_out(track: Track) -> TrackOut:
    return TrackOut(
        id=track.id,
        title=track.title,
        artist=track.artist,
        file=track.file_url,
        quadrant=track.quadrant,
    )


@router.get("/library", response_model=dict[str, list[TrackOut]])
def music_library(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Return the local music library grouped by emotion quadrant."""
    tracks = db.scalars(
        select(Track).order_by(Track.id).offset(offset).limit(limit)
    ).all()
    library = {quadrant: [] for quadrant in QUADRANTS}
    for track in tracks:
        library.setdefault(track.quadrant, []).append(track_to_out(track))
    return library
