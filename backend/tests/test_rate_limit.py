"""限流中间件测试。

使用独立 FastAPI app 实例验证 RateLimitMiddleware 的各项行为，
避免与单例 app 的限流状态互相干扰。
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.rate_limit import RateLimitMiddleware


def _make_settings(**overrides: Any) -> SimpleNamespace:
    defaults: dict[str, Any] = {
        "rate_limit_enabled": True,
        "rate_limit_default": "60/minute",
        "rate_limit_auth": "5/minute",
        "rate_limit_ai": "10/minute",
        "api_v1_prefix": "/api/v1",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _build_app(settings: SimpleNamespace) -> FastAPI:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, settings=settings)

    @app.get("/")
    async def root() -> dict[str, bool]:
        return {"success": True}

    @app.post("/api/v1/auth/login")
    async def login() -> dict[str, bool]:
        return {"success": True}

    @app.post("/api/v1/auth/register")
    async def register() -> dict[str, bool]:
        return {"success": True}

    @app.post("/api/v1/planning/destinations")
    async def plan() -> dict[str, bool]:
        return {"success": True}

    return app


@contextmanager
def _client(settings: SimpleNamespace) -> Generator[TestClient, None, None]:
    app = _build_app(settings)
    with TestClient(app) as client:
        yield client


def test_default_rate_limit_exceeded() -> None:
    """连续请求超过默认阈值时返回 429。"""
    settings = _make_settings(rate_limit_default="3/minute")
    with _client(settings) as client:
        for _ in range(3):
            response = client.get("/")
            assert response.status_code == 200

        response = client.get("/")
        assert response.status_code == 429
        payload = response.json()
        assert payload["success"] is False
        assert payload["error"]["code"] == "rate_limited"
        assert payload["error"]["message"] == "请求过于频繁，请稍后再试"


def test_auth_rate_limit_stricter_than_default() -> None:
    """登录/注册接口使用更严格的 auth 限流，且与 default 桶相互独立。"""
    settings = _make_settings(
        rate_limit_default="10/minute",
        rate_limit_auth="2/minute",
    )
    with _client(settings) as client:
        for _ in range(2):
            response = client.post("/api/v1/auth/login")
            assert response.status_code == 200

        response = client.post("/api/v1/auth/login")
        assert response.status_code == 429

        # default 桶不受 auth 限流影响
        response = client.get("/")
        assert response.status_code == 200


def test_register_uses_auth_rule() -> None:
    """注册接口同样使用 auth 限流规则。"""
    settings = _make_settings(rate_limit_auth="1/minute")
    with _client(settings) as client:
        assert client.post("/api/v1/auth/register").status_code == 200
        assert client.post("/api/v1/auth/register").status_code == 429


def test_ai_rate_limit() -> None:
    """/api/v1/planning/ 前缀使用 ai 限流规则。"""
    settings = _make_settings(rate_limit_ai="2/minute", rate_limit_default="10/minute")
    with _client(settings) as client:
        for _ in range(2):
            assert client.post("/api/v1/planning/destinations").status_code == 200
        assert client.post("/api/v1/planning/destinations").status_code == 429

        # default 桶独立
        assert client.get("/").status_code == 200



def test_rate_limit_headers_on_success() -> None:
    """成功响应包含 X-RateLimit-* 头。"""
    settings = _make_settings(rate_limit_default="5/minute")
    with _client(settings) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers["X-RateLimit-Limit"] == "5"
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers


def test_rate_limit_headers_on_429() -> None:
    """429 响应包含 X-RateLimit-* 和 Retry-After 头。"""
    settings = _make_settings(rate_limit_default="1/minute")
    with _client(settings) as client:
        assert client.get("/").status_code == 200
        response = client.get("/")
        assert response.status_code == 429
        assert response.headers["X-RateLimit-Limit"] == "1"
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert "X-RateLimit-Reset" in response.headers
        assert "Retry-After" in response.headers


def test_429_response_contains_retry_after_detail() -> None:
    """429 响应体的 details 包含 retry_after 字段。"""
    settings = _make_settings(rate_limit_default="1/minute")
    with _client(settings) as client:
        client.get("/")
        response = client.get("/")
        assert response.status_code == 429
        details = response.json()["error"]["details"]
        assert any(d["field"] == "retry_after" for d in details)


def test_rate_limit_disabled() -> None:
    """rate_limit_enabled=False 时不限流。"""
    settings = _make_settings(
        rate_limit_enabled=False,
        rate_limit_default="2/minute",
    )
    with _client(settings) as client:
        for _ in range(10):
            assert client.get("/").status_code == 200


def test_rate_limit_remaining_decreases() -> None:
    """X-RateLimit-Remaining 随请求递减。"""
    settings = _make_settings(rate_limit_default="3/minute")
    with _client(settings) as client:
        r1 = client.get("/")
        assert r1.headers["X-RateLimit-Remaining"] == "2"
        r2 = client.get("/")
        assert r2.headers["X-RateLimit-Remaining"] == "1"
        r3 = client.get("/")
        assert r3.headers["X-RateLimit-Remaining"] == "0"
        r4 = client.get("/")
        assert r4.status_code == 429
