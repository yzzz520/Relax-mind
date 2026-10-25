from .base import MoodAnalyzer
from .mock import MockAnalyzer


def get_analyzer(name: str) -> MoodAnalyzer:
    if name.lower() == "mock":
        return MockAnalyzer()
    raise ValueError(f"Unsupported MOOD_ANALYZER: {name}")
