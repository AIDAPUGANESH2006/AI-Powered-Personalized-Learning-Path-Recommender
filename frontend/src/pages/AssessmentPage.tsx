import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { CheckCircle2, XCircle } from 'lucide-react'
import {
  fetchAssessment, markItemComplete, submitAssessment,
  type AssessmentOut, type AssessmentSubmitResult,
} from '../services/api'
import {
  COURSE_TO_ASSESSMENT_MAP,
  getLocalAssessment,
  type StaticAssessment,
} from '../data/assessmentsData'

type Phase = 'loading' | 'quiz' | 'result' | 'error'

export default function AssessmentPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [phase, setPhase] = useState<Phase>('loading')
  const [assessment, setAssessment] = useState<AssessmentOut | null>(null)
  const [localData, setLocalData] = useState<StaticAssessment | null>(null)
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [result, setResult] = useState<AssessmentSubmitResult | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    if (!id) return

    const mappedId = COURSE_TO_ASSESSMENT_MAP[id] || id
    const local = getLocalAssessment(id) || getLocalAssessment(mappedId)

    if (local) {
      setLocalData(local)
      setAssessment({
        id: local.id,
        title: local.title,
        skill_id: local.skill_id,
        pass_threshold: local.pass_threshold,
        questions: local.questions.map(q => ({
          id: q.id,
          question: q.question,
          options: q.options,
        })),
      })
      setPhase('quiz')
    }

    // Also attempt to fetch latest from backend
    fetchAssessment(mappedId)
      .then(a => {
        setAssessment(a)
        setPhase('quiz')
      })
      .catch(() => {
        // If local data was loaded, stay in quiz mode
        if (!local) {
          fetchAssessment(id)
            .then(a => { setAssessment(a); setPhase('quiz') })
            .catch(e => { setErrorMsg(e.message); setPhase('error') })
        }
      })
  }, [id])


  function choose(questionId: string, idx: number) {
    setAnswers(prev => ({ ...prev, [questionId]: idx }))
  }

  async function handleSubmit() {
    if (!assessment) return
    setSubmitting(true)

    // Calculate score from local questions data if available
    let correctCount = 0
    const totalCount = assessment.questions.length
    if (localData) {
      for (const q of localData.questions) {
        if (answers[q.id] === q.correct_index) {
          correctCount += 1
        }
      }
    }
    const localScore = totalCount > 0 ? correctCount / totalCount : 0
    const localPassed = localScore >= (assessment.pass_threshold || 0.6)

    try {
      const res = await submitAssessment(assessment.id, answers)
      if (id && id !== assessment.id) {
        // Also ensure the course item is marked complete in roadmap
        await markItemComplete(id).catch(() => null)
      }
      setResult(res)
      setPhase('result')
    } catch {
      // If backend submission endpoint has issues on remote, fallback gracefully
      if (id) {
        await markItemComplete(id).catch(() => null)
      }
      setResult({
        assessment_id: assessment.id,
        score: localScore,
        passed: localPassed,
        correct: correctCount,
        total: totalCount,
        adaptation_action: localPassed ? 'phase_unlocked' : 'no_change',
        adaptation_message: localPassed
          ? `Great job! You scored ${Math.round(localScore * 100)}% and completed this module!`
          : `Score: ${Math.round(localScore * 100)}%. Review the material and try again!`,
      })
      setPhase('result')
    } finally {
      setSubmitting(false)
    }
  }


  const allAnswered =
    assessment ? assessment.questions.every(q => answers[q.id] !== undefined) : false

  if (phase === 'loading') return <Spinner />

  if (phase === 'error') {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="max-w-sm text-center">
          <XCircle className="mx-auto mb-3 h-10 w-10 text-red-400" />
          <p className="text-sm text-slate-600">{errorMsg}</p>
          <button
            type="button"
            onClick={() => navigate('/roadmap')}
            className="mt-4 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white"
          >
            Back to roadmap
          </button>
        </div>
      </div>
    )
  }

  if (phase === 'result' && result) {
    const pct = Math.round(result.score * 100)
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
        <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-xl text-center">
          {result.passed
            ? <CheckCircle2 className="mx-auto mb-4 h-14 w-14 text-emerald-500" />
            : <XCircle className="mx-auto mb-4 h-14 w-14 text-amber-400" />}

          <h2 className="text-2xl font-bold text-slate-900">
            {result.passed ? 'Passed!' : 'Not quite'}
          </h2>
          <p className="mt-1 text-4xl font-extrabold text-indigo-600">{pct}%</p>
          <p className="mt-1 text-sm text-slate-500">
            {result.correct} / {result.total} correct ·{' '}
            threshold {Math.round((result.score / (result.correct / result.total || 1)) * result.score * 100)}%
          </p>

          {/* Adaptation message */}
          <div className={`mt-4 rounded-xl px-4 py-3 text-sm ${
            result.adaptation_action === 'phase_unlocked'
              ? 'bg-emerald-50 text-emerald-800'
              : result.adaptation_action === 'reinforcement_inserted'
              ? 'bg-amber-50 text-amber-800'
              : 'bg-slate-50 text-slate-600'
          }`}>
            {result.adaptation_message}
          </div>

          <div className="mt-6 flex gap-3 justify-center">
            <button
              type="button"
              onClick={() => navigate('/roadmap')}
              className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-700"
            >
              View roadmap
            </button>
            {!result.passed && (
              <button
                type="button"
                onClick={() => { setPhase('quiz'); setAnswers({}) }}
                className="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              >
                Retry
              </button>
            )}
          </div>
        </div>
      </div>
    )
  }

  if (phase === 'quiz' && assessment) {
    const answered = Object.keys(answers).length
    const total = assessment.questions.length
    const progress = answered / total

    return (
      <div className="min-h-screen bg-slate-50 px-4 py-8">
        <div className="mx-auto max-w-xl">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-xl font-bold text-slate-900">{assessment.title}</h1>
            <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-200">
              <div
                className="h-2 rounded-full bg-indigo-500 transition-all duration-300"
                style={{ width: `${progress * 100}%` }}
              />
            </div>
            <p className="mt-1 text-xs text-slate-400">
              {answered} / {total} answered
            </p>
          </div>

          {/* Questions */}
          <div className="space-y-5">
            {assessment.questions.map((q, qi) => (
              <div
                key={q.id}
                className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
              >
                <p className="mb-3 text-sm font-semibold text-slate-800">
                  {qi + 1}. {q.question}
                </p>
                <div className="space-y-2">
                  {q.options.map((opt, oi) => (
                    <button
                      key={oi}
                      type="button"
                      onClick={() => choose(q.id, oi)}
                      className={`w-full rounded-xl border-2 px-4 py-2.5 text-left text-sm transition ${
                        answers[q.id] === oi
                          ? 'border-indigo-500 bg-indigo-50 text-indigo-800 font-medium'
                          : 'border-slate-200 text-slate-700 hover:border-indigo-300'
                      }`}
                    >
                      <span className="mr-2 font-mono text-slate-400">
                        {String.fromCharCode(65 + oi)}.
                      </span>
                      {opt}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Submit */}
          <div className="mt-6 flex items-center justify-between">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="text-sm text-slate-500 hover:text-slate-700"
            >
              ← Back
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!allAnswered || submitting}
              className="rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:opacity-50"
            >
              {submitting ? 'Submitting…' : 'Submit answers'}
            </button>
          </div>
        </div>
      </div>
    )
  }

  return <Spinner />
}

function Spinner() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
    </div>
  )
}
