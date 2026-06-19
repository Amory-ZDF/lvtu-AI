/**
 * 统一 API 客户端封装
 * - baseURL 从环境变量读取
 * - 自动注入 Authorization header
 * - 响应解包：从 {success, data, meta} 中提取 data
 * - 错误处理：抛出带 code 的 ApiError
 * - 401 时自动跳转登录页
 */

import type {
  ApiResponse,
  ApiErrorResponse,
  ApiErrorObject,
} from '@/types'

/** 带错误码的 API 异常 */
export class ApiError extends Error {
  code: string
  details?: ApiErrorObject['details']
  status: number

  constructor(
    message: string,
    code: string,
    status: number,
    details?: ApiErrorObject['details'],
  ) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.details = details
  }
}

/** 查询参数类型 */
export type QueryParams = Record<string, string | number | boolean | undefined | null>

/** 请求配置 */
export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE'
  body?: unknown
  query?: QueryParams
  /** 是否跳过自动注入 token（如登录接口本身） */
  skipAuth?: boolean
  /** 是否跳过响应解包（直接返回原始响应） */
  raw?: boolean
  headers?: Record<string, string>
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

/** localStorage 中存储 access_token 的 key */
export const ACCESS_TOKEN_KEY = 'lv_access_token'
export const REFRESH_TOKEN_KEY = 'lv_refresh_token'

/** 获取当前 token（避免循环依赖，从 localStorage 直接读取） */
function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

/** 401 跳转登录页（避免在 SSR 或测试环境报错） */
function redirectToLogin(): void {
  if (typeof window === 'undefined') return
  const current = window.location.pathname + window.location.search
  if (!window.location.pathname.startsWith('/login')) {
    window.location.href = `/login?redirect=${encodeURIComponent(current)}`
  }
}

/** 拼接 query string */
function buildQueryString(query: QueryParams): string {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== '') {
      params.append(key, String(value))
    }
  }
  const qs = params.toString()
  return qs ? `?${qs}` : ''
}

/** 判断响应是否为统一包裹格式 */
function isWrappedResponse(json: unknown): json is ApiResponse<unknown> | ApiErrorResponse {
  if (typeof json !== 'object' || json === null) return false
  return 'success' in json
}

/**
 * 发起 API 请求并自动解包
 * @param path 路径，如 `/auth/login`（会拼接到 BASE_URL）
 * @returns 解包后的 data
 */
export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const {
    method = 'GET',
    body,
    query,
    skipAuth = false,
    raw = false,
    headers = {},
  } = options

  const url = `${BASE_URL}${path}${query ? buildQueryString(query) : ''}`

  const finalHeaders: Record<string, string> = {
    Accept: 'application/json',
    ...headers,
  }

  if (body !== undefined && !(body instanceof FormData)) {
    finalHeaders['Content-Type'] = 'application/json'
  }

  if (!skipAuth) {
    const token = getAccessToken()
    if (token) {
      finalHeaders.Authorization = `Bearer ${token}`
    }
  }

  const fetchOptions: RequestInit = {
    method,
    headers: finalHeaders,
  }

  if (body !== undefined) {
    fetchOptions.body = body instanceof FormData ? body : JSON.stringify(body)
  }

  let response: Response
  try {
    response = await fetch(url, fetchOptions)
  } catch (err) {
    throw new ApiError(
      err instanceof Error ? err.message : '网络请求失败',
      'network_error',
      0,
    )
  }

  // 204 No Content
  if (response.status === 204) {
    return undefined as T
  }

  let json: unknown
  const text = await response.text()
  try {
    json = text ? JSON.parse(text) : null
  } catch {
    // 非 JSON 响应
    if (!response.ok) {
      throw new ApiError(`HTTP ${response.status}`, 'http_error', response.status)
    }
    return text as unknown as T
  }

  // 401 自动跳转登录
  if (response.status === 401) {
    redirectToLogin()
    const errObj = extractError(json)
    throw new ApiError(
      errObj?.message || '未授权，请重新登录',
      errObj?.code || 'unauthorized',
      401,
      errObj?.details,
    )
  }

  if (!response.ok) {
    const errObj = extractError(json)
    throw new ApiError(
      errObj?.message || `请求失败 (${response.status})`,
      errObj?.code || 'http_error',
      response.status,
      errObj?.details,
    )
  }

  // raw 模式直接返回原始响应
  if (raw) {
    return json as T
  }

  // 统一包裹格式：提取 data
  if (isWrappedResponse(json)) {
    if (json.success) {
      return (json as ApiResponse<T>).data
    }
    const err = json as ApiErrorResponse
    throw new ApiError(err.error.message, err.error.code, response.status, err.error.details)
  }

  // 资源直返格式（如 /users/.../trips）
  return json as T
}

/** 从响应中提取 error 对象 */
function extractError(json: unknown): ApiErrorObject | null {
  if (typeof json !== 'object' || json === null) return null
  const obj = json as { error?: ApiErrorObject; message?: string; code?: string }
  if (obj.error && typeof obj.error === 'object') {
    return obj.error
  }
  if (obj.message) {
    return { code: obj.code || 'unknown_error', message: obj.message }
  }
  return null
}

/** 便捷方法 */
export const apiClient = {
  get: <T>(path: string, query?: QueryParams, options?: Omit<RequestOptions, 'method' | 'query'>) =>
    apiRequest<T>(path, { ...options, method: 'GET', query }),

  post: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    apiRequest<T>(path, { ...options, method: 'POST', body }),

  patch: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    apiRequest<T>(path, { ...options, method: 'PATCH', body }),

  put: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    apiRequest<T>(path, { ...options, method: 'PUT', body }),

  delete: <T>(path: string, options?: Omit<RequestOptions, 'method'>) =>
    apiRequest<T>(path, { ...options, method: 'DELETE' }),
}

export default apiClient
