import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BookOpen, CheckCircle2, ChevronDown, ChevronUp,
  ClipboardList, FolderGit2, Lock, Zap,
} from 'lucide-react'
import {
  adjustPacing, fetchCareers, generateRoadmap, getRoadmap,
  getProfile, markItemComplete,
  type CareerBrief, type RoadmapItem, type RoadmapOut,
} from '../services/api'

const PACING_OPTIONS = [
  { id: 'fast_track', label: 'Fast Track', hint: '15–20 h/wk' },
  { id: 'balanced',   label: 'Balanced',   hint: '8–12 h/wk' },
  { id: 'relaxed',    label: 'Relaxed',    hint: '4–6 h/wk' },
]

const STATUS_STYLES: Record<string, string> = {
  complete: 'border-emerald-300 bg-emerald-50',
  active:   'border-indigo-400 bg-indigo-50',
  locked:   'border-slate-200 bg-white opacity-60',
}

const ITEM_ICON: Record<string, React.ReactNode> = {
  course:       <BookOpen className="h-4 w-4" />,
  project:      <FolderGit2 className="h-4 w-4" />,
  assessment:   <ClipboardList className="h-4 w-4" />,
  reinforcement:<Zap className="h-4 w-4 text-amber-500" />,
}

function groupByPhase(items: RoadmapItem[]): [string, RoadmapItem[]][] {
  const order: string[] = []
  const map = new Map<string, RoadmapItem[]>()
  for (const item of items) {
    if (!map.has(item.phase_label)) { map.set(item.phase_label, []); order.push(item.phase_label) }
    map.get(item.phase_label)!.push(item)
  }
  return order.map(k => [k, map.get(k)!])
}

