from __future__ import annotations

import httpx
import pytest

from app.core.exceptions import AppException
from app.integrations.llm import json_client
from app.integrations.llm.json_client import OpenAICompatibleJsonClient


def _install_transport(monkeypatch: pytest.MonkeyPatch, handler) -> None:  # type: ignore[no-untyped-def]
    real_client = httpx.Client
    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        json_client.httpx,
        "Client",
        lambda **_kwargs: real_client(transport=transport),
    )


def test_complete_json_returns_object(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            request=request,
            json={"choices": [{"message": {"content": '{"ok": true}'}}]},
        )

    _install_transport(monkeypatch, handler)
    client = OpenAICompatibleJsonClient("https://ark.example/v3", "secret", "model")

    result = client.complete_json([{"role": "user", "content": "test"}])

    assert result == {"ok": True}


def test_model_not_open_has_actionable_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            request=request,
            json={"error": {"code": "ModelNotOpen", "message": "not activated"}},
        )

    _install_transport(monkeypatch, handler)
    client = OpenAICompatibleJsonClient("https://ark.example/v3", "secret", "model")

    with pytest.raises(AppException) as caught:
        client.complete_json([{"role": "user", "content": "test"}])

    assert caught.value.status_code == 503
    assert caught.value.code == "ai_model_not_open"
    assert "方舟控制台" in caught.value.message
