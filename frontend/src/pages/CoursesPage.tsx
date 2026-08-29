import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BookOpen, ChevronDown, ChevronUp,
  FolderGit2, Info, Sliders, Star,
} from 'lucide-react'
import FeedbackControl from '../components/FeedbackControl'
import {
  fetchCareers, fetchRecommendations, getProfile,
  type CareerBrief, type RecommendationItem,
} from '../services/api'

const FACTOR_LABELS: Record<string, string> = {
  skill_gap_match:          'Skill Gap Match',
  goal_relevance:           'Goal Relevance',
  prerequisite_fit:         'Prereq Fit',
  difficulty_fit:           'Difficulty Fit',
  learning_pref_fit:        'Learning Style',
  time_fit:                 'Time Fit',
  user_feedback_adjustment: 'Your Feedback',
}

const FACTOR_COLORS: Record<string, string> = {
  skill_gap_match:          'bg-indigo-500',
  goal_relevance:           'bg-violet-500',
  prerequisite_fit:         'bg-sky-500',
  difficulty_fit:           'bg-amber-500',
  learning_pref_fit:        'bg-pink-500',
  time_fit:                 'bg-teal-500',
  user_feedback_adjustment: 'bg-emerald-500',
}

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-28 flex-shrink-0 text-xs text-slate-500">{label}</span>
      <div className="flex-1 overflow-hidden rounded-full bg-slate-100 h-2">
        <div
          className={`h-2 rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${Math.round(value * 100)}%` }}
        />
      </div>
      <span className="w-8 text-right text-xs font-medium text-slate-600">
        {Math.round(value * 100)}%
      </span>
    </div>
  )
}

function RecommendationCard({ item, rank }: { item: RecommendationItem; rank: number }) {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()

  const difficultyDots = (score: number) => {
    const filled = Math.round(score * 5)
    return Array.from({ length: 5 }, (_, i) => (
      <span
        key={i}
        className={`inline-block h-1.5 w-1.5 rounded-full ${
          i < filled ? 'bg-indigo-500' : 'bg-slate-200'
        }`}
      />
    ))
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:shadow-md">
      {/* Header row */}
      <div className="flex items-start gap-3 p-4">
        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-indigo-100 text-sm font-bold text-indigo-700">
          {rank}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
              {item.item_type === 'course'
                ? <BookOpen className="h-3 w-3" />
                : <FolderGit2 className="h-3 w-3" />}
              {item.item_type}
            </span>
            <span className="inline-flex items-center gap-1 rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-semibold text-indigo-700">
              <Star className="h-3 w-3" />
              {Math.round(item.total_score * 100)}% match
            </span>
          </div>
          <h3 className="mt-1 font-semibold text-slate-900">{item.title}</h3>
          <div className="mt-1 flex items-center gap-2 text-xs text-slate-400">
            <span>Difficulty</span>
            <div className="flex gap-0.5">
              {difficultyDots(item.breakdown.difficulty_fit)}
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex flex-shrink-0 flex-col items-end gap-2">
          {item.item_type === 'assessment' ? (
            <button
              type="button"
              onClick={() => navigate(`/assessment/${item.id}`)}
              className="rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-indigo-700"
            >
              Take Quiz
            </button>
          ) : null}
          <button
            type="button"
            onClick={() => setOpen(o => !o)}
            className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs text-slate-500 transition hover:bg-slate-50"
            aria-expanded={open}
          >
            <Info className="h-3.5 w-3.5" />
            Why this?
            {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          </button>
        </div>
      </div>

      {/* Why this? panel */}
      {open && (
        <div className="border-t border-slate-100 px-4 pb-4 pt-3">
          {item.explanation && (
            <p className="mb-3 rounded-lg bg-indigo-50 px-3 py-2.5 text-sm text-indigo-800">
              {item.explanation}
            </p>
          )}
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Score breakdown
          </p>
          <div className="space-y-1.5">
            {Object.entries(item.breakdown)
              .filter(([k]) => k !== 'total')
              .map(([k, v]) => (
                <ScoreBar
                  key={k}
                  label={FACTOR_LABELS[k] ?? k}
                  value={v as number}
                  color={FACTOR_COLORS[k] ?? 'bg-slate-400'}
                />
              ))}
          </div>
        </div>
      )}

      {/* Feedback */}
      <div className="border-t border-slate-100 px-4 py-2.5">
        <FeedbackControl itemId={item.id} itemType={item.item_type} />
      </div>
    </div>
  )
}

export default function CoursesPage() {
  const [roleId, setRoleId] = useState<string | null>(null)
  const [careers, setCareers] = useState<CareerBrief[]>([])
  const [items, setItems] = useState<RecommendationItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [topN, setTopN] = useState(10)
  const fetchedRef = useRef(false)

  useEffect(() => {
    Promise.all([
      fetchCareers().catch(() => [] as CareerBrief[]),
      getProfile().catch(() => null),
    ]).then(([c, profile]) => {
      setCareers(c)
      if (profile?.target_career_role_id) setRoleId(profile.target_career_role_id)
    })
  }, [])

  useEffect(() => {
    if (!roleId) return
    setLoading(true); setError(null)
    fetchRecommendations(roleId, true, topN)
      .then(setItems)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
    fetchedRef.current = true
  }, [roleId, topN])

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="mx-auto max-w-2xl">
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Recommendations</h1>
            <p className="mt-1 text-sm text-slate-500">
              Ranked by your skill gaps, prereqs, difficulty, and time.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Sliders className="h-4 w-4 text-slate-400" />
            <select
              value={topN}
              onChange={e => setTopN(Number(e.target.value))}
              className="rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-xs text-slate-700 focus:outline-none"
            >
              {[5, 10, 15, 20].map(n => <option key={n} value={n}>Top {n}</option>)}
            </select>
          </div>
        </div>

        {/* Career selector */}
        <div className="mb-5">
          <select
            value={roleId ?? ''}
            onChange={e => setRoleId(e.target.value || null)}
            className="w-full max-w-xs rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          >
            <option value="">Select a career role…</option>
            {careers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>

        {error && (
          <div className="mb-4 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</div>
        )}

        {loading ? (
          <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-8 justify-center">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
            <span className="text-sm text-slate-500">Scoring recommendations…</span>
          </div>
        ) : (
          <div className="space-y-4">
            {items.map(item => (
              <RecommendationCard key={item.id} item={item} rank={item.rank} />
            ))}
            {items.length === 0 && roleId && !loading && (
              <p className="py-8 text-center text-sm text-slate-400">
                No recommendations yet — make sure your profile is complete.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
