import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowRight, BookOpen, CheckCircle2, ClipboardList,
  FolderGit2, Flame, Target, TrendingUp, Zap,
} from 'lucide-react'
import {
  fetchSkillGap, getRoadmap, getProfile,
  type RoadmapItem, type RoadmapOut, type SkillGapItem,
} from '../services/api'

// ── Radial readiness ring ────────────────────────────────────────────────────
function ReadinessRing({ pct }: { pct: number }) {
  const r = 52
  const circ = 2 * Math.PI * r
  const dash = (pct / 100) * circ
  return (
    <div className="relative flex items-center justify-center">
      <svg width="128" height="128" className="-rotate-90">
        <circle cx="64" cy="64" r={r} fill="none" stroke="#e2e8f0" strokeWidth="10" />
        <circle
          cx="64" cy="64" r={r} fill="none"
          stroke="#6366f1" strokeWidth="10"
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
          className="transition-all duration-700"
        />
      </svg>
      <div className="absolute text-center">
        <div className="text-3xl font-extrabold text-slate-900">{pct}%</div>
        <div className="text-xs font-medium text-slate-400">Readiness</div>
      </div>
    </div>
  )
}

// ── Skill bars ───────────────────────────────────────────────────────────────
function SkillBar({ gap }: { gap: SkillGapItem }) {
  const cur = Math.round(gap.current_level * 100)
  const req = Math.round(gap.required_level * 100)
  const color =
    gap.priority === 'HIGH'   ? 'bg-red-400'    :
    gap.priority === 'MEDIUM' ? 'bg-amber-400'  : 'bg-emerald-400'
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs">
        <span className="font-medium text-slate-700">{gap.skill_name}</span>
        <span className="text-slate-400">{cur}% / {req}%</span>
      </div>
      <div className="relative h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className="absolute top-0 h-full w-px bg-slate-300"
          style={{ left: `${req}%` }}
        />
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${cur}%` }}
        />
      </div>
    </div>
  )
}

// ── Next Best Action card ────────────────────────────────────────────────────
function NextActionCard({ item }: { item: RoadmapItem }) {
  const navigate = useNavigate()
  const icon =
    item.item_type === 'assessment'   ? <ClipboardList className="h-5 w-5" /> :
    item.item_type === 'project'      ? <FolderGit2   className="h-5 w-5" /> :
    item.item_type === 'reinforcement'? <Zap           className="h-5 w-5 text-amber-500" /> :
                                        <BookOpen      className="h-5 w-5" />

  const action =
    item.item_type === 'assessment' ? 'Take quiz' : 'Mark as done'

  const dest =
    item.item_type === 'assessment'
      ? `/assessment/${item.item_id}`
      : '/roadmap'

  return (
    <div className="rounded-2xl border border-indigo-200 bg-gradient-to-br from-indigo-50 to-white p-5 shadow-sm">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-indigo-400">
        Next Best Action
      </p>
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-indigo-100 text-indigo-600">
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-slate-900 leading-snug">{item.title}</p>
          <p className="mt-0.5 text-xs text-slate-400">
            {item.item_type} · Wk {item.week_start}–{item.week_end}
          </p>
        </div>
        <button
          type="button"
          onClick={() => navigate(dest)}
          className="flex-shrink-0 inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-indigo-700"
        >
          {action}
          <ArrowRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  )
}

// ── Stat tile ────────────────────────────────────────────────────────────────
function StatTile({
  icon, label, value, sub, color,
}: {
  icon: React.ReactNode; label: string; value: string | number
  sub?: string; color: string
}) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl ${color}`}>
        {icon}
      </div>
      <div>
        <p className="text-xs font-medium text-slate-400">{label}</p>
        <p className="text-xl font-bold text-slate-900">{value}</p>
        {sub && <p className="text-xs text-slate-400">{sub}</p>}
      </div>
    </div>
  )
}

