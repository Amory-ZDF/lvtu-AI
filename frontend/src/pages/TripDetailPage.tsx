/**
 * 行程详情页 (page-trip-detail)
 * 含 4 子 Tab：行程 / 穿搭 / 机位 / 打包
 * 所有数据来自真实后端 API
 * 集成：五态组件、自动保存、版本历史、协同编辑、地图
 */

import { useCallback, useEffect, useMemo, useRef, useState, type DragEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { SpotDetail } from '@/components/SpotDetail'
import { OutfitDetail } from '@/components/OutfitDetail'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorState } from '@/components/ErrorState'
import { EmptyState } from '@/components/EmptyState'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { VersionHistory } from '@/components/VersionHistory'
import { MapView, type MapPoint } from '@/components/MapView'
import { useAutoSave, type SaveStatus } from '@/hooks/useAutoSave'
import { useCollaboration } from '@/hooks/useCollaboration'
import { useUIStore } from '@/store/uiStore'
import { useAuthStore } from '@/store/authStore'
import { trackAnalyticsEvent } from '@/services/analytics'
import {
  getTrip,
  listTripDays,
  listTripPoints,
  createTripPoint,
  updateTripPoint,
  deleteTripPoint,
  reorderTripPoints,
  listPackingItems,
  checkPackingItem,
  createPackingItem,
  deletePackingItem,
} from '@/services/trip'
import { generateOutfitPreviewImage, listOutfits } from '@/services/outfit'
import { listSpots, deleteSpot } from '@/services/spot'
import { createAdjustment } from '@/services/adjustment'
import { getDestinationWeather } from '@/services/planning'
import {
  cssImageWithFallback,
  inferOutfitGender,
  outfitGenderLabel,
  resolveOutfitImage,
  type OutfitGender,
} from '@/utils/outfitImages'
import type {
  Trip,
  TripDay,
  TripPoint,
  TripPointUpdate,
  PackingItem,
  OutfitRecommendation,
  PhotoSpotRecommendation,
  DestinationWeatherPayload,
} from '@/types'
import type {
  SpotCardData,
  SpotDetailData,
  OutfitDetailData,
  OutfitCardData,
  PackCategoryData,
} from '@/data/mock'

type SubTab = 'itinerary' | 'outfit' | 'spots' | 'packing'
type DetailType = 'spot' | 'outfit' | null

/** 删除确认目标 */
interface ConfirmDeleteTarget {
  type: 'point' | 'spot' | 'pack'
  dayId?: string
  index?: number
  id?: string
}

/** 渐变取色 */
const GRADIENTS = [
  'linear-gradient(135deg,oklch(0.63 0.17 198),oklch(0.56 0.15 222))',
  'linear-gradient(135deg,oklch(0.62 0.13 42),oklch(0.55 0.15 62))',
  'linear-gradient(135deg,oklch(0.58 0.15 170),oklch(0.50 0.14 195))',
  'linear-gradient(135deg,oklch(0.56 0.16 215),oklch(0.48 0.14 235))',
]

function pickGradient(id: string): string {
  let hash = 0
  for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) >>> 0
  return GRADIENTS[hash % GRADIENTS.length]
}

/** 格式化时间为 HH:MM */
function formatTime(t: string | null): string {
  if (!t) return ''
  return t.slice(0, 5)
}

/** OutfitRecommendation → OutfitCardData */
function toOutfitCard(o: OutfitRecommendation): OutfitCardData {
  const gender = inferOutfitGender(o.style, o.scene, o.items)
  const fallback = pickGradient(o.id)
  const image = resolveOutfitImage(o.images)
  return {
    id: o.id,
    sceneTag: o.scene,
    emoji: '',
    title: o.style,
    desc: o.items.map((i) => i.name).join(' · '),
    gradient: cssImageWithFallback(image, fallback),
    genderLabel: outfitGenderLabel(gender),
    hasAiPreview: Boolean(image),
  }
}

/** OutfitRecommendation → OutfitDetailData */
function toOutfitDetail(o: OutfitRecommendation): OutfitDetailData {
  const gender = inferOutfitGender(o.style, o.scene, o.items)
  const fallback = pickGradient(o.id)
  const image = resolveOutfitImage(o.images)
  const itemNames = o.items.map((i) => i.name)
  return {
    name: o.style,
    hero: cssImageWithFallback(image, fallback),
    scene: o.scene,
    weather: o.season,
    items: itemNames,
    reason: o.tips || o.items.map((i) => i.name).join('、'),
    spotId: null,
    imageUrl: image || null,
    genderLabel: outfitGenderLabel(gender),
    hasAiPreview: Boolean(image),
  }
}

function groupOutfits(outfits: OutfitRecommendation[]) {
  const groups: Record<OutfitGender, OutfitRecommendation[]> = {
    female: [],
    male: [],
    unisex: [],
  }
  for (const outfit of outfits) {
    groups[inferOutfitGender(outfit.style, outfit.scene, outfit.items)].push(outfit)
  }
  return (['female', 'male', 'unisex'] as OutfitGender[])
    .map((gender) => ({
      gender,
      label: outfitGenderLabel(gender),
      items: groups[gender],
    }))
    .filter((group) => group.items.length > 0)
}

