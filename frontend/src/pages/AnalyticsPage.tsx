import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { getAnalyticsDashboard } from '@/services/analytics'
import { addDataCenterAdmin, getDataCenterAdmins } from '@/services/auth'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorState } from '@/components/ErrorState'
import { EmptyState } from '@/components/EmptyState'
import type {
  AnalyticsDashboardPayload,
  AnalyticsPageButtonMetric,
  DataCenterAdmin,
} from '@/types'

const DAY_OPTIONS = [7, 14, 30, 90]

function formatPercent(value: number): string {
  return `${Math.round(value * 1000) / 10}%`
}

function pageLabel(pagePath: string, pageTitle?: string | null): string {
  if (pageTitle) return pageTitle
  if (pagePath === '/') return '首页'
  if (pagePath === '/start') return '偏好输入页'
  if (pagePath === '/destinations') return '目的地推荐页'
  if (pagePath === '/comparison') return '方案对比页'
  if (pagePath.startsWith('/trips/')) return '行程详情页'
  return pagePath
}

function groupButtonsByPage(buttons: AnalyticsPageButtonMetric[]) {
  return buttons.reduce<Record<string, AnalyticsPageButtonMetric[]>>((groups, item) => {
    const key = item.page_path
    groups[key] = groups[key] || []
    groups[key].push(item)
    return groups
  }, {})
}

