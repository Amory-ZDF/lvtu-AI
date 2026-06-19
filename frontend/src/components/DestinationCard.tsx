/**
 * 目的地卡片
 */

import type { DestinationPreview } from '@/data/mock'

interface DestinationCardProps {
  destination: DestinationPreview
  onCompare?: (id: string) => void
  onGenerate?: (id: string) => void
}

export function DestinationCard({ destination, onCompare, onGenerate }: DestinationCardProps) {
  return (
    <div className={`dest-preview${destination.recommended ? ' recommended' : ''}`}>
      <div className="dp-hero" style={{ backgroundImage: destination.gradient }}>
        <span className="dp-badge">{destination.matchScore}</span>
      </div>
      <div className="dp-body">
        <div className="dp-header">
          <div>
            <h3>{destination.name}</h3>
            <p>{destination.region}</p>
          </div>
          <div className="dp-price">
            {destination.price}
            <span>/人</span>
          </div>
        </div>
        <div className="dp-tags">
          {destination.tags.map((tag) => (
            <span key={tag} className="chip">
              {tag}
            </span>
          ))}
        </div>
        <p className="dp-reason">{destination.reason}</p>
        <div className="dp-sneak">
          <h4>🗓️ 行程预览</h4>
          <div className="dp-stops">
            {destination.stops.map((stop) => (
              <div key={stop.day} className="dp-stop">
                <span>{stop.day}</span>
                {stop.text}
              </div>
            ))}
          </div>
        </div>
        <div className="dp-sneak">
          <h4>📸 亮点机位</h4>
          <div className="dp-highlights">
            {destination.highlights.map((h) => (
              <span key={h}>{h}</span>
            ))}
          </div>
        </div>
        <div className="dp-actions">
          <button className="btn btn-primary" onClick={() => onCompare?.(destination.id)}>
            📊 查看方案对比
          </button>
          <button className="btn btn-outline" onClick={() => onGenerate?.(destination.id)}>
            ✨ 直接生成行程
          </button>
        </div>
      </div>
    </div>
  )
}

export default DestinationCard
