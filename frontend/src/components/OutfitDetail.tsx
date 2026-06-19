/**
 * 穿搭详情弹窗
 */

import type { OutfitDetailData } from '@/data/mock'

interface OutfitDetailProps {
  data: OutfitDetailData
  onClose: () => void
  onViewSpot?: (spotId: string) => void
}

export function OutfitDetail({ data, onClose, onViewSpot }: OutfitDetailProps) {
  return (
    <div className="detail-overlay show" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="detail-panel" onClick={(e) => e.stopPropagation()}>
        <button className="dp-close" onClick={onClose}>×</button>
        <div className="dp-hero-img" style={{ backgroundImage: data.hero }}></div>
        <div className="dp-content">
          <h2>{data.name}</h2>
          <p className="dp-subtitle">🎬 {data.scene} · {data.weather}</p>
          <div className="dp-section">
            <h4>👗 单品清单</h4>
            <div className="dp-items-list">
              {data.items.map((item) => (
                <div key={item} className="dp-item-row">· {item}</div>
              ))}
            </div>
          </div>
          <div className="dp-section">
            <h4>💡 穿搭理由</h4>
            <p>{data.reason}</p>
          </div>
          {data.spotId && (
            <div
              className="dp-link-card"
              onClick={() => onViewSpot?.(data.spotId!)}
            >
              <span className="link-label">📸 查看匹配机位</span>
              <span className="link-arrow">→</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default OutfitDetail
