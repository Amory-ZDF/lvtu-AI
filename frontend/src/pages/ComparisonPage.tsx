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
import { trackAnalyticsEvent } from '@/services/analytics'
import { generateRoutes } from '@/services/planning'
import { createPackingItem, createTrip, createTripDay, createTripPoint } from '@/services/trip'
import { createSpot } from '@/services/spot'
import { createOutfit } from '@/services/outfit'
import type { OutfitGender } from '@/utils/outfitImages'
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

function scoreLabel(score: number): string {
  if (score >= 8) return '高'
  if (score >= 6) return '中'
  return '低'
}

function formatScore(score: number): string {
  return Number.isInteger(score) ? `${score}` : score.toFixed(1)
}

function routeKeywords(option: RouteOption): string[] {
  const text = `${option.title} ${option.summary} ${option.days
    .flatMap((day) => [day.theme, ...day.spots.flatMap((spot) => [spot.name, spot.description, spot.category || ''])])
    .join(' ')}`
  const keywords = [
    ['自然风光', /森林|峡谷|山|湖|海|岛|公园|湿地|日出|日落|观景/],
    ['经典地标', /古城|博物馆|展馆|寺|塔|街区|广场|地标|历史|文化/],
    ['高出片机位', /拍照|机位|观景|日落|人像|摄影|出片/],
    ['城市漫步', /街|巷|咖啡|市集|步行|漫步|夜游/],
    ['在地美食', /美食|餐|小吃|夜市|茶|咖啡/],
  ] as const
  return keywords.filter(([, pattern]) => pattern.test(text)).map(([label]) => label).slice(0, 4)
}

type RouteAudience = 'first-timer' | 'repeat-visitor'

function inferRouteAudience(option: RouteOption, index: number): RouteAudience {
  const text = `${option.title} ${option.summary}`
  if (/复访|再来|来过|深度|小众|经验|二刷|非热门|慢体验/.test(text)) {
    return 'repeat-visitor'
  }
  if (/初访|初游|第一次|首次|经典|覆盖|地标/.test(text)) {
    return 'first-timer'
  }
  return index === 0 ? 'first-timer' : 'repeat-visitor'
}

function isRelaxedPace(pace: string): boolean {
  const normalized = pace.toLowerCase()
  return normalized.includes('relaxed') || normalized.includes('slow') || /慢|轻松|松弛/.test(pace)
}

function routeStats(option: RouteOption, audience: RouteAudience, isRelaxed: boolean): string[] {
  const dayCount = option.days.length
  const spotCount = option.days.reduce((sum, day) => sum + day.spots.length, 0)
  const avgSpots = dayCount > 0 ? Math.round((spotCount / dayCount) * 10) / 10 : spotCount
  return [
    `${dayCount} 天 / ${spotCount} 个点位`,
    `日均 ${avgSpots} 个停留点`,
    audience === 'first-timer'
      ? '经典覆盖，适合初访'
      : isRelaxed
        ? '小众深度，适合复访'
        : '差异探索，适合复访',
  ]
}

function firstSpotNames(option: RouteOption): string {
  return option.days
    .flatMap((day) => day.spots.map((spot) => spot.name))
    .slice(0, 4)
    .join(' → ')
}

function estimateCoverageScore(option: RouteOption): number {
  const dayCount = Math.max(option.days.length, 1)
  const spotCount = option.days.reduce((sum, day) => sum + day.spots.length, 0)
  return Math.min(9.2, 6.6 + (spotCount / dayCount) * 0.55)
}

function estimateFoodScore(option: RouteOption): number {
  const text = `${option.title}${option.summary}${option.days
    .flatMap((day) => day.spots.flatMap((spot) => [spot.name, spot.description, spot.category || '']))
    .join('')}`
  return /美食|餐|小吃|夜市|茶|咖啡/.test(text) ? 8.6 : 7.4
}

