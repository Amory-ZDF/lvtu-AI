"""基于内存滑动窗口的请求限流中间件。

限流维度：按 IP + 规则类别组合（规则由路径前缀映射）。
触发限流时返回 429，并附带标准 RateLimit 响应头。
"""

from __future__ import annotations

import time
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.api.responses import error_response

_UNIT_SECONDS = {"second": 1, "s": 1, "minute": 60, "m": 60, "hour": 3600, "h": 3600}


def parse_rate_limit(spec: str) -> tuple[int, int]:
    """解析 "60/minute" 格式的限流配置，返回 (limit, window_seconds)。"""
    parts = spec.strip().split("/")
    if len(parts) != 2:
        raise ValueError(f"Invalid rate limit spec: {spec}")
    count = int(parts[0])
    unit = parts[1].strip().lower()
    if unit not in _UNIT_SECONDS:
        raise ValueError(f"Unknown rate limit unit: {unit}")
    return count, _UNIT_SECONDS[unit]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """内存滑动窗口限流中间件。

    按 (client_ip, rule) 维度维护请求时间戳列表，窗口内请求数超过阈值时返回 429。
    """

    def __init__(self, app: Any, settings: Any = None) -> None:
        super().__init__(app)
        if settings is None:
            from app.core.config import get_settings

            settings = get_settings()
        self.enabled: bool = settings.rate_limit_enabled
        self._limits: dict[str, tuple[int, int]] = {
            "default": parse_rate_limit(settings.rate_limit_default),
            "auth": parse_rate_limit(settings.rate_limit_auth),
            "ai": parse_rate_limit(settings.rate_limit_ai),
        }
        prefix = settings.api_v1_prefix.rstrip("/")
        self._auth_paths: set[str] = {f"{prefix}/auth/login", f"{prefix}/auth/register"}
        self._ai_prefix: str = f"{prefix}/planning/"
        self._store: dict[str, list[float]] = {}

    def _resolve_rule(self, method: str, path: str) -> str:
        if path in self._auth_paths:
            return "auth"
        if path.startswith(self._ai_prefix):
            return "ai"
        return "default"

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        if request.client:
            return request.client.host
        return "unknown"

    def _build_rate_limited_response(
        self,
        request: Request,
        limit: int,
        reset_seconds: int,
    ) -> JSONResponse:
        payload = error_response(
            code="rate_limited",
            message="请求过于频繁，请稍后再试",
            request=request,
            details=[{"field": "retry_after", "message": str(reset_seconds)}],
        )
        response = JSONResponse(
            status_code=429,
            content=payload.model_dump(mode="json"),
        )
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = "0"
        response.headers["X-RateLimit-Reset"] = str(reset_seconds)
        response.headers["Retry-After"] = str(reset_seconds)
        return response

    async def dispatch(self, request: Request, call_next: Any) -> Response:  # type: ignore[override]
        if not self.enabled:
            return await call_next(request)

        method = request.method
        path = request.url.path
        rule = self._resolve_rule(method, path)
        limit, window = self._limits[rule]

        ip = self._get_client_ip(request)
        key = f"{ip}:{rule}"

        now = time.monotonic()
        cutoff = now - window
        timestamps = [ts for ts in self._store.get(key, []) if ts > cutoff]

        if len(timestamps) >= limit:
            reset_seconds = max(int(timestamps[0] + window - now), 1)
            return self._build_rate_limited_response(request, limit, reset_seconds)

        timestamps.append(now)
        self._store[key] = timestamps
        remaining = max(limit - len(timestamps), 0)
        reset_seconds = max(int(timestamps[0] + window - now), 1)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_seconds)
        return response
