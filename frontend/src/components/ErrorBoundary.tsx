/**
 * 错误边界
 * - 捕获子组件渲染/生命周期错误，展示友好错误页
 * - 生产环境上报到 Sentry（若已初始化）
 */

import { Component, type ErrorInfo, type ReactNode } from 'react'

interface ErrorBoundaryProps {
  children: ReactNode
  /** 自定义降级 UI，不传则使用默认错误页 */
  fallback?: (error: Error, retry: () => void) => ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // 生产环境上报 Sentry（动态导入避免强耦合）
    if (import.meta.env.PROD) {
      import('@sentry/react')
        .then((Sentry) => {
          Sentry.captureException(error, { extra: { componentStack: errorInfo.componentStack } })
        })
        .catch(() => {
          // Sentry 上报失败时静默处理，不影响用户
        })
    }
    // 开发环境输出到控制台便于调试
    if (import.meta.env.DEV) {
      // eslint-disable-next-line no-console
      console.error('[ErrorBoundary]', error, errorInfo)
    }
  }

  handleRetry = (): void => {
    this.setState({ hasError: false, error: null })
  }

  render(): ReactNode {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.handleRetry)
      }
      return (
        <div
          style={{
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '16px',
            padding: '24px',
            textAlign: 'center',
            background: 'var(--surface)',
            color: 'var(--ink)',
          }}
        >
          <div style={{ fontSize: '3rem' }} role="img" aria-label="错误">
            😵
          </div>
          <h1 style={{ fontSize: '1.4rem', margin: 0 }}>出错了，请刷新页面</h1>
          <p style={{ color: 'var(--ink-secondary)', margin: 0, maxWidth: '420px' }}>
            抱歉，应用遇到了一些问题。您可以尝试刷新页面或返回首页继续使用。
          </p>
          <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
            <button
              className="btn btn-primary"
              onClick={this.handleRetry}
              aria-label="重试"
            >
              重试
            </button>
            <button
              className="btn btn-outline"
              onClick={() => {
                window.location.href = '/'
              }}
              aria-label="返回首页"
            >
              返回首页
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

export default ErrorBoundary
