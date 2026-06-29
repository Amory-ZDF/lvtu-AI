/**
 * 规划相关类型定义
 * 与后端 `app/schemas/planning.py` 对齐
 */

/** 图片资源 */
export interface ImageResource {
  category: string
  url: string
  thumbnail_url: string
  alt: string
  provider: string
  placeholder: boolean
  source_url?: string | null
  license?: string | null
  credit?: string | null
}

/** 目的地推荐请求 */
export interface DestinationRecommendationRequest {
  departure_city?: string | null
  budget_min?: number | null
  budget_max?: number | null
  duration_days?: number
  season?: string | null
  travel_style?: string[]
  interests?: string[]
}

/** 目的地推荐项 */
export interface DestinationItem {
  id: string
  name: string
  country_or_region: string
  match_score: number
  budget_range: string
  best_season: string
  vibe_tags: string[]
  reasons: string[]
  hero_image: ImageResource
  gallery: ImageResource[]
}

/** 目的地推荐响应数据 */
export interface DestinationRecommendationPayload {
  query_summary: string
  destinations: DestinationItem[]
}

/** 路线生成请求 */
export interface RouteGenerationRequest {
  destination_id?: string | null
  destination_name: string
  duration_days?: number
  pace?: string
  travelers?: number
  interests?: string[]
}

/** 路线中的景点 */
export interface RouteSpot {
  time_slot: string
  name: string
  description: string
  suggested_duration_hours: number
  category?: string | null
  address?: string | null
  latitude?: number | null
  longitude?: number | null
  images: ImageResource[]
}

/** 路线中的一天计划 */
export interface RouteDayPlan {
  day: number
  theme: string
  commute_tip: string
  spots: RouteSpot[]
}

/** 路线方案 */
export interface RouteOption {
  id: string
  title: string
  pace: string
  estimated_budget: string
  photo_score: number
  summary: string
  days: RouteDayPlan[]
}

/** 路线生成响应数据 */
export interface RouteGenerationPayload {
  destination_name: string
  options: RouteOption[]
}

/** 媒体占位请求 */
export interface MediaPlaceholderRequest {
  categories?: string[]
  destination_name?: string | null
  keywords?: string[]
}

/** 媒体占位分组 */
export interface MediaPlaceholderGroup {
  category: string
  items: ImageResource[]
}

/** 媒体占位响应数据 */
export interface MediaPlaceholderPayload {
  destination_name: string | null
  assets: MediaPlaceholderGroup[]
}
