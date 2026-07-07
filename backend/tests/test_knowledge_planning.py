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
            "quality_score": 0.98,
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
            "quality_score": 0.95,
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
            "quality_score": 0.93,
        },
        {
            "id": "poi-4",
            "destination_name": "测试城",
            "name": "测试经典地标",
            "category": "attraction",
            "address": "中心路 1 号",
            "province": "测试省",
            "latitude": 30.4,
            "longitude": 120.4,
            "recommended_duration_minutes": 120,
            "rating": 4.7,
            "tags": ["attraction", "地标"],
            "quality_score": 0.97,
        },
        {
            "id": "poi-5",
            "destination_name": "测试城",
            "name": "测试博物馆",
            "category": "museum",
            "address": "博物馆路",
            "province": "测试省",
            "latitude": 30.5,
            "longitude": 120.5,
            "recommended_duration_minutes": 90,
            "rating": 4.4,
            "tags": ["museum", "展馆"],
            "quality_score": 0.91,
        },
        {
            "id": "poi-6",
            "destination_name": "测试城",
            "name": "测试经典地标-观景台",
            "category": "photo_spot",
            "address": "中心路高台",
            "province": "测试省",
            "latitude": 30.6,
            "longitude": 120.6,
            "recommended_duration_minutes": 60,
            "rating": 4.7,
            "tags": ["photo_spot", "观景台"],
            "quality_score": 0.92,
        },
        {
            "id": "poi-7",
            "destination_name": "测试城",
            "name": "测试老街",
            "category": "citywalk",
            "address": "老街 8 号",
            "province": "测试省",
            "latitude": 30.7,
            "longitude": 120.7,
            "recommended_duration_minutes": 100,
            "rating": 4.5,
            "tags": ["citywalk", "街区"],
            "quality_score": 0.9,
        },
        {
            "id": "poi-8",
            "destination_name": "测试城",
            "name": "测试山谷",
            "category": "photo_spot",
            "address": "山谷路",
            "province": "测试省",
            "latitude": 30.8,
            "longitude": 120.8,
            "recommended_duration_minutes": 80,
            "rating": 4.5,
            "tags": ["photo_spot", "山谷"],
            "quality_score": 0.89,
        },
        {
            "id": "poi-9",
            "destination_name": "测试城",
            "name": "测试湖边",
            "category": "nature",
            "address": "湖边路",
            "province": "测试省",
            "latitude": 30.9,
            "longitude": 120.9,
            "recommended_duration_minutes": 80,
            "rating": 4.3,
            "tags": ["nature", "湖"],
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
    assert len(result.options) == 2
    first_option, second_option = result.options
    assert "初访" in first_option.title
    assert "复访" in second_option.title
    assert "第一次" in first_option.summary
    assert "已经来过" in second_option.summary

    first_day = first_option.days[0]
    assert first_day.spots[0].name == "测试观景台"
    assert first_day.spots[0].images[0].placeholder is False
    assert first_day.spots[0].time_slot == "09:00"

    first_names = {spot.name for day in first_option.days for spot in day.spots}
    second_names = {spot.name for day in second_option.days for spot in day.spots}
    assert "测试经典地标" in first_names
    assert "测试山谷" in second_names
    assert "测试经典地标-观景台" not in second_names
    assert first_names.isdisjoint(second_names)


def test_local_media_returns_non_placeholder_cards() -> None:
    result = LocalMediaAssetIntegration().placeholders(
        MediaPlaceholderRequest(destination_name="测试城", categories=["destination"])
    )

    assert result.assets[0].items[0].placeholder is False
    assert result.assets[0].items[0].url.startswith("/api/v1/media/place-card.svg")