/** PhotoSpotRecommendation → SpotCardData */
function toSpotCard(s: PhotoSpotRecommendation): SpotCardData {
  return {
    id: s.id,
    timePill: s.best_time || '📷 全天',
    title: s.name,
    subtitle: s.location,
    gradient: s.images[0] ? `url(${s.images[0]})` : pickGradient(s.id),
    compositionTitle: '📐 构图建议',
    composition: s.composition || s.tips || '',
    warningTitle: '⚠️ 注意',
    warning: s.tips || undefined,
    tags: [
      { cls: 'best', text: s.photo_score ? `⭐ ${s.photo_score}%` : '⭐ 高出片' },
      { cls: 'angle', text: s.location },
    ],
  }
}

/** PhotoSpotRecommendation → SpotDetailData */
function toSpotDetail(s: PhotoSpotRecommendation): SpotDetailData {
  return {
    name: s.name,
    hero: s.images[0] ? `url(${s.images[0]})` : pickGradient(s.id),
    time: s.best_time ? `📷 最佳时段 ${s.best_time}` : '📷 全天可拍',
    rate: s.photo_score ? `${s.photo_score}%` : '90%',
    difficulty: '★★☆☆☆',
    difficultyLabel: '简单',
    location: s.location,
    composition: s.composition || s.tips || '',
    outfit: '',
    outfitId: null,
    tags: [
      { c: 'best', t: s.photo_score ? `⭐ ${s.photo_score}%` : '⭐ 高出片' },
      { c: 'angle', t: s.location },
    ],
    warning: s.tips || undefined,
  }
}

/** 将 PackingItem[] 分组为 PackCategoryData[] */
function groupPackingItems(items: PackingItem[]): PackCategoryData[] {
  const groups: Record<string, PackingItem[]> = {}
  for (const item of items) {
    const cat = item.category || '其他'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push(item)
  }
  return Object.entries(groups).map(([cat, list]) => ({
    id: cat,
    title: cat,
    placeholder: `添加${cat}...`,
    items: list.map((i) => ({ id: i.id, name: i.name, packed: i.is_checked })),
  }))
}

/** 保存状态指示器文案 */
function saveStatusText(status: SaveStatus): string {
  switch (status) {
    case 'saving':
      return '保存中...'
    case 'saved':
      return '✓ 已保存'
    case 'error':
      return '⚠ 保存失败'
    default:
      return ''
  }
}

function parseTemperature(value?: string | null): number | null {
  if (!value) return null
  const n = Number(value)
  return Number.isFinite(n) ? n : null
}

function formatWeatherSummary(weather: DestinationWeatherPayload | null, destinationName?: string): string {
  if (!weather) return '正在获取目的地实时天气...'
  if (!weather.available) return weather.message || '暂未获取到实时天气，出发前请再次复核。'
  const city = weather.city || destinationName || weather.destination_name
  const parts = [
    weather.weather,
    weather.temperature ? `${weather.temperature}℃` : null,
    weather.humidity ? `湿度 ${weather.humidity}%` : null,
    weather.wind_direction && weather.wind_power
      ? `${weather.wind_direction}风 ${weather.wind_power}级`
      : null,
  ].filter(Boolean)
  return `${city} · ${parts.join(' · ')}`
}

function buildPackingNotices(params: {
  trip: Trip | null
  days: TripDay[]
  pointsByDay: Record<string, TripPoint[]>
  weather: DestinationWeatherPayload | null
}): string[] {
  const destination = params.trip?.destination_name || '目的地'
  const allPoints = Object.values(params.pointsByDay).flat()
  const routeText = `${destination}${allPoints.map((p) => `${p.name}${p.address || ''}${p.notes || ''}`).join('')}`
  const notices = new Set<string>()
  const temp = parseTemperature(params.weather?.temperature)
  const weatherText = params.weather?.weather || ''

  if (/雨|阵雨|雷|雪/.test(weatherText)) {
    notices.add('天气可能有降水：建议带折叠伞、防水外套，并给电子设备准备防水袋。')
  }
  if (temp !== null && temp >= 30) {
    notices.add('气温偏高：优先准备防晒、遮阳帽、补水和透气速干衣物。')
  }
  if (temp !== null && temp <= 10) {
    notices.add('气温偏低：建议增加保暖外套、围巾和可叠穿内搭。')
  }
  if (/山|峡谷|森林|徒步|栈道|张家界|黄山|川西|云南/.test(routeText)) {
    notices.add('含山地/栈道场景：穿防滑步行鞋，包里留一件轻薄外套。')
  }
  if (/海|岛|湖|湿地|漂流/.test(routeText)) {
    notices.add('含水边场景：建议带防晒、驱蚊和可快速收纳的防水袋。')
  }
  if (/夜景|日落|观景|机位|拍照|摄影/.test(routeText)) {
    notices.add('有拍照/观景安排：提前清理手机存储，带充电宝和镜头布。')
  }
  if (params.days.length >= 4) {
    notices.add('行程超过 3 天：衣物按“可叠穿 + 可重复搭配”准备，减少行李重量。')
  }
  notices.add(`出发前 24 小时复核 ${destination} 天气、景区开放时间和预约规则。`)
  return Array.from(notices).slice(0, 5)
}

