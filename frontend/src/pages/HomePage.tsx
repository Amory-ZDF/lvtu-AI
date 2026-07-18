/**
 * 首页 (page-home)
 * - 已登录：从后端拉取行程列表
 * - 未登录：显示引导登录的空状态
 */

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { TripCard, tripToCardData } from '@/components/TripCard'
import { useUIStore } from '@/store/uiStore'
import { useAuthStore } from '@/store/authStore'
import { listTrips } from '@/services/trip'
import type { Trip } from '@/types'

export function HomePage() {
  const navigate = useNavigate()
  const showToast = useUIStore((s) => s.showToast)
  const user = useAuthStore((s) => s.user)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const logout = useAuthStore((s) => s.logout)

  const [trips, setTrips] = useState<Trip[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [accountOpen, setAccountOpen] = useState(false)

  const loadTrips = (userId: string) => {
    setLoading(true)
    setError(null)
    listTrips(userId, { page: 1, page_size: 8 })
      .then((res) => setTrips(res.items))
      .catch((err) => setError(err instanceof Error ? err.message : '获取行程列表失败'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (!isAuthenticated || !user) return
    loadTrips(user.id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, user])

  const handleTripClick = (id: string) => {
    navigate(`/trips/${id}`)
  }

  const handleAccountClick = () => {
    if (!isAuthenticated) {
      navigate('/login?redirect=/')
      return
    }
    setAccountOpen((value) => !value)
  }

  const handleLogout = () => {
    logout()
    setAccountOpen(false)
    setTrips([])
    showToast('已退出登录')
  }

  const renderTripsSection = () => {
    if (!isAuthenticated) {
      return (
        <div className="home-trip-state">
          <span>登录后查看你的行程</span>
          <button type="button" onClick={() => navigate('/login?redirect=/')}>
            去登录
          </button>
        </div>
      )
    }
    if (!user) return <div className="home-trip-state">正在加载行程...</div>
    if (loading) return <div className="home-trip-state">正在加载行程...</div>
    if (error) {
      return (
        <div className="home-trip-state">
          <span>{error}</span>
          <button type="button" onClick={() => user && loadTrips(user.id)}>
            重试
          </button>
        </div>
      )
    }
    if (trips.length === 0) {
      return (
        <div className="home-trip-state">还没有行程，从上方开始规划吧。</div>
      )
    }
    return (
      <div className="trip-cards">
        {trips.slice(0, 8).map((trip) => (
          <TripCard key={trip.id} trip={tripToCardData(trip)} onClick={handleTripClick} />
        ))}
      </div>
    )
  }

  return (
    <div className="home-page">
      <section className="home-video-hero">
        <video
          className="home-background-video"
          autoPlay
          muted
          loop
          playsInline
          poster="/media/home-scenery-poster.png"
          aria-hidden="true"
        >
          <source src="/media/home-scenery.mp4" type="video/mp4" />
        </video>
        <div className="home-video-overlay" aria-hidden="true" />

        <header className="home-topbar">
          <button className="home-brand" type="button" onClick={() => navigate('/')}>
            旅<span>图</span>
          </button>
          <div className="home-top-actions">
            <div className="home-account-wrap">
              <button
                className="home-nav-button home-account-button"
                type="button"
                onClick={handleAccountClick}
                aria-expanded={isAuthenticated ? accountOpen : undefined}
                aria-label={isAuthenticated ? '打开账户菜单' : '登录账户'}
              >
                <span className="home-account-avatar" aria-hidden="true">
                  {(user?.display_name || '账').charAt(0)}
                </span>
                <span className="home-account-label">
                  {isAuthenticated ? user?.display_name || '账户' : '账户'}
                </span>
              </button>
              {isAuthenticated && accountOpen && (
                <div className="home-account-menu">
                  <strong>{user?.display_name || '旅图用户'}</strong>
                  <button
                    className="home-account-menu-link"
                    type="button"
                    onClick={() => {
                      setAccountOpen(false)
                      navigate('/trips')
                    }}
                  >
                    所有行程
                  </button>
                  <button className="home-account-menu-danger" type="button" onClick={handleLogout}>
                    退出登录
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        <div className="home-one-page-content">
          <div className="home-hero-content">
            <span className="home-hero-kicker">AI TRAVEL PLANNER</span>
            <h1>旅图</h1>
            <p>从一个想法出发，找到目的地，生成真正可以出发的旅程。</p>
            <button className="home-primary-cta" type="button" onClick={() => navigate('/start')}>
              <span>开始规划</span>
              <span aria-hidden="true">→</span>
            </button>
          </div>

          <section className="home-trips-section" id="my-trips">
            <div className="home-trips-inner">
              <div className="section-head">
                <div>
                  <span className="home-section-kicker">YOUR JOURNEYS</span>
                  <h2>我的行程</h2>
                </div>
              </div>
              {renderTripsSection()}
            </div>
          </section>
        </div>

        <a
          className="home-video-credit"
          href="https://v.douyin.com/iXaWArcA_Aw/"
          target="_blank"
          rel="noreferrer"
        >
          @子屿
        </a>
      </section>
    </div>
  )
}

export default HomePage
