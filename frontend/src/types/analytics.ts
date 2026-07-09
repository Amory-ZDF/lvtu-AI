export interface AnalyticsFunnelStep {
  key: string
  label: string
  users: number
  previous_step_rate: number
  overall_rate: number
  dropoff_rate: number
}

export interface AnalyticsPageStay {
  page_path: string
  page_title?: string | null
  views: number
  visitors: number
  avg_stay_seconds: number
  p50_stay_seconds: number
}

export interface AnalyticsPageButtonMetric {
  page_path: string
  page_title?: string | null
  button_label: string
  button_role?: string | null
  clicks: number
  click_users: number
  page_views: number
  click_rate: number
  user_click_rate: number
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
  calculated_at: string
  funnel: AnalyticsFunnelStep[]
  page_stays: AnalyticsPageStay[]
  page_buttons: AnalyticsPageButtonMetric[]
  selection_groups: AnalyticsSelectionGroup[]
}
