/**
 * 鉴权状态管理
 * - token 持久化到 localStorage
 * - user 信息
 * - 登录态判断
 */

import { create } from 'zustand'
import type { TokenResponse, UserProfile } from '@/types'
import { ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY } from '@/services/api'

interface AuthState {
  user: UserProfile | null
  token: TokenResponse | null
  isAuthenticated: boolean
  isLoading: boolean

  setAuth: (user: UserProfile, token: TokenResponse) => void
  setUser: (user: UserProfile | null) => void
  setToken: (token: TokenResponse | null) => void
  setLoading: (loading: boolean) => void
  logout: () => void
}

/** 从 localStorage 恢复 token */
function loadToken(): TokenResponse | null {
  const access = localStorage.getItem(ACCESS_TOKEN_KEY)
  const refresh = localStorage.getItem(REFRESH_TOKEN_KEY)
  if (!access || !refresh) return null
  return {
    access_token: access,
    refresh_token: refresh,
    token_type: 'bearer',
    expires_in: 0,
  }
}

/** 持久化 token */
function persistToken(token: TokenResponse | null): void {
  if (token) {
    localStorage.setItem(ACCESS_TOKEN_KEY, token.access_token)
    localStorage.setItem(REFRESH_TOKEN_KEY, token.refresh_token)
  } else {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: loadToken(),
  isAuthenticated: !!loadToken(),
  isLoading: false,

  setAuth: (user, token) => {
    persistToken(token)
    set({ user, token, isAuthenticated: true })
  },

  setUser: (user) => set({ user }),

  setToken: (token) => {
    persistToken(token)
    set({ token, isAuthenticated: !!token })
  },

  setLoading: (isLoading) => set({ isLoading }),

  logout: () => {
    persistToken(null)
    set({ user: null, token: null, isAuthenticated: false })
  },
}))

export default useAuthStore
