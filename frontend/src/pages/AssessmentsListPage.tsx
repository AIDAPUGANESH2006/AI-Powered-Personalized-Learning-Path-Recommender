import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Award, CheckCircle2, ClipboardList, Clock,
  HelpCircle, Sparkles, TrendingUp, Zap
} from 'lucide-react'
import { fetchAssessments, type AssessmentSummary } from '../services/api'

export default function AssessmentsListPage() {
  const navigate = useNavigate()
  const [assessments, setAssessments] = useState<AssessmentSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchAssessments()
      .then(setAssessments)
      .catch(e => setError((e as Error).message))
      .finally(() => setLoading(false))
  }, [])

  const passedCount = assessments.filter(a => a.passed).length

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="mx-auto max-w-4xl">
        {/* Header */}
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <ClipboardList className="h-7 w-7 text-indigo-600" />
              <h1 className="text-2xl font-bold text-slate-900">Skill Assessments</h1>
            </div>
            <p className="mt-1 text-sm text-slate-500">
              Test your knowledge, validate skill milestones, and trigger adaptive roadmap recommendations.
            </p>
          </div>

          {assessments.length > 0 && (
            <div className="flex items-center gap-3 rounded-2xl bg-white px-5 py-3 shadow-sm border border-slate-200">
              <Award className="h-5 w-5 text-indigo-600" />
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Passed Quizzes</p>
                <p className="text-lg font-bold text-slate-900">{passedCount} / {assessments.length}</p>
              </div>
            </div>
          )}
        </div>

        {error && (
          <div className="mb-6 rounded-xl bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex min-h-[300px] items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
          </div>
        ) : assessments.length === 0 ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center">
            <HelpCircle className="mx-auto mb-3 h-10 w-10 text-slate-400" />
            <p className="text-slate-600 font-medium">No assessments found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {assessments.map(item => {
              const passPct = Math.round(item.pass_threshold * 100)
              const scorePct = item.latest_score !== null ? Math.round(item.latest_score * 100) : null

              return (
                <div
                  key={item.id}
                  className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-6 shadow-sm hover:shadow-md transition"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <span className="inline-flex items-center gap-1.5 rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
                        <Sparkles className="h-3 w-3" />
                        {item.skill_name}
                      </span>

                      {item.passed ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Passed ({scorePct}%)
                        </span>
                      ) : item.latest_score !== null ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700">
                          Score: {scorePct}%
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
                          Not started
                        </span>
                      )}
                    </div>

                    <h2 className="text-lg font-bold text-slate-900 mb-2">
                      {item.title}
                    </h2>

                    <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 mb-4">
                      <span className="flex items-center gap-1">
                        <HelpCircle className="h-3.5 w-3.5 text-slate-400" />
                        {item.question_count} questions
                      </span>
                      <span className="flex items-center gap-1">
                        <TrendingUp className="h-3.5 w-3.5 text-slate-400" />
                        Pass: {passPct}%
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5 text-slate-400" />
                        ~10 mins
                      </span>
                    </div>
                  </div>

                  <div className="border-t border-slate-100 pt-4 flex items-center justify-between">
                    <span className="text-xs text-slate-400">
                      Adaptive feedback enabled
                    </span>
                    <button
                      type="button"
                      onClick={() => navigate(`/assessment/${item.id}`)}
                      className={`inline-flex items-center gap-1.5 rounded-lg px-4 py-2 text-xs font-semibold shadow-sm transition ${
                        item.passed
                          ? 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                          : 'bg-indigo-600 text-white hover:bg-indigo-700'
                      }`}
                    >
                      <Zap className="h-3.5 w-3.5" />
                      {item.passed ? 'Retake Quiz' : 'Take Quiz'}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