export function AnalyticsPage() {
  const [days, setDays] = useState(7)
  const [data, setData] = useState<AnalyticsDashboardPayload | null>(null)
  const [admins, setAdmins] = useState<DataCenterAdmin[]>([])
  const [adminEmail, setAdminEmail] = useState('')
  const [adminName, setAdminName] = useState('')
  const [adminMessage, setAdminMessage] = useState<string | null>(null)
  const [adminLoading, setAdminLoading] = useState(false)
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

  const loadAdmins = () => {
    getDataCenterAdmins()
      .then(setAdmins)
      .catch(() => setAdmins([]))
  }

  useEffect(() => {
    loadDashboard()
    loadAdmins()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days])

  const handleAddAdmin = async (event: FormEvent) => {
    event.preventDefault()
    setAdminMessage(null)
    const email = adminEmail.trim()
    if (!email) {
      setAdminMessage('请输入邮箱')
      return
    }

    setAdminLoading(true)
    try {
      await addDataCenterAdmin({
        email,
        display_name: adminName.trim() || undefined,
      })
      setAdminEmail('')
      setAdminName('')
      setAdminMessage('已添加白名单账号，可直接用邮箱免密登录。')
      loadAdmins()
    } catch (err) {
      setAdminMessage(err instanceof Error ? err.message : '添加失败')
    } finally {
      setAdminLoading(false)
    }
  }

  const buttonsByPage = useMemo(
    () => groupButtonsByPage(data?.page_buttons || []),
    [data?.page_buttons],
  )
  const hasAnalyticsData = Boolean(
    data && (
      data.funnel.some((step) => step.users > 0)
      || data.page_stays.length > 0
      || data.page_buttons.length > 0
      || data.selection_groups.some((group) => group.total > 0)
    ),
  )

  return (
    <div className="page analytics-page">
      <div className="analytics-header">
        <div>
          <h2>📊 数据中台</h2>
          <p className="hint">按互联网产品分析标准查看漏斗、页面停留、按钮点击率和选择占比。</p>
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
      ) : !data || !hasAnalyticsData ? (
        <EmptyState
          icon="📈"
          title="暂无可分析数据"
          description="产生页面访问、按钮点击或选择行为后，这里会展示漏斗、停留和点击率。"
          action={<button className="btn btn-primary" onClick={loadDashboard}>刷新</button>}
        />
      ) : (
        <>
          <section className="analytics-panel">
            <div className="analytics-panel-head">
              <div>
                <h3>转化漏斗</h3>
                <small>按用户去重；展示相邻步骤转化、整体转化和流失率。</small>
              </div>
            </div>
            <div className="funnel-list">
              {data.funnel.map((step, index) => (
                <div className="funnel-step" key={step.key}>
                  <div className="funnel-index">{index + 1}</div>
                  <div className="funnel-main">
                    <strong>{step.label}</strong>
                    <span>{step.users} 人</span>
                  </div>
                  <div className="funnel-metrics">
                    <span>上步转化 {formatPercent(step.previous_step_rate)}</span>
                    <span>整体转化 {formatPercent(step.overall_rate)}</span>
                    <span>流失 {formatPercent(step.dropoff_rate)}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="analytics-panel">
            <div className="analytics-panel-head">
              <div>
                <h3>每个页面的停留时长</h3>
                <small>页面级 PV / UV / 平均停留 / P50 停留，不展示全站平均停留。</small>
              </div>
            </div>
            <div className="analytics-table">
              {data.page_stays.map((page) => (
                <div className="analytics-row analytics-row-grid" key={page.page_path}>
                  <strong>{pageLabel(page.page_path, page.page_title)}</strong>
                  <span>{page.page_path}</span>
                  <span>{page.views} PV · {page.visitors} UV</span>
                  <span>平均 {page.avg_stay_seconds}s · P50 {page.p50_stay_seconds}s</span>
                </div>
              ))}
            </div>
          </section>

          <section className="analytics-panel">
            <div className="analytics-panel-head">
              <div>
                <h3>每个页面中按钮的点击率</h3>
                <small>点击率 = 按钮点击次数 ÷ 当前页面 PV；点击用户率 = 点击用户数 ÷ 当前页面 UV。</small>
              </div>
            </div>
            {Object.entries(buttonsByPage).map(([pagePath, buttons]) => (
              <div className="analytics-button-page" key={pagePath}>
                <h4>{pageLabel(pagePath, buttons[0]?.page_title)}</h4>
                <div className="analytics-table">
                  {buttons.map((button) => (
                    <div
                      className="analytics-row analytics-row-grid"
                      key={`${button.page_path}-${button.button_label}-${button.button_role}`}
                    >
                      <strong>{button.button_label}</strong>
                      <span>{button.clicks} 次点击 · {button.click_users} 人点击</span>
                      <span>{button.page_views} PV 基数</span>
                      <span>
                        点击率 {formatPercent(button.click_rate)}
                        {' · '}
                        用户点击率 {formatPercent(button.user_click_rate)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </section>

          <section className="analytics-panel">
            <div className="analytics-panel-head">
              <div>
                <h3>已选择的比例</h3>
                <small>展示用户在目的地、路线方案、最终确认和兴趣偏好上的选择分布。</small>
              </div>
            </div>
            <div className="analytics-selection-grid">
              {data.selection_groups.map((group) => (
                <div className="analytics-selection-card" key={group.key}>
                  <div className="analytics-panel-head">
                    <h4>{group.label}</h4>
                    <small>{group.total} 次选择</small>
                  </div>
                  {group.options.length === 0 ? (
                    <p className="analytics-empty-note">暂无选择数据</p>
                  ) : (
                    <div className="analytics-table">
                      {group.options.map((option) => (
                        <div className="analytics-choice-row" key={option.label}>
                          <div>
                            <strong>{option.label}</strong>
                            <span>{option.count} 次 · {formatPercent(option.ratio)}</span>
                          </div>
                          <div className="analytics-choice-track">
                            <div style={{ width: formatPercent(option.ratio) }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        </>
      )}

      <section className="analytics-panel analytics-admin-panel">
        <div className="analytics-panel-head">
          <div>
            <h3>白名单账号</h3>
            <small>添加后，对方只需输入邮箱即可进入数据中台。</small>
          </div>
        </div>
        <form className="analytics-admin-form" onSubmit={handleAddAdmin}>
          <input
            type="email"
            value={adminEmail}
            onChange={(event) => setAdminEmail(event.target.value)}
            placeholder="邮箱，例如 amory@example.com"
          />
          <input
            type="text"
            value={adminName}
            onChange={(event) => setAdminName(event.target.value)}
            placeholder="备注名，可选"
          />
          <button className="btn btn-primary" type="submit" disabled={adminLoading}>
            {adminLoading ? '添加中...' : '添加账号'}
          </button>
        </form>
        {adminMessage && <p className="analytics-admin-message">{adminMessage}</p>}
        <div className="analytics-admin-list">
          {admins.map((admin) => (
            <div className="analytics-row inline" key={`${admin.source}-${admin.email}`}>
              <strong>{admin.display_name || admin.email}</strong>
              <span>
                {admin.email} · {admin.source === 'env' ? '后端配置' : '中台添加'}
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

export default AnalyticsPage
