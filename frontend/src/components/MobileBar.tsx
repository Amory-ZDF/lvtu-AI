/**
 * 移动端顶栏
 */

import { useNavigate } from 'react-router-dom'
import { useUIStore } from '@/store/uiStore'

export function MobileBar() {
  const navigate = useNavigate()
  const sidebarOpen = useUIStore((s) => s.sidebarOpen)
  const toggleSidebar = useUIStore((s) => s.toggleSidebar)

  return (
    <div className="mobile-bar">
      <div
        className="mb-logo"
        onClick={() => navigate('/')}
        role="button"
        tabIndex={0}
        aria-label="返回首页"
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            navigate('/')
          }
        }}
      >
        旅<span>图</span>
      </div>
      <button
        type="button"
        className={`mb-hamburger${sidebarOpen ? ' open' : ''}`}
        onClick={toggleSidebar}
        aria-label={sidebarOpen ? '关闭菜单' : '打开菜单'}
        aria-expanded={sidebarOpen}
      >
        <span></span>
        <span></span>
        <span></span>
      </button>
    </div>
  )
}

export default MobileBar
