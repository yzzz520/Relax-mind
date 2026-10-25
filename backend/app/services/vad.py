from collections.abc import Mapping


VALENCE_POSITIVE = {"喜悦": 1.0, "期待": 0.6, "平静": 0.3, "温暖": 0.7}
VALENCE_NEGATIVE = {"悲伤": 1.0, "焦虑": 0.7, "疲惫": 0.5, "孤独": 0.6}
AROUSAL_ACTIVE = {"焦虑": 1.0, "喜悦": 0.8, "期待": 0.6}
AROUSAL_CALM = {
    "平静": 0.8,
    "疲惫": 0.4,
    "孤独": 0.4,
    "悲伤": 0.3,
    "温暖": 0.3,
}


def _weighted(emotions: Mapping[str, int], weights: Mapping[str, float]) -> float:
    return sum(emotions.get(dimension, 0) * weight for dimension, weight in weights.items())


def compute_vad(emotions: Mapping[str, int]) -> tuple[float, float]:
    """Mirror the frontend symmetric normalization formula."""
    positive = _weighted(emotions, VALENCE_POSITIVE)
    negative = _weighted(emotions, VALENCE_NEGATIVE)
    active = _weighted(emotions, AROUSAL_ACTIVE)
    calm = _weighted(emotions, AROUSAL_CALM)
    valence_total = positive + negative
    arousal_total = active + calm
    valence = 0.0 if valence_total == 0 else round(
        (positive - negative) / valence_total,
        2,
    )
    arousal = 0.5 if arousal_total == 0 else round(
        ((active - calm) / arousal_total + 1) / 2,
        2,
    )
    return valence, arousal


def quadrant_of(valence: float, arousal: float) -> str:
    if valence < 0 and arousal < 0.5:
        return "melancholic"
    if valence < 0:
        return "anxious"
    if arousal < 0.5:
        return "calm"
    return "joyful"
