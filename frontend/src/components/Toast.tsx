/**
 * Toast 消息组件（全局）
 */

import { useUIStore } from '@/store/uiStore'

export function ToastContainer() {
  const toasts = useUIStore((s) => s.toasts)

  if (toasts.length === 0) return null

  return (
    <>
      {toasts.map((t) => (
        <div key={t.id} className="toast show">
          {t.text}
        </div>
      ))}
    </>
  )
}

export default ToastContainer
