export interface AnalyticsMetricCard {
  key: string
  label: string
  value: number | string
  unit?: string | null
  description: string
}

export interface AnalyticsTimeseriesPoint {
  date: string
  events: number
  page_views: number
  visitors: number
}

export interface AnalyticsTopPage {
  page_path: string
  views: number
  visitors: number
  avg_stay_seconds: number
}

export interface AnalyticsButtonMetric {
  label: string
  page_path: string
  clicks: number
  visitors: number
}

export interface AnalyticsBreakdownItem {
  name: string
  count: number
  ratio: number
}

export interface AnalyticsFunnelStep {
  key: string
  label: string
  users: number
  conversion_rate: number
}

export interface AnalyticsRecentEvent {
  event_name: string
  event_category: string
  page_path: string
  visitor_id?: string | null
  session_id: string
  element_text?: string | null
  occurred_at: string
}

export interface AnalyticsDashboardPayload {
  range_days: number
  calculated_at: string
  metric_cards: AnalyticsMetricCard[]
  timeseries: AnalyticsTimeseriesPoint[]
  top_pages: AnalyticsTopPage[]
  top_buttons: AnalyticsButtonMetric[]
  device_breakdown: AnalyticsBreakdownItem[]
  funnel: AnalyticsFunnelStep[]
  recent_events: AnalyticsRecentEvent[]
}
