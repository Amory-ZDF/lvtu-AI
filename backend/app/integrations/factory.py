"""Integration 工厂。

根据 settings 选择真实集成或 mock 集成：
- 当 provider == "mock" 或对应 API key 未配置时，降级到 mock 并记录 warning。
- 否则返回真实集成实现。
"""

from __future__ import annotations

import logging

from app.core.config import Settings
from app.integrations.placeholders import (
    MediaAssetIntegration,
    MockMediaAssetIntegration,
    MockRecommendationIntegration,
    MockRoutePlannerIntegration,
    RecommenderIntegration,
    RoutePlannerIntegration,
)

logger = logging.getLogger(__name__)


def get_recommender_integration(settings: Settings) -> RecommenderIntegration:
    """返回目的地推荐集成实例。

    降级规则：
    - settings.ai_provider == "mock" → mock
    - settings.ai_api_key 为空 → mock（记录 warning）
    - settings.ai_base_url 为空 → mock（记录 warning）
    - 否则 → RealLLMRecommendationIntegration
    """
    if settings.ai_provider == "mock":
        return MockRecommendationIntegration()

    if not settings.ai_api_key:
        logger.warning("AI_API_KEY not configured, falling back to mock")
        return MockRecommendationIntegration()

    if not settings.ai_base_url or not settings.ai_model_name:
        logger.warning("AI_BASE_URL or AI_MODEL_NAME not configured, falling back to mock")
        return MockRecommendationIntegration()

    # 延迟导入，避免无 httpx 环境下 import 失败
    from app.integrations.llm import RealLLMRecommendationIntegration

    return RealLLMRecommendationIntegration(
        base_url=settings.ai_base_url,
        api_key=settings.ai_api_key,
        model_name=settings.ai_model_name,
    )


def get_route_planner_integration(settings: Settings) -> RoutePlannerIntegration:
    """返回路线规划集成实例。

    降级规则：
    - settings.agent_provider == "mock" → mock
    - settings.agent_api_key 为空 → mock（记录 warning）
    - settings.agent_base_url 为空 → mock（记录 warning）
    - 否则 → RealRoutePlannerIntegration
    """
    if settings.agent_provider == "mock":
        return MockRoutePlannerIntegration()

    if not settings.agent_api_key:
        logger.warning("AGENT_API_KEY not configured, falling back to mock")
        return MockRoutePlannerIntegration()

    if not settings.agent_base_url or not settings.agent_workflow_name:
        logger.warning(
            "AGENT_BASE_URL or AGENT_WORKFLOW_NAME not configured, falling back to mock",
        )
        return MockRoutePlannerIntegration()

    # 延迟导入，避免无 httpx 环境下 import 失败
    from app.integrations.agent import RealRoutePlannerIntegration

    return RealRoutePlannerIntegration(
        base_url=settings.agent_base_url,
        api_key=settings.agent_api_key,
        workflow_name=settings.agent_workflow_name,
    )


def get_media_asset_integration(settings: Settings) -> MediaAssetIntegration:
    """返回媒体资产集成实例（当前始终返回 mock）。"""
    return MockMediaAssetIntegration()
