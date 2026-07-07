from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.responses import success_response
from app.core.config import Settings, get_settings
from app.core.exceptions import AppException
from app.db.session import get_db_session
from app.middleware.auth import get_current_user, get_current_user_optional
from app.models.analytics_event import AnalyticsEvent
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsBreakdownItem,
    AnalyticsButtonMetric,
    AnalyticsDashboardPayload,
    AnalyticsEventCreate,
    AnalyticsFunnelStep,
    AnalyticsIngestRequest,
    AnalyticsIngestResponse,
    AnalyticsMetricCard,
    AnalyticsRecentEvent,
    AnalyticsTimeseriesPoint,
    AnalyticsTopPage,
)
from app.schemas.common import ApiResponse

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


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _ensure_analytics_admin(user: User, settings: Settings) -> None:
    allowed_emails = {email.lower() for email in settings.analytics_admin_emails}
    if allowed_emails and user.email.lower() not in allowed_emails:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="analytics_forbidden",
            message="当前账号无权访问数据中台",
        )
    if settings.app_env == "production" and not allowed_emails:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="analytics_admin_not_configured",
            message="生产环境需要配置 ANALYTICS_ADMIN_EMAILS 后才能查看数据中台",
        )


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
    _ensure_analytics_admin(current_user, settings)
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
    stay_events = [
        event.duration_ms
        for event in events
        if event.duration_ms is not None and event.event_name in {"page_leave", "page_heartbeat"}
    ]
    session_duration: dict[str, int] = defaultdict(int)
    for event in events:
        if event.duration_ms is not None and event.event_name in {"page_leave", "page_heartbeat"}:
            session_duration[event.session_id] += event.duration_ms

    visitors = {_actor_key(event) for event in events}
    sessions = {event.session_id for event in events}
    active_users = {str(event.user_id) for event in events if event.user_id}
    ctr = _ratio(len(click_events), len(page_views))

    metric_cards = [
        AnalyticsMetricCard(
            key="unique_visitors",
            label="访客数 UV",
            value=len(visitors),
            description="按登录用户、visitor_id 或 session_id 去重",
        ),
        AnalyticsMetricCard(
            key="sessions",
            label="访问会话",
            value=len(sessions),
            description="按 session_id 去重",
        ),
        AnalyticsMetricCard(
            key="page_views",
            label="页面浏览 PV",
            value=len(page_views),
            description="page_view 事件总数",
        ),
        AnalyticsMetricCard(
            key="avg_stay_seconds",
            label="平均停留",
            value=round(_avg(stay_events) / 1000, 1),
            unit="秒",
            description="page_leave/page_heartbeat 的 duration_ms 均值",
        ),
        AnalyticsMetricCard(
            key="click_through_rate",
            label="点击率",
            value=round(ctr * 100, 1),
            unit="%",
            description="按钮/链接点击次数 ÷ 页面浏览次数",
        ),
        AnalyticsMetricCard(
            key="active_users",
            label="登录用户",
            value=len(active_users),
            description="产生事件的登录用户数",
        ),
        AnalyticsMetricCard(
            key="avg_session_seconds",
            label="平均会话时长",
            value=round(_avg(list(session_duration.values())) / 1000, 1),
            unit="秒",
            description="每个 session 内停留时长求和后取均值",
        ),
        AnalyticsMetricCard(
            key="total_events",
            label="事件总量",
            value=len(events),
            description="当前时间窗口内入库埋点数",
        ),
    ]

    daily: dict[str, dict[str, set | int]] = {}
    for offset in range(days - 1, -1, -1):
        date = (now - timedelta(days=offset)).date().isoformat()
        daily[date] = {"events": 0, "page_views": 0, "visitors": set()}
    for event in events:
        date = event.occurred_at.date().isoformat()
        if date not in daily:
            daily[date] = {"events": 0, "page_views": 0, "visitors": set()}
        daily[date]["events"] = int(daily[date]["events"]) + 1
        if event.event_name == "page_view":
            daily[date]["page_views"] = int(daily[date]["page_views"]) + 1
        daily[date]["visitors"].add(_actor_key(event))  # type: ignore[union-attr]

    timeseries = [
        AnalyticsTimeseriesPoint(
            date=date,
            events=int(values["events"]),
            page_views=int(values["page_views"]),
            visitors=len(values["visitors"]),  # type: ignore[arg-type]
        )
        for date, values in sorted(daily.items())
    ]

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
    top_pages = sorted(
        [
            AnalyticsTopPage(
                page_path=page_path,
                views=int(stats["views"]),
                visitors=len(stats["visitors"]),  # type: ignore[arg-type]
                avg_stay_seconds=round(_avg(stats["durations"]) / 1000, 1),  # type: ignore[arg-type]
            )
            for page_path, stats in page_stats.items()
            if int(stats["views"]) > 0
        ],
        key=lambda item: item.views,
        reverse=True,
    )[:10]

    button_stats: dict[tuple[str, str], dict[str, object]] = defaultdict(
        lambda: {"clicks": 0, "visitors": set()}
    )
    for event in click_events:
        label = event.element_text or event.element_role or "未命名控件"
        key = (label, event.page_path)
        button_stats[key]["clicks"] = int(button_stats[key]["clicks"]) + 1
        button_stats[key]["visitors"].add(_actor_key(event))  # type: ignore[union-attr]
    top_buttons = sorted(
        [
            AnalyticsButtonMetric(
                label=label,
                page_path=page_path,
                clicks=int(stats["clicks"]),
                visitors=len(stats["visitors"]),  # type: ignore[arg-type]
            )
            for (label, page_path), stats in button_stats.items()
        ],
        key=lambda item: item.clicks,
        reverse=True,
    )[:10]

    devices = Counter(event.device_type or "unknown" for event in events)
    device_breakdown = [
        AnalyticsBreakdownItem(
            name=name,
            count=count,
            ratio=_ratio(count, len(events)),
        )
        for name, count in devices.most_common()
    ]

    funnel_definitions = [
        ("home_view", "访问首页", lambda e: e.event_name == "page_view" and e.page_path == "/"),
        (
            "start_view",
            "进入规划页",
            lambda e: e.event_name == "page_view" and e.page_path == "/start",
        ),
        (
            "destination_success",
            "生成目的地推荐",
            lambda e: e.event_name == "destination_recommendation_success",
        ),
        ("route_success", "生成路线", lambda e: e.event_name == "route_generation_success"),
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
    funnel: list[AnalyticsFunnelStep] = []
    for key, label, predicate in funnel_definitions:
        users = {_actor_key(event) for event in events if predicate(event)}
        if not funnel:
            first_users = len(users)
        funnel.append(
            AnalyticsFunnelStep(
                key=key,
                label=label,
                users=len(users),
                conversion_rate=_ratio(len(users), first_users),
            )
        )

    recent_events = [
        AnalyticsRecentEvent(
            event_name=event.event_name,
            event_category=event.event_category,
            page_path=event.page_path,
            visitor_id=event.visitor_id,
            session_id=event.session_id,
            element_text=event.element_text,
            occurred_at=event.occurred_at,
        )
        for event in sorted(events, key=lambda item: item.occurred_at, reverse=True)[:30]
    ]

    data = AnalyticsDashboardPayload(
        range_days=days,
        calculated_at=now,
        metric_cards=metric_cards,
        timeseries=timeseries,
        top_pages=top_pages,
        top_buttons=top_buttons,
        device_breakdown=device_breakdown,
        funnel=funnel,
        recent_events=recent_events,
    )
    return success_response(data, request)