// ── Page ─────────────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const navigate = useNavigate()
  const [roadmap, setRoadmap] = useState<RoadmapOut | null>(null)
  const [gaps, setGaps] = useState<SkillGapItem[]>([])
  const [readiness, setReadiness] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getProfile().catch(() => null).then(profile => {
      const roleId = profile?.target_career_role_id
      Promise.all([
        getRoadmap().catch(() => null),
        roleId ? fetchSkillGap(roleId).catch(() => null) : Promise.resolve(null),
      ]).then(([rm, gapData]) => {
        if (rm) setRoadmap(rm)
        if (gapData) { setGaps(gapData.gaps); setReadiness(gapData.career_readiness_pct) }
      }).finally(() => setLoading(false))
    })
  }, [])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
      </div>
    )
  }

  const completedItems = roadmap?.items.filter(i => i.status === 'complete') ?? []
  const activeItem    = roadmap?.items.find(i => i.status === 'active')
  const totalItems    = roadmap?.items.length ?? 0
  const progressPct   = totalItems ? Math.round((completedItems.length / totalItems) * 100) : 0

  const topGaps = [...gaps].slice(0, 6)

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="mx-auto max-w-3xl space-y-6">
        {/* Title */}
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="mt-1 text-sm text-slate-500">Your learning progress at a glance.</p>
        </div>

        {/* Top row: readiness ring + stats */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {/* Readiness card */}
          <div className="flex items-center gap-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <ReadinessRing pct={readiness ?? 0} />
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Career Readiness
              </p>
              {roadmap && (
                <p className="mt-1 text-sm text-slate-600">
                  {completedItems.length}/{totalItems} items complete
                </p>
              )}
              <div className="mt-2 h-2 w-36 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-2 rounded-full bg-indigo-500 transition-all duration-700"
                  style={{ width: `${progressPct}%` }}
                />
              </div>
              <p className="mt-1 text-xs text-slate-400">{progressPct}% of roadmap done</p>
            </div>
          </div>

          {/* Stat grid */}
          <div className="grid grid-cols-2 gap-3">
            <StatTile
              icon={<CheckCircle2 className="h-5 w-5 text-emerald-600" />}
              label="Completed"
              value={completedItems.length}
              color="bg-emerald-50"
            />
            <StatTile
              icon={<TrendingUp className="h-5 w-5 text-indigo-600" />}
              label="Skill Gaps"
              value={gaps.filter(g => g.priority === 'HIGH').length}
              sub="high priority"
              color="bg-indigo-50"
            />
            <StatTile
              icon={<Target className="h-5 w-5 text-violet-600" />}
              label="Roadmap"
              value={roadmap ? `${roadmap.total_weeks}w` : '—'}
              sub={roadmap?.pacing_mode.replace('_', ' ')}
              color="bg-violet-50"
            />
            <StatTile
              icon={<Flame className="h-5 w-5 text-orange-500" />}
              label="Gap Score"
              value={gaps.length ? `${Math.round((1 - (gaps.reduce((s, g) => s + g.gap_size, 0) / gaps.length)) * 100)}%` : '—'}
              sub="avg coverage"
              color="bg-orange-50"
            />
          </div>
        </div>

        {/* Next Best Action */}
        {activeItem && <NextActionCard item={activeItem} />}
        {!activeItem && !roadmap && (
          <div className="rounded-2xl border border-dashed border-indigo-300 bg-indigo-50 p-6 text-center">
            <p className="mb-3 text-sm text-indigo-700">
              You don't have a roadmap yet.
            </p>
            <button
              type="button"
              onClick={() => navigate('/roadmap')}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-700"
            >
              Generate my roadmap
            </button>
          </div>
        )}

        {/* Skill radar bars */}
        {topGaps.length > 0 && (
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-semibold text-slate-800">Skill Progress</h2>
              <button
                type="button"
                onClick={() => navigate('/skill-gap')}
                className="text-xs font-medium text-indigo-600 hover:underline"
              >
                Full analysis →
              </button>
            </div>
            <div className="space-y-3">
              {topGaps.map(g => <SkillBar key={g.skill_id} gap={g} />)}
            </div>
          </div>
        )}

        {/* Quick nav */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            { label: 'Roadmap',       to: '/roadmap',   icon: <Target className="h-4 w-4" /> },
            { label: 'Courses',       to: '/courses',   icon: <BookOpen className="h-4 w-4" /> },
            { label: 'Skill Gap',     to: '/skill-gap', icon: <TrendingUp className="h-4 w-4" /> },
            { label: 'AI Tutor',      to: '/tutor',     icon: <Zap className="h-4 w-4" /> },
          ].map(nav => (
            <button
              key={nav.to}
              type="button"
              onClick={() => navigate(nav.to)}
              className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-indigo-50 hover:border-indigo-200 hover:text-indigo-700"
            >
              {nav.icon}
              {nav.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
