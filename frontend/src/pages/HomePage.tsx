/**
 * 首页 (page-home)
 * - 已登录：从后端拉取行程列表
 * - 未登录：显示引导登录的空状态
 */

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { TripCard } from '@/components/TripCard'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorState } from '@/components/ErrorState'
import { EmptyState } from '@/components/EmptyState'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { useUIStore } from '@/store/uiStore'
import { useAuthStore } from '@/store/authStore'
import { deleteTrip, listTrips } from '@/services/trip'
import type { Trip } from '@/types'
import type { TripCardData } from '@/data/mock'

/** 默认渐变（按 id 哈希取色，保证视觉一致） */
const GRADIENTS = [
  'linear-gradient(135deg,oklch(0.63 0.17 198),oklch(0.56 0.15 222))',
  'linear-gradient(135deg,oklch(0.62 0.13 42),oklch(0.55 0.15 62))',
  'linear-gradient(135deg,oklch(0.58 0.15 170),oklch(0.50 0.14 195))',
  'linear-gradient(135deg,oklch(0.56 0.16 215),oklch(0.48 0.14 235))',
  'linear-gradient(135deg,oklch(0.60 0.15 340),oklch(0.52 0.16 5))',
]

function pickGradient(id: string): string {
  let hash = 0
  for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) >>> 0
  return GRADIENTS[hash % GRADIENTS.length]
}

/** 将 Trip 映射为 TripCard 视图数据 */
function normalizeStatus(status: string | null | undefined): TripCardData['status'] {
  if (status === 'ongoing') return 'ongoing'
  if (status === 'returned' || status === 'archived') return 'returned'
  return 'upcoming'
}

function toCardData(trip: Trip): TripCardData {
  const datePart =
    trip.start_date && trip.end_date
      ? `${trip.start_date} 至 ${trip.end_date}`
      : trip.start_date || ''
  const subtitle = [datePart, trip.notes].filter(Boolean).join(' · ')
  return {
    id: trip.id,
    title: trip.title,
    subtitle: subtitle || trip.destination_name,
    status: normalizeStatus(trip.status),
    gradient: pickGradient(trip.id),
    imageUrl: trip.cover_image_url,
  }
}

export function HomePage() {
  const navigate = useNavigate()
  const showToast = useUIStore((s) => s.showToast)
  const user = useAuthStore((s) => s.user)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  const [trips, setTrips] = useState<Trip[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)

  const loadTrips = (userId: string) => {
    setLoading(true)
    setError(null)
    listTrips(userId)
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

  const handleDeleteConfirm = async () => {
    if (deleting) return
    if (!user || !deleteTargetId) return
    setDeleting(true)
    try {
      await deleteTrip(user.id, deleteTargetId)
      setTrips((prev) => prev.filter((trip) => trip.id !== deleteTargetId))
      setDeleteTargetId(null)
      showToast('行程已删除')
    } catch (err) {
      showToast(err instanceof Error ? err.message : '删除行程失败')
    } finally {
      setDeleting(false)
    }
  }

  const renderTripsSection = () => {
    if (!isAuthenticated) {
      return (
        <EmptyState
          icon="🔐"
          title="登录后查看你的行程"
          description="登录即可保存和管理你的 AI 旅行规划"
          action={
            <button
              className="btn btn-primary"
              onClick={() => navigate('/login?redirect=/')}
            >
              去登录
            </button>
          }
        />
      )
    }
    if (loading) return <LoadingSpinner label="加载行程中..." />
    if (error) {
      return (
        <ErrorState
          title="加载行程失败"
          description={error}
          action={
            <button
              className="btn btn-primary"
              onClick={() => user && loadTrips(user.id)}
            >
              重试
            </button>
          }
        />
      )
    }
    if (trips.length === 0) {
      return (
        <EmptyState
          icon="🗺️"
          title="还没有行程"
          description="点击下方按钮，让 AI 帮你规划第一次旅行"
          action={
            <button className="btn btn-primary" onClick={() => navigate('/start')}>
              ✨ 开始规划
            </button>
          }
        />
      )
    }
    return (
      <div className="trip-cards">
        {trips.map((trip) => (
          <TripCard
            key={trip.id}
            trip={toCardData(trip)}
            editing={editing}
            onClick={handleTripClick}
            onDelete={setDeleteTargetId}
          />
        ))}
        {!editing && (
          <div className="trip-card-new" onClick={() => navigate('/start')}>
            <div className="plus">+</div>
            <p>规划新行程</p>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="page">
      <section className="home-hero">
        <h1>
          想去旅行，但<span className="highlight">不知道去哪</span>？
        </h1>
        <p>旅图 AI 帮你从灵感激发到可执行行程，一站式完成旅行规划</p>
        <button className="btn btn-primary btn-lg" onClick={() => navigate('/start')}>
          ✨ 开始你的行程
        </button>
      </section>

      <section className="my-trips-section">
        <div className="section-head">
          <h2>📌 我的行程</h2>
          {isAuthenticated && trips.length > 0 && (
            <button className="section-action" onClick={() => setEditing((value) => !value)}>
              {editing ? '完成' : '编辑'}
            </button>
          )}
        </div>
        {renderTripsSection()}
      </section>
      <ConfirmDialog
        open={deleteTargetId !== null}
        title="删除行程？"
        description="删除后无法恢复，相关行程安排、机位、穿搭和打包清单都会被删除。"
        confirmText={deleting ? '删除中...' : '确认删除'}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeleteTargetId(null)}
      />
    </div>
  )
}

export default HomePage
