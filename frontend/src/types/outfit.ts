/**
 * 穿搭推荐类型定义
 * 与后端 `app/schemas/outfit.py` 对齐
 */

/** 穿搭单品 */
export interface OutfitItem {
  name: string
  category?: string
  note?: string
  gender?: 'female' | 'male' | 'unisex' | string
}

/** 穿搭推荐 */
export interface OutfitRecommendation {
  id: string
  trip_id: string
  scene: string
  season: string
  style: string
  items: OutfitItem[]
  tips: string | null
  images: string[]
  created_at: string
  updated_at: string
}

/** 穿搭推荐创建请求 */
export interface OutfitRecommendationCreate {
  trip_id?: string | null
  scene: string
  season: string
  style: string
  items: OutfitItem[]
  tips?: string | null
  images?: string[]
}

/** 穿搭推荐更新请求 */
export interface OutfitRecommendationUpdate {
  scene?: string
  season?: string
  style?: string
  items?: OutfitItem[]
  tips?: string | null
  images?: string[]
}

/** AI 穿搭预览图生成结果 */
export interface OutfitPreviewImageResult {
  outfit: OutfitRecommendation
  image_url: string | null
  provider: string
  generated: boolean
  message: string | null
}