export function TripDetailPage() {
  const navigate = useNavigate()
  const { tripId = '' } = useParams()
  const showToast = useUIStore((s) => s.showToast)
  const user = useAuthStore((s) => s.user)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  const [activeTab, setActiveTab] = useState<SubTab>('itinerary')
  const [trip, setTrip] = useState<Trip | null>(null)
  const [days, setDays] = useState<TripDay[]>([])
  const [pointsByDay, setPointsByDay] = useState<Record<string, TripPoint[]>>({})
  const [packingItems, setPackingItems] = useState<PackingItem[]>([])
  const [outfits, setOutfits] = useState<OutfitRecommendation[]>([])
  const [spots, setSpots] = useState<PhotoSpotRecommendation[]>([])
  const [destinationWeather, setDestinationWeather] = useState<DestinationWeatherPayload | null>(null)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [adjusting, setAdjusting] = useState(false)

  // 拖拽
  const [dragSrc, setDragSrc] = useState<{ dayId: string; index: number } | null>(null)
  const [dragOverIndex, setDragOverIndex] = useState<{ dayId: string; index: number } | null>(null)

  // 打包输入
  const [packInputs, setPackInputs] = useState<Record<string, string>>({})

  // 详情弹窗
  const [detailType, setDetailType] = useState<DetailType>(null)
  const [detailId, setDetailId] = useState<string | null>(null)
  const [generatingOutfitId, setGeneratingOutfitId] = useState<string | null>(null)

  // 删除确认
  const [confirmDelete, setConfirmDelete] = useState<ConfirmDeleteTarget | null>(null)

  // 行程点编辑草稿（用于自动保存）
  const [pointDrafts, setPointDrafts] = useState<Record<string, TripPointUpdate>>({})

  // 打包保存状态
  const [packStatus, setPackStatus] = useState<SaveStatus>('idle')

  // 版本历史
  const [versionOpen, setVersionOpen] = useState(false)

  // 远程光标标记
  const [remoteCursor, setRemoteCursor] = useState<{ userId: string } | null>(null)
  const cursorTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // pointsByDay 的 ref，供 saveFn 读取最新值
  const pointsByDayRef = useRef(pointsByDay)
  useEffect(() => {
    pointsByDayRef.current = pointsByDay
  }, [pointsByDay])

  // ── 协同编辑 ──
  const handleRemoteEdit = useCallback(
    (userId: string) => {
      showToast(`他人（${userId.slice(-4)}）已修改行程，请刷新查看`)
    },
    [showToast],
  )
  const handleRemoteCursor = useCallback((userId: string) => {
    setRemoteCursor({ userId })
    if (cursorTimerRef.current) clearTimeout(cursorTimerRef.current)
    cursorTimerRef.current = setTimeout(() => setRemoteCursor(null), 2000)
  }, [])
  const { onlineUsers, connected, sendEdit } = useCollaboration(tripId, {
    onRemoteEdit: handleRemoteEdit,
    onRemoteCursor: handleRemoteCursor,
  })

  // ── 行程点自动保存 ──
  const savePointDrafts = useCallback(
    async (drafts: Record<string, TripPointUpdate>) => {
      const entries = Object.entries(drafts)
      if (entries.length === 0) return
      await Promise.all(
        entries.map(async ([pointId, payload]) => {
          let dayId: string | null = null
          for (const [did, pts] of Object.entries(pointsByDayRef.current)) {
            if (pts.some((p) => p.id === pointId)) {
              dayId = did
              break
            }
          }
          if (!dayId) return
          await updateTripPoint(dayId, pointId, payload)
        }),
      )
    },
    [],
  )
  const pointSave = useAutoSave(pointDrafts, savePointDrafts, 1500)

  // 综合保存状态
  const overallSaveStatus: SaveStatus = useMemo(() => {
    if (pointSave.status === 'saving' || packStatus === 'saving') return 'saving'
    if (pointSave.status === 'error' || packStatus === 'error') return 'error'
    if (pointSave.status === 'saved' || packStatus === 'saved') return 'saved'
    return 'idle'
  }, [pointSave.status, packStatus])

  // ── 初始加载 ──
  const loadData = useCallback(() => {
    if (!tripId || !user) return
    setLoading(true)
    setError(null)
    let cancelled = false

    Promise.all([
      getTrip(user.id, tripId),
      listTripDays(tripId),
      listPackingItems(tripId),
      listOutfits(tripId),
      listSpots(tripId),
    ])
      .then(async ([tripRes, daysRes, packingRes, outfitsRes, spotsRes]) => {
        if (cancelled) return
        setTrip(tripRes)
        setDays(daysRes.items)
        setPackingItems(packingRes.items)
        setOutfits(outfitsRes.items)
        setSpots(spotsRes.items)
        // 加载每天的行程点
        const pointsMap: Record<string, TripPoint[]> = {}
        await Promise.all(
          daysRes.items.map(async (day) => {
            const pts = await listTripPoints(day.id)
            if (!cancelled) pointsMap[day.id] = pts.items
          }),
        )
        if (!cancelled) {
          setPointsByDay(pointsMap)
          // 重置草稿
          setPointDrafts({})
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : '加载行程失败')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [tripId, user])

  useEffect(() => {
    if (!tripId) return
    if (!isAuthenticated || !user) {
      setLoading(false)
      return
    }
    const cleanup = loadData()
    return cleanup
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tripId, isAuthenticated, user])

  useEffect(() => {
    const destinationName = trip?.destination_name
    if (!destinationName) {
      setDestinationWeather(null)
      return
    }
    let cancelled = false
    setDestinationWeather(null)
    getDestinationWeather(destinationName)
      .then((data) => {
        if (!cancelled) setDestinationWeather(data)
      })
      .catch(() => {
        if (!cancelled) {
          setDestinationWeather({
            destination_name: destinationName,
            available: false,
            source: 'amap',
            message: '暂未获取到实时天气，出发前请再次复核。',
          })
        }
      })
    return () => {
      cancelled = true
    }
  }, [trip?.destination_name])

  // ── 拖拽排序 ──
  const handleDragStart = (dayId: string, index: number) => {
    setDragSrc({ dayId, index })
  }

  const handleDragOver = (e: DragEvent, dayId: string, index: number) => {
    e.preventDefault()
    setDragOverIndex({ dayId, index })
  }

  const handleDrop = async (dayId: string, index: number) => {
    if (!dragSrc || dragSrc.dayId !== dayId || dragSrc.index === index) {
      setDragSrc(null)
      setDragOverIndex(null)
      return
    }
    const list = pointsByDay[dayId] || []
    const next = [...list]
    const srcIdx = dragSrc.index
    const dstIdx = index
    // 先保存并交换两个元素的时间（splice 之前索引仍正确）
    const srcTime = next[srcIdx].start_time
    const dstTime = next[dstIdx].start_time
    next[srcIdx] = { ...next[srcIdx], start_time: dstTime }
    next[dstIdx] = { ...next[dstIdx], start_time: srcTime }
    // 再调整顺序
    const [moved] = next.splice(srcIdx, 1)
    next.splice(dstIdx, 0, moved)
    setPointsByDay((prev) => ({ ...prev, [dayId]: next }))
    setDragSrc(null)
    setDragOverIndex(null)
    // 调用重排接口
    try {
      await reorderTripPoints(dayId, next.map((p) => p.id))
    } catch (err) {
      showToast(err instanceof Error ? err.message : '排序失败')
    }
  }

  const handleDragEnd = () => {
    setDragSrc(null)
    setDragOverIndex(null)
  }

  // ── 行程点编辑（内联 + 自动保存 + 协同广播） ──
  const handlePointEdit = (
    dayId: string,
    pointId: string,
    field: keyof TripPointUpdate,
    value: string,
  ) => {
    setPointsByDay((prev) => ({
      ...prev,
      [dayId]: (prev[dayId] || []).map((p) =>
        p.id === pointId ? { ...p, [field]: value || null } : p,
      ),
    }))
    setPointDrafts((prev) => ({
      ...prev,
      [pointId]: { ...prev[pointId], [field]: value || null },
    }))
    // 广播编辑事件
    sendEdit({ pointId, field, value })
  }

  // ── 删除操作（带确认） ──
  const requestDeletePoint = (dayId: string, index: number) => {
    setConfirmDelete({ type: 'point', dayId, index })
  }
  const requestDeleteSpot = (id: string) => {
    setConfirmDelete({ type: 'spot', id })
  }
  const requestDeletePack = (id: string) => {
    setConfirmDelete({ type: 'pack', id })
  }

  const confirmDeleteAction = async () => {
    if (!confirmDelete) return
    const target = confirmDelete
    setConfirmDelete(null)
    if (target.type === 'point' && target.dayId && typeof target.index === 'number') {
      await removeStop(target.dayId, target.index)
    } else if (target.type === 'spot' && target.id) {
      await removeSpot(target.id)
    } else if (target.type === 'pack' && target.id) {
      await removePackItem(target.id)
    }
  }

  const removeStop = async (dayId: string, index: number) => {
    const list = pointsByDay[dayId] || []
    const point = list[index]
    if (!point) return
    setPointsByDay((prev) => ({
      ...prev,
      [dayId]: list.filter((_, i) => i !== index),
    }))
    try {
      await deleteTripPoint(dayId, point.id)
      showToast('已删除行程点')
    } catch (err) {
      showToast(err instanceof Error ? err.message : '删除失败')
      // 回滚
      setPointsByDay((prev) => ({ ...prev, [dayId]: list }))
    }
  }

  const addStop = async (dayId: string) => {
    const list = pointsByDay[dayId] || []
    try {
      const newPoint = await createTripPoint(dayId, {
        name: '新行程点',
        point_type: 'other',
        sort_order: list.length,
      })
      setPointsByDay((prev) => ({ ...prev, [dayId]: [...list, newPoint] }))
      showToast('已添加行程点')
    } catch (err) {
      showToast(err instanceof Error ? err.message : '添加失败')
    }
  }

  // ── 详情弹窗 ──
  const openSpotDetail = (id: string) => {
    setDetailType('spot')
    setDetailId(id)
  }

  const openOutfitDetail = (id: string) => {
    setDetailType('outfit')
    setDetailId(id)
  }

  const closeDetail = () => {
    setDetailType(null)
    setDetailId(null)
  }

  const handleGenerateOutfitPreview = async (outfitId: string) => {
    setGeneratingOutfitId(outfitId)
    try {
      const result = await generateOutfitPreviewImage(outfitId, true)
      setOutfits((prev) => prev.map((item) => (item.id === outfitId ? result.outfit : item)))
      trackAnalyticsEvent({
        event_name: 'outfit_preview_generated',
        event_category: 'conversion',
        metadata: {
          outfit_id: outfitId,
          generated: result.generated,
        },
      })
      showToast(result.message || 'AI 穿搭预览图已生成')
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'AI 穿搭预览生成失败')
    } finally {
      setGeneratingOutfitId(null)
    }
  }

  // ── 自然语言改写 ──
  const handleAdjust = async (instruction: string) => {
    if (!instruction.trim()) return
    setAdjusting(true)
    try {
      await createAdjustment(tripId, { instruction })
      showToast('AI 正在根据你的要求调整行程...')
      // 重新加载行程天和点
      const daysRes = await listTripDays(tripId)
      setDays(daysRes.items)
      const pointsMap: Record<string, TripPoint[]> = {}
      await Promise.all(
        daysRes.items.map(async (day) => {
          const pts = await listTripPoints(day.id)
          pointsMap[day.id] = pts.items
        }),
      )
      setPointsByDay(pointsMap)
      setPointDrafts({})
    } catch (err) {
      showToast(err instanceof Error ? err.message : '调整失败')
    } finally {
      setAdjusting(false)
    }
  }

  // ── 机位删除 ──
  const removeSpot = async (id: string) => {
    setSpots((prev) => prev.filter((s) => s.id !== id))
    try {
      await deleteSpot(id)
      showToast('已删除机位')
    } catch (err) {
      showToast(err instanceof Error ? err.message : '删除失败')
    }
  }

  // ── 打包清单（带保存状态） ──
  const togglePackItem = async (itemId: string) => {
    const item = packingItems.find((i) => i.id === itemId)
    if (!item) return
    const next = !item.is_checked
    setPackingItems((prev) =>
      prev.map((i) => (i.id === itemId ? { ...i, is_checked: next } : i)),
    )
    setPackStatus('saving')
    try {
      await checkPackingItem(tripId, itemId, next)
      setPackStatus('saved')
    } catch (err) {
      showToast(err instanceof Error ? err.message : '更新失败')
      setPackStatus('error')
      setPackingItems((prev) =>
        prev.map((i) => (i.id === itemId ? { ...i, is_checked: !next } : i)),
      )
    }
  }

  const removePackItem = async (itemId: string) => {
    setPackingItems((prev) => prev.filter((i) => i.id !== itemId))
    setPackStatus('saving')
    try {
      await deletePackingItem(tripId, itemId)
      setPackStatus('saved')
    } catch (err) {
      showToast(err instanceof Error ? err.message : '删除失败')
      setPackStatus('error')
    }
  }

  const addPackItem = async (category: string) => {
    const name = (packInputs[category] || '').trim()
    if (!name) return
    setPackStatus('saving')
    try {
      const newItem = await createPackingItem(tripId, { name, category })
      setPackingItems((prev) => [...prev, newItem])
      setPackInputs((prev) => ({ ...prev, [category]: '' }))
      setPackStatus('saved')
    } catch (err) {
      showToast(err instanceof Error ? err.message : '添加失败')
      setPackStatus('error')
    }
  }

  // 打包进度
  const packedCount = packingItems.filter((i) => i.is_checked).length
  const totalCount = packingItems.length
  const packPercent = totalCount > 0 ? Math.round((packedCount / totalCount) * 100) : 0
  const packCategories = groupPackingItems(packingItems)
  const weatherSummary = formatWeatherSummary(destinationWeather, trip?.destination_name)
  const packingNotices = buildPackingNotices({
    trip,
    days,
    pointsByDay,
    weather: destinationWeather,
  })

  // 地图点位（所有有坐标的行程点）
  const mapPoints: MapPoint[] = useMemo(() => {
    const result: MapPoint[] = []
    for (const pts of Object.values(pointsByDay)) {
      for (const p of pts) {
        const latitude = typeof p.latitude === 'number' ? p.latitude : Number(p.latitude)
        const longitude = typeof p.longitude === 'number' ? p.longitude : Number(p.longitude)
        if (Number.isFinite(latitude) && Number.isFinite(longitude)) {
          result.push({ name: p.name, latitude, longitude })
        }
      }
    }
    return result
  }, [pointsByDay])

  // ── 渲染行程点卡片（含内联编辑） ──
  const renderStopCard = (point: TripPoint, index: number, dayId: string) => {
    const isDragging = dragSrc?.dayId === dayId && dragSrc.index === index
    const isDragOver = dragOverIndex?.dayId === dayId && dragOverIndex.index === index
    return (
      <div
        key={point.id}
        className={`stop-card${isDragging ? ' dragging' : ''}${isDragOver ? ' drag-over' : ''}`}
        draggable
        onDragStart={() => handleDragStart(dayId, index)}
        onDragEnd={handleDragEnd}
        onDragOver={(e) => handleDragOver(e, dayId, index)}
        onDrop={() => handleDrop(dayId, index)}
      >
        <span className="stop-handle" title="拖拽排序">⋮⋮</span>
        <input
          type="time"
          className="stop-time"
          value={formatTime(point.start_time)}
          onChange={(e) => handlePointEdit(dayId, point.id, 'start_time', e.target.value)}
          onDragStart={(e) => e.stopPropagation()}
          style={{
            border: 'none',
            background: 'transparent',
            color: 'var(--brand)',
            fontWeight: 600,
            fontSize: '0.85rem',
            width: '70px',
            cursor: 'text',
          }}
        />
        <div className="stop-body" style={{ flex: 1, flexDirection: 'column', gap: '2px' }}>
          <input
            type="text"
            value={point.name}
            placeholder="行程点名称"
            onChange={(e) => handlePointEdit(dayId, point.id, 'name', e.target.value)}
            onDragStart={(e) => e.stopPropagation()}
            style={{
              border: 'none',
              background: 'transparent',
              fontWeight: 700,
              fontSize: '0.95rem',
              width: '100%',
              padding: 0,
              outline: 'none',
            }}
          />
          <input
            type="text"
            value={point.notes || ''}
            placeholder="备注 / 描述"
            onChange={(e) => handlePointEdit(dayId, point.id, 'notes', e.target.value)}
            onDragStart={(e) => e.stopPropagation()}
            style={{
              border: 'none',
              background: 'transparent',
              fontSize: '0.8rem',
              color: 'var(--ink-secondary)',
              width: '100%',
              padding: 0,
              outline: 'none',
            }}
          />
        </div>
        <div className="stop-actions">
          <button
            className="stop-act del"
            title="删除"
            onClick={(e) => {
              e.stopPropagation()
              requestDeletePoint(dayId, index)
            }}
          >
            ×
          </button>
        </div>
      </div>
    )
  }

  const renderDayPanel = (day: TripDay) => {
    const dayPoints = pointsByDay[day.id] || []
    return (
      <div className="day-panel" key={day.id}>
        <div className="day-panel-header">
          <div className={`day-num d1`}>D{day.day_index}</div>
          <div>
            <h4>{day.title || `第 ${day.day_index} 天`}</h4>
            <p>{day.date || day.summary || ''}</p>
          </div>
        </div>
        <div className="stop-list">
          {dayPoints.map((point, index) => renderStopCard(point, index, day.id))}
        </div>
        <button className="add-stop-btn" onClick={() => addStop(day.id)}>
          <span className="plus-circle">+</span> 添加行程点
        </button>
      </div>
    )
  }

  // ── 未登录 ──
  if (!isAuthenticated || !user) {
    return (
      <div className="page">
        <EmptyState
          icon="🔐"
          title="请先登录"
          description="登录后查看行程详情"
          action={
            <button
              className="btn btn-primary"
              onClick={() => navigate(`/login?redirect=/trips/${tripId}`)}
            >
              去登录
            </button>
          }
        />
      </div>
    )
  }

  if (loading) {
    return (
      <div className="page">
        <LoadingSpinner label="加载行程中..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="page">
        <ErrorState
          title="加载行程失败"
          description={error}
          action={<button className="btn btn-primary" onClick={() => navigate(0)}>重试</button>}
        />
      </div>
    )
  }

  if (!trip) {
    return (
      <div className="page">
        <EmptyState
          icon="🗺️"
          title="行程不存在"
          description="该行程可能已被删除"
          action={<button className="btn btn-primary" onClick={() => navigate('/')}>返回首页</button>}
        />
      </div>
    )
  }

  // 当前详情数据
  const currentSpot = spots.find((s) => s.id === detailId)
  const currentOutfit = outfits.find((o) => o.id === detailId)

  // 删除确认弹窗文案
  const deleteConfirmText = confirmDelete
    ? confirmDelete.type === 'point'
      ? '确定要删除这个行程点吗？'
      : confirmDelete.type === 'spot'
        ? '确定要删除这个机位吗？'
        : '确定要删除这个物品吗？'
    : ''

  return (
    <div className="page">
      <button className="back-link" onClick={() => navigate('/')}>
        ← 返回首页
      </button>

      <div className="detail-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ flex: 1, minWidth: '200px' }}>
            <h1>{trip.title}</h1>
            <p className="hint">
              {[trip.destination_name, trip.notes].filter(Boolean).join(' · ')}
            </p>
            <div className="detail-meta">
              {trip.start_date && <span>📅 {trip.start_date}{trip.end_date ? `—${trip.end_date}` : ''}</span>}
              <span>📌 {trip.destination_name}</span>
              <span>🏷️ {trip.status === 'draft' ? '草稿' : trip.status === 'confirmed' ? '已确认' : '已归档'}</span>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px' }}>
            {/* 保存状态指示器 */}
            {overallSaveStatus !== 'idle' && (
              <span
                style={{
                  fontSize: '0.78rem',
                  color:
                    overallSaveStatus === 'error'
                      ? 'oklch(0.5 0.16 22)'
                      : overallSaveStatus === 'saving'
                        ? 'var(--ink-secondary)'
                        : 'oklch(0.5 0.13 150)',
                }}
              >
                {saveStatusText(overallSaveStatus)}
              </span>
            )}
            {/* 协同编辑：在线用户 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              {onlineUsers.map((u) => (
                <span
                  key={u.user_id}
                  title={u.display_name || u.user_id}
                  style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    background: pickGradient(u.user_id),
                    color: '#fff',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                  }}
                >
                  {u.display_name?.[0] || '?'}
                </span>
              ))}
              <span
                style={{
                  fontSize: '0.72rem',
                  color: connected ? 'oklch(0.5 0.13 150)' : 'var(--ink-tertiary)',
                }}
              >
                {connected ? '● 协同在线' : '○ 未连接'}
              </span>
            </div>
            {/* 版本历史入口 */}
            <button
              className="btn btn-secondary"
              style={{ padding: '5px 12px', fontSize: '0.82rem' }}
              onClick={() => setVersionOpen(true)}
            >
              🕘 历史版本
            </button>
          </div>
        </div>
      </div>

      {/* 远程光标提示 */}
      {remoteCursor && (
        <div
          style={{
            display: 'inline-block',
            padding: '4px 10px',
            borderRadius: '12px',
            background: 'var(--surface-2)',
            fontSize: '0.78rem',
            color: 'var(--ink-secondary)',
            marginBottom: '10px',
          }}
        >
          👤 有人正在浏览
        </div>
      )}

      <nav className="sub-tabs">
        <button
          className={`sub-tab${activeTab === 'itinerary' ? ' active' : ''}`}
          onClick={() => setActiveTab('itinerary')}
        >
          📋 行程
        </button>
        <button
          className={`sub-tab${activeTab === 'outfit' ? ' active' : ''}`}
          onClick={() => setActiveTab('outfit')}
        >
          👗 穿搭
        </button>
        <button
          className={`sub-tab${activeTab === 'spots' ? ' active' : ''}`}
          onClick={() => setActiveTab('spots')}
        >
          📸 机位
        </button>
        <button
          className={`sub-tab${activeTab === 'packing' ? ' active' : ''}`}
          onClick={() => setActiveTab('packing')}
        >
          🎒 打包
        </button>
      </nav>

      {/* ── 行程子 Tab ── */}
      {activeTab === 'itinerary' && (
        <div className="sub-panel active">
          {/* 地图 */}
          {mapPoints.length > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <MapView points={mapPoints} height={320} />
            </div>
          )}
          <div className="nl-modify">
            <div className="nl-icon">💬</div>
            <input
              type="text"
              className="nl-input"
              disabled={adjusting}
              placeholder="想调整行程？直接告诉我，比如「把第二天下午改轻松一点」「加一个拍照点」…"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  const val = (e.target as HTMLInputElement).value
                  if (val.trim()) {
                    handleAdjust(val)
                    ;(e.target as HTMLInputElement).value = ''
                  }
                }
              }}
            />
            <button
              className="nl-send"
              disabled={adjusting}
              onClick={(e) => {
                const input = e.currentTarget.previousElementSibling as HTMLInputElement
                if (input.value.trim()) {
                  handleAdjust(input.value)
                  input.value = ''
                }
              }}
            >
              →
            </button>
          </div>
          {days.length === 0 ? (
            <EmptyState
              icon="📅"
              title="还没有行程安排"
              description="点击下方按钮添加第一天"
            />
          ) : (
            <div className="day-grid">
              {days.map((day) => renderDayPanel(day))}
            </div>
          )}
          {trip.notes && (
            <div className="notes-bar">
              <strong>⚠️ 注意事项</strong>&nbsp;&nbsp;{trip.notes}
            </div>
          )}
        </div>
      )}

      {/* ── 穿搭子 Tab ── */}
      {activeTab === 'outfit' && (
        <div className="sub-panel active">
          <div className="outfit-top-row">
            <div className="outfit-intro">
              <h2 style={{ fontSize: '1.25rem', marginBottom: '2px' }}>👗 穿搭推荐</h2>
              <p className="hint">基于行程场景与天气生成</p>
            </div>
          </div>
          {outfits.length === 0 ? (
            <EmptyState icon="👗" title="暂无穿搭推荐" description="AI 将根据行程自动生成穿搭建议" />
          ) : (
            <>
              {groupOutfits(outfits).map((group) => (
                <div className="outfit-day" key={group.gender}>
                  <h3>
                    <span className="day-badge d1">{group.label}</span>
                    共 {group.items.length} 套推荐
                  </h3>
                  <div className="outfit-cards">
                    {group.items.map((o) => {
                      const card = toOutfitCard(o)
                      const isGeneratingPreview = generatingOutfitId === o.id
                      const handleOutfitCardClick = () => {
                        if (!card.hasAiPreview) {
                          if (!isGeneratingPreview) void handleGenerateOutfitPreview(o.id)
                          return
                        }
                        openOutfitDetail(o.id)
                      }
                      return (
                        <div
                          key={o.id}
                          className={`outfit-card${card.hasAiPreview ? ' has-preview' : ' needs-preview'}${isGeneratingPreview ? ' is-generating' : ''}`}
                          onClick={handleOutfitCardClick}
                        >
                          <div
                            className={`outfit-visual${card.hasAiPreview ? ' has-preview' : ' needs-preview'}${isGeneratingPreview ? ' is-generating' : ''}`}
                            style={{ backgroundImage: card.gradient }}
                          >
                            <span className="scene-tag">{card.sceneTag}</span>
                            {card.genderLabel && <span className="gender-tag">{card.genderLabel}</span>}
                            <span className={card.hasAiPreview ? 'ai-preview-tag' : 'outfit-preview-hint'}>
                              {isGeneratingPreview
                                ? '正在生成...'
                                : card.hasAiPreview
                                  ? 'AI 预览'
                                  : '点击生成 AI 预览'}
                            </span>
                            {card.emoji && <span className="emoji">{card.emoji}</span>}
                          </div>
                          <div className="outfit-body">
                            <h5>{card.title}</h5>
                            <p>{card.desc}</p>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      )}

      {/* ── 机位子 Tab ── */}
      {activeTab === 'spots' && (
        <div className="sub-panel active">
          <div style={{ marginBottom: '20px' }}>
            <h2 style={{ fontSize: '1.25rem', marginBottom: '2px' }}>📸 机位推荐</h2>
            <p className="hint">
              {trip.destination_name} · {spots.length}个精选机位 · 含拍摄时间、构图建议
            </p>
          </div>
          {spots.length === 0 ? (
            <EmptyState icon="📸" title="暂无机位推荐" description="AI 将根据行程自动推荐拍照机位" />
          ) : (
            <div className="spots-grid">
              {spots.map((s) => {
                const card = toSpotCard(s)
                return (
                  <div
                    key={s.id}
                    className="spot-card"
                    onClick={() => openSpotDetail(s.id)}
                  >
                    <button
                      className="spot-del"
                      title="删除"
                      onClick={(e) => {
                        e.stopPropagation()
                        requestDeleteSpot(s.id)
                      }}
                    >
                      ×
                    </button>
                    <div className="spot-hero" style={{ backgroundImage: card.gradient }}>
                      <span className="spot-time-pill">{card.timePill}</span>
                      <div className="spot-hero-text">
                        <h3>{card.title}</h3>
                        <p>{card.subtitle}</p>
                      </div>
                    </div>
                    <div className="spot-body">
                      <div className="spot-tip">
                        <h5>{card.compositionTitle}</h5>
                        <p>{card.composition}</p>
                      </div>
                      {card.warning && (
                        <div className="spot-tip">
                          <h5>{card.warningTitle}</h5>
                          <p>{card.warning}</p>
                        </div>
                      )}
                      <div className="spot-tags">
                        {card.tags.map((tag) => (
                          <span key={tag.text} className={`spot-tag ${tag.cls}`}>
                            {tag.text}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* ── 打包子 Tab ── */}
      {activeTab === 'packing' && (
        <div className="sub-panel active">
          <div className="pack-layout">
            <div>
              <h2 style={{ fontSize: '1.25rem', marginBottom: '4px' }}>🎒 打包清单</h2>
              <p className="hint" style={{ marginBottom: '22px' }}>
                点击标记已打包
              </p>
              {packCategories.length === 0 ? (
                <EmptyState icon="🎒" title="暂无打包清单" description="在下方添加你的第一件物品" />
              ) : (
                packCategories.map((cat) => (
                  <div key={cat.id} className="pack-category">
                    <h4>{cat.title}</h4>
                    <div className="pack-items">
                      {cat.items.map((item) => (
                        <div
                          key={item.id}
                          className={`pack-item${item.packed ? ' packed' : ''}`}
                          onClick={() => togglePackItem(item.id)}
                        >
                          <span className="pack-check">{item.packed ? '✓' : ''}</span>
                          <span className="item-name">{item.name}</span>
                          <button
                            className="del-btn"
                            title="删除"
                            onClick={(e) => {
                              e.stopPropagation()
                              requestDeletePack(item.id)
                            }}
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                    <div className="pack-add-row">
                      <input
                        className="pack-input"
                        placeholder={cat.placeholder}
                        value={packInputs[cat.id] || ''}
                        onChange={(e) =>
                          setPackInputs((prev) => ({ ...prev, [cat.id]: e.target.value }))
                        }
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') addPackItem(cat.id)
                        }}
                      />
                      <button
                        className="add-btn"
                        style={{ width: 'auto', margin: 0, padding: '7px 12px', flexShrink: 0 }}
                        onClick={() => addPackItem(cat.id)}
                      >
                        +
                      </button>
                    </div>
                  </div>
                ))
              )}
              {/* 兜底添加分类 */}
              <div className="pack-add-row" style={{ marginTop: '12px' }}>
                <input
                  className="pack-input"
                  placeholder="添加新分类的物品..."
                  value={packInputs['default'] || ''}
                  onChange={(e) =>
                    setPackInputs((prev) => ({ ...prev, default: e.target.value }))
                  }
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') addPackItem('其他')
                  }}
                />
                <button
                  className="add-btn"
                  style={{ width: 'auto', margin: 0, padding: '7px 12px', flexShrink: 0 }}
                  onClick={() => addPackItem('其他')}
                >
                  +
                </button>
              </div>
            </div>
            <aside className="pack-sidebar-card">
              <h4>📦 打包进度</h4>
              <div className="bar">
                <div className="bar-fill" style={{ width: `${packPercent}%` }}></div>
              </div>
              <p>
                <span className="pack-count">{packedCount}</span>
                <small> / {totalCount} 件已打包</small>
              </p>
              <div className="pack-side-section">
                <h4>🌤️ 目的地天气</h4>
                <p className="pack-weather-main">{weatherSummary}</p>
                {destinationWeather?.available && destinationWeather.report_time && (
                  <small>高德天气 · {destinationWeather.report_time}</small>
                )}
              </div>
              <div className="pack-side-section">
                <h4>⚠️ 出发注意事项</h4>
                <ul className="pack-notice-list">
                  {packingNotices.map((notice) => (
                    <li key={notice}>{notice}</li>
                  ))}
                </ul>
              </div>
            </aside>
          </div>
        </div>
      )}

      {/* 详情弹窗 */}
      {detailType === 'spot' && detailId && currentSpot && (
        <SpotDetail
          data={toSpotDetail(currentSpot)}
          onClose={closeDetail}
        />
      )}
      {detailType === 'outfit' && detailId && currentOutfit && (
        <OutfitDetail
          data={toOutfitDetail(currentOutfit)}
          onClose={closeDetail}
          onGenerateImage={() => handleGenerateOutfitPreview(currentOutfit.id)}
          generatingImage={generatingOutfitId === currentOutfit.id}
        />
      )}

      {/* 删除确认弹窗 */}
      <ConfirmDialog
        open={confirmDelete !== null}
        title="确认删除"
        description={deleteConfirmText}
        confirmText="删除"
        onConfirm={confirmDeleteAction}
        onCancel={() => setConfirmDelete(null)}
      />

      {/* 版本历史 */}
      <VersionHistory
        open={versionOpen}
        tripId={tripId}
        onClose={() => setVersionOpen(false)}
        onRestored={() => {
          showToast('已回退到历史版本')
          // 刷新页面数据
          if (loadData) loadData()
        }}
      />
    </div>
  )
}

export default TripDetailPage
