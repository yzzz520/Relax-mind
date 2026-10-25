from typing import Protocol

from ...models import Track


class MusicProvider(Protocol):
    async def pick(self, quadrant: str, seed: str) -> Track | None: ...
