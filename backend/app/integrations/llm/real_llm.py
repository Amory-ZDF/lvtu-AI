"""基于 OpenAI Chat Completions API 的真实 LLM 集成实现。"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

from app.core.exceptions import AppException
from app.core.safety import sanitize_content, validate_ai_output
from app.integrations.prompts.destination import build_destination_prompt
from app.schemas.planning import (
    DestinationItem,
    DestinationRecommendationPayload,
    DestinationRecommendationRequest,
    ImageResource,
)

logger = logging.getLogger(__name__)


def _placeholder_image(description: str, category: str = "destination") -> ImageResource:
    """根据 LLM 返回的画面描述生成占位图资源。"""
    return ImageResource(
        category=category,
        url="",
        thumbnail_url="",
        alt=description,
        provider="real-llm",
        placeholder=True,
    )


class RealLLMRecommendationIntegration:
    """基于 OpenAI Chat Completions API 的目的地推荐集成。

    兼容 OpenAI Chat Completions API 格式：
    POST {base_url}/chat/completions
    Authorization: Bearer {api_key}
    Body: {"model": ..., "messages": [...], "temperature": 0.7,
           "response_format": {"type": "json_object"}}
    """

    def __init__(self, base_url: str, api_key: str, model_name: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model_name = model_name

    def recommend(
        self,
        request: DestinationRecommendationRequest,
    ) -> DestinationRecommendationPayload:
        messages = build_destination_prompt(request)
        raw_content = self._call_chat_completions(messages)
        data = self._parse_json_response(raw_content)
        return self._build_payload(data, request)

    def _call_chat_completions(self, messages: list[dict]) -> str:
        """调用 LLM Chat Completions API 并返回 message content。"""
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "model": self._model_name,
            "messages": messages,
            "temperature": 0.7,
            "response_format": {"type": "json_object"},
        }

        prompt_length = sum(len(m.get("content", "")) for m in messages)
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
                success = True
                return content
        except httpx.HTTPStatusError as exc:
            logger.exception(
                "LLM API returned non-2xx status: %s, body=%s",
                exc.response.status_code,
                exc.response.text[:500],
            )
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
        except (KeyError, IndexError) as exc:
            logger.exception("LLM API response missing expected fields: %s", exc)
            raise AppException(
                status_code=502,
                code="ai_response_invalid",
                message="LLM 服务返回结构异常",
            ) from exc
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "LLM call: prompt_length=%s response_status=%s success=%s elapsed_ms=%s",
                prompt_length,
                status_code,
                success,
                elapsed_ms,
            )

    @staticmethod
    def _parse_json_response(content: str) -> dict:
        """解析 LLM 返回的 JSON 字符串。"""
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            logger.exception("Failed to parse LLM JSON response: %s", content[:500])
            raise AppException(
                status_code=502,
                code="ai_response_invalid",
                message="LLM 返回内容无法解析为 JSON",
            ) from exc
        if not isinstance(data, dict):
            raise AppException(
                status_code=502,
                code="ai_response_invalid",
                message="LLM 返回内容不是 JSON 对象",
            )
        return data

    def _build_payload(
        self,
        data: dict,
        request: DestinationRecommendationRequest,
    ) -> DestinationRecommendationPayload:
        """将 LLM 返回的 JSON 转换为 DestinationRecommendationPayload。"""
        validate_ai_output(data, ["destinations"])

        destinations_raw = data.get("destinations", [])
        if not isinstance(destinations_raw, list):
            raise AppException(
                status_code=502,
                code="ai_response_invalid",
                message="destinations 字段不是列表",
            )

        destinations: list[DestinationItem] = []
        for idx, item in enumerate(destinations_raw):
            if not isinstance(item, dict):
                continue
            hero_desc = sanitize_content(
                str(item.get("hero_image_description", "destination hero image")),
            )
            gallery_raw = item.get("gallery_descriptions", [])
            if not isinstance(gallery_raw, list):
                gallery_raw = []
            gallery = [
                _placeholder_image(sanitize_content(str(desc)), category="spot")
                for desc in gallery_raw
            ]
            if not gallery:
                gallery = [_placeholder_image(hero_desc, category="spot")]

            vibe_tags = item.get("vibe_tags", [])
            reasons = item.get("reasons", [])
            destinations.append(
                DestinationItem(
                    id=str(item.get("id", f"dest-{idx}")),
                    name=sanitize_content(str(item.get("name", ""))),
                    country_or_region=sanitize_content(
                        str(item.get("country_or_region", "")),
                    ),
                    match_score=int(item.get("match_score", 80)),
                    budget_range=sanitize_content(str(item.get("budget_range", ""))),
                    best_season=sanitize_content(str(item.get("best_season", ""))),
                    vibe_tags=[sanitize_content(str(t)) for t in vibe_tags],
                    reasons=[sanitize_content(str(r)) for r in reasons],
                    hero_image=_placeholder_image(hero_desc, category="destination"),
                    gallery=gallery,
                ),
            )

        if not destinations:
            raise AppException(
                status_code=502,
                code="ai_response_invalid",
                message="LLM 未返回任何目的地",
            )

        season = request.season or "全年"
        styles = request.travel_style or []
        summary = (
            f"{request.duration_days} 天行程，季节偏好 {season}，"
            f"风格偏好 {'/'.join(styles) if styles else '不限'}"
        )
        return DestinationRecommendationPayload(
            query_summary=summary,
            destinations=destinations,
        )