/** 将 RouteOption 映射为 PlanOption 视图数据 */
function toPlanOption(option: RouteOption, index: number): PlanOption {
  const letter = index === 0 ? 'A' : 'B'
  const audience = inferRouteAudience(option, index)
  const isRelaxed = isRelaxedPace(option.pace) || audience === 'repeat-visitor'
  const comfortScore = isRelaxed ? 8.8 : 7.2
  const densityScore = isRelaxed ? 6.8 : 8.6
  const coverageScore = estimateCoverageScore(option)
  const foodScore = estimateFoodScore(option)
  const keywords = routeKeywords(option)
  return {
    id: letter,
    title: option.title,
    subtitle: option.pace,
    price: option.estimated_budget,
    metrics: [
      { level: scoreToLevel(option.photo_score), label: `出片指数 · ${scoreLabel(option.photo_score)} (${formatScore(option.photo_score)}/10)` },
      { level: scoreToLevel(comfortScore), label: `轻松程度 · ${scoreLabel(comfortScore)} (${formatScore(comfortScore)}/10)` },
      { level: scoreToLevel(densityScore), label: `节奏密度 · ${isRelaxed ? '中低' : '高'} (${formatScore(densityScore)}/10)` },
      { level: scoreToLevel(foodScore), label: `美食覆盖 · ${scoreLabel(foodScore)} (${formatScore(foodScore)}/10)` },
    ],
    description: option.summary,
    summaryStats: routeStats(option, audience, isRelaxed),
    differentiators: [
      firstSpotNames(option) ? `核心动线：${firstSpotNames(option)}` : '',
      keywords.length > 0 ? `内容侧重：${keywords.join(' / ')}` : '',
      audience === 'first-timer'
        ? '差异重点：经典地标优先，降低首次决策成本。'
        : '差异重点：减少重复经典点，增加小众机位和慢体验。',
    ].filter(Boolean),
    scoreBreakdown: [
      {
        label: '出片',
        score: `${formatScore(option.photo_score)}/10`,
        reason: '参考景观点位、观景/日落/机位词和真实 POI 组合。',
      },
      {
        label: '舒适',
        score: `${formatScore(comfortScore)}/10`,
        reason: isRelaxed ? '节奏更松，日均点位压力更低。' : '覆盖更满，需要接受更密集转场。',
      },
      {
        label: '覆盖',
        score: `${formatScore(coverageScore)}/10`,
        reason: '按天数、点位数和主题覆盖估算。',
      },
      {
        label: '美食',
        score: `${formatScore(foodScore)}/10`,
        reason: '基于路线文本中的餐饮/街区/夜市等信号估算。',
      },
    ],
    bestFor: audience === 'first-timer'
      ? '适合第一次来、旅行次数不多、希望经典点位尽量多覆盖的人。'
      : '适合已经来过、旅行经验较多、想要小众机位和慢体验的人。',
    tradeoff: audience === 'first-timer'
      ? '取舍：节奏更紧，建议提前确认体力和交通。'
      : '取舍：经典点位覆盖略少，但体验更松、重复感更低。',
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

  const outfitSeeds: Array<{
    gender: OutfitGender
    scene: string
    style: string
    items: Array<{ name: string; category: string; gender: OutfitGender }>
    tips: string
  }> = [
    {
      gender: 'female',
      scene: '女生 · 城市漫步 / 景点拍照',
      style: '女生轻户外舒适穿搭',
      items: [
        { name: '透气短上衣或衬衫', category: '上装', gender: 'female' },
        { name: '舒适长裤/半裙', category: '下装', gender: 'female' },
        { name: '防滑步行鞋', category: '鞋履', gender: 'female' },
        { name: '薄外套或防晒衣', category: '外套', gender: 'female' },
      ],
      tips: '女生版本优先选择低饱和色和轻量层次，兼顾走路舒适度与照片轮廓。',
    },
    {
      gender: 'male',
      scene: '男生 · 城市漫步 / 景点拍照',
      style: '男生轻户外舒适穿搭',
      items: [
        { name: '透气 T 恤或休闲衬衫', category: '上装', gender: 'male' },
        { name: '直筒休闲裤', category: '下装', gender: 'male' },
        { name: '防滑步行鞋', category: '鞋履', gender: 'male' },
        { name: '轻薄夹克或防晒外套', category: '外套', gender: 'male' },
      ],
      tips: '男生版本强调干净线条和实穿层次，适合城市步行、景点拍照和长时间移动。',
    },
    {
      gender: 'female',
      scene: '女生 · 日落 / 观景台',
      style: '女生出片层次感穿搭',
      items: [
        { name: '浅色内搭', category: '上装', gender: 'female' },
        { name: '有廓形的外套或针织衫', category: '外套', gender: 'female' },
        { name: '长裤/长裙', category: '下装', gender: 'female' },
        { name: '小体积斜挎包', category: '配饰', gender: 'female' },
      ],
      tips: '女生版本在日落场景保留外套或披肩，既防风也能增加照片层次。',
    },
    {
      gender: 'female',
      scene: '女生 · 美食街 / 夜游',
      style: '女生夜游轻便出片穿搭',
      items: [
        { name: '修身针织或短外套', category: '上装', gender: 'female' },
        { name: '深色直筒裤/长裙', category: '下装', gender: 'female' },
        { name: '舒适低跟鞋或运动鞋', category: '鞋履', gender: 'female' },
        { name: '小包和轻量配饰', category: '配饰', gender: 'female' },
      ],
      tips: '女生夜游版本控制体积感，方便吃饭、步行和夜景拍照。',
    },
    {
      gender: 'male',
      scene: '男生 · 日落 / 观景台',
      style: '男生出片层次感穿搭',
      items: [
        { name: '浅色内搭', category: '上装', gender: 'male' },
        { name: '廓形衬衫/轻夹克', category: '外套', gender: 'male' },
        { name: '深色直筒裤', category: '下装', gender: 'male' },
        { name: '小背包或斜挎包', category: '配饰', gender: 'male' },
      ],
      tips: '男生版本在观景台和日落场景用外套制造轮廓，避免单薄、也更适合风大环境。',
    },
    {
      gender: 'male',
      scene: '男生 · 美食街 / 夜游',
      style: '男生夜游轻便出片穿搭',
      items: [
        { name: '干净纯色 T 恤/针织', category: '上装', gender: 'male' },
        { name: '深色直筒裤', category: '下装', gender: 'male' },
        { name: '轻便运动鞋', category: '鞋履', gender: 'male' },
        { name: '薄夹克或衬衫外套', category: '外套', gender: 'male' },
      ],
      tips: '男生夜游版本强调干净利落和行动方便，适合夜景、餐饮和临时加点。',
    },
  ]

  await Promise.all(
    outfitSeeds.map((outfit) =>
      createOutfit(tripId, {
        scene: outfit.scene,
        season: '按出发日期复核天气',
        style: outfit.style,
        items: outfit.items,
        tips: outfit.tips,
        images: [],
      }),
    ),
  )

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
      .then((data) => {
        setRouteOptions(data)
        trackAnalyticsEvent({
          event_name: 'route_generation_success',
          event_category: 'conversion',
          metadata: {
            destination_name: destinationName,
            duration_days: duration,
            option_count: data.options.length,
          },
        })
      })
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

  const handleOptionSelect = (optionId: 'A' | 'B') => {
    setSelected(optionId)
    const optionIndex = optionId === 'A' ? 0 : 1
    const selectedOption = (routeOptions as RouteGenerationPayload | null)?.options?.[optionIndex]
    trackAnalyticsEvent({
      event_name: 'route_option_selected',
      event_category: 'selection',
      metadata: {
        destination_name: destinationName,
        option_id: optionId,
        route_title: selectedOption?.title || optionId,
        selection_label: selectedOption?.title || optionId,
      },
    })
  }

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
      trackAnalyticsEvent({
        event_name: 'route_option_confirmed',
        event_category: 'selection',
        metadata: {
          destination_name: destinationName,
          option_id: selected,
          route_title: selectedOption.title,
          selection_label: selectedOption.title,
        },
      })
      trackAnalyticsEvent({
        event_name: 'trip_created',
        event_category: 'conversion',
        metadata: {
          destination_name: destinationName,
          option_id: selected,
          route_title: selectedOption.title,
          selection_label: selectedOption.title,
        },
      })
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
                onSelect={handleOptionSelect}
              />
            ))}
          </div>
          <div className="score-method-card">
            <h4>评分怎么来的？</h4>
            <p>
              当前综合参考四类信号：出片潜力 40%（观景/日落/机位/自然风光等 POI），
              节奏舒适 25%（日均点位和路线 pace），主题覆盖 20%（经典地标、自然、街区等丰富度），
              旅行实用 15%（美食、休息和转场可执行性）。分数用于比较方案差异，不是绝对排名。
            </p>
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
