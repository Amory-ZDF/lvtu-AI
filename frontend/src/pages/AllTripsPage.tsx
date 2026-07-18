import { useEffect, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { EmptyState } from '@/components/EmptyState'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { TripCard, tripToCardData } from '@/components/TripCard'
import { listTrips } from '@/services/trip'
import { useAuthStore } from '@/store/authStore'
import type { Trip } from '@/types'

const PAGE_SIZE = 24

export function AllTripsPage() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const [trips, setTrips] = useState<Trip[]>([])
  const [page, setPage] = useState(0)
  const [total, setTotal] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadTrips = (nextPage: number) => {
    if (!user) return
    setLoading(true)
    setError(null)
    listTrips(user.id, { page: nextPage, page_size: PAGE_SIZE })
      .then((response) => {
        setTrips((current) => nextPage === 1 ? response.items : [...current, ...response.items])
        setPage(nextPage)
        setTotal(response.meta.total)
        setHasMore(response.meta.has_more)
      })
      .catch((err) => setError(err instanceof Error ? err.message : '获取行程列表失败'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (user) loadTrips(1)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

  if (!isAuthenticated) {
    return <Navigate to="/login?redirect=/trips" replace />
  }

  if (!user) {
    return (
      <div className="page all-trips-page">
        <div className="all-trips-state">
          <LoadingSpinner label="正在加载账户..." />
        </div>
      </div>
    )
  }

  return (
    <div className="page all-trips-page">
      <button className="back-link" type="button" onClick={() => navigate('/')}>
        ← 返回首页
      </button>

      <header className="all-trips-header">
        <div>
          <h1>所有行程</h1>
          <p>按最近更新时间排序，继续打开任何一段旅程。</p>
        </div>
        {!loading || trips.length > 0 ? <span>{total} 个行程</span> : null}
      </header>

      {loading && trips.length === 0 ? (
        <div className="all-trips-state">
          <LoadingSpinner label="正在加载行程..." />
        </div>
      ) : error && trips.length === 0 ? (
        <EmptyState
          title="暂时无法获取行程"
          description={error}
          action={<button className="btn btn-primary" type="button" onClick={() => loadTrips(1)}>重试</button>}
        />
      ) : trips.length === 0 ? (
        <EmptyState
          title="还没有行程"
          description="先完成一次规划，你的行程会出现在这里。"
          action={<button className="btn btn-primary" type="button" onClick={() => navigate('/start')}>开始规划</button>}
        />
      ) : (
        <>
          <div className="trip-cards all-trips-grid">
            {trips.map((trip) => (
              <TripCard
                key={trip.id}
                trip={tripToCardData(trip)}
                onClick={(tripId) => navigate(`/trips/${tripId}`)}
              />
            ))}
          </div>
          <div className="all-trips-footer">
            {error ? <p>{error}</p> : null}
            {hasMore ? (
              <button
                className="btn btn-secondary"
                type="button"
                disabled={loading}
                onClick={() => loadTrips(page + 1)}
              >
                {loading ? '加载中...' : '加载更多'}
              </button>
            ) : null}
          </div>
        </>
      )}
    </div>
  )
}

export default AllTripsPage
