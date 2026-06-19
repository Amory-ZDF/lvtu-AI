/**
 * 确认对话框
 */

import type { ReactNode } from 'react'

interface ConfirmDialogProps {
  open: boolean
  title: string
  description?: string
  confirmText?: string
  cancelText?: string
  onConfirm: () => void
  onCancel: () => void
  children?: ReactNode
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmText = '确定',
  cancelText = '取消',
  onConfirm,
  onCancel,
  children,
}: ConfirmDialogProps) {
  if (!open) return null

  return (
    <div
      className="detail-overlay show"
      onClick={(e) => e.target === e.currentTarget && onCancel()}
    >
      <div
        className="detail-panel"
        style={{ width: '420px', maxWidth: '94vw' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="dp-content" style={{ paddingTop: '28px' }}>
          <h2 style={{ fontSize: '1.15rem', marginBottom: '8px' }}>{title}</h2>
          {description && (
            <p className="hint" style={{ marginBottom: '20px' }}>{description}</p>
          )}
          {children}
          <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
            <button className="btn btn-secondary" style={{ flex: 1, justifyContent: 'center' }} onClick={onCancel}>
              {cancelText}
            </button>
            <button className="btn btn-primary" style={{ flex: 1, justifyContent: 'center' }} onClick={onConfirm}>
              {confirmText}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ConfirmDialog
