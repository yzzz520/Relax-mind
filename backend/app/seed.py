import logging

from sqlalchemy import select

from .db import SessionLocal, init_db
from .deps import hash_password
from .models import Admin, Track


logger = logging.getLogger(__name__)

TRACKS = (
    {
        "id": "melancholic-1",
        "title": "melancholic-1",
        "artist": "待确认",
        "file_url": "/audio/melancholic-1.mp3",
        "quadrant": "melancholic",
    },
    {
        "id": "anxious-1",
        "title": "anxious-1",
        "artist": "待确认",
        "file_url": "/audio/anxious-1.mp3",
        "quadrant": "anxious",
    },
    {
        "id": "joyful-1",
        "title": "joyful-1",
        "artist": "待确认",
        "file_url": "/audio/joyful-1.mp3",
        "quadrant": "joyful",
    },
    {
        "id": "calm-1",
        "title": "calm-1",
        "artist": "待确认",
        "file_url": "/audio/calm-1.mp3",
        "quadrant": "calm",
    },
)


def seed_database() -> None:
    with SessionLocal() as db:
        admin = db.scalar(select(Admin).where(Admin.username == "admin"))
        if not admin:
            db.add(
                Admin(
                    username="admin",
                    password_hash=hash_password("admin123"),
                )
            )

        existing_tracks = set(db.scalars(select(Track.id)).all())
        for item in TRACKS:
            if item["id"] not in existing_tracks:
                db.add(
                    Track(
                        **item,
                        duration=None,
                        license="PLACEHOLDER",
                        source=None,
                    )
                )
        db.commit()
    logger.info("Database seed completed")


if __name__ == "__main__":
    init_db()
    seed_database()
