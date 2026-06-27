#!/usr/bin/env python3
"""Build cleaned travel knowledge seed files from private POI candidates.

Input defaults to:
    lv_private_data/raw/amap/poi_candidates_latest.json

Output defaults to:
    lv_private_data/processed/knowledge/

The generated files are private data artifacts and must not be committed to the
public repository.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRIVATE_DIR = REPO_ROOT.parent / f"{REPO_ROOT.name}_private_data"
DEFAULT_INPUT = DEFAULT_PRIVATE_DIR / "raw" / "amap" / "poi_candidates_latest.json"
DEFAULT_OUTPUT_DIR = DEFAULT_PRIVATE_DIR / "processed" / "knowledge"

PHOTO_KEYWORDS = {"拍照", "观景台", "夜景", "日落", "网红打卡"}
SCENIC_KEYWORDS = {"景点", "风景名胜"}
MUSEUM_WORDS = ("博物馆", "美术馆", "展览馆", "艺术馆", "纪念馆")
CULTURE_WORDS = ("寺", "庙", "古镇", "古城", "故居", "遗址", "古迹", "园林", "祠")
NATURE_WORDS = ("公园", "山", "湖", "海", "湿地", "森林", "草原", "峡谷", "瀑布", "沙滩")
STREET_WORDS = ("步行街", "老街", "街区", "市集", "夜市", "小镇", "广场")
LOW_VALUE_WORDS = (
    "停车场",
    "公共厕所",
    "售票处",
    "游客中心",
    "入口",
    "出口",
    "管理处",
    "派出所",
    "服务区",
)
PHOTO_SERVICE_WORDS = (
    "婚纱",
    "儿童摄影",
    "摄影工作室",
    "照相馆",
    "证件照",
    "写真馆",
    "影楼",
    "冲印",
    "快印",
    "图文",
    "广告",
    "喷绘",
    "打印",
    "复印",
    "刻章",
    "标书",
    "装订",
    "印刷",
    "服装直播",
)
SERVICE_TYPE_WORDS = (
    "生活服务",
    "摄影冲印",
    "生活服务场所",
    "公司企业",
    "广告装饰",
)
DESTINATION_TYPE_WORDS = (
    "风景名胜",
    "公园广场",
    "博物馆",
    "特色商业街",
    "步行街",
    "露营地",
    "科教文化场所",
)
DESTINATION_NAME_WORDS = (
    "景区",
    "风景区",
    "旅游区",
    "观景台",
    "公园",
    "广场",
    "博物馆",
    "美术馆",
    "展览馆",
    "艺术馆",
    "纪念馆",
    "文化中心",
    "文化园",
    "古镇",
    "古城",
    "步行街",
)
PHOTO_SERVICE_RESCUE_WORDS = ("博物馆", "文化中心", "文化园")
PHOTO_COMMERCIAL_TYPE_WORDS = (
    "餐饮服务",
    "住宿服务",
    "购物服务",
    "生活服务",
    "公司企业",
    "商务住宅",
    "金融保险",
    "医疗保健",
    "汽车服务",
    "政府机构",
    "培训机构",
)
STRICT_COMMERCIAL_TYPE_WORDS = ("餐饮服务", "住宿服务")
PHOTO_COMMERCIAL_NAME_WORDS = (
    "咖啡",
    "烘焙",
    "餐厅",
    "饭店",
    "酒吧",
    "茶饮",
    "奶茶",
    "火锅",
    "宴会",
    "酒店",
    "民宿",
    "客栈",
    "购物中心",
    "商场",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^0-9a-z\u4e00-\u9fa5_-]+", "", value)
    return value[:80] or "unknown"


def clean_name(value: Any) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_float(value: Any) -> float | None:
    if value in (None, "", []):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def has_any(text: str, words: tuple[str, ...] | set[str]) -> bool:
    return any(word in text for word in words)


def is_photo_service_business(item: dict[str, Any]) -> bool:
    name = clean_name(item.get("name"))
    type_text = clean_name(item.get("type"))
    combined = f"{name} {type_text}"
    if has_any(combined, PHOTO_SERVICE_WORDS) and not has_any(
        name, PHOTO_SERVICE_RESCUE_WORDS
    ):
        return True
    if clean_name(item.get("query_keyword")) != "拍照":
        return False
    if has_any(name, PHOTO_COMMERCIAL_NAME_WORDS) and not has_any(
        name, PHOTO_SERVICE_RESCUE_WORDS
    ):
        return True
    if has_any(type_text, DESTINATION_TYPE_WORDS):
        return False
    return (
        has_any(type_text, SERVICE_TYPE_WORDS)
        or has_any(type_text, PHOTO_COMMERCIAL_TYPE_WORDS)
        or has_any(name, PHOTO_COMMERCIAL_NAME_WORDS)
    )


def is_non_destination_commercial(item: dict[str, Any]) -> bool:
    name = clean_name(item.get("name"))
    type_text = clean_name(item.get("type"))
    if has_any(type_text, DESTINATION_TYPE_WORDS):
        return False
    if has_any(type_text, STRICT_COMMERCIAL_TYPE_WORDS):
        return True
    if has_any(name, DESTINATION_NAME_WORDS):
        return False
    return has_any(type_text, PHOTO_COMMERCIAL_TYPE_WORDS)


def classify_poi(item: dict[str, Any]) -> tuple[str, list[str]]:
    name = clean_name(item.get("name"))
    type_text = clean_name(item.get("type"))
    keyword = clean_name(item.get("query_keyword"))
    combined = f"{name} {type_text} {keyword}"
    tags = set(item.get("tags") or [])

    if keyword in PHOTO_KEYWORDS or has_any(combined, ("观景台", "夜景", "日落", "打卡")):
        category = "photo_spot"
        tags.update(["photogenic", "photo_spot"])
    elif has_any(combined, MUSEUM_WORDS):
        category = "museum"
        tags.update(["culture", "indoor"])
    elif has_any(combined, CULTURE_WORDS):
        category = "culture"
        tags.update(["culture", "heritage"])
    elif has_any(combined, NATURE_WORDS):
        category = "nature"
        tags.update(["nature", "outdoor"])
    elif has_any(combined, STREET_WORDS):
        category = "citywalk"
        tags.update(["citywalk", "local_life"])
    elif keyword in SCENIC_KEYWORDS:
        category = "attraction"
        tags.add("attraction")
    else:
        category = "attraction"

    if "夜景" in combined:
        tags.add("night_view")
    if "日落" in combined:
        tags.add("sunset")
    if "亲子" in combined:
        tags.add("family")
    return category, sorted(str(tag) for tag in tags if tag)


def recommended_duration(category: str) -> int:
    return {
        "photo_spot": 45,
        "museum": 120,
        "culture": 90,
        "nature": 150,
        "citywalk": 90,
        "attraction": 90,
    }.get(category, 90)


def quality_score(item: dict[str, Any], category: str) -> float:
    score = 0.45
    if category in {"photo_spot", "museum", "culture", "nature"}:
        score += 0.12
    if clean_name(item.get("address")):
        score += 0.06
    has_location = (
        parse_float(item.get("latitude")) is not None
        and parse_float(item.get("longitude")) is not None
    )
    if has_location:
        score += 0.12
    rating = parse_float(item.get("rating"))
    if rating is not None:
        if rating >= 4.5:
            score += 0.12
        elif rating >= 4.0:
            score += 0.08
        else:
            score += 0.03
    if int(item.get("photo_count") or 0) > 0:
        score += 0.08
    if clean_name(item.get("query_keyword")) in PHOTO_KEYWORDS:
        score += 0.04
    return round(min(score, 0.98), 3)


def should_drop(item: dict[str, Any]) -> bool:
    name = clean_name(item.get("name"))
    if not name:
        return True
    if parse_float(item.get("latitude")) is None or parse_float(item.get("longitude")) is None:
        return True
    combined = f"{name} {clean_name(item.get('type'))} {clean_name(item.get('address'))}"
    return (
        has_any(combined, LOW_VALUE_WORDS)
        or is_photo_service_business(item)
        or is_non_destination_commercial(item)
    )


def build_poi(item: dict[str, Any]) -> dict[str, Any] | None:
    if should_drop(item):
        return None
    city = clean_name(item.get("query_city") or item.get("city") or "未知")
    name = clean_name(item.get("name"))
    category, tags = classify_poi(item)
    lat = parse_float(item.get("latitude"))
    lng = parse_float(item.get("longitude"))
    if lat is None or lng is None:
        return None
    source_id = clean_name(item.get("source_id"))
    poi_id = f"amap-{source_id}" if source_id else f"{slugify(city)}-{slugify(name)}"
    score = quality_score(item, category)
    return {
        "id": poi_id,
        "source": "amap",
        "source_id": source_id or None,
        "destination_name": city,
        "name": name,
        "canonical_name": name,
        "category": category,
        "address": clean_name(item.get("address")) or None,
        "province": clean_name(item.get("province")) or None,
        "city": clean_name(item.get("city")) or city,
        "district": clean_name(item.get("district")) or None,
        "latitude": lat,
        "longitude": lng,
        "recommended_duration_minutes": recommended_duration(category),
        "price_level": "unknown",
        "rating": parse_float(item.get("rating")),
        "tags": tags,
        "quality_score": score,
        "confidence_score": score,
        "raw_type": clean_name(item.get("type")) or None,
        "query_keyword": clean_name(item.get("query_keyword")) or None,
    }


def dedupe_pois(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for item in items:
        key = f"{item['destination_name']}|{item['canonical_name']}"
        existing = deduped.get(key)
        if existing is None or item["quality_score"] > existing["quality_score"]:
            deduped[key] = item
        elif existing is not None:
            existing_tags = set(existing.get("tags") or [])
            existing_tags.update(item.get("tags") or [])
            existing["tags"] = sorted(existing_tags)
    return sorted(
        deduped.values(),
        key=lambda x: (x["destination_name"], -x["quality_score"], x["name"]),
    )


def haversine_km(a: dict[str, Any], b: dict[str, Any]) -> float:
    radius_km = 6371.0
    lat1 = math.radians(float(a["latitude"]))
    lon1 = math.radians(float(a["longitude"]))
    lat2 = math.radians(float(b["latitude"]))
    lon2 = math.radians(float(b["longitude"]))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * radius_km * math.asin(math.sqrt(h))


def edge_score(distance_km: float, a: dict[str, Any], b: dict[str, Any]) -> float:
    if distance_km <= 1.2:
        score = 0.92
    elif distance_km <= 3:
        score = 0.82
    elif distance_km <= 5:
        score = 0.68
    elif distance_km <= 8:
        score = 0.52
    else:
        score = 0.35
    if a["category"] != b["category"]:
        score += 0.04
    if "photogenic" in set(a.get("tags") or []) or "photogenic" in set(b.get("tags") or []):
        score += 0.03
    return round(min(score, 0.98), 3)


def build_edges(
    pois_by_city: dict[str, list[dict[str, Any]]],
    max_pois_per_city: int,
) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for city, pois in pois_by_city.items():
        selected = sorted(pois, key=lambda x: -x["quality_score"])[:max_pois_per_city]
        for poi in selected:
            candidates: list[tuple[float, dict[str, Any]]] = []
            for other in selected:
                if poi["id"] == other["id"]:
                    continue
                distance_km = haversine_km(poi, other)
                if distance_km <= 8:
                    candidates.append((distance_km, other))
            candidates.sort(key=lambda x: x[0])
            for distance_km, other in candidates[:6]:
                score = edge_score(distance_km, poi, other)
                edges.append(
                    {
                        "destination_name": city,
                        "from_poi_id": poi["id"],
                        "to_poi_id": other["id"],
                        "distance_km": round(distance_km, 2),
                        "estimated_travel_minutes": max(8, round(distance_km / 18 * 60)),
                        "transport_mode": "taxi_or_transit",
                        "compatibility_score": score,
                        "reason": (
                            "距离较近，适合同日组合" if score >= 0.65 else "可组合但需要控制节奏"
                        ),
                    }
                )
    return edges


def top_by_categories(
    pois: list[dict[str, Any]],
    categories: set[str],
    limit: int,
) -> list[dict[str, Any]]:
    filtered = [poi for poi in pois if poi["category"] in categories]
    return sorted(filtered, key=lambda x: -x["quality_score"])[:limit]


def route_points(pois: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "poi_id": poi["id"],
            "name": poi["name"],
            "category": poi["category"],
            "suggested_duration_minutes": poi["recommended_duration_minutes"],
        }
        for poi in pois
    ]


def build_route_templates(pois_by_city: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    templates: list[dict[str, Any]] = []
    route_specs = [
        ("classic-1d", "经典初游路线", {"attraction", "culture", "museum", "nature"}, "balanced"),
        ("photo-1d", "高出片打卡路线", {"photo_spot", "nature", "citywalk"}, "relaxed"),
        ("culture-1d", "人文 Citywalk 路线", {"museum", "culture", "citywalk"}, "relaxed"),
    ]
    for city, pois in pois_by_city.items():
        for suffix, title, categories, pace in route_specs:
            selected = top_by_categories(pois, categories, 5)
            if len(selected) < 3:
                continue
            templates.append(
                {
                    "id": f"{slugify(city)}-{suffix}",
                    "destination_name": city,
                    "title": f"{city}{title}",
                    "duration_days": 1,
                    "pace": pace,
                    "theme_tags": sorted(
                        {tag for poi in selected for tag in poi.get("tags", [])}
                    )[:10],
                    "suitable_people": ["solo", "friends", "couple"],
                    "estimated_budget": "unknown",
                    "route_points": [{"day": 1, "points": route_points(selected)}],
                    "highlights": [poi["name"] for poi in selected[:3]],
                    "quality_score": round(
                        sum(poi["quality_score"] for poi in selected) / len(selected),
                        3,
                    ),
                    "source": "heuristic_from_amap_pois",
                }
            )
    return templates


def build_photo_spots(pois: list[dict[str, Any]]) -> list[dict[str, Any]]:
    spots: list[dict[str, Any]] = []
    for poi in pois:
        tags = set(poi.get("tags") or [])
        if poi["category"] != "photo_spot" and "photogenic" not in tags:
            continue
        spots.append(
            {
                "id": f"photo-{poi['id']}",
                "poi_id": poi["id"],
                "destination_name": poi["destination_name"],
                "name": poi["name"],
                "location": poi.get("address"),
                "latitude": poi["latitude"],
                "longitude": poi["longitude"],
                "best_time": "待补充",
                "composition": "待结合 UGC 摘要补充构图建议",
                "photo_score": round(poi["quality_score"] * 10, 1),
                "tags": sorted(tags | {"photo_spot"}),
                "source": poi["source"],
                "source_id": poi.get("source_id"),
            }
        )
    return spots


def coverage_report(
    *,
    pois_by_city: dict[str, list[dict[str, Any]]],
    photo_spots: list[dict[str, Any]],
    route_templates: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> str:
    photo_by_city = defaultdict(int)
    route_by_city = defaultdict(int)
    edge_by_city = defaultdict(int)
    for spot in photo_spots:
        photo_by_city[spot["destination_name"]] += 1
    for route in route_templates:
        route_by_city[route["destination_name"]] += 1
    for edge in edges:
        edge_by_city[edge["destination_name"]] += 1

    lines = [
        "# 旅图知识种子覆盖报告\n",
        f"- generated_at: {datetime.now().isoformat()}\n",
        f"- city_count: {len(pois_by_city)}\n",
        f"- poi_count: {sum(len(items) for items in pois_by_city.values())}\n",
        f"- photo_spot_count: {len(photo_spots)}\n",
        f"- route_template_count: {len(route_templates)}\n",
        f"- poi_edge_count: {len(edges)}\n\n",
        "| 城市 | POI | 机位候选 | 线路模板 | 组合边 | 样例 POI |\n",
        "|---|---:|---:|---:|---:|---|\n",
    ]
    for city, pois in sorted(pois_by_city.items(), key=lambda x: (-len(x[1]), x[0])):
        samples = "、".join(poi["name"] for poi in pois[:4])
        lines.append(
            f"| {city} | {len(pois)} | {photo_by_city[city]} | "
            f"{route_by_city[city]} | {edge_by_city[city]} | {samples} |\n"
        )
    return "".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build cleaned travel knowledge seeds.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max-edge-pois-per-city", type=int, default=60)
    args = parser.parse_args()

    input_path = args.input.expanduser()
    output_dir = args.output_dir.expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    raw = load_json(input_path)
    cleaned = [poi for item in raw.get("items", []) if (poi := build_poi(item)) is not None]
    pois = dedupe_pois(cleaned)
    pois_by_city: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for poi in pois:
        pois_by_city[poi["destination_name"]].append(poi)
    for city in pois_by_city:
        pois_by_city[city].sort(key=lambda x: -x["quality_score"])

    photo_spots = build_photo_spots(pois)
    edges = build_edges(pois_by_city, args.max_edge_pois_per_city)
    route_templates = build_route_templates(pois_by_city)

    metadata = {
        "generated_at": datetime.now().isoformat(),
        "input": str(input_path),
        "city_count": len(pois_by_city),
        "poi_count": len(pois),
        "photo_spot_count": len(photo_spots),
        "poi_edge_count": len(edges),
        "route_template_count": len(route_templates),
    }
    outputs = {
        "pois_latest.json": {"metadata": metadata, "items": pois},
        "photo_spots_latest.json": {"metadata": metadata, "items": photo_spots},
        "poi_edges_latest.json": {"metadata": metadata, "items": edges},
        "route_templates_latest.json": {"metadata": metadata, "items": route_templates},
    }
    for filename, payload in outputs.items():
        write_json(output_dir / filename, payload)

    report = coverage_report(
        pois_by_city=pois_by_city,
        photo_spots=photo_spots,
        route_templates=route_templates,
        edges=edges,
    )
    (output_dir / "coverage_report_latest.md").write_text(report, encoding="utf-8")

    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    print(f"output_dir={output_dir}")


if __name__ == "__main__":
    main()
