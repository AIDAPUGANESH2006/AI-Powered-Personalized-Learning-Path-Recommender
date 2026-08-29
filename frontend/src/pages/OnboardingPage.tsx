import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft, ChevronRight, CheckCircle2 } from 'lucide-react'
import {
  createProfile,
  fetchCareers,
  fetchSkills,
  type CareerBrief,
  type LearningStyle,
  type SkillBrief,
  type SkillInput,
} from '../services/api'

// ── types ─────────────────────────────────────────────────────────────────────

interface FormState {
  target_career_role_id: string
  experience_level: string
  education: string
  goal: string
  timeline_months: number
  hours_per_week: number
  learning_style: LearningStyle | ''
  skills: SkillInput[]
}

const EXPERIENCE_LEVELS = [
  { id: 'student', label: 'Student' },
  { id: 'entry', label: 'Entry level (0–2 yrs)' },
  { id: 'mid', label: 'Mid level (2–5 yrs)' },
  { id: 'senior', label: 'Senior (5+ yrs)' },
]

const LEARNING_STYLES: { id: LearningStyle; label: string; emoji: string }[] = [
  { id: 'visual', label: 'Visual', emoji: '📊' },
  { id: 'hands_on', label: 'Hands-on', emoji: '🛠️' },
  { id: 'reading', label: 'Reading / docs', emoji: '📖' },
  { id: 'mixed', label: 'Mixed', emoji: '🔀' },
]

const STEP_TITLES = [
  'Career goal',
  'Background',
  'Schedule',
  'Current skills',
  'Review & submit',
]

// ── component ─────────────────────────────────────────────────────────────────

