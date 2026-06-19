/**
 * 鉴权相关类型定义
 * 与后端 `app/schemas/auth.py` 和 `app/schemas/domain.py` 对齐
 */

/** 用户偏好档案 */
export interface UserPreference {
  id: string
  user_id: string
  departure_city: string | null
  preferred_styles: string[]
  budget_level: string | null
  language: string | null
  timezone: string | null
  created_at: string
  updated_at: string
}

/** 用户档案（含偏好） */
export interface UserProfile {
  id: string
  email: string
  username: string
  display_name: string
  avatar_url: string | null
  bio: string | null
  created_at: string
  updated_at: string
  preference: UserPreference | null
}

/** Token 响应 */
export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

/** 登录/注册成功响应 */
export interface AuthResponse {
  token: TokenResponse
  user: UserProfile
}

/** 注册请求 */
export interface RegisterRequest {
  email: string
  username: string
  password: string
  display_name: string
}

/** 登录请求 */
export interface LoginRequest {
  email: string
  password: string
}

/** 刷新 token 请求 */
export interface RefreshRequest {
  refresh_token: string
}
