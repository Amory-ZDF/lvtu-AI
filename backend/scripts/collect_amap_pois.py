#!/usr/bin/env python3
"""Collect China POI candidates from AMap Web Service API into the private data folder.

This script intentionally writes outputs outside the public repository by default.
AMap is suitable for domestic China POI collection. Use another source for overseas
destinations such as Kyoto or Tokyo.

Examples:
    cd backend
    python -m scripts.collect_amap_pois --cities 北京,上海,杭州 --limit-per-keyword 60
    python -m scripts.collect_amap_pois --cities 大理 --keywords 景点,拍照,观景台,日落
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRIVATE_DIR = REPO_ROOT.parent / f"{REPO_ROOT.name}_private_data"
DEFAULT_OUTPUT_DIR = DEFAULT_PRIVATE_DIR / "raw" / "amap"

AMAP_PLACE_TEXT_URL = "https://restapi.amap.com/v3/place/text"
DEFAULT_KEYWORDS = [
    "景点",
    "风景名胜",
    "博物馆",
    "美术馆",
    "公园",
    "古镇",
    "寺庙",
    "观景台",
    "夜景",
    "日落",
    "拍照",
    "网红打卡",
    "咖啡",
    "市集",
]


def _load_dotenv_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_local_env() -> None:
    """Load local env files without printing secret values."""
    for path in [
        REPO_ROOT / ".env",
        REPO_ROOT / ".env.production",
        REPO_ROOT / "backend" / ".env",
        REPO_ROOT / "backend" / ".env.production",
    ]:
        _load_dotenv_file(path)


def split_csv(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def amap_get(params: dict[str, Any]) -> dict[str, Any]:
    headers = {"User-Agent": "lv-tu-dev-data-collector/0.1"}
    with httpx.Client(timeout=20.0, headers=headers) as client:
        response = client.get(AMAP_PLACE_TEXT_URL, params=params)
        response.raise_for_status()
        data = response.json()
    if data.get("status") != "1":
        info = data.get("info") or "unknown error"
        infocode = data.get("infocode") or "unknown"
        raise RuntimeError(f"AMap API error: {info} ({infocode})")
    return data


def normalize_poi(raw: dict[str, Any], city: str, keyword: str) -> dict[str, Any]:
    location = str(raw.get("location") or "")
    lng: float | None = None
    lat: float | None = None
    if "," in location:
        lng_text, lat_text = location.split(",", 1)
        try:
            lng = float(lng_text)
            lat = float(lat_text)
        except ValueError:
            lng = None
            lat = None

    photos = raw.get("photos")
    photo_count = len(photos) if isinstance(photos, list) else 0
    tags = [keyword]
    type_text = str(raw.get("type") or "")
    for part in type_text.split(";"):
        if part and part not in tags:
            tags.append(part)

    biz_ext = raw.get("biz_ext")
    biz_ext = biz_ext if isinstance(biz_ext, dict) else {}

    return {
        "source": "amap",
        "source_id": raw.get("id"),
        "query_city": city,
        "query_keyword": keyword,
        "name": raw.get("name"),
        "type": raw.get("type"),
        "typecode": raw.get("typecode"),
        "province": raw.get("pname"),
        "city": raw.get("cityname"),
        "district": raw.get("adname"),
        "address": raw.get("address"),
        "latitude": lat,
        "longitude": lng,
        "business_area": raw.get("business_area"),
        "rating": biz_ext.get("rating"),
        "cost": biz_ext.get("cost"),
        "photo_count": photo_count,
        "tags": tags,
        "raw_type": type(raw).__name__,
    }


def poi_key(item: dict[str, Any]) -> str:
    if item.get("source_id"):
        return f"amap:{item['source_id']}"
    return "|".join(
        str(item.get(field) or "")
        for field in ["name", "city", "district", "address", "latitude", "longitude"]
    )


def collect_city_keyword(
    *,
    api_key: str,
    city: str,
    keyword: str,
    limit: int,
    sleep_seconds: float,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page = 1
    offset = 20
    while len(items) < limit:
        data = amap_get(
            {
                "key": api_key,
                "keywords": keyword,
                "city": city,
                "citylimit": "true",
                "offset": offset,
                "page": page,
                "extensions": "all",
            }
        )
        pois = data.get("pois") or []
        if not isinstance(pois, list) or not pois:
            break

        for raw in pois:
            if isinstance(raw, dict):
                items.append(normalize_poi(raw, city, keyword))
                if len(items) >= limit:
                    break

        if len(pois) < offset:
            break
        page += 1
        time.sleep(sleep_seconds)
    return items


def main() -> None:
    load_local_env()
    parser = argparse.ArgumentParser(description="Collect AMap POI candidates into private data.")
    parser.add_argument("--cities", required=True, help="Comma-separated city names or adcodes.")
    parser.add_argument("--keywords", default=None, help="Comma-separated keywords.")
    parser.add_argument("--limit-per-keyword", type=int, default=80)
    parser.add_argument("--sleep", type=float, default=0.25, help="Seconds between paged requests.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    api_key = os.getenv("AMAP_API_KEY") or os.getenv("VITE_AMAP_KEY")
    if not api_key:
        raise SystemExit("AMAP_API_KEY is missing. Put it in backend/.env or export it locally.")

    cities = split_csv(args.cities, [])
    keywords = split_csv(args.keywords, DEFAULT_KEYWORDS)
    output_dir = args.output_dir.expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    all_items: list[dict[str, Any]] = []
    stats: list[dict[str, Any]] = []
    for city in cities:
        for keyword in keywords:
            print(f"[collect] city={city} keyword={keyword} limit={args.limit_per_keyword}")
            try:
                items = collect_city_keyword(
                    api_key=api_key,
                    city=city,
                    keyword=keyword,
                    limit=args.limit_per_keyword,
                    sleep_seconds=args.sleep,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"  failed: {exc}")
                stats.append({"city": city, "keyword": keyword, "count": 0, "error": str(exc)})
                continue
            print(f"  got {len(items)}")
            stats.append({"city": city, "keyword": keyword, "count": len(items)})
            all_items.extend(items)
            time.sleep(args.sleep)

    deduped: dict[str, dict[str, Any]] = {}
    for item in all_items:
        key = poi_key(item)
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = item
        else:
            existing_tags = set(existing.get("tags") or [])
            existing_tags.update(item.get("tags") or [])
            existing["tags"] = sorted(existing_tags)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    payload = {
        "source": "amap_place_text",
        "collected_at": datetime.now().isoformat(),
        "cities": cities,
        "keywords": keywords,
        "raw_count": len(all_items),
        "deduped_count": len(deduped),
        "stats": stats,
        "items": list(deduped.values()),
    }

    output_file = output_dir / f"poi_candidates_{timestamp}.json"
    latest_file = output_dir / "poi_candidates_latest.json"
    for path in [output_file, latest_file]:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 60)
    print(f"raw_count={len(all_items)}")
    print(f"deduped_count={len(deduped)}")
    print(f"output={output_file}")
    print(f"latest={latest_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
