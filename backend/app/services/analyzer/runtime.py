import logging

from ...config import settings
from .base import AnalysisResult, MoodAnalyzer
from .llm import AnalyzerFailure, LLMAnalyzer
from .mock import MockAnalyzer


logger = logging.getLogger(__name__)
_effective_analyzer = "mock-fallback"


def _llm_configured() -> bool:
    return bool(
        settings.llm_base_url
        and settings.llm_api_key
        and settings.llm_model
    )


def set_effective_analyzer(name: str) -> None:
    global _effective_analyzer
    if name not in {"llm", "mock-fallback"}:
        raise ValueError(f"Unknown analyzer state: {name}")
    _effective_analyzer = name


def get_effective_analyzer() -> str:
    return _effective_analyzer


def initialize_analyzer_state() -> None:
    if settings.mood_analyzer.lower() == "llm" and _llm_configured():
        set_effective_analyzer("llm")
        logger.info(
            "Analyzer ready provider=llm model=%s base_url=%s",
            settings.llm_model,
            settings.llm_base_url,
        )
        return

    set_effective_analyzer("mock-fallback")
    if settings.mood_analyzer.lower() == "llm":
        logger.warning(
            "LLM analyzer unavailable provider=mock-fallback reason=config"
        )
    else:
        logger.info("Analyzer configured provider=mock")


async def analyze_with_fallback(text: str) -> tuple[AnalysisResult, MoodAnalyzer]:
    if settings.mood_analyzer.lower() != "llm":
        analyzer = MockAnalyzer()
        set_effective_analyzer("mock-fallback")
        return await analyzer.analyze(text), analyzer

    analyzer = LLMAnalyzer()
    try:
        result = await analyzer.analyze(text)
    except AnalyzerFailure as exc:
        logger.warning(
            "Analyzer fallback engaged provider=mock-fallback reason=%s",
            exc.reason,
        )
        fallback = MockAnalyzer()
        set_effective_analyzer("mock-fallback")
        return await fallback.analyze(text), fallback
    except Exception as exc:
        logger.warning(
            "Analyzer fallback engaged provider=mock-fallback "
            "reason=unknown detail=%s",
            str(exc),
        )
        fallback = MockAnalyzer()
        set_effective_analyzer("mock-fallback")
        return await fallback.analyze(text), fallback

    set_effective_analyzer("llm")
    return result, analyzer
