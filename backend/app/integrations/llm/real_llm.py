"""基于 OpenAI Chat Completions API 的真实 LLM 集成实现。"""

from __future__ import annotations

from app.core.exceptions import AppException
from app.core.safety import sanitize_content, validate_ai_output
from app.integrations.llm.json_client import OpenAICompatibleJsonClient
from app.integrations.prompts.destination import build_destination_prompt
from app.schemas.planning import (
    DestinationItem,
    DestinationRecommendationPayload,
    DestinationRecommendationRequest,
    ImageResource,
)


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
        self._client = OpenAICompatibleJsonClient(base_url, api_key, model_name)

    def recommend(
        self,
        request: DestinationRecommendationRequest,
    ) -> DestinationRecommendationPayload:
        messages = build_destination_prompt(request)
        data = self._client.complete_json(messages, temperature=0.7)
        return self._build_payload(data, request)

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
