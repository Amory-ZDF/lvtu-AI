from __future__ import annotations

import math
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.responses import success_response
from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.middleware.auth import get_current_user, get_current_user_optional
from app.models.analytics_event import AnalyticsEvent
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsDashboardPayload,
    AnalyticsDurationBucket,
    AnalyticsEventCreate,
    AnalyticsEventMetric,
    AnalyticsFunnelStep,
    AnalyticsIngestRequest,
    AnalyticsIngestResponse,
    AnalyticsPageButtonMetric,
    AnalyticsPageStay,
    AnalyticsSelectionGroup,
    AnalyticsSelectionOption,
)
from app.schemas.common import ApiResponse
from app.services.analytics_admin_service import ensure_analytics_admin

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_db_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
CurrentUserOptional = Annotated[User | None, Depends(get_current_user_optional)]
CurrentUser = Annotated[User, Depends(get_current_user)]

ANALYTICS_TIMEZONE = "Asia/Shanghai"
_SHANGHAI_TZ = ZoneInfo(ANALYTICS_TIMEZONE)
_DURATION_BUCKETS = [
    ("<3s", 0, 3_000),
    ("3-10s", 3_000, 10_000),
    ("10-30s", 10_000, 30_000),
    ("30-60s", 30_000, 60_000),
    ("1-3min", 60_000, 180_000),
    (">3min", 180_000, None),
]
_KEY_CTA_KEYWORDS = (
    "开始",
    "生成",
    "选择",
    "确认",
    "创建",
    "登录",
    "进入数据中台",
    "生成预览",
)


def _clean_metadata(value: dict) -> dict:
    cleaned = dict(value or {})
    for key in list(cleaned):
        if key.lower() in {"password", "token", "authorization", "api_key", "secret"}:
            cleaned.pop(key, None)
    return cleaned


def _analytics_event_from_payload(
    payload: AnalyticsEventCreate,
    *,
    user_id,
) -> AnalyticsEvent:
    return AnalyticsEvent(
        user_id=user_id,
        visitor_id=payload.visitor_id,
        session_id=payload.session_id,
        event_name=payload.event_name,
        event_category=payload.event_category,
        page_path=payload.page_path,
        page_title=payload.page_title,
        referrer=payload.referrer,
        element_text=payload.element_text,
        element_role=payload.element_role,
        element_id=payload.element_id,
        target_url=payload.target_url,
        duration_ms=payload.duration_ms,
        viewport_width=payload.viewport_width,
        viewport_height=payload.viewport_height,
        device_type=payload.device_type,
        user_agent=payload.user_agent,
        metadata_=_clean_metadata(payload.metadata),
        occurred_at=payload.occurred_at or datetime.now(UTC),
    )


def _actor_key(event: AnalyticsEvent) -> str:
    if event.user_id:
        return f"user:{event.user_id}"
    if event.visitor_id:
        return f"visitor:{event.visitor_id}"
    return f"session:{event.session_id}"


