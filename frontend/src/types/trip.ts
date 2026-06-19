/**
 * 行程相关类型定义
 * 与后端 `app/schemas/domain.py` 对齐
 */

/** 行程状态 */
export type TripStatus = 'draft' | 'confirmed' | 'archived'

/** 行程 */
export interface Trip {
  id: string
  user_id: string
  title: string
  destination_name: string
  start_date: string | null
  end_date: string | null
  status: TripStatus
  cover_image_url: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

/** 行程创建请求 */
export interface TripCreate {
  title: string
  destination_name: string
  start_date?: string | null
  end_date?: string | null
  status?: TripStatus
  cover_image_url?: string | null
  notes?: string | null
}

/** 行程更新请求 */
export interface TripUpdate {
  title?: string
  destination_name?: string
  start_date?: string | null
  end_date?: string | null
  status?: TripStatus
  cover_image_url?: string | null
  notes?: string | null
}

/** 行程天 */
export interface TripDay {
  id: string
  trip_id: string
  day_index: number
  date: string | null
  title: string | null
  summary: string | null
  created_at: string
  updated_at: string
}

/** 行程天创建请求 */
export interface TripDayCreate {
  day_index?: number | null
  date?: string | null
  title?: string | null
  summary?: string | null
}

/** 行程天更新请求 */
export interface TripDayUpdate {
  day_index?: number | null
  date?: string | null
  title?: string | null
  summary?: string | null
}

/** 行程点类型 */
export type TripPointType = 'spot' | 'meal' | 'transport' | 'hotel' | 'other'

/** 行程点 */
export interface TripPoint {
  id: string
  trip_day_id: string
  name: string
  point_type: TripPointType
  address: string | null
  latitude: number | null
  longitude: number | null
  start_time: string | null
  end_time: string | null
  sort_order: number
  notes: string | null
  image_url: string | null
  created_at: string
  updated_at: string
}

/** 行程点创建请求 */
export interface TripPointCreate {
  name: string
  point_type?: TripPointType
  address?: string | null
  latitude?: number | null
  longitude?: number | null
  start_time?: string | null
  end_time?: string | null
  sort_order?: number | null
  notes?: string | null
  image_url?: string | null
}

/** 行程点更新请求 */
export interface TripPointUpdate {
  name?: string
  point_type?: TripPointType
  address?: string | null
  latitude?: number | null
  longitude?: number | null
  start_time?: string | null
  end_time?: string | null
  sort_order?: number | null
  notes?: string | null
  image_url?: string | null
}

/** 重排序请求 */
export interface SortOrderUpdate {
  ordered_ids: string[]
}

/** 打包清单项 */
export interface PackingItem {
  id: string
  trip_id: string
  name: string
  category: string | null
  quantity: number
  is_checked: boolean
  note: string | null
  created_at: string
  updated_at: string
}

/** 打包清单创建请求 */
export interface PackingItemCreate {
  name: string
  category?: string | null
  quantity?: number
  is_checked?: boolean
  note?: string | null
}

/** 打包清单更新请求 */
export interface PackingItemUpdate {
  name?: string
  category?: string | null
  quantity?: number
  is_checked?: boolean
  note?: string | null
}

/** 打包勾选状态更新请求 */
export interface PackingItemCheckUpdate {
  is_checked: boolean
}
