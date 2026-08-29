import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertTriangle, ArrowRight, CheckCircle2, TrendingUp } from 'lucide-react'
import { fetchCareers, fetchSkillGap, getProfile, type CareerBrief, type SkillGapItem } from '../services/api'

const PRIORITY_COLOR: Record<string, string> = {
  HIGH:   'bg-red-500',
  MEDIUM: 'bg-amber-400',
  LOW:    'bg-emerald-400',
}
const PRIORITY_BADGE: Record<string, string> = {
  HIGH:   'bg-red-50 text-red-700 ring-red-200',
  MEDIUM: 'bg-amber-50 text-amber-700 ring-amber-200',
  LOW:    'bg-emerald-50 text-emerald-700 ring-emerald-200',
}

export default function SkillGapPage() {
  const navigate = useNavigate()
  const [roleId, setRoleId] = useState<string | null>(null)
  const [careers, setCareers] = useState<CareerBrief[]>([])
  const [gaps, setGaps] = useState<SkillGapItem[]>([])
  const [readiness, setReadiness] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Pre-select the career from the user's profile
  useEffect(() => {
    Promise.all([
      getProfile().catch(() => null),
      fetchCareers().catch(() => [] as CareerBrief[]),
    ]).then(([profile, c]) => {
      setCareers(c)
      if (profile?.target_career_role_id) setRoleId(profile.target_career_role_id)
    })
  }, [])

  useEffect(() => {
    if (!roleId) return
    setLoading(true)
    setError(null)
    fetchSkillGap(roleId)
      .then(r => { setGaps(r.gaps); setReadiness(r.career_readiness_pct) })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [roleId])

  const highGaps = gaps.filter(g => g.priority === 'HIGH')
  const otherGaps = gaps.filter(g => g.priority !== 'HIGH')

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="mx-auto max-w-3xl">
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Skill Gap Analysis</h1>
            <p className="mt-1 text-sm text-slate-500">
              See exactly where you stand against your target role.
            </p>
          </div>
          {readiness !== null && (
            <div className="flex-shrink-0 rounded-2xl bg-indigo-600 px-5 py-3 text-center text-white shadow-lg">
              <div className="text-3xl font-extrabold leading-none">{readiness}%</div>
              <div className="mt-0.5 text-xs font-medium opacity-80">Career Readiness</div>
            </div>
          )}
        </div>

        {/* Career selector */}
        <div className="mb-6">
          <label className="mb-1.5 block text-sm font-medium text-slate-700">
            Analysing for
          </label>
          <select
            value={roleId ?? ''}
            onChange={e => setRoleId(e.target.value || null)}
            className="w-full max-w-xs rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          >
            <option value="">Select a career role…</option>
            {careers.map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>

        {loading && (
          <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-500">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
            Calculating gaps…
          </div>
        )}

        {error && (
          <div className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</div>
        )}

        {!loading && gaps.length === 0 && readiness !== null && (
          <div className="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-6">
            <CheckCircle2 className="h-6 w-6 flex-shrink-0 text-emerald-500" />
            <p className="text-sm font-medium text-emerald-800">
              You already meet all requirements for this role. Time to apply!
            </p>
          </div>
        )}

        {highGaps.length > 0 && (
          <section className="mb-6">
            <div className="mb-3 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              <h2 className="text-sm font-semibold text-slate-700">
                High-priority gaps ({highGaps.length})
              </h2>
            </div>
            <div className="space-y-3">
              {highGaps.map(g => <GapCard key={g.skill_id} gap={g} />)}
            </div>
          </section>
        )}

        {otherGaps.length > 0 && (
          <section className="mb-8">
            <div className="mb-3 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-slate-400" />
              <h2 className="text-sm font-semibold text-slate-700">
                Medium & low gaps ({otherGaps.length})
              </h2>
            </div>
            <div className="space-y-3">
              {otherGaps.map(g => <GapCard key={g.skill_id} gap={g} />)}
            </div>
          </section>
        )}

        {gaps.length > 0 && (
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => navigate('/roadmap')}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow transition hover:bg-indigo-700"
            >
              View my roadmap
              <ArrowRight className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={() => navigate('/courses')}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
            >
              Browse recommendations
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function GapCard({ gap }: { gap: SkillGapItem }) {
  const currentPct = Math.round(gap.current_level * 100)
  const requiredPct = Math.round(gap.required_level * 100)
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <span className="font-medium text-slate-800">{gap.skill_name}</span>
        <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ${PRIORITY_BADGE[gap.priority]}`}>
          {gap.priority}
        </span>
      </div>
      <div className="flex items-center gap-3">
        <div className="relative h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
          {/* Required level indicator */}
          <div
            className="absolute top-0 h-full w-px bg-slate-400"
            style={{ left: `${requiredPct}%` }}
          />
          {/* Current level bar */}
          <div
            className={`h-full rounded-full transition-all duration-500 ${PRIORITY_COLOR[gap.priority]}`}
            style={{ width: `${currentPct}%` }}
          />
        </div>
        <span className="w-24 flex-shrink-0 text-right text-xs text-slate-500">
          {currentPct}% → {requiredPct}%
        </span>
      </div>
    </div>
  )
}
