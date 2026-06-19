import { NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  flowBaseline,
  modalRegistry,
  responsibilityBaseline,
  routeMeta,
  statusRegistry,
} from '../data/baseline'
import { useDemoState } from '../hooks/useDemoState'
import { ModalHost } from '../modals/ModalHost'

function StatusBoard() {
  const { statusMap, cycleStatus } = useDemoState()
  return (
    <section className="panel-card compact">
      <p className="eyebrow">状态基线</p>
      <div className="status-list">
        {statusRegistry.map((item) => (
          <button
            key={item.key}
            className="status-row"
            onClick={() => cycleStatus(item.key)}
            type="button"
          >
            <span>
              <strong>{item.label}</strong>
              <small>{item.options.join(' / ')}</small>
            </span>
            <b data-state={statusMap[item.key]}>{statusMap[item.key]}</b>
          </button>
        ))}
      </div>
    </section>
  )
}

export function AppShell() {
  const location = useLocation()
  const { openModal, variant } = useDemoState()
  const currentRoute = routeMeta.find((route) =>
    route.path === '/'
      ? location.pathname === '/'
      : location.pathname === route.path ||
        location.pathname.startsWith(`${route.path}/`),
  )

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">{variant.appName}</p>
          <h1>{variant.headline}</h1>
        </div>
        <nav className="nav-grid" aria-label="主导航">
          {routeMeta.map((route) => (
            <NavLink
              key={route.key}
              className={({ isActive }) =>
                `nav-link${isActive ? ' active' : ''}`
              }
              to={route.path}
            >
              <span>{route.label}</span>
              <small>{route.phase}</small>
            </NavLink>
          ))}
        </nav>
      </header>

      <div className="content-grid">
        <main className="page-column">
          <div className="context-banner">
            <span>当前页</span>
            <strong>{currentRoute?.label ?? '旅图原型'}</strong>
            <p>{variant.accent}</p>
          </div>
          <Outlet />
        </main>
        <aside className="side-column">
          <section className="panel-card compact">
            <p className="eyebrow">路径基线</p>
            {flowBaseline.map((flow) => (
              <div key={flow.name} className="flow-block">
                <h3>{flow.name}</h3>
                <ol>
                  {flow.steps.map((step) => (
                    <li key={step}>{step}</li>
                  ))}
                </ol>
              </div>
            ))}
          </section>
          <section className="panel-card compact">
            <p className="eyebrow">职责边界</p>
            <ul className="plain-list">
              {responsibilityBaseline.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
          <section className="panel-card compact">
            <p className="eyebrow">全局弹窗</p>
            <div className="action-stack">
              {Object.entries(modalRegistry).map(([key, modal]) => (
                <button
                  key={key}
                  className="ghost-button"
                  onClick={() => openModal(key)}
                  type="button"
                >
                  {modal.title}
                </button>
              ))}
            </div>
          </section>
          <StatusBoard />
        </aside>
      </div>
      <ModalHost />
    </div>
  )
}
