/**
 * 方案对比页 (page-comparison)
 * 从路由 state 读取选中的目的地，调用 generateRoutes 获取方案对比
 * "选择此方案"调用 createTrip 创建行程，跳转 /trips/{newTripId}
 */

import { useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { PlanOptionCard } from '@/components/PlanOptionCard'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorState } from '@/components/ErrorState'
import { EmptyState } from '@/components/EmptyState'
import { useUIStore } from '@/store/uiStore'
import { useAuthStore } from '@/store/authStore'
import { useTripStore } from '@/store/tripStore'
import { generateRoutes } from '@/services/planning'
import { createTrip } from '@/services/trip'
import type { RouteOption, RouteGenerationPayload } from '@/types'
import type { PlanOption } from '@/data/mock'

/** 路由 state 结构 */
interface ComparisonLocationState {
  destinationName?: string
}

/** 将分数映射为 level（后端 photo_score 为 0-10 量级） */
function scoreToLevel(score: number): 'high' | 'mid' | 'low' {
  if (score >= 8) return 'high'
  if (score >= 6) return 'mid'
  return 'low'
}

/** 将 RouteOption 映射为 PlanOption 视图数据 */
function toPlanOption(option: RouteOption, index: number): PlanOption {
  const letter = index === 0 ? 'A' : 'B'
  const isRelaxed = option.pace.includes('慢') || option.pace.includes('轻松')
  return {
    id: letter,
    title: option.title,
    subtitle: option.pace,
    price: option.estimated_budget,
    metrics: [
      { level: scoreToLevel(option.photo_score), label: `出片指数 · ${option.photo_score >= 8 ? '高' : option.photo_score >= 6 ? '中' : '低'} (${option.photo_score}/10)` },
      { level: isRelaxed ? 'high' : 'mid', label: `轻松程度 · ${isRelaxed ? '高' : '中'}` },
      { level: isRelaxed ? 'mid' : 'high', label: `节奏密度 · ${isRelaxed ? '中低' : '高'}` },
      { level: 'high', label: '美食覆盖 · 高' },
    ],
    description: option.summary,
  }
}

export function ComparisonPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const showToast = useUIStore((s) => s.showToast)
  const user = useAuthStore((s) => s.user)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const routeOptions = useTripStore((s) => s.routeOptions)
  const setRouteOptions = useTripStore((s) => s.setRouteOptions)
  const lastRequest = useTripStore((s) => s.lastRecommendRequest)

  const routeState = (location.state || {}) as ComparisonLocationState
  const destinationName = routeState.destinationName || routeOptions?.destination_name || ''

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<'A' | 'B'>('A')
  const [creating, setCreating] = useState(false)

  const fetchRoutes = () => {
    if (!destinationName) return
    setLoading(true)
    setError(null)
    const duration = lastRequest?.duration_days || 3
    generateRoutes({ destination_name: destinationName, duration_days: duration })
      .then((data) => setRouteOptions(data))
      .catch((err) => setError(err instanceof Error ? err.message : '路线生成失败'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    // 若 store 中已有结果且目的地匹配，直接使用；否则请求
    if (!routeOptions || routeOptions.destination_name !== destinationName) {
      fetchRoutes()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const options: PlanOption[] =
    (routeOptions as RouteGenerationPayload | null)?.options?.map((o, i) => toPlanOption(o, i)) || []

  const handleSelectPlan = async () => {
    if (!isAuthenticated || !user) {
      showToast('请先登录后再创建行程')
      navigate('/login?redirect=/comparison')
      return
    }
    const selectedOption = (routeOptions as RouteGenerationPayload | null)?.options?.[selected === 'A' ? 0 : 1]
    if (!selectedOption) return
    setCreating(true)
    try {
      const trip = await createTrip(user.id, {
        title: `${destinationName} · ${selectedOption.title}`,
        destination_name: destinationName,
        status: 'draft',
        notes: selectedOption.summary,
      })
      showToast('行程已创建')
      navigate(`/trips/${trip.id}`)
    } catch (err) {
      showToast(err instanceof Error ? err.message : '创建行程失败')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="page">
      <button className="back-link" onClick={() => navigate('/destinations')}>
        ← 返回目的地选择
      </button>
      <h2>方案对比</h2>
      <p className="hint" style={{ marginBottom: '20px' }}>
        {destinationName ? `选择一条最适合你的 ${destinationName} 旅行路线` : '选择一条最适合你的旅行路线'}
      </p>

      <div className="steps-bar">
        <div className="step-item">
          <div className="step-circle done">✓</div>
          <span className="step-label done">偏好输入</span>
        </div>
        <div className="step-line done"></div>
        <div className="step-item">
          <div className="step-circle done">✓</div>
          <span className="step-label done">智能分析</span>
        </div>
        <div className="step-line done"></div>
        <div className="step-item">
          <div className="step-circle done">✓</div>
          <span className="step-label done">目的地推荐</span>
        </div>
        <div className="step-line done"></div>
        <div className="step-item">
          <div className="step-circle current">4</div>
          <span className="step-label active">生成方案</span>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner label="正在生成路线方案..." />
      ) : error ? (
        <ErrorState
          title="路线生成失败"
          description={error}
          action={<button className="btn btn-primary" onClick={fetchRoutes}>重试</button>}
        />
      ) : options.length === 0 ? (
        <EmptyState
          icon="🗺️"
          title="暂无方案"
          description="请先从目的地推荐页选择一个目的地"
          action={<button className="btn btn-primary" onClick={() => navigate('/destinations')}>去选目的地</button>}
        />
      ) : (
        <>
          <div className="compare-layout">
            {options.map((option) => (
              <PlanOptionCard
                key={option.id}
                option={option}
                selected={selected === option.id}
                onSelect={setSelected}
              />
            ))}
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              className="btn btn-primary btn-lg"
              onClick={handleSelectPlan}
              disabled={creating}
            >
              {creating ? '创建中...' : '✅ 选择此方案 · 生成行程'}
            </button>
            <button className="btn btn-secondary" onClick={() => showToast('已保留备选')}>
              📌 保留备选
            </button>
          </div>
        </>
      )}
    </div>
  )
}

export default ComparisonPage
