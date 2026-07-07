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


class AnalyticsMetricCard(BaseModel):
    key: str
    label: str
    value: float | int | str
    unit: str | None = None
    description: str


class AnalyticsTimeseriesPoint(BaseModel):
    date: str
    events: int
    page_views: int
    visitors: int


class AnalyticsTopPage(BaseModel):
    page_path: str
    views: int
    visitors: int
    avg_stay_seconds: float


class AnalyticsButtonMetric(BaseModel):
    label: str
    page_path: str
    clicks: int
    visitors: int


class AnalyticsBreakdownItem(BaseModel):
    name: str
    count: int
    ratio: float


class AnalyticsRecentEvent(BaseModel):
    event_name: str
    event_category: str
    page_path: str
    visitor_id: str | None = None
    session_id: str
    element_text: str | None = None
    occurred_at: datetime


class AnalyticsFunnelStep(BaseModel):
    key: str
    label: str
    users: int
    conversion_rate: float


class AnalyticsDashboardPayload(BaseModel):
    range_days: int
    calculated_at: datetime
    metric_cards: list[AnalyticsMetricCard]
    timeseries: list[AnalyticsTimeseriesPoint]
    top_pages: list[AnalyticsTopPage]
    top_buttons: list[AnalyticsButtonMetric]
    device_breakdown: list[AnalyticsBreakdownItem]
    funnel: list[AnalyticsFunnelStep]
    recent_events: list[AnalyticsRecentEvent]
