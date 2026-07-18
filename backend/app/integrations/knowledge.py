from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from app.integrations.media_images import ImageLookup, WikimediaImageLookup
from app.schemas.planning import (
    DestinationItem,
    DestinationRecommendationPayload,
    DestinationRecommendationRequest,
    ImageResource,
    MediaPlaceholderGroup,
    MediaPlaceholderPayload,
    MediaPlaceholderRequest,
    RouteDayPlan,
    RouteGenerationPayload,
    RouteGenerationRequest,
    RouteOption,
    RouteSpot,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_KNOWLEDGE_DIR = (
    REPO_ROOT.parent / f"{REPO_ROOT.name}_private_data" / "processed" / "knowledge"
)

CATEGORY_LABELS = {
    "photo_spot": "高出片机位",
    "museum": "博物馆/展馆",
    "culture": "人文古迹",
    "nature": "自然风光",
    "citywalk": "城市漫步",
    "attraction": "经典景点",
}

POI_FAMILY_SUFFIXES = (
    "国家森林公园",
    "森林公园",
    "风景名胜区",
    "风景区",
    "旅游区",
    "景区",
    "观景台",
)

INTEREST_CATEGORY_HINTS = {
    "拍照": {"photo_spot"},
    "摄影": {"photo_spot"},
    "出片": {"photo_spot"},
    "机位": {"photo_spot"},
    "自然": {"nature"},
    "山": {"nature"},
    "海": {"nature"},
    "湖": {"nature"},
    "徒步": {"nature"},
    "人文": {"culture", "museum", "citywalk"},
    "历史": {"culture", "museum"},
    "文化": {"culture", "museum"},
    "博物馆": {"museum"},
    "展览": {"museum"},
    "citywalk": {"citywalk"},
    "城市": {"citywalk"},
    "街区": {"citywalk"},
    "古镇": {"culture", "citywalk"},
    "亲子": {"museum", "nature", "attraction"},
    "美食": {"citywalk"},
}

SNOW_MOUNTAIN_TERMS = ("雪山", "冰川", "雪峰", "雪域", "滑雪", "高山")

TIME_SLOTS = {
    "relaxed": ["09:30", "12:00", "15:00", "17:30"],
    "balanced": ["09:00", "11:30", "14:30", "17:00"],
    "compact": ["08:30", "10:30", "13:30", "16:30"],
}
ROUTE_REAL_IMAGE_LIMIT = 12


def _load_items(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload.get("items") or [])


def _slug(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())[:40] or "unknown"


def _poi_family(name: str, city: str) -> str:
    original = name.strip()
    value = original.replace(city, "", 1).strip() if city else original
    for separator in ("-", "—", "·", "（", "("):
        value = value.split(separator, 1)[0].strip()

    for marker in ("国家森林公园", "森林公园"):
        if marker in value:
            prefix = value.split(marker, 1)[0].strip()
            if len(prefix) >= 2:
                return prefix

    mountain_index = value.find("山")
    if mountain_index >= 1 and any(
        marker in value[mountain_index + 1 :]
        for marker in ("公园", "景区", "寺", "索道", "栈道", "峡", "观景")
    ):
        return value[: mountain_index + 1]

    for suffix in POI_FAMILY_SUFFIXES:
        if value.endswith(suffix) and len(value) > len(suffix) + 1:
            value = value[: -len(suffix)].strip()
            break
    return value or original


def _family_conflicts(family: str, families: set[str]) -> bool:
    if family in families:
        return True
    if len(family) >= 3:
        return any(
            (other.startswith(family) or family.startswith(other))
            for other in families
            if len(other) >= 3
        )
    if len(family) == 2:
        return f"{family}山" in families or any(f"{other}山" == family for other in families)
    return False


def _float(value: Any) -> float | None:
    if value in (None, "", []):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round_score(value: float) -> int:
    return max(60, min(98, round(value)))


def _budget_range(city: str, duration_days: int) -> str:
    premium = {"北京", "上海", "深圳", "杭州", "厦门", "三亚", "阿坝", "甘孜"}
    popular = {"成都", "重庆", "广州", "南京", "苏州", "青岛", "大理", "丽江"}
    if city in premium:
        low, high = 650, 1200
    elif city in popular:
        low, high = 520, 980
    else:
        low, high = 420, 850
    return f"{low * duration_days}-{high * duration_days} RMB"


def _season_text(city: str, requested: str | None) -> str:
    if requested:
        return f"{requested}可去，出发前建议复核天气"
    if city in {"万宁", "三亚", "海口", "琼海", "厦门", "珠海", "舟山"}:
        return "10 月到次年 4 月更舒适，夏季注意台风和暴晒"
    if city in {"阿坝", "甘孜", "张家界", "黄山", "九江"}:
        return "春秋景观稳定，夏季适合避暑，冬季注意交通"
    return "春秋最稳，周末短途和 3-5 天深度游都适合"


def _image_resource(
    *,
    category: str,
    title: str,
    subtitle: str,
    tags: list[str] | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> ImageResource:
    params = {
        "title": title,
        "subtitle": subtitle,
        "category": category,
    }
    if tags:
        params["tags"] = " · ".join(tags[:3])
    if latitude is not None and longitude is not None:
        params["lat"] = f"{latitude:.5f}"
        params["lng"] = f"{longitude:.5f}"
    query = urlencode(params)
    url = f"/api/v1/media/place-card.svg?{query}"
    return ImageResource(
        category=category,
        url=url,
        thumbnail_url=url,
        alt=f"{title} - {subtitle}",
        provider="lv-local-card",
        placeholder=False,
    )


def _real_or_card_image_resource(
    *,
    image_lookup: ImageLookup | None,
    query: str,
    category: str,
    title: str,
    subtitle: str,
    tags: list[str] | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> ImageResource:
    if image_lookup:
        image = image_lookup.find(
            query=query,
            category=category,
            alt=f"{title} - {subtitle}",
        )
        if image:
            return image
    return _image_resource(
        category=category,
        title=title,
        subtitle=subtitle,
        tags=tags,
        latitude=latitude,
        longitude=longitude,
    )


@dataclass(slots=True)
class CitySummary:
    name: str
    province: str
    poi_count: int
    photo_count: int
    avg_quality: float
    category_counts: Counter[str]
    top_tags: list[str]
    top_pois: list[dict[str, Any]]
    top_photo_pois: list[dict[str, Any]]
    latitude: float | None
    longitude: float | None


class KnowledgeStore:
    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.data_dir = Path(data_dir).expanduser() if data_dir else DEFAULT_KNOWLEDGE_DIR
        self.pois = _load_items(self.data_dir / "pois_latest.json")
        self.photo_spots = _load_items(self.data_dir / "photo_spots_latest.json")
        self.route_templates = _load_items(self.data_dir / "route_templates_latest.json")
        self._pois_by_city: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._templates_by_city: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for poi in self.pois:
            self._pois_by_city[str(poi.get("destination_name") or "")].append(poi)
        for template in self.route_templates:
            self._templates_by_city[str(template.get("destination_name") or "")].append(template)
        for city in self._pois_by_city:
            self._pois_by_city[city].sort(
                key=lambda x: _float(x.get("quality_score")) or 0,
                reverse=True,
            )

    @property
    def available(self) -> bool:
        return bool(self.pois and self._pois_by_city)

    @property
    def city_count(self) -> int:
        return len(self._pois_by_city)

    @property
    def poi_count(self) -> int:
        return len(self.pois)

    def resolve_city(self, value: str | None) -> str | None:
        if not value:
            return None
        candidate = value.strip()
        if candidate in self._pois_by_city:
            return candidate
        stripped = candidate.removesuffix("市").removesuffix("地区").removesuffix("州")
        if stripped in self._pois_by_city:
            return stripped
        for city in self._pois_by_city:
            if city in candidate or candidate in city:
                return city
        return None

    def city_pois(self, city: str) -> list[dict[str, Any]]:
        return list(self._pois_by_city.get(city) or [])

    def city_templates(self, city: str) -> list[dict[str, Any]]:
        return list(self._templates_by_city.get(city) or [])

    def summaries(self) -> list[CitySummary]:
        summaries: list[CitySummary] = []
        for city, pois in self._pois_by_city.items():
            if not pois:
                continue
            province = str(pois[0].get("province") or "中国")
            category_counts = Counter(str(p.get("category") or "attraction") for p in pois)
            tags = Counter(
                str(tag)
                for p in pois[:50]
                for tag in (p.get("tags") or [])
                if str(tag) not in {"景点", "风景名胜", "旅游景点"}
            )
            latitudes = [_float(p.get("latitude")) for p in pois]
            longitudes = [_float(p.get("longitude")) for p in pois]
            valid_latitudes = [value for value in latitudes if value is not None]
            valid_longitudes = [value for value in longitudes if value is not None]
            qualities = [_float(p.get("quality_score")) or 0.5 for p in pois]
            summaries.append(
                CitySummary(
                    name=city,
                    province=province,
                    poi_count=len(pois),
                    photo_count=category_counts["photo_spot"],
                    avg_quality=sum(qualities) / len(qualities),
                    category_counts=category_counts,
                    top_tags=[tag for tag, _ in tags.most_common(8)],
                    top_pois=pois[:8],
                    top_photo_pois=[
                        p for p in pois if str(p.get("category")) == "photo_spot"
                    ][:6],
                    latitude=(
                        sum(valid_latitudes) / len(valid_latitudes)
                        if valid_latitudes
                        else None
                    ),
                    longitude=(
                        sum(valid_longitudes) / len(valid_longitudes)
                        if valid_longitudes
                        else None
                    ),
                )
            )
        return summaries


class KnowledgeRecommendationIntegration:
    def __init__(
        self,
        data_dir: str | Path | None = None,
        *,
        real_images_enabled: bool = False,
        image_lookup: ImageLookup | None = None,
    ) -> None:
        self.store = KnowledgeStore(data_dir)
        self.image_lookup = image_lookup or (
            WikimediaImageLookup() if real_images_enabled else None
        )
        self._remaining_route_real_images = ROUTE_REAL_IMAGE_LIMIT

    def recommend(
        self,
        request: DestinationRecommendationRequest,
    ) -> DestinationRecommendationPayload:
        if not self.store.available:
            return DestinationRecommendationPayload(
                query_summary="本地知识库暂不可用，请先生成或挂载私有知识种子。",
                destinations=[],
            )

        desired_categories = self._desired_categories(request)
        target_cities = self._target_cities(request)
        excluded_cities = self._excluded_cities(request)
        summaries = [
            summary
            for summary in self.store.summaries()
            if summary.name not in excluded_cities
        ]
        ranked = sorted(
            summaries,
            key=lambda item: self._score_city(
                item,
                desired_categories,
                request,
                target_cities,
            ),
            reverse=True,
        )[:6]

        destinations = [
            self._to_destination_item(summary, request, desired_categories, target_cities)
            for summary in ranked
        ]
        interests = request.interests or ["自然", "拍照", "城市漫步"]
        summary_parts = [
            f"基于本地知识库 {self.store.city_count} 城、{self.store.poi_count} 个真实 POI "
            f"匹配：{request.duration_days} 天，兴趣 {'/'.join(interests[:4])}"
        ]
        if target_cities:
            summary_parts.append(f"明确目的地：{'/'.join(sorted(target_cities))}")
        if excluded_cities:
            summary_parts.append(f"已排除已浏览目的地 {len(excluded_cities)} 个")
        summary = "；".join(summary_parts)
        return DestinationRecommendationPayload(query_summary=summary, destinations=destinations)

    def _recommendation_text(self, request: DestinationRecommendationRequest) -> str:
        return " ".join([*request.interests, *request.travel_style]).lower()

    def _target_cities(self, request: DestinationRecommendationRequest) -> set[str]:
        text = self._recommendation_text(request).replace(" ", "")
        if not text:
            return set()

        targets: set[str] = set()
        for city in self.store._pois_by_city:
            city_lower = city.lower()
            if len(city) >= 2 and (
                city_lower in text
                or f"{city_lower}市" in text
                or f"{city_lower}地区" in text
                or f"{city_lower}州" in text
            ):
                targets.add(city)
        for value in [*request.interests, *request.travel_style]:
            resolved = self.store.resolve_city(value)
            if resolved:
                targets.add(resolved)
        return targets

    def _excluded_cities(self, request: DestinationRecommendationRequest) -> set[str]:
        excluded: set[str] = set()
        for value in request.exclude_destination_names:
            resolved = self.store.resolve_city(value)
            if resolved:
                excluded.add(resolved)
                continue
            candidate = value.strip().removesuffix("市").removesuffix("地区").removesuffix("州")
            if candidate:
                excluded.add(candidate)
        return excluded

    def _desired_categories(
        self,
        request: DestinationRecommendationRequest,
    ) -> set[str]:
        desired: set[str] = set()
        text_items = [*request.interests, *request.travel_style]
        for text in text_items:
            lower = text.lower()
            for hint, categories in INTEREST_CATEGORY_HINTS.items():
                if hint.lower() in lower:
                    desired.update(categories)
        if not desired:
            desired.update({"photo_spot", "nature", "citywalk"})
        return desired

    def _score_city(
        self,
        summary: CitySummary,
        desired_categories: set[str],
        request: DestinationRecommendationRequest,
        target_cities: set[str],
    ) -> float:
        category_total = sum(summary.category_counts.values()) or 1
        interest_count = sum(summary.category_counts[c] for c in desired_categories)
        interest_ratio = interest_count / category_total
        photo_ratio = summary.photo_count / max(summary.poi_count, 1)
        scale_score = min(summary.poi_count / 70, 1.0)
        duration_fit = 1 - min(abs(summary.poi_count / 18 - request.duration_days) / 10, 0.25)
        return (
            summary.avg_quality * 45
            + interest_ratio * 26
            + photo_ratio * 12
            + scale_score * 10
            + duration_fit * 7
            + self._intent_boost(summary, request, target_cities)
        )

    def _intent_boost(
        self,
        summary: CitySummary,
        request: DestinationRecommendationRequest,
        target_cities: set[str],
    ) -> float:
        boost = 0.0
        if summary.name in target_cities:
            boost += 130

        request_text = self._recommendation_text(request)
        requested_snow_terms = [
            term for term in SNOW_MOUNTAIN_TERMS if term.lower() in request_text
        ]
        if requested_snow_terms:
            city_text = self._city_keyword_text(summary)
            matched_terms = [term for term in requested_snow_terms if term in city_text]
            if matched_terms:
                boost += 72 + min(len(matched_terms) * 8, 24)
            elif "雪山" in request_text and any(
                term in city_text for term in ("冰川", "雪峰", "雪域")
            ):
                boost += 56

        return boost

    def _city_keyword_text(self, summary: CitySummary) -> str:
        parts = [summary.name, summary.province, *summary.top_tags]
        for poi in self.store.city_pois(summary.name):
            parts.extend(
                [
                    str(poi.get("name") or ""),
                    str(poi.get("category") or ""),
                    " ".join(str(tag) for tag in (poi.get("tags") or [])),
                ],
            )
        return " ".join(parts)

    def _to_destination_item(
        self,
        summary: CitySummary,
        request: DestinationRecommendationRequest,
        desired_categories: set[str],
        target_cities: set[str],
    ) -> DestinationItem:
        score = self._score_city(summary, desired_categories, request, target_cities)
        top_names = [p["name"] for p in summary.top_pois[:3]]
        photo_text = (
            f"{summary.photo_count} 个机位候选"
            if summary.photo_count
            else "以经典景点和城市漫步为主"
        )
        tags = [
            CATEGORY_LABELS.get(category, category)
            for category, _ in summary.category_counts.most_common(3)
        ]
        tags.extend(tag for tag in summary.top_tags if tag not in tags)
        tags = tags[:6]
        reasons = [
            f"知识库已覆盖 {summary.poi_count} 个可用地点，含 {photo_text}",
            f"代表点：{'、'.join(top_names)}",
            f"适合 {request.duration_days} 天做 {'/'.join(tags[:3])} 主题组合",
        ]
        hero = _real_or_card_image_resource(
            image_lookup=self.image_lookup,
            query=summary.name,
            category="destination",
            title=summary.name,
            subtitle=f"{summary.province} · {summary.poi_count} POI · {photo_text}",
            tags=tags,
            latitude=summary.latitude,
            longitude=summary.longitude,
        )
        gallery = [
            _image_resource(
                category=str(p.get("category") or "spot"),
                title=str(p.get("name") or summary.name),
                subtitle=CATEGORY_LABELS.get(str(p.get("category")), "旅行地点"),
                tags=[str(tag) for tag in (p.get("tags") or [])],
                latitude=_float(p.get("latitude")),
                longitude=_float(p.get("longitude")),
            )
            for p in summary.top_pois[:4]
        ]
        return DestinationItem(
            id=f"city-{_slug(summary.name)}",
            name=summary.name,
            country_or_region=f"中国 · {summary.province}",
            match_score=_round_score(score + 15),
            budget_range=_budget_range(summary.name, request.duration_days),
            best_season=_season_text(summary.name, request.season),
            vibe_tags=tags,
            reasons=reasons,
            hero_image=hero,
            gallery=gallery,
        )


class KnowledgeRoutePlannerIntegration:
    def __init__(
        self,
        data_dir: str | Path | None = None,
        *,
        real_images_enabled: bool = False,
        image_lookup: ImageLookup | None = None,
    ) -> None:
        self.store = KnowledgeStore(data_dir)
        self.image_lookup = image_lookup or (
            WikimediaImageLookup() if real_images_enabled else None
        )

    def generate_plan(
        self,
        request: RouteGenerationRequest,
    ) -> RouteGenerationPayload:
        city = self.store.resolve_city(request.destination_name)
        if not city:
            return RouteGenerationPayload(destination_name=request.destination_name, options=[])
        pois = self.store.city_pois(city)
        if not pois:
            return RouteGenerationPayload(destination_name=request.destination_name, options=[])
        self._remaining_route_real_images = ROUTE_REAL_IMAGE_LIMIT

        first_timer_option = self._build_option(
            city=city,
            request=request,
            route_id="knowledge-first-timer",
            title=f"{city}经典初访覆盖线",
            pace=request.pace or "balanced",
            categories={"attraction", "culture", "museum", "nature", "photo_spot"},
            spots_per_day=4,
            audience="第一次来或旅行次数不多，想稳妥覆盖经典点位的人",
            focus_text="经典景点、自然风光、高出片机位",
        )
        first_timer_names = {
            spot.name
            for day in first_timer_option.days
            for spot in day.spots
        }
        repeat_visitor_option = self._build_option(
            city=city,
            request=request,
            route_id="knowledge-repeat-visitor",
            title=f"{city}复访深度出片线",
            pace="relaxed",
            categories={"photo_spot", "citywalk", "nature", "culture"},
            spots_per_day=3,
            audience="已经来过或旅行经验较多，想找更小众机位和慢节奏体验的人",
            focus_text="小众机位、城市漫步、深度体验",
            exclude_names=first_timer_names,
        )
        options = [first_timer_option, repeat_visitor_option]
        options = [option for option in options if option.days]
        return RouteGenerationPayload(destination_name=city, options=options)

    def _build_option(
        self,
        *,
        city: str,
        request: RouteGenerationRequest,
        route_id: str,
        title: str,
        pace: str,
        categories: set[str],
        spots_per_day: int,
        audience: str,
        focus_text: str,
        exclude_names: set[str] | None = None,
    ) -> RouteOption:
        pois = self._select_pois(
            city,
            categories,
            request.duration_days * spots_per_day,
            exclude_names=exclude_names,
        )
        days: list[RouteDayPlan] = []
        for day_index in range(request.duration_days):
            chunk = pois[day_index * spots_per_day : (day_index + 1) * spots_per_day]
            if not chunk:
                break
            days.append(self._build_day(city, day_index + 1, chunk, pace))

        photo_scores = [
            _float(p.get("quality_score")) or 0.75
            for p in pois
            if str(p.get("category")) == "photo_spot"
        ]
        avg_photo = sum(photo_scores) / len(photo_scores) if photo_scores else 0.78
        return RouteOption(
            id=route_id,
            title=title,
            pace=pace,
            estimated_budget=_budget_range(city, request.duration_days),
            photo_score=round(min(avg_photo * 10, 9.8), 1),
            summary=(
                f"适合{audience}。基于 {city} 本地知识库真实 POI 生成，优先组合"
                f"{focus_text}。"
            ),
            days=days,
        )

    def _select_pois(
        self,
        city: str,
        categories: set[str],
        limit: int,
        exclude_names: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        pois = self.store.city_pois(city)
        excluded_names = exclude_names or set()
        excluded_families = {
            _poi_family(name, city)
            for name in excluded_names
        }
        selected: list[dict[str, Any]] = []
        selected_families: set[str] = set()

        def append_candidates(
            candidates: list[dict[str, Any]],
            *,
            allow_excluded: bool = False,
            allow_same_family: bool = False,
        ) -> None:
            for poi in candidates:
                if len(selected) >= limit:
                    return
                name = str(poi.get("name") or "")
                family = _poi_family(name, city)
                if poi in selected:
                    continue
                if not allow_excluded and (
                    name in excluded_names
                    or _family_conflicts(family, excluded_families)
                ):
                    continue
                if not allow_same_family and _family_conflicts(
                    family,
                    selected_families,
                ):
                    continue
                selected.append(poi)
                selected_families.add(family)

        append_candidates(
            [p for p in pois if str(p.get("category")) in categories],
        )
        if len(selected) < limit:
            append_candidates(pois)
        if len(selected) < limit:
            append_candidates(pois, allow_same_family=True)
        if len(selected) < limit:
            append_candidates(pois, allow_excluded=True, allow_same_family=True)
        return selected[:limit]

    def _build_day(
        self,
        city: str,
        day: int,
        pois: list[dict[str, Any]],
        pace: str,
    ) -> RouteDayPlan:
        theme_tags = [
            CATEGORY_LABELS.get(str(p.get("category")), "旅行地点")
            for p in pois[:2]
        ]
        slots = TIME_SLOTS.get(pace, TIME_SLOTS["balanced"])
        spots: list[RouteSpot] = []
        for index, poi in enumerate(pois):
            category = str(poi.get("category") or "attraction")
            minutes = int(poi.get("recommended_duration_minutes") or 90)
            rating = _float(poi.get("rating"))
            rating_text = f"；高德评分 {rating:.1f}" if rating else ""
            address = str(poi.get("address") or "地址待复核")
            latitude = _float(poi.get("latitude"))
            longitude = _float(poi.get("longitude"))
            spots.append(
                RouteSpot(
                    time_slot=slots[min(index, len(slots) - 1)],
                    name=str(poi.get("name") or "未命名地点"),
                    description=(
                        f"{CATEGORY_LABELS.get(category, '旅行地点')}，{address}"
                        f"；建议停留约 {minutes} 分钟{rating_text}。"
                    ),
                    suggested_duration_hours=round(minutes / 60, 1),
                    category=category,
                    address=address,
                    latitude=latitude,
                    longitude=longitude,
                    images=[
                        _real_or_card_image_resource(
                            image_lookup=self._route_image_lookup(),
                            query=f"{poi.get('name') or '旅行地点'} {city}",
                            category=category,
                            title=str(poi.get("name") or "旅行地点"),
                            subtitle=address,
                            tags=[str(tag) for tag in (poi.get("tags") or [])],
                            latitude=latitude,
                            longitude=longitude,
                        )
                    ],
                )
            )
        return RouteDayPlan(
            day=day,
            theme=f"D{day} · {' + '.join(theme_tags)}",
            commute_tip="本日地点来自真实 POI 坐标，出发前建议用地图复核实时交通。",
            spots=spots,
        )

    def _route_image_lookup(self) -> ImageLookup | None:
        if not self.image_lookup or self._remaining_route_real_images <= 0:
            return None
        self._remaining_route_real_images -= 1
        return self.image_lookup


class LocalMediaAssetIntegration:
    def placeholders(
        self,
        request: MediaPlaceholderRequest,
    ) -> MediaPlaceholderPayload:
        categories = request.categories or ["destination", "viewpoint", "outfit"]
        destination = request.destination_name or "旅图目的地"
        assets = [
            MediaPlaceholderGroup(
                category=category,
                items=[
                    _image_resource(
                        category=category,
                        title=destination,
                        subtitle=f"{category} · {keyword or '旅行灵感'}",
                        tags=request.keywords,
                    )
                    for keyword in (request.keywords[:2] or ["推荐图卡", "地图图卡"])
                ],
            )
            for category in categories
        ]
        return MediaPlaceholderPayload(destination_name=request.destination_name, assets=assets)
