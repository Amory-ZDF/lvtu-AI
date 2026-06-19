/**
 * 错误状态
 */

import type { ReactNode } from 'react'

interface ErrorStateProps {
  icon?: string
  title: string
  description?: string
  action?: ReactNode
}

export function ErrorState({ icon = '⚠️', title, description, action }: ErrorStateProps) {
  return (
    <div style={{ textAlign: 'center', padding: '48px 24px' }}>
      <div style={{ fontSize: '3rem', marginBottom: '12px' }}>{icon}</div>
      <h3 style={{ marginBottom: '6px', color: 'oklch(0.5 0.16 22)' }}>{title}</h3>
      {description && (
        <p className="hint" style={{ marginBottom: '16px' }}>{description}</p>
      )}
      {action}
    </div>
  )
}

export default ErrorState
