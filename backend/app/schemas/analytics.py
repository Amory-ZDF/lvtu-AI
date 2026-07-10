from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AnalyticsEventCreate(BaseModel):
    visitor_id: str | None = Field(default=None, max_length=128)
    session_id: str = Field(..., min_length=1, max_length=128)
    event_name: str = Field(..., min_length=1, max_length=64)
    event_category: str = Field(default="engagement", max_length=32)
    page_path: str = Field(default="/", max_length=512)
    page_title: str | None = Field(default=None, max_length=255)
    referrer: str | None = Field(default=None, max_length=512)
    element_text: str | None = Field(default=None, max_length=255)
    element_role: str | None = Field(default=None, max_length=64)
    element_id: str | None = Field(default=None, max_length=128)
    target_url: str | None = Field(default=None, max_length=512)
    duration_ms: int | None = Field(default=None, ge=0, le=24 * 60 * 60 * 1000)
    viewport_width: int | None = Field(default=None, ge=0, le=10000)
    viewport_height: int | None = Field(default=None, ge=0, le=10000)
    device_type: str | None = Field(default=None, max_length=32)
    user_agent: str | None = Field(default=None, max_length=512)
    metadata: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime | None = None


class AnalyticsIngestRequest(BaseModel):
    events: list[AnalyticsEventCreate] = Field(..., min_length=1, max_length=50)


class AnalyticsIngestResponse(BaseModel):
    accepted: int


class AnalyticsDurationBucket(BaseModel):
    label: str
    count: int
    ratio: float


class AnalyticsPageStay(BaseModel):
    page_path: str
    page_title: str | None = None
    views: int
    visitors: int
    sessions: int
    avg_stay_seconds: float
    p50_stay_seconds: float
    p75_stay_seconds: float
    p90_stay_seconds: float
    p95_stay_seconds: float
    duration_buckets: list[AnalyticsDurationBucket]
    bounce_count: int
    bounce_rate: float
    exit_count: int
    exit_rate: float
    normal_leave_count: int
    normal_leave_rate: float


class AnalyticsPageButtonMetric(BaseModel):
    page_path: str
    page_title: str | None = None
    button_label: str
    button_role: str | None = None
    event_name: str
    module: str
    clicks: int
    click_users: int
    click_sessions: int
    page_views: int
    page_sessions: int
    click_rate: float
    user_click_rate: float
    session_click_rate: float
    page_click_share: float
    is_key_cta: bool


class AnalyticsEventMetric(BaseModel):
    event_name: str
    event_category: str
    page_path: str
    module: str
    events: int
    users: int
    sessions: int
    event_share: float


class AnalyticsSelectionOption(BaseModel):
    label: str
    count: int
    ratio: float


class AnalyticsSelectionGroup(BaseModel):
    key: str
    label: str
    total: int
    options: list[AnalyticsSelectionOption]


class AnalyticsFunnelStep(BaseModel):
    key: str
    label: str
    users: int
    sessions: int
    previous_step_rate: float
    overall_rate: float
    dropoff_users: int
    dropoff_rate: float


class AnalyticsDashboardPayload(BaseModel):
    range_days: int
    range_label: str
    timezone: str
    calculated_at: datetime
    funnel: list[AnalyticsFunnelStep]
    page_stays: list[AnalyticsPageStay]
    page_buttons: list[AnalyticsPageButtonMetric]
    event_groups: list[AnalyticsEventMetric]
    selection_groups: list[AnalyticsSelectionGroup]
