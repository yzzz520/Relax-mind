import json
import logging
import re
import time
from dataclasses import dataclass

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from ...config import settings
from ..vad import compute_vad
from .base import AnalysisResult


logger = logging.getLogger(__name__)
RETRYABLE_REASONS = {"json_parse", "validation"}
EMOTION_KEYS = {"喜悦", "期待", "平静", "温暖", "悲伤", "焦虑", "疲惫", "孤独"}


@dataclass
class AnalyzerFailure(Exception):
    reason: str
    detail: str = ""

    def __str__(self) -> str:
        return self.reason if not self.detail else f"{self.reason}: {self.detail}"


class LLMAnalysisPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    emotions: dict[str, int]
    keywords: list[str] = Field(min_length=3, max_length=5)
    fine_labels: list[str] = Field(
        alias="fineLabels",
        min_length=5,
        max_length=8,
    )
    comment: str = Field(min_length=2)

    @field_validator("emotions")
    @classmethod
    def validate_emotions(cls, value: dict[str, int]) -> dict[str, int]:
        if set(value) != EMOTION_KEYS:
            raise ValueError("emotions must contain the fixed eight dimensions")
        if any(not 0 <= score <= 100 for score in value.values()):
            raise ValueError("emotion scores must be between 0 and 100")
        return value


SYSTEM_PROMPT = """你是情绪分析器。只返回一个 JSON 对象，不要 Markdown 代码块，不要额外说明。
JSON 必须严格使用以下结构：
{
  "emotions": {
    "喜悦": 0-100 的整数,
    "期待": 0-100 的整数,
    "平静": 0-100 的整数,
    "温暖": 0-100 的整数,
    "悲伤": 0-100 的整数,
    "焦虑": 0-100 的整数,
    "疲惫": 0-100 的整数,
    "孤独": 0-100 的整数
  },
  "keywords": ["3-5 个原文关键词"],
  "fineLabels": ["5-8 个情绪状态词"],
  "comment": "2-3 句自然、克制、具体的中文疗愈语"
}
emotions 必须且只能包含以上八个键。"""


class LLMAnalyzer:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.api_key = api_key or settings.llm_api_key
        self.model = model or settings.llm_model
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.llm_timeout_seconds
        )
        self.transport = transport

    async def _request(self, text: str) -> str | dict:
        if not self.base_url or not self.api_key or not self.model:
            raise AnalyzerFailure("config", "missing base URL, API key, or model")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
        except httpx.TimeoutException as exc:
            raise AnalyzerFailure("timeout", str(exc)) from exc
        except httpx.RequestError as exc:
            raise AnalyzerFailure("network", str(exc)) from exc

        if response.status_code >= 400:
            raise AnalyzerFailure(
                f"http_{response.status_code}",
                response.text[:300],
            )

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise AnalyzerFailure("json_parse", str(exc)) from exc
        return content

    @staticmethod
    def _parse_payload(content: str | dict) -> LLMAnalysisPayload:
        if isinstance(content, dict):
            data = content
        else:
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip())
            try:
                data = json.loads(cleaned)
            except json.JSONDecodeError as exc:
                raise AnalyzerFailure("json_parse", str(exc)) from exc
        try:
            return LLMAnalysisPayload.model_validate(data)
        except ValidationError as exc:
            raise AnalyzerFailure("validation", str(exc)) from exc

    async def analyze(self, text: str) -> AnalysisResult:
        for attempt in (1, 2):
            started = time.perf_counter()
            try:
                content = await self._request(text)
                payload = self._parse_payload(content)
            except AnalyzerFailure as exc:
                elapsed_ms = (time.perf_counter() - started) * 1000
                logger.warning(
                    "LLM call failed provider=llm model=%s attempt=%d "
                    "duration_ms=%.2f reason=%s detail=%s",
                    self.model,
                    attempt,
                    elapsed_ms,
                    exc.reason,
                    exc.detail,
                )
                if exc.reason in RETRYABLE_REASONS and attempt == 1:
                    continue
                raise

            elapsed_ms = (time.perf_counter() - started) * 1000
            valence, arousal = compute_vad(payload.emotions)
            logger.info(
                "LLM call succeeded provider=llm model=%s attempt=%d "
                "duration_ms=%.2f",
                self.model,
                attempt,
                elapsed_ms,
            )
            return AnalysisResult(
                emotions=dict(payload.emotions),
                valence=valence,
                arousal=arousal,
                keywords=list(payload.keywords),
                fine_labels=list(payload.fine_labels),
                comment=payload.comment,
            )

        raise AnalyzerFailure("unknown", "LLM analyzer exhausted retries")
