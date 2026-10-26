import asyncio
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx


TEST_DB = Path(__file__).resolve().parents[1] / "batch-a-test.db"
TEST_DB.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{TEST_DB.as_posix()}"
os.environ["JWT_SECRET"] = "batch-a-test-secret"
os.environ["MOOD_ANALYZER"] = "mock"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.config import settings  # noqa: E402
from app.db import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Admin, Track  # noqa: E402
from app.services.analyzer import runtime as analyzer_runtime  # noqa: E402
from app.services.analyzer.base import AnalysisResult  # noqa: E402
from app.services.analyzer.llm import AnalyzerFailure, LLMAnalyzer  # noqa: E402
from app.services.music.local import LocalProvider  # noqa: E402


class BatchATest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)
        engine.dispose()
        TEST_DB.unlink(missing_ok=True)

    def user_token(self):
        response = self.client.post(
            "/api/auth/login",
            json={"nickname": "测试用户"},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["token"]

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "UP")
        self.assertEqual(response.json()["analyzer"], "mock-fallback")

    def test_login_history_and_admin_error_message(self):
        token = self.user_token()
        history = self.client.get(
            "/api/capsules",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(history.status_code, 200)

        wrong = self.client.post(
            "/api/auth/admin-login",
            json={"username": "admin", "password": "wrong"},
        )
        missing = self.client.post(
            "/api/auth/admin-login",
            json={"username": "missing", "password": "wrong"},
        )
        self.assertEqual(wrong.status_code, 401)
        self.assertEqual(missing.status_code, 401)
        self.assertEqual(wrong.json()["detail"], "账号或密码错误")
        self.assertEqual(
            wrong.json()["detail"],
            missing.json()["detail"],
        )
        admin_login = self.client.post(
            "/api/auth/admin-login",
            json={"username": "admin", "password": "admin123"},
        )
        self.assertEqual(admin_login.status_code, 200)
        self.assertEqual(admin_login.json()["user"]["role"], "admin")

    def test_admin_password_is_hashed(self):
        with SessionLocal() as db:
            admin = db.scalar(select(Admin).where(Admin.username == "admin"))
            self.assertIsNotNone(admin)
            self.assertNotEqual(admin.password_hash, "admin123")
            self.assertTrue(admin.password_hash.startswith("$2"))

    def test_music_provider_adjacent_fallback_then_none(self):
        with SessionLocal() as db:
            melancholic = db.get(Track, "melancholic-1")
            anxious = db.get(Track, "anxious-1")
            db.delete(melancholic)
            db.flush()
            adjacent = asyncio.run(
                LocalProvider(db).pick("melancholic", "fallback-seed")
            )
            self.assertEqual(adjacent.quadrant, "anxious")

            db.delete(anxious)
            db.flush()
            missing = asyncio.run(
                LocalProvider(db).pick("melancholic", "fallback-seed")
            )
            self.assertIsNone(missing)
            db.rollback()

    def test_library_and_mock_analysis(self):
        library = self.client.get("/api/music/library")
        self.assertEqual(library.status_code, 200)
        self.assertEqual(set(library.json()), {"melancholic", "anxious", "joyful", "calm"})

        token = self.user_token()
        headers = {"Authorization": f"Bearer {token}"}
        first = self.client.post(
            "/api/capsules/analyze",
            json={"text": "今天面试被挂了，外面还在下雨，感觉好累"},
            headers=headers,
        )
        self.assertEqual(first.status_code, 200)
        capsule = first.json()
        self.assertEqual(capsule["valence"], -0.76)
        self.assertEqual(capsule["arousal"], 0.44)
        self.assertEqual(capsule["quadrant"], "melancholic")
        self.assertEqual(capsule["music"]["id"], "melancholic-1")
        self.assertRegex(capsule["createdAt"], r"\+08:00$")

        calm = self.client.post(
            "/api/capsules/analyze",
            json={"text": "今天晒了被子，很舒服"},
            headers=headers,
        ).json()
        self.assertEqual(calm["quadrant"], "calm")
        self.assertEqual(calm["music"]["id"], "calm-1")

        expected = (
            ("我终于拿到 offer 了，想大喊一声", 0.82, 0.7, "joyful"),
            ("一个人在外地，晚上有点想家", -0.39, 0.3, "melancholic"),
            ("明天要答辩，紧张到睡不着", -0.53, 0.65, "anxious"),
        )
        for text, valence, arousal, quadrant in expected:
            result = self.client.post(
                "/api/capsules/analyze",
                json={"text": text},
                headers=headers,
            ).json()
            self.assertEqual(result["valence"], valence)
            self.assertEqual(result["arousal"], arousal)
            self.assertEqual(result["quadrant"], quadrant)

        repeated = [
            self.client.post(
                "/api/capsules/analyze",
                json={"text": "今天面试被挂了，外面还在下雨，感觉好累"},
                headers=headers,
            ).json()["music"]["id"]
            for _ in range(3)
        ]
        self.assertEqual(repeated, ["melancholic-1"] * 3)

    @staticmethod
    def llm_payload():
        return {
            "emotions": {
                "喜悦": 20,
                "期待": 30,
                "平静": 70,
                "温暖": 60,
                "悲伤": 10,
                "焦虑": 5,
                "疲惫": 15,
                "孤独": 5,
            },
            "keywords": ["阳光", "安静", "松弛"],
            "fineLabels": ["松弛", "满足", "安心", "慢下来", "踏实"],
            "comment": "今天的光很柔和。让这一刻慢一点。",
        }

    def test_llm_analyzer_success_and_http_400_logging(self):
        async def success_handler(request):
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    self.llm_payload(),
                                    ensure_ascii=False,
                                )
                            }
                        }
                    ]
                },
            )

        analyzer = LLMAnalyzer(
            base_url="https://llm.test/v1",
            api_key="test-key",
            model="deepseek-flash",
            transport=httpx.MockTransport(success_handler),
        )
        result = asyncio.run(analyzer.analyze("今天晒了被子，很舒服"))
        self.assertEqual(result.fine_labels[0], "松弛")

        async def bad_model_handler(request):
            return httpx.Response(400, text="invalid model")

        failing = LLMAnalyzer(
            base_url="https://llm.test/v1",
            api_key="test-key",
            model="missing-model",
            transport=httpx.MockTransport(bad_model_handler),
        )
        with self.assertLogs(
            "app.services.analyzer.llm",
            level="WARNING",
        ) as captured:
            with self.assertRaises(AnalyzerFailure) as raised:
                asyncio.run(failing.analyze("测试"))
        self.assertEqual(raised.exception.reason, "http_400")
        self.assertIn("reason=http_400", "\n".join(captured.output))
        self.assertIn("duration_ms=", "\n".join(captured.output))

        async def bad_key_handler(request):
            return httpx.Response(401, text="invalid api key")

        unauthorized = LLMAnalyzer(
            base_url="https://llm.test/v1",
            api_key="bad-key",
            model="deepseek-flash",
            transport=httpx.MockTransport(bad_key_handler),
        )
        with self.assertRaises(AnalyzerFailure) as unauthorized_error:
            asyncio.run(unauthorized.analyze("测试"))
        self.assertEqual(unauthorized_error.exception.reason, "http_401")

    def test_llm_timeout_json_and_validation_reasons(self):
        async def timeout_handler(request):
            raise httpx.ReadTimeout("timeout", request=request)

        timeout_analyzer = LLMAnalyzer(
            base_url="https://llm.test/v1",
            api_key="test-key",
            model="deepseek-flash",
            transport=httpx.MockTransport(timeout_handler),
        )
        with self.assertRaises(AnalyzerFailure) as timeout_error:
            asyncio.run(timeout_analyzer.analyze("测试"))
        self.assertEqual(timeout_error.exception.reason, "timeout")

        async def json_handler(request):
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "not-json"}}]},
            )

        json_analyzer = LLMAnalyzer(
            base_url="https://llm.test/v1",
            api_key="test-key",
            model="deepseek-flash",
            transport=httpx.MockTransport(json_handler),
        )
        with self.assertRaises(AnalyzerFailure) as json_error:
            asyncio.run(json_analyzer.analyze("测试"))
        self.assertEqual(json_error.exception.reason, "json_parse")

        async def validation_handler(request):
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {"message": {"content": '{"emotions": {}}'}}
                    ]
                },
            )

        validation_analyzer = LLMAnalyzer(
            base_url="https://llm.test/v1",
            api_key="test-key",
            model="deepseek-flash",
            transport=httpx.MockTransport(validation_handler),
        )
        with self.assertRaises(AnalyzerFailure) as validation_error:
            asyncio.run(validation_analyzer.analyze("测试"))
        self.assertEqual(validation_error.exception.reason, "validation")

    def test_health_tracks_fallback_and_llm_recovery(self):
        original = (
            settings.mood_analyzer,
            settings.llm_api_key,
            settings.llm_base_url,
            settings.llm_model,
        )

        class FailingAnalyzer:
            async def analyze(_analyzer, _text):
                raise AnalyzerFailure("http_400", "invalid model")

        class WorkingAnalyzer:
            async def analyze(_analyzer, _text):
                return AnalysisResult(
                    emotions=self.llm_payload()["emotions"],
                    valence=0.5,
                    arousal=0.4,
                    keywords=["阳光", "安静", "松弛"],
                    fine_labels=["松弛", "满足", "安心", "慢下来", "踏实"],
                    comment="今天的光很柔和。让这一刻慢一点。",
                )

        try:
            settings.mood_analyzer = "llm"
            settings.llm_api_key = "test-key"
            settings.llm_base_url = "https://llm.test/v1"
            settings.llm_model = "missing-model"
            headers = {"Authorization": f"Bearer {self.user_token()}"}
            with patch(
                "app.services.analyzer.runtime.LLMAnalyzer",
                return_value=FailingAnalyzer(),
            ):
                with self.assertLogs(
                    "app.services.analyzer.runtime",
                    level="WARNING",
                ) as captured:
                    response = self.client.post(
                        "/api/capsules/analyze",
                        json={"text": "今天有点安静"},
                        headers=headers,
                    )
            self.assertEqual(response.status_code, 200)
            self.assertIn("reason=http_400", "\n".join(captured.output))
            self.assertEqual(
                self.client.get("/api/health").json()["analyzer"],
                "mock-fallback",
            )

            settings.llm_model = "deepseek-flash"
            with patch(
                "app.services.analyzer.runtime.LLMAnalyzer",
                return_value=WorkingAnalyzer(),
            ):
                response = self.client.post(
                    "/api/capsules/analyze",
                    json={"text": "今天有点安静"},
                    headers=headers,
                )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                self.client.get("/api/health").json()["analyzer"],
                "llm",
            )
        finally:
            (
                settings.mood_analyzer,
                settings.llm_api_key,
                settings.llm_base_url,
                settings.llm_model,
            ) = original
            analyzer_runtime.set_effective_analyzer("mock-fallback")


if __name__ == "__main__":
    unittest.main()
