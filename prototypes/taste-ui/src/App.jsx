import { useEffect } from 'react'
import { AppRouter } from './routes/AppRouter'
import { DemoStateProvider } from './hooks/useDemoState'
import { variant } from './data/variant'

export default function App() {
  useEffect(() => {
    document.title = variant.appName
  }, [])

  return (
    <DemoStateProvider variant={variant}>
      <AppRouter />
    </DemoStateProvider>
  )
}
