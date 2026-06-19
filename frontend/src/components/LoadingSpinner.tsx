/**
 * 加载指示器
 */

interface LoadingSpinnerProps {
  size?: number
  label?: string
}

export function LoadingSpinner({ size = 46, label }: LoadingSpinnerProps) {
  return (
    <div style={{ textAlign: 'center', padding: '24px' }}>
      <div
        className="spinner"
        style={{
          width: size,
          height: size,
          borderRadius: '50%',
          border: '3px solid var(--border)',
          borderTopColor: 'var(--brand)',
          animation: 'spin 0.8s linear infinite',
          margin: '0 auto 14px',
        }}
      />
      {label && (
        <p style={{ fontSize: '0.88rem', color: 'var(--ink-secondary)' }}>{label}</p>
      )}
    </div>
  )
}

export default LoadingSpinner
