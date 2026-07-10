/**
 * 行程卡片
 */

import type { TripCardData } from '@/data/mock'
import { LazyImage } from '@/components/LazyImage'

interface TripCardProps {
  trip: TripCardData
  onClick?: (id: string) => void
  editing?: boolean
  onDelete?: (id: string) => void
}

function statusLabel(status: TripCardData['status']): string {
  if (status === 'ongoing') return '旅行中'
  if (status === 'returned') return '已返程'
  return '待出行'
}

export function TripCard({ trip, onClick, editing = false, onDelete }: TripCardProps) {
  return (
    <div
      className={`trip-card${editing ? ' editing' : ''}`}
      style={{ cursor: editing ? 'default' : 'pointer' }}
      onClick={(e) => {
        e.stopPropagation()
        if (editing) return
        onClick?.(trip.id)
      }}
    >
      <div
        className="card-img"
        style={trip.imageUrl ? undefined : { backgroundImage: trip.gradient }}
      >
        {trip.imageUrl && (
          <LazyImage
            src={trip.imageUrl}
            alt={trip.title}
            placeholder={trip.gradient}
            containerStyle={{ position: 'absolute', inset: 0 }}
          />
        )}
        <span className={`card-status ${trip.status}`}>
          {statusLabel(trip.status)}
        </span>
        {editing && (
          <button
            className="trip-delete-btn"
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              onDelete?.(trip.id)
            }}
          >
            删除
          </button>
        )}
      </div>
      <div className="card-body">
        <h4>{trip.title}</h4>
        <p>{trip.subtitle}</p>
      </div>
    </div>
  )
}

export default TripCard
