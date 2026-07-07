import { useEffect, useState } from 'react'
import { getAnalyticsDashboard } from '@/services/analytics'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorState } from '@/components/ErrorState'
import { EmptyState } from '@/components/EmptyState'
import type { AnalyticsDashboardPayload } from '@/types'

const DAY_OPTIONS = [7, 14, 30, 90]

function formatPercent(value: number): string {
  return `${Math.round(value * 1000) / 10}%`
}

function maxValue(values: number[]): number {
  return Math.max(...values, 1)
}

export function AnalyticsPage() {
  const [days, setDays] = useState(7)
  const [data, setData] = useState<AnalyticsDashboardPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadDashboard = () => {
    setLoading(true)
    setError(null)
    getAnalyticsDashboard(days)
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : '数据加载失败'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadDashboard()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days])

  const maxEvents = maxValue(data?.timeseries.map((item) => item.events) || [])
  const hasEvents = (data?.metric_cards.find((item) => item.key === 'total_events')?.value || 0) !== 0

  return (
    <div className="page analytics-page">
      <div className="analytics-header">
        <div>
          <h2>📊 数据中台</h2>
          <p className="hint">查看真实用户行为、按钮点击、页面停留和关键转化漏斗。</p>
        </div>
        <div className="analytics-actions">
          <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
            {DAY_OPTIONS.map((option) => (
              <option key={option} value={option}>近 {option} 天</option>
            ))}
          </select>
          <button className="btn btn-secondary" onClick={loadDashboard}>
            刷新
          </button>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner label="正在加载数据中台..." />
      ) : error ? (
        <ErrorState
          title="数据中台加载失败"
          description={error}
          action={<button className="btn btn-primary" onClick={loadDashboard}>重试</button>}
        />
      ) : !data || !hasEvents ? (
        <EmptyState
          icon="📈"
          title="暂无埋点数据"
          description="部署埋点后，用户访问、点击、停留时长会从这里开始累计。"
          action={<button className="btn btn-primary" onClick={loadDashboard}>刷新</button>}
        />
      ) : (
        <>
          <div className="analytics-grid">
            {data.metric_cards.map((card) => (
              <div className="analytics-card" key={card.key}>
                <span>{card.label}</span>
                <strong>{card.value}{card.unit || ''}</strong>
                <small>{card.description}</small>
              </div>
            ))}
          </div>

          <div className="analytics-panel">
            <div className="analytics-panel-head">
              <h3>趋势</h3>
              <small>事件量 / PV / UV</small>
            </div>
            <div className="analytics-bars">
              {data.timeseries.map((item) => (
                <div className="analytics-bar-item" key={item.date}>
                  <div className="analytics-bar-track">
                    <div
                      className="analytics-bar-fill"
                      style={{ height: `${Math.max(8, (item.events / maxEvents) * 100)}%` }}
                      title={`${item.date}: ${item.events} events`}
                    />
                  </div>
                  <span>{item.date.slice(5)}</span>
                  <small>{item.page_views} PV / {item.visitors} UV</small>
                </div>
              ))}
            </div>
          </div>

          <div className="analytics-two-col">
            <div className="analytics-panel">
              <div className="analytics-panel-head">
                <h3>热门页面</h3>
                <small>按 PV 排序</small>
              </div>
              <div className="analytics-table">
                {data.top_pages.map((page) => (
                  <div className="analytics-row" key={page.page_path}>
                    <strong>{page.page_path}</strong>
                    <span>{page.views} PV · {page.visitors} UV · 停留 {page.avg_stay_seconds}s</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="analytics-panel">
              <div className="analytics-panel-head">
                <h3>按钮点击</h3>
                <small>自动捕获 button/link</small>
              </div>
              <div className="analytics-table">
                {data.top_buttons.map((button) => (
                  <div className="analytics-row" key={`${button.page_path}-${button.label}`}>
                    <strong>{button.label}</strong>
                    <span>{button.page_path} · {button.clicks} 次 · {button.visitors} 人</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="analytics-two-col">
            <div className="analytics-panel">
              <div className="analytics-panel-head">
                <h3>核心漏斗</h3>
                <small>按用户去重</small>
              </div>
              <div className="funnel-list">
                {data.funnel.map((step, index) => (
                  <div className="funnel-step" key={step.key}>
                    <div className="funnel-index">{index + 1}</div>
                    <div>
                      <strong>{step.label}</strong>
                      <span>{step.users} 人 · 转化 {formatPercent(step.conversion_rate)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="analytics-panel">
              <div className="analytics-panel-head">
                <h3>设备分布</h3>
                <small>desktop / tablet / mobile</small>
              </div>
              <div className="analytics-table">
                {data.device_breakdown.map((item) => (
                  <div className="analytics-row inline" key={item.name}>
                    <strong>{item.name}</strong>
                    <span>{item.count} 次 · {formatPercent(item.ratio)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="analytics-panel">
            <div className="analytics-panel-head">
              <h3>最近事件</h3>
              <small>最多展示 30 条</small>
            </div>
            <div className="analytics-table">
              {data.recent_events.map((event) => (
                <div
                  className="analytics-row inline"
                  key={`${event.session_id}-${event.occurred_at}-${event.event_name}`}
                >
                  <strong>{event.event_name}</strong>
                  <span>
                    {event.page_path}
                    {event.element_text ? ` · ${event.element_text}` : ''}
                    {' · '}
                    {new Date(event.occurred_at).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default AnalyticsPage
