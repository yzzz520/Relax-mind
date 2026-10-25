import struct

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import Track


ADJACENT_QUADRANT = {
    "melancholic": "anxious",
    "anxious": "melancholic",
    "calm": "joyful",
    "joyful": "calm",
}


def stable_hash(value: str) -> int:
    """Match JavaScript charCodeAt-based hashing, including UTF-16 units."""
    encoded = value.encode("utf-16-le")
    result = 0
    for index in range(0, len(encoded), 2):
        unit = struct.unpack_from("<H", encoded, index)[0]
        result = (result * 31 + unit) & 0xFFFFFFFF
    return result


class LocalProvider:
    def __init__(self, db: Session):
        self.db = db

    def _tracks(self, quadrant: str) -> list[Track]:
        return list(
            self.db.scalars(
                select(Track).where(Track.quadrant == quadrant).order_by(Track.id)
            ).all()
        )

    async def pick(self, quadrant: str, seed: str) -> Track | None:
        tracks = self._tracks(quadrant)
        if not tracks:
            adjacent = ADJACENT_QUADRANT.get(quadrant)
            tracks = self._tracks(adjacent) if adjacent else []
        if not tracks:
            return None
        return tracks[stable_hash(seed) % len(tracks)]
