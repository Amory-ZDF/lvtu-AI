/**
 * useAuth Hook
 * 封装鉴权相关操作，结合 Zustand store 和 auth service
 */

import { useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { authService } from '@/services/auth'
import type { LoginRequest, RegisterRequest } from '@/types'

export interface UseAuthReturn {
  user: ReturnType<typeof useAuthStore.getState>['user']
  isAuthenticated: boolean
  isLoading: boolean

  login: (payload: LoginRequest) => Promise<void>
  register: (payload: RegisterRequest) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<boolean>
  requireAuth: () => boolean
}

export function useAuth(): UseAuthReturn {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const isLoading = useAuthStore((s) => s.isLoading)
  const setAuth = useAuthStore((s) => s.setAuth)
  const setUser = useAuthStore((s) => s.setUser)
  const setLoading = useAuthStore((s) => s.setLoading)
  const logoutStore = useAuthStore((s) => s.logout)

  /** 登录 */
  const login = useCallback(
    async (payload: LoginRequest) => {
      const res = await authService.login(payload)
      setAuth(res.user, res.token)
    },
    [setAuth],
  )

  /** 注册并自动登录 */
  const register = useCallback(
    async (payload: RegisterRequest) => {
      const res = await authService.register(payload)
      setAuth(res.user, res.token)
    },
    [setAuth],
  )

  /** 登出 */
  const logout = useCallback(() => {
    logoutStore()
    navigate('/login')
  }, [logoutStore, navigate])

  /** 启动时检查 token 有效性，返回是否已认证 */
  const checkAuth = useCallback(async (): Promise<boolean> => {
    if (!isAuthenticated) return false
    setLoading(true)
    try {
      const me = await authService.getMe()
      setUser(me)
      return true
    } catch {
      logoutStore()
      return false
    } finally {
      setLoading(false)
    }
  }, [isAuthenticated, setLoading, setUser, logoutStore])

  /** 未登录拦截：未登录时跳转 /login，返回是否已认证 */
  const requireAuth = useCallback((): boolean => {
    if (!isAuthenticated) {
      const current = window.location.pathname + window.location.search
      navigate(`/login?redirect=${encodeURIComponent(current)}`)
      return false
    }
    return true
  }, [isAuthenticated, navigate])

  // 启动时若有 token 但无 user，尝试拉取用户信息
  useEffect(() => {
    if (isAuthenticated && !user) {
      void checkAuth()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    checkAuth,
    requireAuth,
  }
}

export default useAuth
