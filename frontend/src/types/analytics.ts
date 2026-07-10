export interface AnalyticsFunnelStep {
  key: string
  label: string
  users: number
  sessions: number
  previous_step_rate: number
  overall_rate: number
  dropoff_users: number
  dropoff_rate: number
}

export interface AnalyticsDurationBucket {
  label: string
  count: number
  ratio: number
}

export interface AnalyticsPageStay {
  page_path: string
  page_title?: string | null
  views: number
  visitors: number
  sessions: number
  avg_stay_seconds: number
  p50_stay_seconds: number
  p75_stay_seconds: number
  p90_stay_seconds: number
  p95_stay_seconds: number
  duration_buckets: AnalyticsDurationBucket[]
  bounce_count: number
  bounce_rate: number
  exit_count: number
  exit_rate: number
  normal_leave_count: number
  normal_leave_rate: number
}

export interface AnalyticsPageButtonMetric {
  page_path: string
  page_title?: string | null
  button_label: string
  button_role?: string | null
  event_name: string
  module: string
  clicks: number
  click_users: number
  click_sessions: number
  page_views: number
  page_sessions: number
  click_rate: number
  user_click_rate: number
  session_click_rate: number
  page_click_share: number
  is_key_cta: boolean
}

export interface AnalyticsEventMetric {
  event_name: string
  event_category: string
  page_path: string
  module: string
  events: number
  users: number
  sessions: number
  event_share: number
}

export interface AnalyticsSelectionOption {
  label: string
  count: number
  ratio: number
}

export interface AnalyticsSelectionGroup {
  key: string
  label: string
  total: number
  options: AnalyticsSelectionOption[]
}

export interface AnalyticsDashboardPayload {
  range_days: number
  range_label: string
  timezone: string
  calculated_at: string
  funnel: AnalyticsFunnelStep[]
  page_stays: AnalyticsPageStay[]
  page_buttons: AnalyticsPageButtonMetric[]
  event_groups: AnalyticsEventMetric[]
  selection_groups: AnalyticsSelectionGroup[]
}
