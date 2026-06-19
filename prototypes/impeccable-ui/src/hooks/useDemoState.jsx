import { createContext, useContext, useMemo, useState } from 'react'

const DemoStateContext = createContext(null)
const order = ['loading', 'empty', 'success', 'error', 'confirm']
const defaults = {
  generation: 'loading',
  import: 'confirm',
  save: 'success',
  publish: 'empty',
  delete: 'confirm',
}

export function DemoStateProvider({ children, variant }) {
  const [activeModal, setActiveModal] = useState(null)
  const [statusMap, setStatusMap] = useState(defaults)
  const cycleStatus = (key) =>
    setStatusMap((current) => ({
      ...current,
      [key]: order[(order.indexOf(current[key] ?? 'empty') + 1) % order.length],
    }))
  const setStatus = (key, value) =>
    setStatusMap((current) => ({ ...current, [key]: value }))
  const value = useMemo(
    () => ({
      variant,
      activeModal,
      statusMap,
      cycleStatus,
      setStatus,
      openModal: setActiveModal,
      closeModal: () => setActiveModal(null),
    }),
    [activeModal, statusMap, variant],
  )
  return (
    <DemoStateContext.Provider value={value}>
      {children}
    </DemoStateContext.Provider>
  )
}

export function useDemoState() {
  const context = useContext(DemoStateContext)
  if (!context) throw new Error('useDemoState 必须在 DemoStateProvider 中使用')
  return context
}
