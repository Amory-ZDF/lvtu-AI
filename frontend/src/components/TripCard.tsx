/**
 * 行程卡片
 */

import type { TripCardData } from '@/data/mock'
import { LazyImage } from '@/components/LazyImage'

interface TripCardProps {
  trip: TripCardData
  onClick?: (id: string) => void
}

export function TripCard({ trip, onClick }: TripCardProps) {
  return (
    <div
      className="trip-card"
      style={{ cursor: 'pointer' }}
      onClick={(e) => {
        e.stopPropagation()
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
          {trip.status === 'draft' ? '草稿' : '已确认'}
        </span>
      </div>
      <div className="card-body">
        <h4>{trip.title}</h4>
        <p>{trip.subtitle}</p>
      </div>
    </div>
  )
}

export default TripCard
