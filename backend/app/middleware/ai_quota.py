"""AI 调用配额中间件。

按 (user_id 或 IP) + 日期 维度限制 AI 调用次数，超限返回 429。
仅对 /api/v1/planning/ 路径生效。
使用内存计数器，后续可替换为 Redis。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.api.responses import error_response

logger = logging.getLogger(__name__)


class AIQuotaMiddleware(BaseHTTPMiddleware):
    """AI 调用每日配额中间件。

    按 (identity, date) 维度计数，超过 ai_quota_daily_limit 时返回 429。
    identity 优先使用已认证用户的 user_id（从 request.state 读取），
    否则回退到客户端 IP。
    """

    def __init__(self, app: Any, settings: Any = None) -> None:
        super().__init__(app)
        if settings is None:
            from app.core.config import get_settings

            settings = get_settings()
        self._daily_limit: int = getattr(settings, "ai_quota_daily_limit", 50)
        prefix = getattr(settings, "api_v1_prefix", "/api/v1").rstrip("/")
        self._planning_prefix: str = f"{prefix}/planning/"
        # 计数器：{(identity, date_str): count}
        self._counters: dict[tuple[str, str], int] = {}

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        if request.client:
            return request.client.host
        return "unknown"

    def _resolve_identity(self, request: Request) -> str:
        """解析调用者身份：优先 user_id，回退 IP。"""
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        return f"ip:{self._get_client_ip(request)}"

    def _today_key(self) -> str:
        """返回 UTC 当日日期字符串，用于计数器 key。"""
        return datetime.now(timezone.utc).date().isoformat()

    def _build_quota_exceeded_response(self, request: Request) -> JSONResponse:
        payload = error_response(
            code="ai_quota_exceeded",
            message="今日 AI 调用次数已达上限，请明天再试",
            request=request,
            details=[{"field": "limit", "message": str(self._daily_limit)}],
        )
        response = JSONResponse(
            status_code=429,
            content=payload.model_dump(mode="json"),
        )
        response.headers["X-AI-Quota-Limit"] = str(self._daily_limit)
        response.headers["X-AI-Quota-Remaining"] = "0"
        return response

    async def dispatch(self, request: Request, call_next: Any) -> Response:  # type: ignore[override]
        path = request.url.path
        if not path.startswith(self._planning_prefix):
            return await call_next(request)

        identity = self._resolve_identity(request)
        today = self._today_key()
        key = (identity, today)
        current = self._counters.get(key, 0)

        if current >= self._daily_limit:
            logger.warning(
                "AI quota exceeded for %s: %d/%d",
                identity,
                current,
                self._daily_limit,
            )
            return self._build_quota_exceeded_response(request)

        self._counters[key] = current + 1
        remaining = max(self._daily_limit - self._counters[key], 0)

        response = await call_next(request)
        response.headers["X-AI-Quota-Limit"] = str(self._daily_limit)
        response.headers["X-AI-Quota-Remaining"] = str(remaining)
        return response
