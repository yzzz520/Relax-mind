from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AnalysisResult:
    emotions: dict[str, int]
    valence: float
    arousal: float
    keywords: list[str]
    fine_labels: list[str]
    comment: str


class MoodAnalyzer(Protocol):
    async def analyze(self, text: str) -> AnalysisResult: ...
