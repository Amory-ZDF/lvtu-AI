"""OpenAI-compatible JSON chat client shared by AI integrations."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


class OpenAICompatibleJsonClient:
    def __init__(self, base_url: str, api_key: str, model_name: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model_name = model_name

    def complete_json(self, messages: list[dict], *, temperature: float = 0.2) -> dict:
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "model": self._model_name,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }

        prompt_length = sum(len(message.get("content", "")) for message in messages)
        start = time.perf_counter()
        success = False
        status_code: int | None = None
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=headers, json=body)
                status_code = response.status_code
                response.raise_for_status()
                payload = response.json()
                content = payload["choices"][0]["message"]["content"]
                data = json.loads(content)
                if not isinstance(data, dict):
                    raise ValueError("LLM response is not a JSON object")
                success = True
                return data
        except httpx.HTTPStatusError as exc:
            provider_code = _provider_error_code(exc.response)
            logger.exception(
                "LLM API returned non-2xx status: %s, provider_code=%s",
                exc.response.status_code,
                provider_code,
            )
            if exc.response.status_code == 404 and provider_code in {
                "ModelNotOpen",
                "InvalidEndpointOrModel.NotFound",
            }:
                raise AppException(
                    status_code=503,
                    code="ai_model_not_open",
                    message="文本模型尚未在方舟控制台开通，行程未发生变化",
                ) from exc
            raise AppException(
                status_code=502,
                code="ai_provider_error",
                message=f"LLM 服务返回错误状态：{exc.response.status_code}",
            ) from exc
        except httpx.RequestError as exc:
            logger.exception("LLM API request failed: %s", exc)
            raise AppException(
                status_code=502,
                code="ai_provider_unreachable",
                message="无法连接 LLM 服务",
            ) from exc
        except (json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError) as exc:
            logger.exception("LLM API returned invalid JSON response")
            raise AppException(
                status_code=502,
                code="ai_response_invalid",
                message="LLM 服务返回的调整方案格式异常",
            ) from exc
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "LLM JSON call: prompt_length=%s response_status=%s success=%s elapsed_ms=%s",
                prompt_length,
                status_code,
                success,
                elapsed_ms,
            )


def _provider_error_code(response: httpx.Response) -> str | None:
    try:
        payload = response.json()
    except ValueError:
        return None
    error = payload.get("error") if isinstance(payload, dict) else None
    if not isinstance(error, dict):
        return None
    code = error.get("code")
    return str(code) if code else None
