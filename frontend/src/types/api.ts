/**
 * API 通用类型定义
 * 与后端 `app/schemas/common.py` 中的 ApiResponse 结构对齐
 */

/** 分页元信息 */
export interface PaginationMeta {
  total: number
  limit: number
  offset: number
}

/** 请求元信息 */
export interface RequestMeta {
  request_id: string
  timestamp: string
  provider?: string | null
  warnings?: unknown[]
}

/** 统一成功响应 */
export interface ApiResponse<T> {
  success: true
  data: T
  meta: RequestMeta
}

/** 错误详情条目 */
export interface ApiErrorDetail {
  field?: string
  message: string
}

/** 错误响应中的 error 对象 */
export interface ApiErrorObject {
  code: string
  message: string
  details?: ApiErrorDetail[]
}

/** 统一错误响应 */
export interface ApiErrorResponse {
  success: false
  error: ApiErrorObject
  meta: RequestMeta
}

/** 带分页的响应数据 */
export interface PaginatedData<T> {
  items: T[]
  pagination: PaginationMeta
}

/** 列表接口分页元信息（与后端 meta 字段对齐） */
export interface ListMeta {
  page: number
  page_size: number
  total: number
  has_more: boolean
}

/** 列表接口响应数据（{ items, meta } 格式，apiClient 已自动解包 data） */
export interface ListResponse<T> {
  items: T[]
  meta: ListMeta
}

/** 列表查询参数 */
export interface ListQuery {
  page?: number
  page_size?: number
}
