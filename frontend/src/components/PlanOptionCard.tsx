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
      {option.summaryStats && option.summaryStats.length > 0 && (
        <div className="plan-stat-row">
          {option.summaryStats.map((stat) => (
            <span key={stat}>{stat}</span>
          ))}
        </div>
      )}
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
      {option.differentiators && option.differentiators.length > 0 && (
        <div className="plan-diff-block">
          <h4>核心差异</h4>
          {option.differentiators.map((item) => (
            <p key={item}>{item}</p>
          ))}
        </div>
      )}
      {option.scoreBreakdown && option.scoreBreakdown.length > 0 && (
        <div className="plan-score-grid">
          {option.scoreBreakdown.map((item) => (
            <div key={item.label} className="plan-score-item">
              <strong>{item.label}</strong>
              <span>{item.score}</span>
              <small>{item.reason}</small>
            </div>
          ))}
        </div>
      )}
      {(option.bestFor || option.tradeoff) && (
        <div className="plan-fit-note">
          {option.bestFor && <p>✅ {option.bestFor}</p>}
          {option.tradeoff && <p>⚖️ {option.tradeoff}</p>}
        </div>
      )}
    </div>
  )
}

export default PlanOptionCard
