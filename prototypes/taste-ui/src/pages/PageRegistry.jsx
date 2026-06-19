import { dataModelBaseline, mockData, pageBaseline } from '../data/baseline'
import { useDemoState } from '../hooks/useDemoState'

function Section({ title, description, children }) {
  return (
    <section className="panel-card">
      <div className="section-head">
        <div>
          <p className="eyebrow">页面基线</p>
          <h2>{title}</h2>
        </div>
        {description ? <p>{description}</p> : null}
      </div>
      {children}
    </section>
  )
}

function Metrics({ items }) {
  return (
    <section className="metric-strip">
      {items.map((item) => (
        <article key={item.label} className="metric-card">
          <small>{item.label}</small>
          <strong>{item.value}</strong>
          <p>{item.note}</p>
        </article>
      ))}
    </section>
  )
}

function DatasetCards({ datasetKey }) {
  return (
    <div className="card-grid">
      {mockData[datasetKey].map((item) => (
        <article key={item.id} className="data-card">
          {Object.entries(item).map(([field, value]) => (
            <div key={field} className="data-row">
              <span>{field}</span>
              <strong>{String(value)}</strong>
            </div>
          ))}
        </article>
      ))}
    </div>
  )
}

export function PageRenderer({ pageKey }) {
  const { openModal, cycleStatus, statusMap, variant } = useDemoState()
  const page = pageBaseline[pageKey]
  const metrics = [
    { label: '页面目标', value: page.title, note: page.summary },
    { label: '风格取向', value: variant.tone, note: variant.surface },
    {
      label: '当前主状态',
      value: statusMap[page.statusKeys[0]] ?? 'empty',
      note: '点击动作或状态卡可切换演示',
    },
  ]

  return (
    <div className="scenario-stack">
      <Section title={page.title} description={page.summary}>
        <div className="hero-grid">
          <div>
            <h3>关键模块</h3>
            <ul className="chip-list">
              {page.modules.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3>涉及数据模型</h3>
            <ul className="plain-list dense">
              {page.datasets.map((datasetKey) => {
                const model = dataModelBaseline.find(
                  (item) => item.key === datasetKey,
                )
                return (
                  <li key={datasetKey}>
                    {model.label}: {model.fields.join(' / ')}
                  </li>
                )
              })}
            </ul>
          </div>
        </div>
      </Section>
      <Metrics items={metrics} />
      <Section
        title="关键动作与弹窗"
        description="所有动作均走统一弹窗注册表和状态基线。"
      >
        <div className="action-stack horizontal">
          {page.actions.map((action) => (
            <button
              key={action.label}
              className="primary-button"
              onClick={() => {
                openModal(action.modal)
                cycleStatus(action.status)
              }}
              type="button"
            >
              {action.label}
            </button>
          ))}
        </div>
      </Section>
      {page.datasets.map((datasetKey) => (
        <Section
          key={datasetKey}
          title={`${dataModelBaseline.find((item) => item.key === datasetKey).label} mock`}
          description="集中管理于 data 层，不在页面硬编码。"
        >
          <DatasetCards datasetKey={datasetKey} />
        </Section>
      ))}
      <Section
        title="状态说明"
        description="覆盖 loading / empty / success / error / confirm 五种演示状态。"
      >
        <div className="state-grid">
          {page.statusKeys.map((statusKey) => (
            <button
              key={statusKey}
              className="state-card"
              onClick={() => cycleStatus(statusKey)}
              type="button"
            >
              <span>{statusKey}</span>
              <strong data-state={statusMap[statusKey]}>
                {statusMap[statusKey]}
              </strong>
              <small>点击切换状态用于评审演示</small>
            </button>
          ))}
        </div>
      </Section>
    </div>
  )
}
