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
  const copyPrompt = async () => {
    if (!data.aiPrompt) return
    try {
      await navigator.clipboard.writeText(data.aiPrompt)
    } catch {
      /* browser may block clipboard in some local contexts */
    }
  }

  return (
    <div className="detail-overlay show" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="detail-panel" onClick={(e) => e.stopPropagation()}>
        <button className="dp-close" onClick={onClose}>×</button>
        <div
          className="dp-hero-img"
          style={{ backgroundImage: data.hero, backgroundSize: 'cover', backgroundPosition: 'center' }}
        ></div>
        <div className="dp-content">
          <h2>{data.name}</h2>
          <p className="dp-subtitle">
            🎬 {data.scene} · {data.weather}
            {data.genderLabel ? ` · ${data.genderLabel}` : ''}
          </p>
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
          {data.aiPrompt && (
            <div className="dp-section">
              <h4>🖼️ AI 生图预览</h4>
              <p style={{ marginBottom: '8px' }}>
                当前先展示提示词；配置后端生图 API Key 后，可直接用这段提示词生成穿搭预览图。
              </p>
              <div className="prompt-box">{data.aiPrompt}</div>
              <button className="btn btn-outline" style={{ marginTop: '10px' }} onClick={copyPrompt}>
                复制提示词
              </button>
            </div>
          )}
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