export default function RoadmapPage() {
  const navigate = useNavigate()
  const [roadmap, setRoadmap] = useState<RoadmapOut | null>(null)
  const [careers, setCareers] = useState<CareerBrief[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)
  const [selectedRole, setSelectedRole] = useState('')
  const [pacing, setPacing] = useState('balanced')
  const [expandedPhases, setExpandedPhases] = useState<Set<string>>(new Set())

  useEffect(() => {
    Promise.all([
      getRoadmap().catch(() => null),
      fetchCareers().catch(() => [] as CareerBrief[]),
      getProfile().catch(() => null),
    ]).then(([rm, c, profile]) => {
      setCareers(c)
      if (rm) {
        setRoadmap(rm)
        setPacing(rm.pacing_mode)
        // Expand active phase by default
        const activeItem = rm.items.find(i => i.status === 'active')
        if (activeItem) setExpandedPhases(new Set([activeItem.phase_label]))
      }
      if (!rm && profile?.target_career_role_id) setSelectedRole(profile.target_career_role_id)
    }).finally(() => setLoading(false))
  }, [])

  async function handleGenerate() {
    if (!selectedRole) return
    setGenerating(true); setError(null)
    try {
      const rm = await generateRoadmap(selectedRole, pacing)
      setRoadmap(rm)
      const activeItem = rm.items.find(i => i.status === 'active')
      if (activeItem) setExpandedPhases(new Set([activeItem.phase_label]))
    } catch (e) { setError((e as Error).message) }
    finally { setGenerating(false) }
  }

  async function handlePacingChange(newPacing: string) {
    setPacing(newPacing)
    if (!roadmap) return
    try { setRoadmap(await adjustPacing(newPacing)) }
    catch { /* silent */ }
  }

  async function handleComplete(itemId: string) {
    try { setRoadmap(await markItemComplete(itemId)) }
    catch (e) { setError((e as Error).message) }
  }

  function togglePhase(label: string) {
    setExpandedPhases(prev => {
      const next = new Set(prev)
      next.has(label) ? next.delete(label) : next.add(label)
      return next
    })
  }

  if (loading) return <LoadingState />

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="mx-auto max-w-3xl">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900">Learning Roadmap</h1>
          <p className="mt-1 text-sm text-slate-500">
            Your prerequisite-aware path to career readiness.
          </p>
        </div>

        {error && <div className="mb-4 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</div>}

        {!roadmap ? (
          /* Generate panel */
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-base font-semibold text-slate-800">Generate your roadmap</h2>
            <div className="mb-4">
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Target career</label>
              <select
                value={selectedRole}
                onChange={e => setSelectedRole(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
              >
                <option value="">Select…</option>
                {careers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <PacingSelector value={pacing} onChange={handlePacingChange} />
            <button
              type="button"
              onClick={handleGenerate}
              disabled={!selectedRole || generating}
              className="mt-4 w-full rounded-lg bg-indigo-600 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:opacity-50"
            >
              {generating ? 'Generating…' : 'Generate Roadmap'}
            </button>
          </div>
        ) : (
          <>
            {/* Roadmap header */}
            <div className="mb-4 flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 rounded-xl bg-white px-4 py-2 shadow-sm ring-1 ring-slate-200">
                <span className="text-xs font-medium text-slate-500">Total</span>
                <span className="font-bold text-slate-900">{roadmap.total_weeks}w</span>
              </div>
              <div className="flex items-center gap-2 rounded-xl bg-white px-4 py-2 shadow-sm ring-1 ring-slate-200">
                <span className="text-xs font-medium text-slate-500">Items</span>
                <span className="font-bold text-slate-900">{roadmap.items.length}</span>
              </div>
              <div className="flex items-center gap-2 rounded-xl bg-emerald-50 px-4 py-2 shadow-sm ring-1 ring-emerald-200">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                <span className="font-bold text-emerald-700">
                  {roadmap.items.filter(i => i.status === 'complete').length} done
                </span>
              </div>
              <div className="ml-auto">
                <PacingSelector value={pacing} onChange={handlePacingChange} compact />
              </div>
            </div>

            {/* Narrative */}
            {roadmap.narrative && (
              <div className="mb-5 rounded-xl border border-indigo-100 bg-indigo-50 px-4 py-3 text-sm text-indigo-800">
                {roadmap.narrative}
              </div>
            )}

            {/* Phases */}
            <div className="space-y-3">
              {groupByPhase(roadmap.items).map(([phase, items]) => {
                const isOpen = expandedPhases.has(phase)
                const doneCount = items.filter(i => i.status === 'complete').length
                const hasActive = items.some(i => i.status === 'active')
                return (
                  <div key={phase} className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
                    <button
                      type="button"
                      onClick={() => togglePhase(phase)}
                      className="flex w-full items-center justify-between px-5 py-4 text-left hover:bg-slate-50"
                    >
                      <div className="flex items-center gap-3">
                        <span className="font-semibold text-slate-800">{phase}</span>
                        {hasActive && (
                          <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-700">
                            In progress
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-slate-400">{doneCount}/{items.length} done</span>
                        {isOpen ? <ChevronUp className="h-4 w-4 text-slate-400" /> : <ChevronDown className="h-4 w-4 text-slate-400" />}
                      </div>
                    </button>

                    {isOpen && (
                      <div className="divide-y divide-slate-100 px-5 pb-4">
                        {items.map(item => (
                          <RoadmapRow
                            key={item.item_id}
                            item={item}
                            onComplete={() => handleComplete(item.item_id)}
                            onStartAssessment={() => navigate(`/assessment/${item.item_id}`)}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function RoadmapRow({
  item, onComplete, onStartAssessment,
}: {
  item: RoadmapItem
  onComplete: () => void
  onStartAssessment: () => void
}) {
  return (
    <div className={`flex items-center gap-3 rounded-lg border px-3 py-3 my-1.5 transition ${STATUS_STYLES[item.status]}`}>
      <div className={`flex-shrink-0 ${item.status === 'locked' ? 'text-slate-300' : item.status === 'complete' ? 'text-emerald-500' : 'text-indigo-500'}`}>
        {item.status === 'locked'   ? <Lock className="h-4 w-4" /> :
         item.status === 'complete' ? <CheckCircle2 className="h-4 w-4" /> :
         ITEM_ICON[item.item_type] ?? <BookOpen className="h-4 w-4" />}
      </div>

      <div className="flex-1 min-w-0">
        <p className="truncate text-sm font-medium text-slate-800">{item.title}</p>
        <p className="text-xs text-slate-400">
          Wk {item.week_start}–{item.week_end} · {item.item_type}
        </p>
      </div>

      {item.status === 'active' && (
        item.item_type === 'assessment' ? (
          <button
            type="button"
            onClick={onStartAssessment}
            className="flex-shrink-0 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-indigo-700"
          >
            Take quiz
          </button>
        ) : (
          <button
            type="button"
            onClick={onComplete}
            className="flex-shrink-0 rounded-lg border border-emerald-300 bg-white px-3 py-1.5 text-xs font-semibold text-emerald-700 transition hover:bg-emerald-50"
          >
            Mark done
          </button>
        )
      )}
    </div>
  )
}

function PacingSelector({ value, onChange, compact = false }: {
  value: string; onChange: (v: string) => void; compact?: boolean
}) {
  if (compact) {
    return (
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-xs font-medium text-slate-700 focus:outline-none"
      >
        {PACING_OPTIONS.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
      </select>
    )
  }
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium text-slate-700">Pacing mode</label>
      <div className="flex gap-2">
        {PACING_OPTIONS.map(p => (
          <button
            key={p.id}
            type="button"
            onClick={() => onChange(p.id)}
            className={`rounded-lg border-2 px-3 py-2 text-sm transition ${
              value === p.id
                ? 'border-indigo-500 bg-indigo-50 text-indigo-800'
                : 'border-slate-200 text-slate-600 hover:border-indigo-300'
            }`}
          >
            <div className="font-semibold">{p.label}</div>
            <div className="text-xs opacity-70">{p.hint}</div>
          </button>
        ))}
      </div>
    </div>
  )
}

function LoadingState() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
    </div>
  )
}
