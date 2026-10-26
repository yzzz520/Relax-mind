import asyncio
import json
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

from jose import JWTError, jwt


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.services.analyzer.runtime import analyze_with_fallback  # noqa: E402
from backend.app.services.vad import quadrant_of  # noqa: E402


logger = logging.getLogger(__name__)
API_VERSION = "0.1.0"


class AuthConfigurationError(RuntimeError):
    pass


def verify_supabase_token(authorization: str | None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise JWTError("missing bearer token")

    secret = os.getenv("SUPABASE_JWT_SECRET", "")
    if not secret:
        raise AuthConfigurationError("SUPABASE_JWT_SECRET is not configured")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise JWTError("empty bearer token")

    claims = jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        audience="authenticated",
    )
    if not claims.get("sub"):
        raise JWTError("token subject is missing")
    return claims


def analyze_request(authorization: str | None, raw_body: bytes) -> tuple[int, dict]:
    try:
        verify_supabase_token(authorization)
    except AuthConfigurationError:
        logger.error("Supabase JWT secret is not configured")
        return 500, {"detail": "服务配置不完整"}
    except JWTError:
        return 401, {"detail": "未登录或登录已过期"}

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return 422, {"detail": "请求参数不合法"}

    text = str(payload.get("text", "")).strip() if isinstance(payload, dict) else ""
    if not 4 <= len(text) <= 200:
        return 422, {"detail": "请求参数不合法"}

    try:
        analysis, _ = asyncio.run(analyze_with_fallback(text))
    except Exception:
        logger.exception("Analyze function failed")
        return 500, {"detail": "分析失败，请稍后重试"}

    return 200, {
        "emotions": analysis.emotions,
        "valence": analysis.valence,
        "arousal": analysis.arousal,
        "keywords": analysis.keywords,
        "fineLabels": analysis.fine_labels,
        "comment": analysis.comment,
        "quadrant": quadrant_of(analysis.valence, analysis.arousal),
    }


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        raw_body = self.rfile.read(length) if length > 0 else b""
        status, payload = analyze_request(
            self.headers.get("Authorization"),
            raw_body,
        )
        self._send_json(status, payload)

    def do_GET(self) -> None:
        self._send_json(405, {"detail": "Method Not Allowed"})

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Allow", "POST, OPTIONS")
        self.end_headers()
