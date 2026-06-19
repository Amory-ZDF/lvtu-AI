/**
 * 方案对比卡片
 */

import type { PlanOption } from '@/data/mock'

interface PlanOptionCardProps {
  option: PlanOption
  selected: boolean
  onSelect: (id: 'A' | 'B') => void
}

export function PlanOptionCard({ option, selected, onSelect }: PlanOptionCardProps) {
  return (
    <div
      className={`compare-card${selected ? ' selected' : ''}`}
      onClick={() => onSelect(option.id)}
    >
      <h2>{option.title}</h2>
      <p className="subtitle">{option.subtitle}</p>
      <div className="price">
        {option.price} <small>/ 人 · 不含大交通</small>
      </div>
      <div className="compare-metrics">
        {option.metrics.map((m) => (
          <div key={m.label} className="metric-row">
            <span className={`metric-dot ${m.level}`}></span>
            {m.label}
          </div>
        ))}
      </div>
      <p style={{ fontSize: '0.8rem', color: 'var(--ink-secondary)', marginTop: '12px', lineHeight: 1.5 }}>
        {option.description}
      </p>
    </div>
  )
}

export default PlanOptionCard
