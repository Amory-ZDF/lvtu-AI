/**
 * 侧边栏导航
 */

import { NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useUIStore } from '@/store/uiStore'
import { useI18n } from '@/hooks/useI18n'

export function Sidebar() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const sidebarOpen = useUIStore((s) => s.sidebarOpen)
  const setSidebarOpen = useUIStore((s) => s.setSidebarOpen)
  const { t } = useI18n()

  const NAV_ITEMS = [
    { to: '/', icon: '🏠', label: t('nav.home'), end: true },
    { to: '/community', icon: '💬', label: t('nav.community'), end: false },
  ]

  const handleNavClick = () => {
    setSidebarOpen(false)
  }

  const handleLogoClick = () => {
    navigate('/')
    setSidebarOpen(false)
  }

  const displayName = user?.display_name || t('user.guest')
  const initial = displayName.charAt(0) || '游'
  const bio = user?.bio || (isAuthenticated ? t('user.bioAuthed') : t('user.bioGuest'))

  return (
    <aside className={`sidebar${sidebarOpen ? ' open' : ''}`}>
      <div
        className="sidebar-logo"
        onClick={handleLogoClick}
        role="button"
        tabIndex={0}
        aria-label="返回首页"
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            handleLogoClick()
          }
        }}
      >
        {t('app.name').charAt(0)}
        <span>{t('app.name').charAt(1)}</span>
      </div>
      <nav className="side-nav">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => isActive ? 'active' : ''}
            onClick={handleNavClick}
          >
            <span className="nav-icon">{item.icon}</span> {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="side-user">
        <div className="side-avatar">{initial}</div>
        <div className="side-user-info">
          <strong>{displayName}</strong>
          {bio}
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