def _avg(values: list[int | float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def _median(values: list[int | float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return round(float(ordered[mid]), 2)
    return round((ordered[mid - 1] + ordered[mid]) / 2, 2)


def _percentile(values: list[int | float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return round(ordered[0], 2)
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return round(ordered[lower], 2)
    weight = position - lower
    return round(ordered[lower] * (1 - weight) + ordered[upper] * weight, 2)


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _metadata(event: AnalyticsEvent) -> dict[str, Any]:
    return event.metadata_ or {}


def _metadata_text(event: AnalyticsEvent, keys: list[str]) -> str | None:
    metadata = _metadata(event)
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _page_title_by_path(events: list[AnalyticsEvent]) -> dict[str, str]:
    titles: dict[str, str] = {}
    for event in events:
        if event.page_title and event.page_path not in titles:
            titles[event.page_path] = event.page_title
    return titles


def _module_for_event(event: AnalyticsEvent) -> str:
    metadata = _metadata(event)
    module = metadata.get("module")
    if isinstance(module, str) and module.strip():
        return module.strip()[:64]
    path = event.page_path or "/"
    if path == "/":
        return "home"
    if path.startswith("/start"):
        return "preference"
    if path.startswith("/destinations"):
        return "destination"
    if path.startswith("/comparison"):
        return "route_comparison"
    if path.startswith("/trips/"):
        tab = metadata.get("tab")
        if isinstance(tab, str) and tab.strip():
            return f"trip_{tab.strip()[:32]}"
        return "trip_detail"
    if path.startswith("/data-center"):
        return "data_center"
    if path.startswith("/login"):
        return "auth"
    return "other"


def _budget_label(metadata: dict[str, Any]) -> str | None:
    explicit = metadata.get("budget_label")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    min_value = metadata.get("budget_min")
    max_value = metadata.get("budget_max")
    if isinstance(min_value, int) and isinstance(max_value, int):
        return f"{min_value}-{max_value} 元"
    if isinstance(max_value, int):
        return f"≤{max_value} 元"
    return None


def _duration_buckets(values: list[int | float]) -> list[AnalyticsDurationBucket]:
    total = len(values)
    buckets: list[AnalyticsDurationBucket] = []
    for label, lower, upper in _DURATION_BUCKETS:
        count = sum(
            1
            for value in values
            if value >= lower and (upper is None or value < upper)
        )
        buckets.append(
            AnalyticsDurationBucket(
                label=label,
                count=count,
                ratio=_ratio(count, total),
            )
        )
    return buckets


def _is_key_cta(label: str, event: AnalyticsEvent | None) -> bool:
    if any(keyword in label for keyword in _KEY_CTA_KEYWORDS):
        return True
    if event is None:
        return False
    return event.event_name in {
        "destination_recommendation_success",
        "destination_selected",
        "route_option_confirmed",
        "trip_created",
        "outfit_preview_generated",
    }


@router.post("/events", response_model=ApiResponse[AnalyticsIngestResponse])
def ingest_analytics_events(
    payload: AnalyticsIngestRequest,
    request: Request,
    db: SessionDep,
    settings: SettingsDep,
    current_user: CurrentUserOptional,
) -> ApiResponse[AnalyticsIngestResponse]:
    if not settings.analytics_enabled:
        return success_response(AnalyticsIngestResponse(accepted=0), request)

    user_id = current_user.id if current_user else None
    events = [
        _analytics_event_from_payload(event, user_id=user_id)
        for event in payload.events
    ]
    db.add_all(events)
    db.commit()
    return success_response(AnalyticsIngestResponse(accepted=len(events)), request)


@router.get("/dashboard", response_model=ApiResponse[AnalyticsDashboardPayload])
def get_analytics_dashboard(
    request: Request,
    db: SessionDep,
    settings: SettingsDep,
    current_user: CurrentUser,
    days: int = Query(default=7, ge=0, le=365),
) -> ApiResponse[AnalyticsDashboardPayload]:
    ensure_analytics_admin(current_user, settings, db)
    now = datetime.now(_SHANGHAI_TZ)
    stmt = select(AnalyticsEvent).order_by(AnalyticsEvent.occurred_at.asc())
    range_label = "全部"
    if days > 0:
        start = (now - timedelta(days=days)).astimezone(UTC)
        stmt = stmt.where(AnalyticsEvent.occurred_at >= start)
        range_label = f"近 {days} 天"
    events = list(db.scalars(stmt))

    page_views = [event for event in events if event.event_name == "page_view"]
    click_events = [event for event in events if event.event_category == "click"]
    page_titles = _page_title_by_path(events)

    funnel_definitions = [
        ("home_view", "访问首页", lambda e: e.event_name == "page_view" and e.page_path == "/"),
        (
            "start_view",
            "进入偏好输入页",
            lambda e: e.event_name == "page_view" and e.page_path == "/start",
        ),
        (
            "destination_success",
            "生成目的地推荐",
            lambda e: e.event_name == "destination_recommendation_success",
        ),
        (
            "destinations_view",
            "查看目的地推荐页",
            lambda e: e.event_name == "page_view" and e.page_path == "/destinations",
        ),
        (
            "destination_selected",
            "选择目的地",
            lambda e: e.event_name == "destination_selected",
        ),
        ("route_success", "生成路线方案", lambda e: e.event_name == "route_generation_success"),
        (
            "comparison_view",
            "查看路线对比页",
            lambda e: e.event_name == "page_view" and e.page_path == "/comparison",
        ),
        (
            "route_selected",
            "点击路线方案",
            lambda e: e.event_name == "route_option_selected",
        ),
        (
            "route_confirmed",
            "确认路线方案",
            lambda e: e.event_name in {"route_option_confirmed", "trip_created"},
        ),
        (
            "trip_detail_view",
            "进入行程详情",
            lambda e: e.event_name == "page_view" and e.page_path.startswith("/trips/"),
        ),
        ("map_view", "查看地图", lambda e: e.event_name == "map_viewed"),
        ("weather_view", "查看天气", lambda e: e.event_name == "weather_loaded"),
        (
            "outfit_view",
            "查看穿搭",
            lambda e: e.event_name in {"trip_tab_view", "outfit_detail_view"}
            and _metadata(e).get("tab") == "outfit",
        ),
        (
            "spot_view",
            "查看机位",
            lambda e: e.event_name in {"trip_tab_view", "photo_spot_detail_view"}
            and _metadata(e).get("tab") == "spots",
        ),
        (
            "packing_view",
            "查看打包",
            lambda e: e.event_name == "trip_tab_view" and _metadata(e).get("tab") == "packing",
        ),
        (
            "outfit_preview",
            "生成穿搭预览",
            lambda e: e.event_name == "outfit_preview_generated",
        ),
        (
            "itinerary_adjustment",
            "自然语言调整行程",
            lambda e: e.event_name == "itinerary_adjustment_success",
        ),
        (
            "autosave",
            "保存行程编辑",
            lambda e: e.event_name == "trip_point_autosaved",
        ),
    ]
    first_users = 0
    previous_users = 0
    funnel: list[AnalyticsFunnelStep] = []
    for key, label, predicate in funnel_definitions:
        users = {_actor_key(event) for event in events if predicate(event)}
        sessions = {event.session_id for event in events if predicate(event)}
        if not funnel:
            first_users = len(users)
            previous_users = len(users)
        current_users = len(users)
        current_sessions = len(sessions)
        previous_rate = 1.0 if not funnel else _ratio(current_users, previous_users)
        dropoff_rate = max(0.0, round(1 - previous_rate, 4))
        funnel.append(
            AnalyticsFunnelStep(
                key=key,
                label=label,
                users=current_users,
                sessions=current_sessions,
                previous_step_rate=previous_rate,
                overall_rate=_ratio(current_users, first_users),
                dropoff_users=max(previous_users - current_users, 0),
                dropoff_rate=dropoff_rate,
            )
        )
        previous_users = current_users

    session_page_views: dict[str, list[AnalyticsEvent]] = defaultdict(list)
    session_events: dict[str, list[AnalyticsEvent]] = defaultdict(list)
    for event in events:
        session_events[event.session_id].append(event)
        if event.event_name == "page_view":
            session_page_views[event.session_id].append(event)

    bounce_by_page: Counter[str] = Counter()
    exit_by_page: Counter[str] = Counter()
    for session_id, views in session_page_views.items():
        if not views:
            continue
        landing_page = views[0].page_path
        exit_by_page[views[-1].page_path] += 1
        has_interaction = any(
            event.event_category in {"click", "conversion", "selection", "form"}
            for event in session_events.get(session_id, [])
        )
        if len(views) == 1 and not has_interaction:
            bounce_by_page[landing_page] += 1

    page_stats: dict[str, dict[str, object]] = defaultdict(
        lambda: {"views": 0, "visitors": set(), "sessions": set(), "durations": []}
    )
    for event in events:
        stats = page_stats[event.page_path]
        stats["visitors"].add(_actor_key(event))  # type: ignore[union-attr]
        stats["sessions"].add(event.session_id)  # type: ignore[union-attr]
        if event.event_name == "page_view":
            stats["views"] = int(stats["views"]) + 1
        if event.duration_ms is not None and event.event_name in {"page_leave", "page_heartbeat"}:
            stats["durations"].append(event.duration_ms)  # type: ignore[union-attr]

    page_stays = sorted(
        [
            AnalyticsPageStay(
                page_path=page_path,
                page_title=page_titles.get(page_path),
                views=int(stats["views"]),
                visitors=len(stats["visitors"]),  # type: ignore[arg-type]
                sessions=len(stats["sessions"]),  # type: ignore[arg-type]
                avg_stay_seconds=round(_avg(stats["durations"]) / 1000, 1),  # type: ignore[arg-type]
                p50_stay_seconds=round(_median(stats["durations"]) / 1000, 1),  # type: ignore[arg-type]
                p75_stay_seconds=round(_percentile(stats["durations"], 0.75) / 1000, 1),  # type: ignore[arg-type]
                p90_stay_seconds=round(_percentile(stats["durations"], 0.90) / 1000, 1),  # type: ignore[arg-type]
                p95_stay_seconds=round(_percentile(stats["durations"], 0.95) / 1000, 1),  # type: ignore[arg-type]
                duration_buckets=_duration_buckets(stats["durations"]),  # type: ignore[arg-type]
                bounce_count=bounce_by_page.get(page_path, 0),
                bounce_rate=_ratio(
                    bounce_by_page.get(page_path, 0),
                    len(stats["sessions"]),  # type: ignore[arg-type]
                ),
                exit_count=exit_by_page.get(page_path, 0),
                exit_rate=_ratio(
                    exit_by_page.get(page_path, 0),
                    len(stats["sessions"]),  # type: ignore[arg-type]
                ),
                normal_leave_count=max(
                    len(stats["sessions"]) - exit_by_page.get(page_path, 0),  # type: ignore[arg-type]
                    0,
                ),
                normal_leave_rate=_ratio(
                    max(
                        len(stats["sessions"]) - exit_by_page.get(page_path, 0),  # type: ignore[arg-type]
                        0,
                    ),
                    len(stats["sessions"]),  # type: ignore[arg-type]
                ),
            )
            for page_path, stats in page_stats.items()
            if int(stats["views"]) > 0
        ],
        key=lambda item: item.views,
        reverse=True,
    )

    page_view_count = Counter(event.page_path for event in page_views)
    page_visitor_sets: dict[str, set[str]] = defaultdict(set)
    page_session_sets: dict[str, set[str]] = defaultdict(set)
    for event in page_views:
        page_visitor_sets[event.page_path].add(_actor_key(event))
        page_session_sets[event.page_path].add(event.session_id)

    page_click_count = Counter(event.page_path for event in click_events)
    button_stats: dict[tuple[str, str, str | None, str, str], dict[str, object]] = defaultdict(
        lambda: {"clicks": 0, "users": set(), "sessions": set(), "sample": None}
    )
    for event in click_events:
        label = event.element_text or event.element_role or "未命名控件"
        module = _module_for_event(event)
        key = (event.page_path, label, event.element_role, event.event_name, module)
        button_stats[key]["clicks"] = int(button_stats[key]["clicks"]) + 1
        button_stats[key]["users"].add(_actor_key(event))  # type: ignore[union-attr]
        button_stats[key]["sessions"].add(event.session_id)  # type: ignore[union-attr]
        if button_stats[key]["sample"] is None:
            button_stats[key]["sample"] = event

    page_buttons = sorted(
        [
            AnalyticsPageButtonMetric(
                page_path=page_path,
                page_title=page_titles.get(page_path),
                button_label=label,
                button_role=role,
                event_name=event_name,
                module=module,
                clicks=int(stats["clicks"]),
                click_users=len(stats["users"]),  # type: ignore[arg-type]
                click_sessions=len(stats["sessions"]),  # type: ignore[arg-type]
                page_views=page_view_count.get(page_path, 0),
                page_sessions=len(page_session_sets.get(page_path, set())),
                click_rate=_ratio(int(stats["clicks"]), page_view_count.get(page_path, 0)),
                user_click_rate=_ratio(
                    len(stats["users"]),  # type: ignore[arg-type]
                    len(page_visitor_sets.get(page_path, set())),
                ),
                session_click_rate=_ratio(
                    len(stats["sessions"]),  # type: ignore[arg-type]
                    len(page_session_sets.get(page_path, set())),
                ),
                page_click_share=_ratio(int(stats["clicks"]), page_click_count.get(page_path, 0)),
                is_key_cta=_is_key_cta(label, stats["sample"]),  # type: ignore[arg-type]
            )
            for (page_path, label, role, event_name, module), stats in button_stats.items()
        ],
        key=lambda item: (item.page_path, -item.clicks, item.button_label),
    )

    event_stats: dict[tuple[str, str, str, str], dict[str, object]] = defaultdict(
        lambda: {"events": 0, "users": set(), "sessions": set()}
    )
    for event in events:
        module = _module_for_event(event)
        key = (event.event_name, event.event_category, event.page_path, module)
        event_stats[key]["events"] = int(event_stats[key]["events"]) + 1
        event_stats[key]["users"].add(_actor_key(event))  # type: ignore[union-attr]
        event_stats[key]["sessions"].add(event.session_id)  # type: ignore[union-attr]

    total_events = len(events)
    event_groups = sorted(
        [
            AnalyticsEventMetric(
                event_name=event_name,
                event_category=event_category,
                page_path=page_path,
                module=module,
                events=int(stats["events"]),
                users=len(stats["users"]),  # type: ignore[arg-type]
                sessions=len(stats["sessions"]),  # type: ignore[arg-type]
                event_share=_ratio(int(stats["events"]), total_events),
            )
            for (event_name, event_category, page_path, module), stats in event_stats.items()
        ],
        key=lambda item: (-item.events, item.page_path, item.event_name),
    )[:40]

    def build_selection_group(
        key: str,
        label: str,
        counter: Counter[str],
    ) -> AnalyticsSelectionGroup:
        total = sum(counter.values())
        return AnalyticsSelectionGroup(
            key=key,
            label=label,
            total=total,
            options=[
                AnalyticsSelectionOption(
                    label=name,
                    count=count,
                    ratio=_ratio(count, total),
                )
                for name, count in counter.most_common(10)
            ],
        )

    destination_counter: Counter[str] = Counter()
    route_selected_counter: Counter[str] = Counter()
    route_confirmed_counter: Counter[str] = Counter()
    interest_counter: Counter[str] = Counter()
    budget_counter: Counter[str] = Counter()
    duration_counter: Counter[str] = Counter()

    for event in events:
        metadata = _metadata(event)
        if event.event_name == "destination_selected":
            destination = _metadata_text(event, ["destination_name", "selection_label"])
            if destination:
                destination_counter[destination] += 1
        elif event.event_name == "route_option_selected":
            route = _metadata_text(event, ["route_title", "selection_label", "option_id"])
            if route:
                route_selected_counter[route] += 1
        elif event.event_name == "route_option_confirmed":
            route = _metadata_text(event, ["route_title", "selection_label", "option_id"])
            if route:
                route_confirmed_counter[route] += 1

        interests = metadata.get("interests")
        if isinstance(interests, list):
            for interest in interests:
                if isinstance(interest, str) and interest.strip():
                    interest_counter[interest.strip()] += 1

        budget = _budget_label(metadata)
        if budget:
            budget_counter[budget] += 1

        duration_days = metadata.get("duration_days")
        if isinstance(duration_days, int) and duration_days > 0:
            duration_counter[f"{duration_days} 天"] += 1

    selection_groups = [
        build_selection_group("destination_selected", "目的地选择占比", destination_counter),
        build_selection_group("route_option_selected", "路线方案点击占比", route_selected_counter),
        build_selection_group(
            "route_option_confirmed",
            "最终方案确认占比",
            route_confirmed_counter,
        ),
        build_selection_group("interest_selected", "兴趣偏好选择占比", interest_counter),
        build_selection_group("budget_selected", "预算区间占比", budget_counter),
        build_selection_group("duration_selected", "行程天数占比", duration_counter),
    ]

    data = AnalyticsDashboardPayload(
        range_days=days,
        range_label=range_label,
        timezone=ANALYTICS_TIMEZONE,
        calculated_at=now,
        funnel=funnel,
        page_stays=page_stays,
        page_buttons=page_buttons,
        event_groups=event_groups,
        selection_groups=selection_groups,
    )
    return success_response(data, request)
