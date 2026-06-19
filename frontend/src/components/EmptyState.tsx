/**
 * 空状态
 */

import type { ReactNode } from 'react'

interface EmptyStateProps {
  icon?: string
  title: string
  description?: string
  action?: ReactNode
}

export function EmptyState({ icon = '📭', title, description, action }: EmptyStateProps) {
  return (
    <div style={{ textAlign: 'center', padding: '48px 24px' }}>
      <div style={{ fontSize: '3rem', marginBottom: '12px' }}>{icon}</div>
      <h3 style={{ marginBottom: '6px' }}>{title}</h3>
      {description && (
        <p className="hint" style={{ marginBottom: '16px' }}>{description}</p>
      )}
      {action}
    </div>
  )
}

export default EmptyState
