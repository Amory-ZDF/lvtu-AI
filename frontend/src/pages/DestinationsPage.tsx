/**
 * 目的地推荐页 (page-destinations)
 * 从 tripStore 读取推荐结果，若无则用默认参数重新请求
 */

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { DestinationCard } from '@/components/DestinationCard'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorState } from '@/components/ErrorState'
import { EmptyState } from '@/components/EmptyState'
import { useUIStore } from '@/store/uiStore'
import { useAuthStore } from '@/store/authStore'
import { useTripStore } from '@/store/tripStore'
import { recommendDestinations } from '@/services/planning'
import { createTrip } from '@/services/trip'
import type { DestinationItem, DestinationRecommendationPayload } from '@/types'
import type { DestinationPreview } from '@/data/mock'

/** 默认渐变（按 id 哈希取色） */
const GRADIENTS = [
  'linear-gradient(135deg,oklch(0.63 0.17 198),oklch(0.56 0.15 222))',
  'linear-gradient(135deg,oklch(0.62 0.13 42),oklch(0.55 0.15 62))',
  'linear-gradient(135deg,oklch(0.58 0.15 170),oklch(0.50 0.14 195))',
  'linear-gradient(135deg,oklch(0.56 0.16 215),oklch(0.48 0.14 235))',
  'linear-gradient(135deg,oklch(0.60 0.15 340),oklch(0.52 0.16 5))',
]

function pickGradient(id: string): string {
  let hash = 0
  for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) >>> 0
  return GRADIENTS[hash % GRADIENTS.length]
}

/** 将 DestinationItem 映射为 DestinationPreview 视图数据 */
function toPreview(item: DestinationItem, index: number): DestinationPreview {
  const heroUrl = item.hero_image?.url && !item.hero_image.placeholder
    ? `url(${item.hero_image.url})`
    : pickGradient(item.id)
  return {
    id: item.id,
    name: item.name,
    region: `${item.country_or_region} · ${item.best_season}`,
    duration: '',
    season: item.best_season,
    matchScore: item.match_score >= 90 ? `最佳匹配 · ${item.match_score}%` : `${item.match_score}% 匹配`,
    price: item.budget_range,
    gradient: heroUrl,
    tags: item.vibe_tags,
    reason: item.reasons[0] || '',
    stops: [],
    highlights: item.gallery.slice(0, 4).map((g) => g.alt).filter(Boolean),
    recommended: index === 0,
  }
}

export function DestinationsPage() {
  const navigate = useNavigate()
  const showToast = useUIStore((s) => s.showToast)
  const user = useAuthStore((s) => s.user)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const destinations = useTripStore((s) => s.destinations)
  const setDestinations = useTripStore((s) => s.setDestinations)
  const lastRecommendRequest = useTripStore((s) => s.lastRecommendRequest)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /** 用默认参数请求推荐 */
  const fetchDefault = () => {
    setLoading(true)
    setError(null)
    const payload = lastRecommendRequest || {
      duration_days: 3,
      interests: ['自然', '拍照', '美食'],
    }
    recommendDestinations(payload)
      .then((data) => setDestinations(data))
      .catch((err) =>
        setError(err instanceof Error ? err.message : '获取推荐失败'),
      )
      .finally(() => setLoading(false))
  }

  // 若 store 中无数据，尝试用默认参数请求
  useEffect(() => {
    if (!destinations) fetchDefault()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleCompare = (id: string) => {
    const item = destinations?.destinations.find((d) => d.id === id)
    navigate('/comparison', {
      state: { destination: item ? toPreview(item, 0) : null, destinationName: item?.name },
    })
  }

  const handleGenerate = async (id: string) => {
    if (!isAuthenticated || !user) {
      showToast('请先登录后再创建行程')
      navigate('/login?redirect=/destinations')
      return
    }
    const item = destinations?.destinations.find((d) => d.id === id)
    if (!item) return
    showToast('正在创建行程...')
    try {
      const trip = await createTrip(user.id, {
        title: item.name,
        destination_name: item.name,
        status: 'draft',
      })
      showToast('行程已创建')
      navigate(`/trips/${trip.id}`)
    } catch (err) {
      showToast(err instanceof Error ? err.message : '创建行程失败')
    }
  }

  const handleRefresh = () => {
    fetchDefault()
    showToast('正在换一批...')
  }

  const items: DestinationPreview[] = (destinations as DestinationRecommendationPayload | null)?.destinations?.map(
    (d, i) => toPreview(d, i),
  ) || []

  return (
    <div className="page">
      <button className="back-link" onClick={() => navigate('/start')}>
        ← 返回修改偏好
      </button>
      <h2>为你找到 {items.length} 个目的地</h2>
      <p className="hint" style={{ marginBottom: '20px' }}>
        {destinations?.query_summary || '基于你的偏好生成'}
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
          <div className="step-circle current">3</div>
          <span className="step-label active">目的地推荐</span>
        </div>
        <div className="step-line"></div>
        <div className="step-item">
          <div className="step-circle">4</div>
          <span className="step-label">生成方案</span>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner label="正在为你匹配目的地..." />
      ) : error ? (
        <ErrorState
          title="获取推荐失败"
          description={error}
          action={<button className="btn btn-primary" onClick={fetchDefault}>重试</button>}
        />
      ) : items.length === 0 ? (
        <EmptyState
          icon="🌍"
          title="暂无推荐目的地"
          description="试试调整你的偏好后重新生成"
          action={<button className="btn btn-primary" onClick={() => navigate('/start')}>返回修改偏好</button>}
        />
      ) : (
        <>
          <div className="dest-scroll">
            {items.map((dest) => (
              <DestinationCard
                key={dest.id}
                destination={dest}
                onCompare={handleCompare}
                onGenerate={handleGenerate}
              />
            ))}
          </div>
          <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
            <button className="btn btn-secondary" onClick={handleRefresh}>
              🔄 换一批目的地
            </button>
          </div>
        </>
      )}
    </div>
  )
}

export default DestinationsPage
