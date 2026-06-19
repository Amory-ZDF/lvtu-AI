/**
 * 鉴权服务
 * 与后端 `app/api/v1/auth.py` 对齐
 */

import { apiClient } from './api'
import type {
  AuthResponse,
  LoginRequest,
  RefreshRequest,
  RegisterRequest,
  TokenResponse,
  UserProfile,
} from '@/types'

/**
 * 注册
 * POST /auth/register
 * 注意：后端使用 OAuth2PasswordRequestForm 处理登录，但 register 接收 JSON
 */
export async function register(payload: RegisterRequest): Promise<AuthResponse> {
  return apiClient.post<AuthResponse>('/auth/register', payload, { skipAuth: true })
}

/**
 * 登录
 * POST /auth/login
 * 后端使用 OAuth2PasswordRequestForm，字段为 username/password
 * 这里将 email 作为 username 传入
 */
export async function login(payload: LoginRequest): Promise<AuthResponse> {
  const formData = new URLSearchParams()
  formData.append('username', payload.email)
  formData.append('password', payload.password)

  // OAuth2 form 接口需要 form-urlencoded
  const response = await fetch(
    `${import.meta.env.VITE_API_BASE_URL || '/api/v1'}/auth/login`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        Accept: 'application/json',
      },
      body: formData.toString(),
    },
  )

  const json = await response.json()
  if (!response.ok || !json.success) {
    const err = json.error || { code: 'login_failed', message: '登录失败' }
    throw new Error(err.message)
  }

  return json.data as AuthResponse
}

/**
 * 刷新 token
 * POST /auth/refresh
 */
export async function refreshToken(refresh_token: string): Promise<TokenResponse> {
  return apiClient.post<TokenResponse>(
    '/auth/refresh',
    { refresh_token } satisfies RefreshRequest,
    { skipAuth: true },
  )
}

/**
 * 获取当前用户信息
 * GET /auth/me
 */
export async function getMe(): Promise<UserProfile> {
  return apiClient.get<UserProfile>('/auth/me')
}

export const authService = {
  register,
  login,
  refreshToken,
  getMe,
}

export default authService
