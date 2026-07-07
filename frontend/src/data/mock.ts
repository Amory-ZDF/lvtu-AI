/**
 * Shared UI data types.
 *
 * Real/mock business data is intentionally not committed to the public repository.
 */

/** 我的行程卡片（首页） */
export interface TripCardData {
  id: string
  title: string
  subtitle: string
  status: 'draft' | 'confirmed'
  gradient: string
  /** 封面图 URL（存在时优先用 LazyImage 渲染，gradient 作为兜底） */
  imageUrl?: string | null
}

/** 目的地预览卡片 */
export interface DestinationPreview {
  id: string
  name: string
  region: string
  duration: string
  season: string
  matchScore: string
  price: string
  gradient: string
  tags: string[]
  reason: string
  stops: { day: string; text: string }[]
  highlights: string[]
  recommended?: boolean
}

/** 方案对比卡片 */
export interface PlanOption {
  id: 'A' | 'B'
  title: string
  subtitle: string
  price: string
  metrics: { level: 'high' | 'mid' | 'low'; label: string }[]
  description: string
  summaryStats?: string[]
  differentiators?: string[]
  scoreBreakdown?: { label: string; score: string; reason: string }[]
  bestFor?: string
  tradeoff?: string
}

/** 行程点（用于拖拽排序） */
export interface StopCardData {
  id: string
  time: string
  title: string
  desc: string
  spotId?: string
  outfitId?: string
}

/** 穿搭卡片 */
export interface OutfitCardData {
  id: string
  sceneTag: string
  emoji: string
  title: string
  desc: string
  gradient: string
  genderLabel?: string
  hasAiPreview?: boolean
}

export interface OutfitDayData {
  dayBadge: 'd1' | 'd2'
  dayLabel: string
  title: string
  cards: OutfitCardData[]
}

/** 机位卡片 */
export interface SpotCardData {
  id: string
  timePill: string
  title: string
  subtitle: string
  gradient: string
  compositionTitle: string
  composition: string
  outfitTitle?: string
  outfit?: string
  warningTitle?: string
  warning?: string
  tags: { cls: 'best' | 'angle' | 'gear' | 'style'; text: string }[]
}

/** 机位详情数据 */
export interface SpotDetailData {
  name: string
  hero: string
  time: string
  rate: string
  difficulty: string
  difficultyLabel: string
  location: string
  composition: string
  outfit: string
  outfitId: string | null
  tags: { c: 'best' | 'angle' | 'gear' | 'style'; t: string }[]
  warning?: string
}

/** 穿搭详情数据 */
export interface OutfitDetailData {
  name: string
  hero: string
  scene: string
  weather: string
  items: string[]
  reason: string
  spotId: string | null
  imageUrl?: string | null
  aiPrompt?: string
  genderLabel?: string
  hasAiPreview?: boolean
}

/** 打包清单 */
export interface PackItemData {
  id: string
  name: string
  packed: boolean
}

export interface PackCategoryData {
  id: string
  title: string
  placeholder: string
  items: PackItemData[]
}
