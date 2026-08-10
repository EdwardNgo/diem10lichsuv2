import json
import os
import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Message

from diem10_api.core.logging import get_logger
from diem10_api.core.request_context import new_request_id, set_request_id

logger = get_logger("http")

SENSITIVE_HEADERS = frozenset(
    {
        "authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
    }
)
SKIP_PATHS = frozenset({"/healthz"})


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _max_body_bytes() -> int:
    return int(os.getenv("LOG_MAX_BODY_BYTES", "65536"))


def _sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    sanitized: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in SENSITIVE_HEADERS:
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = value
    return sanitized


def _decode_body(raw: bytes) -> object:
    if not raw:
        return None
    max_bytes = _max_body_bytes()
    truncated = len(raw) > max_bytes
    payload = raw[:max_bytes]
    try:
        parsed: object = json.loads(payload)
    except json.JSONDecodeError:
        parsed = payload.decode("utf-8", errors="replace")
    if truncated:
        return {"truncated": True, "bytes": len(raw), "body": parsed}
    return parsed


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("x-request-id") or new_request_id()
        set_request_id(request_id)
        started_at = time.perf_counter()

        if request.url.path in SKIP_PATHS:
            response = await call_next(request)
            response.headers["x-request-id"] = request_id
            return response

        request_body = await request.body()
        log_request = _bool_env("LOG_REQUEST_BODY", True)
        log_response = _bool_env("LOG_RESPONSE_BODY", True)

        logger.info(
            "request.received",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query=str(request.query_params),
            client_ip=request.client.host if request.client is not None else None,
            headers=_sanitize_headers(dict(request.headers)),
            body=_decode_body(request_body) if log_request else "[disabled]",
        )

        async def receive() -> Message:
            return {"type": "http.request", "body": request_body, "more_body": False}

        request = Request(request.scope, receive)
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)

        response_body = b""
        if log_response:
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
                background=response.background,
            )

        logger.info(
            "request.completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            response_headers=_sanitize_headers(dict(response.headers)),
            response_body=_decode_body(response_body) if log_response else "[disabled]",
        )
        response.headers["x-request-id"] = request_id
        return response
