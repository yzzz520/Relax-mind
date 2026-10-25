import os
import unittest
from pathlib import Path
import asyncio


TEST_DB = Path(__file__).resolve().parents[1] / "batch-a-test.db"
TEST_DB.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{TEST_DB.as_posix()}"
os.environ["JWT_SECRET"] = "batch-a-test-secret"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.db import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Admin, Track  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
