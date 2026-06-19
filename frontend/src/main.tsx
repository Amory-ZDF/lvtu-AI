/**
 * React 入口
 * - 初始化 Sentry（生产环境 + DSN 存在时）
 * - 初始化 i18n
 * - 挂载 App 到 #root
 */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import * as Sentry from '@sentry/react'
import App from './App'
import './i18n'
import './styles/index.css'

// Sentry 初始化：仅当 DSN 存在时（开发环境通常无 DSN，自动跳过）
const sentryDsn = import.meta.env.VITE_SENTRY_DSN
if (sentryDsn) {
  Sentry.init({
    dsn: sentryDsn,
    environment: import.meta.env.MODE,
    tracesSampleRate: 0.1,
  })
}

const rootEl = document.getElementById('root')
if (!rootEl) throw new Error('Root element #root not found')

createRoot(rootEl).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
