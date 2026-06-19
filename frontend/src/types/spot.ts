/**
 * 机位推荐类型定义
 * 与后端 `app/schemas/spot.py` 对齐
 */

/** 机位推荐 */
export interface PhotoSpotRecommendation {
  id: string
  trip_id: string
  trip_point_id: string | null
  name: string
  location: string
  composition: string | null
  best_time: string | null
  photo_score: number | null
  tips: string | null
  images: string[]
  created_at: string
  updated_at: string
}

/** 机位推荐创建请求 */
export interface PhotoSpotRecommendationCreate {
  trip_id?: string | null
  trip_point_id?: string | null
  name: string
  location: string
  composition?: string | null
  best_time?: string | null
  photo_score?: number | null
  tips?: string | null
  images?: string[]
}

/** 机位推荐更新请求 */
export interface PhotoSpotRecommendationUpdate {
  trip_point_id?: string | null
  name?: string
  location?: string
  composition?: string | null
  best_time?: string | null
  photo_score?: number | null
  tips?: string | null
  images?: string[]
}
