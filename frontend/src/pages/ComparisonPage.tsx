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
import { createPackingItem, createTrip, createTripDay, createTripPoint } from '@/services/trip'
import { createSpot } from '@/services/spot'
import { createOutfit } from '@/services/outfit'
import { outfitPhotoUrl } from '@/utils/outfitImages'
import type { ImageResource, RouteOption, RouteGenerationPayload, TripPoint } from '@/types'
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

function imageUrl(images: ImageResource[] | undefined): string | null {
  return images?.find((img) => !img.placeholder)?.url || images?.[0]?.url || null
}

function toTime(value: string | null | undefined, fallback: string): string {
  if (!value) return fallback
  return /^\d{2}:\d{2}$/.test(value) ? value : fallback
}

async function createGeneratedTripContent(tripId: string, option: RouteOption): Promise<void> {
  const createdPoints: TripPoint[] = []
  for (const day of option.days) {
    const tripDay = await createTripDay(tripId, {
      day_index: day.day,
      title: day.theme,
      summary: day.commute_tip,
    })
    for (const [index, spot] of day.spots.entries()) {
      const point = await createTripPoint(tripDay.id, {
        name: spot.name,
        point_type: 'spot',
        address: spot.address || null,
        latitude: spot.latitude ?? null,
        longitude: spot.longitude ?? null,
        start_time: toTime(spot.time_slot, ['09:00', '11:30', '14:30', '17:00'][index] || '09:00'),
        sort_order: index + 1,
        notes: spot.description,
        image_url: imageUrl(spot.images),
      })
      createdPoints.push(point)
    }
  }

  const photoCandidates = option.days
    .flatMap((day) => day.spots)
    .filter((spot) => /拍照|机位|观景|日落|海|山|公园|景区/.test(`${spot.name}${spot.description}`))
    .slice(0, 5)

  for (const [index, spot] of photoCandidates.entries()) {
    const linkedPoint = createdPoints.find((point) => point.name === spot.name)
    await createSpot(tripId, {
      trip_point_id: linkedPoint?.id || null,
      name: spot.name,
      location: spot.description.split('；')[0] || spot.name,
      composition: index % 2 === 0 ? '优先使用广角横构图，保留前景和远景层次。' : '建议人物站在画面三分线位置，避开正午强光。',
      best_time: spot.time_slot,
      photo_score: Math.round(option.photo_score * 10),
      tips: '到达前用地图复核开放时间和实时人流。',
      images: imageUrl(spot.images) ? [imageUrl(spot.images)!] : [],
    })
  }

  await Promise.all([
    createOutfit(tripId, {
      scene: '城市漫步 / 景点拍照',
      season: '按出发日期复核天气',
      style: '轻户外舒适穿搭',
      items: [
        { name: '透气上衣', category: '上装' },
        { name: '舒适长裤/半裙', category: '下装' },
        { name: '防滑步行鞋', category: '鞋履' },
        { name: '薄外套或防晒衣', category: '外套' },
      ],
      tips: '优先选择低饱和色，和自然/古城/海边背景更协调。',
      images: [outfitPhotoUrl(`${tripId}-citywalk`, '城市漫步 / 景点拍照', '轻户外舒适穿搭')],
    }),
    createOutfit(tripId, {
      scene: '日落 / 观景台',
      season: '早晚温差场景',
      style: '出片层次感穿搭',
      items: [
        { name: '浅色内搭', category: '上装' },
        { name: '有廓形的外套', category: '外套' },
        { name: '小体积斜挎包', category: '配饰' },
      ],
      tips: '日落场景建议保留外套或披肩，既防风也能增加照片层次。',
      images: [outfitPhotoUrl(`${tripId}-sunset`, '日落 / 观景台', '出片层次感穿搭')],
    }),
  ])

  const packing = [
    ['证件', '身份证 / 护照'],
    ['电子设备', '充电器和充电宝'],
    ['拍照', '手机支架或小型三脚架'],
    ['拍照', '备用存储空间'],
    ['衣物', '舒适步行鞋'],
    ['护理', '防晒用品'],
    ['药品', '常用药'],
  ]
  await Promise.all(
    packing.map(([category, name]) => createPackingItem(tripId, { category, name })),
  )
}

export function ComparisonPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const showToast = useUIStore((s) => s.showToast)
  const user = useAuthStore((s) => s.user)
  const token = useAuthStore((s) => s.token)
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
    if (isAuthenticated && token && !user) {
      showToast('登录态恢复中，请稍后再试')
      return
    }
    if (!isAuthenticated || !user) {
      showToast('请先登录后再创建行程')
      navigate('/login?redirect=/comparison')
      return
    }
    const selectedOption = (routeOptions as RouteGenerationPayload | null)?.options?.[selected === 'A' ? 0 : 1]
    if (!selectedOption) return
    setCreating(true)
    try {
      const cover = imageUrl(selectedOption.days[0]?.spots[0]?.images)
      const trip = await createTrip(user.id, {
        title: `${destinationName} · ${selectedOption.title}`,
        destination_name: destinationName,
        status: 'draft',
        cover_image_url: cover,
        notes: selectedOption.summary,
      })
      showToast('行程已创建，正在写入每日安排...')
      await createGeneratedTripContent(trip.id, selectedOption)
      showToast('完整行程、机位、穿搭和打包清单已生成')
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
