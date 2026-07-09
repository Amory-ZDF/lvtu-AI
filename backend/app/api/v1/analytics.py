from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

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
    AnalyticsEventCreate,
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
    days: int = Query(default=7, ge=1, le=90),
) -> ApiResponse[AnalyticsDashboardPayload]:
    ensure_analytics_admin(current_user, settings, db)
    now = datetime.now(UTC)
    start = now - timedelta(days=days)
    events = list(
        db.scalars(
            select(AnalyticsEvent)
            .where(AnalyticsEvent.occurred_at >= start)
            .order_by(AnalyticsEvent.occurred_at.asc())
        )
    )

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
            "destination_selected",
            "选择目的地",
            lambda e: e.event_name == "destination_selected",
        ),
        ("route_success", "生成路线方案", lambda e: e.event_name == "route_generation_success"),
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
        (
            "outfit_preview",
            "生成穿搭预览",
            lambda e: e.event_name == "outfit_preview_generated",
        ),
    ]
    first_users = 0
    previous_users = 0
    funnel: list[AnalyticsFunnelStep] = []
    for key, label, predicate in funnel_definitions:
        users = {_actor_key(event) for event in events if predicate(event)}
        if not funnel:
            first_users = len(users)
            previous_users = len(users)
        current_users = len(users)
        previous_rate = 1.0 if not funnel else _ratio(current_users, previous_users)
        dropoff_rate = max(0.0, round(1 - previous_rate, 4))
        funnel.append(
            AnalyticsFunnelStep(
                key=key,
                label=label,
                users=current_users,
                previous_step_rate=previous_rate,
                overall_rate=_ratio(current_users, first_users),
                dropoff_rate=dropoff_rate,
            )
        )
        previous_users = current_users

    page_stats: dict[str, dict[str, object]] = defaultdict(
        lambda: {"views": 0, "visitors": set(), "durations": []}
    )
    for event in events:
        stats = page_stats[event.page_path]
        stats["visitors"].add(_actor_key(event))  # type: ignore[union-attr]
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
                avg_stay_seconds=round(_avg(stats["durations"]) / 1000, 1),  # type: ignore[arg-type]
                p50_stay_seconds=round(_median(stats["durations"]) / 1000, 1),  # type: ignore[arg-type]
            )
            for page_path, stats in page_stats.items()
            if int(stats["views"]) > 0
        ],
        key=lambda item: item.views,
        reverse=True,
    )

    page_view_count = Counter(event.page_path for event in page_views)
    page_visitor_sets: dict[str, set[str]] = defaultdict(set)
    for event in page_views:
        page_visitor_sets[event.page_path].add(_actor_key(event))

    button_stats: dict[tuple[str, str, str | None], dict[str, object]] = defaultdict(
        lambda: {"clicks": 0, "users": set()}
    )
    for event in click_events:
        label = event.element_text or event.element_role or "未命名控件"
        key = (event.page_path, label, event.element_role)
        button_stats[key]["clicks"] = int(button_stats[key]["clicks"]) + 1
        button_stats[key]["users"].add(_actor_key(event))  # type: ignore[union-attr]

    page_buttons = sorted(
        [
            AnalyticsPageButtonMetric(
                page_path=page_path,
                page_title=page_titles.get(page_path),
                button_label=label,
                button_role=role,
                clicks=int(stats["clicks"]),
                click_users=len(stats["users"]),  # type: ignore[arg-type]
                page_views=page_view_count.get(page_path, 0),
                click_rate=_ratio(int(stats["clicks"]), page_view_count.get(page_path, 0)),
                user_click_rate=_ratio(
                    len(stats["users"]),  # type: ignore[arg-type]
                    len(page_visitor_sets.get(page_path, set())),
                ),
            )
            for (page_path, label, role), stats in button_stats.items()
        ],
        key=lambda item: (item.page_path, -item.clicks, item.button_label),
    )

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

    for event in events:
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

        interests = _metadata(event).get("interests")
        if isinstance(interests, list):
            for interest in interests:
                if isinstance(interest, str) and interest.strip():
                    interest_counter[interest.strip()] += 1

    selection_groups = [
        build_selection_group("destination_selected", "目的地选择占比", destination_counter),
        build_selection_group("route_option_selected", "路线方案点击占比", route_selected_counter),
        build_selection_group(
            "route_option_confirmed",
            "最终方案确认占比",
            route_confirmed_counter,
        ),
        build_selection_group("interest_selected", "兴趣偏好选择占比", interest_counter),
    ]

    data = AnalyticsDashboardPayload(
        range_days=days,
        calculated_at=now,
        funnel=funnel,
        page_stays=page_stays,
        page_buttons=page_buttons,
        selection_groups=selection_groups,
    )
    return success_response(data, request)
