from sqlalchemy.orm import Session

from .base import MusicProvider
from .local import LocalProvider


def get_music_provider(name: str, db: Session) -> MusicProvider:
    if name.lower() == "local":
        return LocalProvider(db)
    raise ValueError(f"Unsupported MUSIC_PROVIDER: {name}")
