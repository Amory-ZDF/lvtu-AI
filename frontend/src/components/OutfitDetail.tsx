/**
 * 穿搭详情弹窗
 */

import type { KeyboardEvent } from 'react'
import type { OutfitDetailData } from '@/data/mock'

interface OutfitDetailProps {
  data: OutfitDetailData
  onClose: () => void
  onViewSpot?: (spotId: string) => void
  onGenerateImage?: () => void
  generatingImage?: boolean
}

export function OutfitDetail({
  data,
  onClose,
  onViewSpot,
  onGenerateImage,
  generatingImage = false,
}: OutfitDetailProps) {
  const canGenerateFromHero = Boolean(onGenerateImage && !data.hasAiPreview && !generatingImage)
  const safeImageUrl = data.imageUrl?.replace(/"/g, '\\"')

  const handleHeroKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (!canGenerateFromHero) return
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onGenerateImage?.()
    }
  }

  return (
    <div className="detail-overlay show" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="detail-panel" onClick={(e) => e.stopPropagation()}>
        <button className="dp-close" onClick={onClose}>×</button>
        <div
          className={`dp-hero-img outfit-hero-img${data.hasAiPreview ? ' has-preview' : ' needs-preview'}${generatingImage ? ' is-generating' : ''}`}
          onClick={() => canGenerateFromHero && onGenerateImage?.()}
          onKeyDown={handleHeroKeyDown}
          role={canGenerateFromHero ? 'button' : undefined}
          tabIndex={canGenerateFromHero ? 0 : undefined}
        >
          <div className="outfit-hero-blur" style={{ backgroundImage: data.hero }} />
          {safeImageUrl && (
            <div
              className="outfit-hero-full"
              style={{ backgroundImage: `url("${safeImageUrl}")` }}
              aria-label={`${data.name}穿搭预览`}
            />
          )}
          {onGenerateImage && (!data.hasAiPreview || generatingImage) && (
            <div className="outfit-hero-cta">
              <strong>{generatingImage ? '正在生成 AI 穿搭预览...' : '点击生成 AI 穿搭预览'}</strong>
              <span>生成前会用模糊背景占位，图片仅作穿搭氛围参考。</span>
            </div>
          )}
        </div>
        <div className="dp-content">
          <h2>{data.name}</h2>
          <p className="dp-subtitle">
            🎬 {data.scene} · {data.weather}
            {data.genderLabel ? ` · ${data.genderLabel}` : ''}
          </p>
          {onGenerateImage && (
            <div className="dp-ai-preview-actions">
              <button
                className="btn btn-primary"
                type="button"
                disabled={generatingImage}
                onClick={onGenerateImage}
              >
                {generatingImage
                  ? '正在生成...'
                  : data.hasAiPreview
                    ? '重新生成 AI 穿搭预览'
                    : '生成 AI 穿搭预览'}
              </button>
              <span>AI 生成，仅作穿搭氛围参考。</span>
            </div>
          )}
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
