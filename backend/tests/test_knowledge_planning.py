from __future__ import annotations

import json
from pathlib import Path

from app.integrations.knowledge import (
    KnowledgeRecommendationIntegration,
    KnowledgeRoutePlannerIntegration,
    LocalMediaAssetIntegration,
)
from app.schemas.planning import (
    DestinationRecommendationRequest,
    MediaPlaceholderRequest,
    RouteGenerationRequest,
)


def _write_payload(path: Path, items: list[dict]) -> None:
    path.write_text(
        json.dumps({"metadata": {}, "items": items}, ensure_ascii=False),
        encoding="utf-8",
    )


def _seed_dir(tmp_path: Path) -> Path:
    pois = [
        {
            "id": "poi-1",
            "destination_name": "测试城",
            "name": "测试观景台",
            "category": "photo_spot",
            "address": "山海路 1 号",
            "province": "测试省",
            "latitude": 30.1,
            "longitude": 120.1,
            "recommended_duration_minutes": 60,
            "rating": 4.8,
            "tags": ["photo_spot", "观景台"],
            "quality_score": 0.96,
        },
        {
            "id": "poi-2",
            "destination_name": "测试城",
            "name": "测试古镇",
            "category": "culture",
            "address": "古镇街",
            "province": "测试省",
            "latitude": 30.2,
            "longitude": 120.2,
            "recommended_duration_minutes": 120,
            "rating": 4.6,
            "tags": ["culture", "古镇"],
            "quality_score": 0.9,
        },
        {
            "id": "poi-3",
            "destination_name": "测试城",
            "name": "测试公园",
            "category": "nature",
            "address": "公园路",
            "province": "测试省",
            "latitude": 30.3,
            "longitude": 120.3,
            "recommended_duration_minutes": 90,
            "rating": 4.5,
            "tags": ["nature", "公园"],
            "quality_score": 0.88,
        },
    ]
    _write_payload(tmp_path / "pois_latest.json", pois)
    _write_payload(tmp_path / "photo_spots_latest.json", [])
    _write_payload(tmp_path / "route_templates_latest.json", [])
    return tmp_path


def test_knowledge_recommendation_uses_seed_data(tmp_path: Path) -> None:
    integration = KnowledgeRecommendationIntegration(_seed_dir(tmp_path))
    result = integration.recommend(
        DestinationRecommendationRequest(duration_days=2, interests=["拍照", "自然"])
    )

    assert result.destinations
    item = result.destinations[0]
    assert item.name == "测试城"
    assert item.hero_image.placeholder is False
    assert item.hero_image.provider == "lv-local-card"
    assert "测试观景台" in item.reasons[1]


def test_knowledge_route_generation_uses_real_pois(tmp_path: Path) -> None:
    integration = KnowledgeRoutePlannerIntegration(_seed_dir(tmp_path))
    result = integration.generate_plan(
        RouteGenerationRequest(destination_name="测试城", duration_days=1)
    )

    assert result.destination_name == "测试城"
    assert result.options
    first_day = result.options[0].days[0]
    assert first_day.spots[0].name == "测试观景台"
    assert first_day.spots[0].images[0].placeholder is False
    assert first_day.spots[0].time_slot == "09:30"


def test_local_media_returns_non_placeholder_cards() -> None:
    result = LocalMediaAssetIntegration().placeholders(
        MediaPlaceholderRequest(destination_name="测试城", categories=["destination"])
    )

    assert result.assets[0].items[0].placeholder is False
    assert result.assets[0].items[0].url.startswith("/api/v1/media/place-card.svg")
