/**
 * 机位详情弹窗
 */

import type { SpotDetailData } from '@/data/mock'

interface SpotDetailProps {
  data: SpotDetailData
  onClose: () => void
  onViewOutfit?: (outfitId: string) => void
}

export function SpotDetail({ data, onClose, onViewOutfit }: SpotDetailProps) {
  return (
    <div className="detail-overlay show" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="detail-panel" onClick={(e) => e.stopPropagation()}>
        <button className="dp-close" onClick={onClose}>×</button>
        <div className="dp-hero-img" style={{ backgroundImage: data.hero }}></div>
        <div className="dp-content">
          <h2>{data.name}</h2>
          <p className="dp-subtitle">{data.time}</p>
          <div className="dp-metrics">
            <div className="dp-metric">
              <div className="val">{data.rate}</div>
              <div className="lbl">出片率</div>
            </div>
            <div className="dp-metric stars">
              <div className="val">{data.difficulty}</div>
              <div className="lbl">拍摄难度 · {data.difficultyLabel}</div>
            </div>
          </div>
          <div className="dp-location">
            <span className="pin">📍</span> {data.location}
          </div>
          <div className="dp-section">
            <h4>📐 构图指南</h4>
            <p>{data.composition}</p>
          </div>
          <div className="dp-section">
            <h4>👗 穿搭建议</h4>
            <p>{data.outfit}</p>
          </div>
          {data.outfitId && (
            <div
              className="dp-link-card"
              onClick={() => onViewOutfit?.(data.outfitId!)}
            >
              <span className="link-label">👗 查看完整穿搭方案</span>
              <span className="link-arrow">→</span>
            </div>
          )}
          {data.warning && (
            <div className="dp-section">
              <h4>⚠️ 注意事项</h4>
              <p>{data.warning}</p>
            </div>
          )}
          <div className="dp-tags-row">
            {data.tags.map((t) => (
              <span key={t.t} className={`spot-tag ${t.c}`}>{t.t}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default SpotDetail
