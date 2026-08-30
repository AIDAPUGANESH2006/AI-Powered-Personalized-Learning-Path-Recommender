import { useEffect, useState } from 'react'
import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
  useLocation,
} from 'react-router-dom'
import {
  BookOpen,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  Map,
  Route as RouteIcon,
  TrendingUp,
  Zap,
} from 'lucide-react'

import { AuthProvider, useAuth } from './hooks/useAuth'
import AssessmentPage      from './pages/AssessmentPage'
import AssessmentsListPage  from './pages/AssessmentsListPage'
import CoursesPage         from './pages/CoursesPage'
import DashboardPage       from './pages/DashboardPage'
import LandingPage         from './pages/LandingPage'
import LoginPage           from './pages/LoginPage'
import OnboardingPage      from './pages/OnboardingPage'
import RegisterPage        from './pages/RegisterPage'
import RoadmapPage         from './pages/RoadmapPage'
import SkillGapPage        from './pages/SkillGapPage'
import TutorPage           from './pages/TutorPage'
import { fetchHealth, type HealthResponse } from './services/api'

// ── Nav config ──────────────────────────────────────────────────────────────
const NAV_ITEMS = [
  { to: '/dashboard',   label: 'Dashboard',   icon: <LayoutDashboard className="h-4 w-4" /> },
  { to: '/roadmap',     label: 'Roadmap',     icon: <Map            className="h-4 w-4" /> },
  { to: '/courses',     label: 'Courses',     icon: <BookOpen       className="h-4 w-4" /> },
  { to: '/assessments', label: 'Assessments', icon: <ClipboardList  className="h-4 w-4" /> },
  { to: '/skill-gap',   label: 'Skill Gap',   icon: <TrendingUp     className="h-4 w-4" /> },
  { to: '/tutor',       label: 'AI Tutor',    icon: <Zap            className="h-4 w-4" /> },
]


// ── Guards ───────────────────────────────────────────────────────────────────
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

// ── Shared nav bar (only shown when authenticated) ───────────────────────────
function NavBar() {
  const { logout } = useAuth()
  const location   = useLocation()

  return (
    <nav className="sticky top-0 z-50 border-b border-slate-200 bg-white shadow-sm">
      <div className="mx-auto flex max-w-5xl items-center gap-1 px-4 py-2">
        {/* Logo */}
        <Link
          to="/dashboard"
          className="mr-4 flex items-center gap-1.5 text-indigo-700 font-bold text-sm"
        >
          <RouteIcon className="h-5 w-5" />
          PathWise AI
        </Link>

        {/* Links */}
        <div className="flex flex-1 items-center gap-0.5 overflow-x-auto">
          {NAV_ITEMS.map(item => {
            const active = location.pathname.startsWith(item.to)
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium whitespace-nowrap transition ${
                  active
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'text-slate-500 hover:bg-slate-100 hover:text-slate-800'
                }`}
              >
                {item.icon}
                {item.label}
              </Link>
            )
          })}
        </div>

        {/* Logout */}
        <button
          type="button"
          onClick={logout}
          className="ml-2 inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
          aria-label="Sign out"
        >
          <LogOut className="h-4 w-4" />
          <span className="hidden sm:inline">Sign out</span>
        </button>
      </div>
    </nav>
  )
}

// ── App shell ─────────────────────────────────────────────────────────────────
function AppShell() {
  const { isAuthenticated } = useAuth()
  const location            = useLocation()
  const [health, setHealth] = useState<HealthResponse | null>(null)

  // Hide nav on public / full-screen pages
  const publicPaths  = ['/', '/login', '/register']
  const fullscreen   = ['/tutor']
  const showNav      = isAuthenticated && !publicPaths.includes(location.pathname)
  const showFooter   =
    import.meta.env.DEV &&
    !fullscreen.some(p => location.pathname.startsWith(p))

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => null)
  }, [])

  return (
    <div className="flex min-h-screen flex-col">
      {showNav && <NavBar />}

      <main className="flex-1">
        <Routes>
          {/* Public */}
          <Route path="/"         element={<LandingPage />} />
          <Route path="/login"    element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected */}
          <Route path="/onboarding" element={<ProtectedRoute><OnboardingPage /></ProtectedRoute>} />
          <Route path="/dashboard"  element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/roadmap"    element={<ProtectedRoute><RoadmapPage /></ProtectedRoute>} />
          <Route path="/courses"    element={<ProtectedRoute><CoursesPage /></ProtectedRoute>} />
          <Route path="/assessments" element={<ProtectedRoute><AssessmentsListPage /></ProtectedRoute>} />
          <Route path="/skill-gap"  element={<ProtectedRoute><SkillGapPage /></ProtectedRoute>} />
          <Route path="/tutor"      element={<ProtectedRoute><TutorPage /></ProtectedRoute>} />
          <Route
            path="/assessment/:id"
            element={<ProtectedRoute><AssessmentPage /></ProtectedRoute>}
          />

          {/* Catch-all */}
          <Route path="*" element={<Navigate to={isAuthenticated ? '/dashboard' : '/'} replace />} />
        </Routes>
      </main>

      {/* Dev API status footer */}
      {showFooter && (
        <footer className="border-t border-slate-200 bg-white px-6 py-2">
          <div className="mx-auto flex max-w-5xl items-center justify-between text-xs text-slate-400">
            <span>PathWise AI — dev build</span>
            {health ? (
              <span className="rounded bg-emerald-50 px-2 py-0.5 font-medium text-emerald-700">
                API {health.status} · v{health.version}
              </span>
            ) : (
              <span className="rounded bg-amber-50 px-2 py-0.5 font-medium text-amber-600">
                API unreachable — start backend on :8000
              </span>
            )}
          </div>
        </footer>
      )}
    </div>
  )
}

// ── Root ──────────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppShell />
      </AuthProvider>
    </BrowserRouter>
  )
}
