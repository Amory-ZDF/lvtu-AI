/**
 * 行程卡片
 */

import type { TripCardData } from '@/data/mock'
import type { Trip } from '@/types'

interface TripCardProps {
  trip: TripCardData
  onClick?: (id: string) => void
}

function formatTripDuration(trip: Trip): string {
  if (!trip.start_date || !trip.end_date) return '日期待定'
  const start = Date.parse(trip.start_date)
  const end = Date.parse(trip.end_date)
  if (!Number.isFinite(start) || !Number.isFinite(end) || end < start) return '日期待定'
  const days = Math.floor((end - start) / 86400000) + 1
  return `${days}天${Math.max(days - 1, 0)}晚`
}

export function tripToCardData(trip: Trip): TripCardData {
  const destination = trip.destination_name.trim()
  const routeTitle = (trip.title.split('·').pop() || trip.title).trim()
  const description = routeTitle.startsWith(destination)
    ? routeTitle.slice(destination.length).trim()
    : routeTitle
  return {
    id: trip.id,
    destination,
    duration: formatTripDuration(trip),
    description: description || '经典初访覆盖线',
  }
}

export function TripCard({ trip, onClick }: TripCardProps) {
  return (
    <button
      className="trip-card"
      type="button"
      onClick={() => onClick?.(trip.id)}
    >
      <div className="trip-card-head">
        <h3>{trip.destination}</h3>
        <span>{trip.duration}</span>
      </div>
      <p>{trip.description}</p>
      <span className="trip-card-arrow" aria-hidden="true">→</span>
    </button>
  )
}

export default TripCard
