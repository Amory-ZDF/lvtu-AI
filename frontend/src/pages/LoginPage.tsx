/**
 * 登录/注册页 (page-login)
 */

import { useState, type FormEvent } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { useI18n } from '@/hooks/useI18n'
import type { LoginRequest, RegisterRequest } from '@/types'

type TabMode = 'login' | 'register'

interface FormErrors {
  email?: string
  username?: string
  password?: string
  display_name?: string
}

const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/

export function LoginPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { login, register } = useAuth()
  const { t } = useI18n()

  const [mode, setMode] = useState<TabMode>('login')
  const [loading, setLoading] = useState(false)
  const [serverError, setServerError] = useState<string | null>(null)
  const [errors, setErrors] = useState<FormErrors>({})

  // 表单字段
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')

  const redirectTarget = searchParams.get('redirect') || '/'

  const validate = (): boolean => {
    const next: FormErrors = {}
    if (!EMAIL_PATTERN.test(email)) {
      next.email = t('login.emailInvalid')
    }
    if (password.length < 8) {
      next.password = t('login.passwordTooShort')
    }
    if (mode === 'register') {
      if (!username.trim()) {
        next.username = t('login.usernameRequired')
      }
      if (!displayName.trim()) {
        next.display_name = t('login.displayNameRequired')
      }
    }
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setServerError(null)
    if (!validate()) return

    setLoading(true)
    try {
      if (mode === 'login') {
        const payload: LoginRequest = { email, password }
        await login(payload)
      } else {
        const payload: RegisterRequest = {
          email,
          username,
          password,
          display_name: displayName,
        }
        await register(payload)
      }
      navigate(redirectTarget)
    } catch (err) {
      setServerError(err instanceof Error ? err.message : t('login.operationFailed'))
    } finally {
      setLoading(false)
    }
  }

  const switchMode = (next: TabMode) => {
    setMode(next)
    setErrors({})
    setServerError(null)
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          {t('app.name').charAt(0)}
          <span>{t('app.name').charAt(1)}</span>
        </div>
        <p className="login-subtitle">{t('login.subtitle')}</p>

        <div className="login-tabs">
          <button
            className={`login-tab${mode === 'login' ? ' active' : ''}`}
            onClick={() => switchMode('login')}
            aria-label={t('login.loginTab')}
          >
            {t('login.loginTab')}
          </button>
          <button
            className={`login-tab${mode === 'register' ? ' active' : ''}`}
            onClick={() => switchMode('register')}
            aria-label={t('login.registerTab')}
          >
            {t('login.registerTab')}
          </button>
        </div>

        {serverError && <div className="login-error">{serverError}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>{t('login.email')}</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t('login.emailPlaceholder')}
              autoComplete="email"
            />
            {errors.email && <div className="login-form-error">{errors.email}</div>}
          </div>

          {mode === 'register' && (
            <>
              <div className="form-group">
                <label>{t('login.username')}</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder={t('login.usernamePlaceholder')}
                  autoComplete="username"
                />
                {errors.username && (
                  <div className="login-form-error">{errors.username}</div>
                )}
              </div>
              <div className="form-group">
                <label>{t('login.displayName')}</label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder={t('login.displayNamePlaceholder')}
                />
                {errors.display_name && (
                  <div className="login-form-error">{errors.display_name}</div>
                )}
              </div>
            </>
          )}

          <div className="form-group">
            <label>{t('login.password')}</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={mode === 'register' ? t('login.passwordPlaceholderRegister') : t('login.passwordPlaceholderLogin')}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            />
            {errors.password && <div className="login-form-error">{errors.password}</div>}
          </div>

          <button
            className="btn btn-primary btn-lg"
            type="submit"
            disabled={loading}
            style={{ width: '100%', justifyContent: 'center', marginTop: '8px' }}
          >
            {loading ? t('login.processing') : mode === 'login' ? t('login.loginTab') : t('login.registerTab')}
          </button>
        </form>

        <Link to="/" className="login-back">
          {t('login.backHome')}
        </Link>
      </div>
    </div>
  )
}

export default LoginPage
