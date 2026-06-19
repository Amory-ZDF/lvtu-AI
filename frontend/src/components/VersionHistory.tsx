/**
 * 版本历史组件
 * 侧边抽屉式展示行程版本快照列表，支持回退到指定版本
 */

import { useEffect, useState } from 'react'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorState } from '@/components/ErrorState'
import { EmptyState } from '@/components/EmptyState'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { listVersions, restoreVersion, type TripVersion } from '@/services/version'

interface VersionHistoryProps {
  open: boolean
  tripId: string
  onClose: () => void
  onRestored: () => void
}

/** 格式化时间为本地可读格式 */
function formatTime(iso: string): string {
  try {
    const d = new Date(iso)
    if (Number.isNaN(d.getTime())) return iso
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
      d.getDate(),
    ).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(
      d.getMinutes(),
    ).padStart(2, '0')}`
  } catch {
    return iso
  }
}

export function VersionHistory({ open, tripId, onClose, onRestored }: VersionHistoryProps) {
  const [versions, setVersions] = useState<TripVersion[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [confirmId, setConfirmId] = useState<string | null>(null)
  const [restoring, setRestoring] = useState(false)

  const loadVersions = () => {
    setLoading(true)
    setError(null)
    listVersions(tripId)
      .then((res) => setVersions(res.items))
      .catch((err) => setError(err instanceof Error ? err.message : '获取版本列表失败'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (open && tripId) {
      loadVersions()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, tripId])

  const handleRestore = async () => {
    if (!confirmId) return
    setRestoring(true)
    try {
      await restoreVersion(tripId, confirmId)
      setConfirmId(null)
      onRestored()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : '回退版本失败')
    } finally {
      setRestoring(false)
    }
  }

  if (!open) return null

  return (
    <>
      <div
        className="detail-overlay show"
        onClick={(e) => e.target === e.currentTarget && onClose()}
      >
        <div
          className="detail-panel"
          style={{ width: '460px', maxWidth: '94vw', maxHeight: '85vh', overflow: 'auto' }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="dp-content" style={{ paddingTop: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '1.15rem' }}>🕘 历史版本</h2>
              <button className="btn btn-secondary" style={{ padding: '4px 10px' }} onClick={onClose}>
                关闭
              </button>
            </div>

            {loading ? (
              <LoadingSpinner label="加载版本中..." />
            ) : error ? (
              <ErrorState
                title="加载版本失败"
                description={error}
                action={
                  <button className="btn btn-primary" onClick={loadVersions}>
                    重试
                  </button>
                }
              />
            ) : versions.length === 0 ? (
              <EmptyState
                icon="🕘"
                title="暂无历史版本"
                description="编辑行程后会自动生成版本快照"
              />
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {versions.map((v) => (
                  <div
                    key={v.id}
                    style={{
                      border: '1px solid var(--border)',
                      borderRadius: '12px',
                      padding: '14px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <strong>v{v.version_number}</strong>
                      <span className="hint" style={{ fontSize: '0.8rem' }}>
                        {formatTime(v.created_at)}
                      </span>
                    </div>
                    {v.note && (
                      <p className="hint" style={{ margin: '6px 0 10px' }}>
                        {v.note}
                      </p>
                    )}
                    <button
                      className="btn btn-secondary"
                      style={{ width: '100%', justifyContent: 'center', padding: '6px' }}
                      disabled={restoring}
                      onClick={() => setConfirmId(v.id)}
                    >
                      回退到此版本
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <ConfirmDialog
        open={confirmId !== null}
        title="回退版本"
        description="确定要回退到此版本吗？当前未保存的修改将被覆盖。"
        confirmText={restoring ? '回退中...' : '确定回退'}
        onConfirm={handleRestore}
        onCancel={() => setConfirmId(null)}
      />
    </>
  )
}

export default VersionHistory
