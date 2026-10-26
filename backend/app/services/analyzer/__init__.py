from .base import MoodAnalyzer
from .llm import LLMAnalyzer
from .mock import MockAnalyzer


def get_analyzer(name: str) -> MoodAnalyzer:
    if name.lower() == "mock":
        return MockAnalyzer()
    if name.lower() == "llm":
        return LLMAnalyzer()
    raise ValueError(f"Unsupported MOOD_ANALYZER: {name}")
