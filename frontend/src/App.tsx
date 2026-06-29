/**
 * 根组件
 * - BrowserRouter 路由配置
 * - 布局：Sidebar + MobileBar + 主内容区
 * - 登录页独立于主布局
 * - 路由级懒加载（首屏 HomePage / LoginPage 同步，其余按需加载）
 * - ErrorBoundary 包裹整个应用
 */

import { lazy, Suspense, useEffect } from 'react'
import {
  BrowserRouter,
  Routes,
  Route,
  Outlet,
  useLocation,
  Navigate,
} from 'react-router-dom'
import Sidebar from '@/components/Sidebar'
import MobileBar from '@/components/MobileBar'
import ToastContainer from '@/components/Toast'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { useUIStore } from '@/store/uiStore'
import { useAuthStore } from '@/store/authStore'
import { getMe } from '@/services/auth'
// 首屏优先：HomePage / LoginPage 保持同步加载
import HomePage from '@/pages/HomePage'
import LoginPage from '@/pages/LoginPage'
// 其余页面懒加载，生成独立 chunk 按需加载
const StartPage = lazy(() => import('@/pages/StartPage'))
const DestinationsPage = lazy(() => import('@/pages/DestinationsPage'))
const ComparisonPage = lazy(() => import('@/pages/ComparisonPage'))
const TripDetailPage = lazy(() => import('@/pages/TripDetailPage'))

/** 路由级加载占位 */
function RouteFallback() {
  return (
    <div style={{ padding: '48px 0' }}>
      <LoadingSpinner label="加载中..." />
    </div>
  )
}

function AuthBootstrap() {
  const user = useAuthStore((s) => s.user)
  const token = useAuthStore((s) => s.token)
  const setUser = useAuthStore((s) => s.setUser)
  const logout = useAuthStore((s) => s.logout)

  useEffect(() => {
    if (!token || user) return
    let cancelled = false
    getMe()
      .then((profile) => {
        if (!cancelled) setUser(profile)
      })
      .catch(() => {
        if (!cancelled) logout()
      })
    return () => {
      cancelled = true
    }
  }, [logout, setUser, token, user])

  return null
}

/** 主布局：侧边栏 + 移动端顶栏 + 内容区 */
function Layout() {
  const sidebarOpen = useUIStore((s) => s.sidebarOpen)
  const setSidebarOpen = useUIStore((s) => s.setSidebarOpen)
  const location = useLocation()

  // 路由切换时自动关闭移动端侧边栏
  useEffect(() => {
    setSidebarOpen(false)
  }, [location.pathname, setSidebarOpen])

  return (
    <div className="app-layout">
      <Sidebar />
      <div
        className={`sidebar-overlay${sidebarOpen ? ' show' : ''}`}
        onClick={() => setSidebarOpen(false)}
        role="button"
        tabIndex={-1}
        aria-label="关闭侧边栏"
      />
      <div className="main">
        <MobileBar />
        <Outlet />
      </div>
    </div>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthBootstrap />
        <ToastContainer />
        <Routes>
          {/* 登录页独立于主布局 */}
          <Route path="/login" element={<LoginPage />} />
          {/* 主布局路由 */}
          <Route element={<Layout />}>
            <Route path="/" element={<HomePage />} />
            <Route
              path="/start"
              element={
                <Suspense fallback={<RouteFallback />}>
                  <StartPage />
                </Suspense>
              }
            />
            <Route
              path="/destinations"
              element={
                <Suspense fallback={<RouteFallback />}>
                  <DestinationsPage />
                </Suspense>
              }
            />
            <Route
              path="/comparison"
              element={
                <Suspense fallback={<RouteFallback />}>
                  <ComparisonPage />
                </Suspense>
              }
            />
            <Route
              path="/trips/:tripId"
              element={
                <Suspense fallback={<RouteFallback />}>
                  <TripDetailPage />
                </Suspense>
              }
            />
          </Route>
          {/* 兜底：未知路由重定向到首页 */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  )
}