export default function OnboardingPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const [careers, setCareers] = useState<CareerBrief[]>([])
  const [skills, setSkills] = useState<SkillBrief[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitted, setSubmitted] = useState(false)

  const [form, setForm] = useState<FormState>({
    target_career_role_id: '',
    experience_level: '',
    education: '',
    goal: '',
    timeline_months: 6,
    hours_per_week: 10,
    learning_style: '',
    skills: [],
  })

  useEffect(() => {
    Promise.all([
      fetchCareers().catch(() => [] as CareerBrief[]),
      fetchSkills().catch(() => [] as SkillBrief[]),
    ]).then(([c, s]) => {
      setCareers(c)
      setSkills(s)
    })
  }, [])

  function setField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm(f => ({ ...f, [key]: value }))
  }

  function setSkillLevel(skillId: string, level: number) {
    setForm(f => {
      const existing = f.skills.find(s => s.skill_id === skillId)
      if (existing) {
        return {
          ...f,
          skills: f.skills.map(s => (s.skill_id === skillId ? { ...s, level } : s)),
        }
      }
      return { ...f, skills: [...f.skills, { skill_id: skillId, level }] }
    })
  }

  function toggleSkill(skillId: string) {
    setForm(f => {
      if (f.skills.find(s => s.skill_id === skillId)) {
        return { ...f, skills: f.skills.filter(s => s.skill_id !== skillId) }
      }
      return { ...f, skills: [...f.skills, { skill_id: skillId, level: 0.5 }] }
    })
  }

  async function handleSubmit() {
    setLoading(true)
    setError(null)
    try {
      await createProfile({
        target_career_role_id: form.target_career_role_id || undefined,
        experience_level: form.experience_level || undefined,
        education: form.education || undefined,
        goal: form.goal || undefined,
        timeline_months: form.timeline_months,
        hours_per_week: form.hours_per_week,
        learning_style: form.learning_style || undefined,
        skills: form.skills,
      })
      setSubmitted(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save profile')
    } finally {
      setLoading(false)
    }
  }

  if (submitted) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-slate-50 to-indigo-50 px-4">
        <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-10 text-center shadow-xl">
          <CheckCircle2 className="mx-auto mb-4 h-14 w-14 text-emerald-500" />
          <h2 className="mb-2 text-2xl font-bold text-slate-900">You're all set!</h2>
          <p className="mb-6 text-slate-500">
            Your profile has been saved. Skill gap analysis and roadmap generation are coming in the next phase.
          </p>
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-700"
          >
            Go to dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-indigo-50 px-4 py-10">
      <div className="mx-auto max-w-xl">
        {/* Progress bar */}
        <div className="mb-8">
          <div className="mb-2 flex justify-between text-xs text-slate-500">
            {STEP_TITLES.map((title, i) => (
              <span
                key={title}
                className={i === step ? 'font-semibold text-indigo-600' : ''}
              >
                {title}
              </span>
            ))}
          </div>
          <div className="h-1.5 w-full rounded-full bg-slate-200">
            <div
              className="h-1.5 rounded-full bg-indigo-500 transition-all duration-300"
              style={{ width: `${((step + 1) / STEP_TITLES.length) * 100}%` }}
            />
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-xl">
          {/* Step 0 — Career goal */}
          {step === 0 && (
            <div>
              <h2 className="mb-1 text-xl font-bold text-slate-900">What's your target career?</h2>
              <p className="mb-5 text-sm text-slate-500">Pick the role you're working towards.</p>

              {careers.length === 0 ? (
                <p className="text-sm text-amber-600">
                  Career options unavailable — backend may be offline. You can still continue.
                </p>
              ) : (
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  {careers.map(c => (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => setField('target_career_role_id', c.id)}
                      className={`rounded-xl border-2 p-4 text-left text-sm transition ${
                        form.target_career_role_id === c.id
                          ? 'border-indigo-500 bg-indigo-50 text-indigo-800'
                          : 'border-slate-200 text-slate-700 hover:border-indigo-300'
                      }`}
                    >
                      <span className="font-semibold">{c.name}</span>
                      <p className="mt-1 text-xs text-slate-500 line-clamp-2">{c.description}</p>
                    </button>
                  ))}
                </div>
              )}

              <div className="mt-5">
                <label className="mb-1 block text-sm font-medium text-slate-700">
                  Describe your goal in your own words <span className="text-slate-400">(optional)</span>
                </label>
                <textarea
                  rows={3}
                  value={form.goal}
                  onChange={e => setField('goal', e.target.value)}
                  placeholder="e.g. I want to transition from web dev to ML engineering within a year"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
                />
              </div>
            </div>
          )}

          {/* Step 1 — Background */}
          {step === 1 && (
            <div>
              <h2 className="mb-1 text-xl font-bold text-slate-900">Tell us about yourself</h2>
              <p className="mb-5 text-sm text-slate-500">This helps calibrate the difficulty of recommendations.</p>

              <div className="mb-4">
                <label className="mb-2 block text-sm font-medium text-slate-700">Experience level</label>
                <div className="grid grid-cols-2 gap-3">
                  {EXPERIENCE_LEVELS.map(lvl => (
                    <button
                      key={lvl.id}
                      type="button"
                      onClick={() => setField('experience_level', lvl.id)}
                      className={`rounded-xl border-2 px-4 py-3 text-sm font-medium transition ${
                        form.experience_level === lvl.id
                          ? 'border-indigo-500 bg-indigo-50 text-indigo-800'
                          : 'border-slate-200 text-slate-700 hover:border-indigo-300'
                      }`}
                    >
                      {lvl.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label htmlFor="education" className="mb-1 block text-sm font-medium text-slate-700">
                  Education background <span className="text-slate-400">(optional)</span>
                </label>
                <input
                  id="education"
                  type="text"
                  value={form.education}
                  onChange={e => setField('education', e.target.value)}
                  placeholder="e.g. B.Tech CSE, 3rd year"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
                />
              </div>
            </div>
          )}

          {/* Step 2 — Schedule */}
          {step === 2 && (
            <div>
              <h2 className="mb-1 text-xl font-bold text-slate-900">How much time do you have?</h2>
              <p className="mb-5 text-sm text-slate-500">Used to estimate your roadmap pacing.</p>

              <div className="mb-6">
                <label className="mb-1 block text-sm font-medium text-slate-700">
                  Target timeline: <span className="font-semibold text-indigo-600">{form.timeline_months} months</span>
                </label>
                <input
                  type="range"
                  min={1}
                  max={24}
                  value={form.timeline_months}
                  onChange={e => setField('timeline_months', Number(e.target.value))}
                  className="w-full accent-indigo-600"
                />
                <div className="mt-1 flex justify-between text-xs text-slate-400">
                  <span>1 month</span>
                  <span>24 months</span>
                </div>
              </div>

              <div className="mb-6">
                <label className="mb-1 block text-sm font-medium text-slate-700">
                  Hours per week: <span className="font-semibold text-indigo-600">{form.hours_per_week}h</span>
                </label>
                <input
                  type="range"
                  min={2}
                  max={40}
                  step={2}
                  value={form.hours_per_week}
                  onChange={e => setField('hours_per_week', Number(e.target.value))}
                  className="w-full accent-indigo-600"
                />
                <div className="mt-1 flex justify-between text-xs text-slate-400">
                  <span>2h</span>
                  <span>40h</span>
                </div>
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">Learning style</label>
                <div className="grid grid-cols-2 gap-3">
                  {LEARNING_STYLES.map(ls => (
                    <button
                      key={ls.id}
                      type="button"
                      onClick={() => setField('learning_style', ls.id)}
                      className={`rounded-xl border-2 px-4 py-3 text-sm font-medium transition ${
                        form.learning_style === ls.id
                          ? 'border-indigo-500 bg-indigo-50 text-indigo-800'
                          : 'border-slate-200 text-slate-700 hover:border-indigo-300'
                      }`}
                    >
                      <span className="mr-2">{ls.emoji}</span>{ls.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 3 — Skills */}
          {step === 3 && (
            <div>
              <h2 className="mb-1 text-xl font-bold text-slate-900">What do you already know?</h2>
              <p className="mb-5 text-sm text-slate-500">
                Select skills you have, then drag the slider to rate your confidence (0 = heard of it, 1 = expert).
              </p>

              {skills.length === 0 ? (
                <p className="text-sm text-amber-600">Skill catalog unavailable — backend may be offline.</p>
              ) : (
                <div className="max-h-96 space-y-2 overflow-y-auto pr-1">
                  {skills.map(s => {
                    const selected = form.skills.find(fs => fs.skill_id === s.id)
                    return (
                      <div
                        key={s.id}
                        className={`rounded-xl border-2 p-3 transition ${
                          selected ? 'border-indigo-400 bg-indigo-50' : 'border-slate-200'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <button
                            type="button"
                            onClick={() => toggleSkill(s.id)}
                            className="flex items-center gap-2 text-sm font-medium text-slate-800"
                          >
                            <span
                              className={`h-4 w-4 rounded border-2 flex-shrink-0 ${
                                selected ? 'border-indigo-500 bg-indigo-500' : 'border-slate-400'
                              }`}
                            />
                            {s.name}
                          </button>
                          {selected && (
                            <span className="text-xs font-semibold text-indigo-600">
                              {Math.round(selected.level * 100)}%
                            </span>
                          )}
                        </div>
                        {selected && (
                          <input
                            type="range"
                            min={0}
                            max={1}
                            step={0.05}
                            value={selected.level}
                            onChange={e => setSkillLevel(s.id, Number(e.target.value))}
                            className="mt-2 w-full accent-indigo-600"
                          />
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}

          {/* Step 4 — Review */}
          {step === 4 && (
            <div>
              <h2 className="mb-1 text-xl font-bold text-slate-900">Review your profile</h2>
              <p className="mb-5 text-sm text-slate-500">Everything looks good? Hit submit to save.</p>

              {error && (
                <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
                  {error}
                </div>
              )}

              <dl className="space-y-3 text-sm">
                <ReviewRow label="Career goal" value={
                  careers.find(c => c.id === form.target_career_role_id)?.name ?? '—'
                } />
                <ReviewRow label="Goal description" value={form.goal || '—'} />
                <ReviewRow label="Experience" value={
                  EXPERIENCE_LEVELS.find(e => e.id === form.experience_level)?.label ?? '—'
                } />
                <ReviewRow label="Education" value={form.education || '—'} />
                <ReviewRow label="Timeline" value={`${form.timeline_months} months`} />
                <ReviewRow label="Hours / week" value={`${form.hours_per_week}h`} />
                <ReviewRow label="Learning style" value={
                  LEARNING_STYLES.find(l => l.id === form.learning_style)?.label ?? '—'
                } />
                <ReviewRow
                  label="Skills selected"
                  value={
                    form.skills.length === 0
                      ? 'None'
                      : form.skills
                          .map(fs => {
                            const skill = skills.find(s => s.id === fs.skill_id)
                            return `${skill?.name ?? fs.skill_id} (${Math.round(fs.level * 100)}%)`
                          })
                          .join(', ')
                  }
                />
              </dl>
            </div>
          )}

          {/* Navigation */}
          <div className="mt-8 flex justify-between">
            <button
              type="button"
              onClick={() => setStep(s => s - 1)}
              disabled={step === 0}
              className="inline-flex items-center gap-1 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-40"
            >
              <ChevronLeft className="h-4 w-4" />
              Back
            </button>

            {step < STEP_TITLES.length - 1 ? (
              <button
                type="button"
                onClick={() => setStep(s => s + 1)}
                className="inline-flex items-center gap-1 rounded-lg bg-indigo-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-indigo-700"
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSubmit}
                disabled={loading}
                className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:opacity-60"
              >
                {loading ? 'Saving…' : 'Save profile'}
                <CheckCircle2 className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-3">
      <dt className="w-36 flex-shrink-0 font-medium text-slate-500">{label}</dt>
      <dd className="text-slate-800">{value}</dd>
    </div>
  )
}
