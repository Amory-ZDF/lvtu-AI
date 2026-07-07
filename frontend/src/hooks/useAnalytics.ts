import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import { flushAnalyticsEvents, trackAnalyticsEvent } from '@/services/analytics'

interface PageTimer {
  path: string
  title: string
  startedAt: number
}

function readableElementText(element: HTMLElement): string {
  if (element.dataset.analyticsLabel) return element.dataset.analyticsLabel
  if (element.getAttribute('aria-label')) return element.getAttribute('aria-label') || ''
  if (element.getAttribute('title')) return element.getAttribute('title') || ''
  if (element instanceof HTMLInputElement) return element.value || element.name || element.type
  return element.textContent || element.id || element.tagName.toLowerCase()
}

function trackPageDuration(timer: PageTimer, eventName: string): void {
  const duration = Math.round(performance.now() - timer.startedAt)
  if (duration < 500) return
  trackAnalyticsEvent({
    event_name: eventName,
    event_category: 'engagement',
    page_path: timer.path,
    page_title: timer.title,
    duration_ms: duration,
  }, true)
}

export function AnalyticsTracker() {
  const location = useLocation()
  const timerRef = useRef<PageTimer | null>(null)

  useEffect(() => {
    const path = `${location.pathname}${location.search}`
    if (timerRef.current) {
      trackPageDuration(timerRef.current, 'page_leave')
    }
    timerRef.current = {
      path,
      title: document.title,
      startedAt: performance.now(),
    }
    trackAnalyticsEvent({
      event_name: 'page_view',
      event_category: 'page',
      page_path: path,
      page_title: document.title,
    })
  }, [location.pathname, location.search])

  useEffect(() => {
    const handleClick = (event: MouseEvent) => {
      const target = event.target
      if (!(target instanceof Element)) return
      const element = target.closest(
        'button,a,[role="button"],input[type="button"],input[type="submit"],[data-analytics]',
      )
      if (!(element instanceof HTMLElement)) return

      const isLink = element instanceof HTMLAnchorElement
      trackAnalyticsEvent({
        event_name: isLink ? 'link_click' : 'button_click',
        event_category: 'click',
        element_text: readableElementText(element),
        element_role: element.dataset.analytics || element.getAttribute('role') || element.tagName.toLowerCase(),
        element_id: element.id || undefined,
        target_url: isLink ? element.href : undefined,
      })
    }

    const handleSubmit = (event: SubmitEvent) => {
      const form = event.target
      if (!(form instanceof HTMLFormElement)) return
      trackAnalyticsEvent({
        event_name: 'form_submit',
        event_category: 'form',
        element_text: form.getAttribute('aria-label') || form.id || 'form',
        element_role: 'form',
        target_url: form.action || undefined,
      })
    }

    const handleVisibility = () => {
      if (document.visibilityState === 'hidden' && timerRef.current) {
        trackPageDuration(timerRef.current, 'page_heartbeat')
        timerRef.current.startedAt = performance.now()
        void flushAnalyticsEvents(true)
      }
    }

    const handleBeforeUnload = () => {
      if (timerRef.current) {
        trackPageDuration(timerRef.current, 'page_leave')
      }
      void flushAnalyticsEvents(true)
    }

    document.addEventListener('click', handleClick, true)
    document.addEventListener('submit', handleSubmit, true)
    document.addEventListener('visibilitychange', handleVisibility)
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => {
      document.removeEventListener('click', handleClick, true)
      document.removeEventListener('submit', handleSubmit, true)
      document.removeEventListener('visibilitychange', handleVisibility)
      window.removeEventListener('beforeunload', handleBeforeUnload)
    }
  }, [])

  return null
}
