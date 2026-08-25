import { useEffect, useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import OnboardingPage from './pages/OnboardingPage'
import RegisterPage from './pages/RegisterPage'
import { fetchHealth, type HealthResponse } from './services/api'

// Guard: redirect unauthenticated users to /login
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function AppShell() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [healthError, setHealthError] = useState<string | null>(null)

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((error: Error) => setHealthError(error.message))
  }, [])

  return (
    <>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/onboarding"
          element={
            <ProtectedRoute>
              <OnboardingPage />
            </ProtectedRoute>
          }
        />
        {/* Future routes land here */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      {/* Dev-only API status footer */}
      {import.meta.env.DEV && (
        <footer className="border-t border-slate-200 bg-white px-6 py-3">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
            <span>PathWise AI — Phase 3 scaffold</span>
            {health && (
              <span className="rounded-md bg-emerald-50 px-2 py-1 font-medium text-emerald-700">
                API {health.status} · {health.app} v{health.version}
              </span>
            )}
            {healthError && (
              <span className="rounded-md bg-amber-50 px-2 py-1 font-medium text-amber-700">
                API unreachable — start backend on port 8000
              </span>
            )}
          </div>
        </footer>
      )}
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppShell />
      </AuthProvider>
    </BrowserRouter>
  )
}
