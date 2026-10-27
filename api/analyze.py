import asyncio
import json
import logging
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler
from pathlib import Path

import httpx
from jose import jwk, jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.services.analyzer.runtime import analyze_with_fallback  # noqa: E402
from backend.app.services.vad import quadrant_of  # noqa: E402


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.INFO)
API_VERSION = "0.1.0"
JWKS_CACHE_TTL_SECONDS = 60 * 60
JWKS_TIMEOUT_SECONDS = 10.0

_jwks_cache: dict[str, object] = {
    "keys": {},
    "expires_at": 0.0,
}
_jwks_lock = threading.Lock()


class TokenValidationError(RuntimeError):
    def __init__(
        self,
        reason: str,
        detail: str,
        *,
        alg: str | None = None,
        kid: str | None = None,
    ):
        super().__init__(detail)
        self.reason = reason
        self.detail = detail
        self.alg = alg
        self.kid = kid


def _log_verification_failure(
    reason: str,
    detail: str,
    alg: str | None,
    kid: str | None,
) -> None:
    logger.warning(
        "Supabase JWT verification failed reason=%s alg=%s kid=%s detail=%s",
        reason,
        alg or "unknown",
        kid or "-",
        detail,
    )


def _fail(
    reason: str,
    detail: str,
    *,
    alg: str | None = None,
    kid: str | None = None,
) -> None:
    _log_verification_failure(reason, detail, alg, kid)
    raise TokenValidationError(reason, detail, alg=alg, kid=kid)


def _supabase_url() -> str:
    return (
        os.getenv("SUPABASE_URL")
        or os.getenv("VITE_SUPABASE_TARGET_URL")
        or ""
    ).rstrip("/")


def _load_jwks(
    force_refresh: bool = False,
    *,
    alg: str | None = None,
    kid: str | None = None,
) -> dict[str, dict]:
    now = time.monotonic()
    with _jwks_lock:
        cached_keys = _jwks_cache["keys"]
        expires_at = float(_jwks_cache["expires_at"])
        if (
            not force_refresh
            and cached_keys
            and now < expires_at
        ):
            return cached_keys

        base_url = _supabase_url()
        if not base_url:
            _fail(
                "jwks_fetch_failed",
                "SUPABASE_URL is not configured",
                alg=alg,
                kid=kid,
            )

        jwks_url = f"{base_url}/auth/v1/.well-known/jwks.json"
        try:
            response = httpx.get(jwks_url, timeout=JWKS_TIMEOUT_SECONDS)
            response.raise_for_status()
            payload = response.json()
            key_list = payload.get("keys", [])
            keys = {
                item["kid"]: item
                for item in key_list
                if isinstance(item, dict) and item.get("kid")
            }
            if not keys:
                raise ValueError("JWKS response has no usable keys")
        except Exception as exc:
            _fail(
                "jwks_fetch_failed",
                f"url={jwks_url} error={type(exc).__name__}",
                alg=alg,
                kid=kid,
            )

        _jwks_cache["keys"] = keys
        _jwks_cache["expires_at"] = now + JWKS_CACHE_TTL_SECONDS
        return keys


def _public_key_for_kid(kid: str, alg: str) -> dict:
    keys = _load_jwks(alg=alg, kid=kid)
    if kid not in keys:
        keys = _load_jwks(force_refresh=True, alg=alg, kid=kid)
    if kid not in keys:
        _fail(
            "kid_not_found",
            "no matching JWKS key",
            alg=alg,
            kid=kid,
        )
    return keys[kid]


def _decode_token(
    token: str,
    key,
    algorithm: str,
    *,
    kid: str | None,
) -> dict:
    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=[algorithm],
            audience="authenticated",
        )
    except ExpiredSignatureError as exc:
        _fail(
            "expired",
            str(exc),
            alg=algorithm,
            kid=kid,
        )
    except JWTClaimsError as exc:
        lower = str(exc).lower()
        reason = "wrong_audience" if "audience" in lower else "token_malformed"
        _fail(reason, str(exc), alg=algorithm, kid=kid)
    except JWTError as exc:
        _fail(
            "signature_invalid",
            str(exc),
            alg=algorithm,
            kid=kid,
        )

    if not claims.get("sub"):
        _fail(
            "token_malformed",
            "token subject is missing",
            alg=algorithm,
            kid=kid,
        )

    logger.info(
        "Supabase JWT verified alg=%s kid=%s sub=%s",
        algorithm,
        kid or "-",
        claims["sub"],
    )
    return claims


def verify_supabase_token(authorization: str | None) -> dict:
    if not authorization:
        _fail("token_missing", "Authorization header is missing")

    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        _fail("token_missing", "Bearer token is missing")
    token = token.strip()

    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        _fail("token_malformed", str(exc))

    algorithm = header.get("alg")
    kid = header.get("kid")

    if algorithm == "ES256":
        if not kid:
            _fail(
                "kid_not_found",
                "ES256 token has no kid",
                alg=algorithm,
            )
        key_data = _public_key_for_kid(kid, algorithm)
        try:
            public_key = jwk.construct(key_data, algorithm="ES256")
        except Exception as exc:
            _fail(
                "signature_invalid",
                f"invalid JWKS key: {type(exc).__name__}",
                alg=algorithm,
                kid=kid,
            )
        return _decode_token(
            token,
            public_key,
            "ES256",
            kid=kid,
        )

    if algorithm == "HS256":
        secret = os.getenv("SUPABASE_JWT_SECRET", "")
        if not secret:
            _fail(
                "signature_invalid",
                "SUPABASE_JWT_SECRET is not configured",
                alg=algorithm,
                kid=kid,
            )
        return _decode_token(
            token,
            secret,
            "HS256",
            kid=kid,
        )

    _fail(
        "token_malformed",
        f"unsupported JWT algorithm: {algorithm}",
        alg=algorithm,
        kid=kid,
    )


def analyze_request(authorization: str | None, raw_body: bytes) -> tuple[int, dict]:
    try:
        verify_supabase_token(authorization)
    except TokenValidationError:
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
