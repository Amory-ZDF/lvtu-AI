import { apiClient, ACCESS_TOKEN_KEY } from '@/services/api'
import type { AnalyticsDashboardPayload } from '@/types/analytics'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
const ANALYTICS_ENABLED = import.meta.env.VITE_ANALYTICS_ENABLED !== 'false'
const VISITOR_KEY = 'lv_analytics_visitor_id'
const SESSION_KEY = 'lv_analytics_session_id'

export interface AnalyticsEventPayload {
  event_name: string
  event_category?: string
  page_path?: string
  page_title?: string
  referrer?: string
  element_text?: string
  element_role?: string
  element_id?: string
  target_url?: string
  duration_ms?: number
  metadata?: Record<string, unknown>
}

interface AnalyticsEventBody extends AnalyticsEventPayload {
  visitor_id: string
  session_id: string
  event_category: string
  page_path: string
  page_title: string
  viewport_width: number
  viewport_height: number
  device_type: string
  user_agent: string
  occurred_at: string
}

let queue: AnalyticsEventBody[] = []
let flushTimer: number | null = null

function makeId(prefix: string): string {
  const randomId =
    typeof crypto !== 'undefined' && 'randomUUID' in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`
  return `${prefix}_${randomId}`
}

function getVisitorId(): string {
  const existing = localStorage.getItem(VISITOR_KEY)
  if (existing) return existing
  const next = makeId('v')
  localStorage.setItem(VISITOR_KEY, next)
  return next
}

function getSessionId(): string {
  const existing = sessionStorage.getItem(SESSION_KEY)
  if (existing) return existing
  const next = makeId('s')
  sessionStorage.setItem(SESSION_KEY, next)
  return next
}

function deviceType(): string {
  const width = window.innerWidth
  if (width < 768) return 'mobile'
  if (width < 1024) return 'tablet'
  return 'desktop'
}

function currentPath(): string {
  return `${window.location.pathname}${window.location.search}`
}

function trimText(value: string | undefined, max = 255): string | undefined {
  const text = value?.replace(/\s+/g, ' ').trim()
  if (!text) return undefined
  return text.length > max ? text.slice(0, max) : text
}

function scheduleFlush(): void {
  if (flushTimer !== null) return
  flushTimer = window.setTimeout(() => {
    flushTimer = null
    void flushAnalyticsEvents()
  }, 1200)
}

export function trackAnalyticsEvent(event: AnalyticsEventPayload, immediate = false): void {
  if (!ANALYTICS_ENABLED || typeof window === 'undefined') return
  const body: AnalyticsEventBody = {
    visitor_id: getVisitorId(),
    session_id: getSessionId(),
    event_name: event.event_name,
    event_category: event.event_category || 'engagement',
    page_path: event.page_path || currentPath(),
    page_title: event.page_title || document.title,
    referrer: event.referrer || document.referrer,
    element_text: trimText(event.element_text),
    element_role: trimText(event.element_role, 64),
    element_id: trimText(event.element_id, 128),
    target_url: trimText(event.target_url, 512),
    duration_ms: event.duration_ms,
    viewport_width: window.innerWidth,
    viewport_height: window.innerHeight,
    device_type: deviceType(),
    user_agent: navigator.userAgent.slice(0, 512),
    metadata: {
      language: navigator.language,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      ...event.metadata,
    },
    occurred_at: new Date().toISOString(),
  }
  queue.push(body)
  if (immediate || queue.length >= 10) {
    void flushAnalyticsEvents()
  } else {
    scheduleFlush()
  }
}

export async function flushAnalyticsEvents(keepalive = false): Promise<void> {
  if (!ANALYTICS_ENABLED || queue.length === 0) return
  const events = queue
  queue = []
  const headers: Record<string, string> = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  }
  const token = localStorage.getItem(ACCESS_TOKEN_KEY)
  if (token) headers.Authorization = `Bearer ${token}`

  try {
    const response = await fetch(`${BASE_URL}/analytics/events`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ events }),
      keepalive,
    })
    if (!response.ok) {
      queue = [...events, ...queue].slice(-50)
    }
  } catch {
    queue = [...events, ...queue].slice(-50)
  }
}

export function getAnalyticsDashboard(days: number): Promise<AnalyticsDashboardPayload> {
  return apiClient.get<AnalyticsDashboardPayload>('/analytics/dashboard', { days })
}
