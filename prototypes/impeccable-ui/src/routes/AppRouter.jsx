import { Navigate, Route, Routes } from 'react-router-dom'
import { PageRenderer } from '../pages/PageRegistry'
import { AppShell } from '../components/AppShell'

export function AppRouter() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<PageRenderer pageKey="home" />} />
        <Route path="/auth" element={<PageRenderer pageKey="auth" />} />
        <Route path="/start" element={<PageRenderer pageKey="start" />} />
        <Route
          path="/destinations"
          element={<PageRenderer pageKey="destinations" />}
        />
        <Route path="/compare" element={<PageRenderer pageKey="compare" />} />
        <Route
          path="/workspace"
          element={<PageRenderer pageKey="workspace" />}
        />
        <Route
          path="/trip/:tripId?"
          element={<PageRenderer pageKey="tripDetail" />}
        />
        <Route path="/import" element={<PageRenderer pageKey="import" />} />
        <Route path="/discover" element={<PageRenderer pageKey="discover" />} />
        <Route
          path="/community"
          element={<PageRenderer pageKey="community" />}
        />
        <Route
          path="/community/:postId?"
          element={<PageRenderer pageKey="communityDetail" />}
        />
        <Route path="/my-trips" element={<PageRenderer pageKey="myTrips" />} />
      </Route>
      <Route path="*" element={<Navigate replace to="/" />} />
    </Routes>
  )
}
