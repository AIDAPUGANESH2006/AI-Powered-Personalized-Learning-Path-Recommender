import { ArrowRight, BrainCircuit, Route, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-indigo-50">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-2 text-indigo-700">
          <Route className="h-7 w-7" />
          <span className="text-xl font-bold tracking-tight">PathWise AI</span>
        </div>
        <span className="rounded-full bg-indigo-100 px-3 py-1 text-xs font-medium text-indigo-700">
          HCL AMPlified
        </span>
      </header>

      <main className="mx-auto max-w-6xl px-6 pb-20 pt-10">
        <section className="grid items-center gap-12 lg:grid-cols-2">
          <div>
            <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-white px-3 py-1 text-sm text-indigo-700 shadow-sm">
              <Sparkles className="h-4 w-4" />
              Explainable · Adaptive · Prerequisite-aware
            </p>
            <h1 className="text-4xl font-bold leading-tight tracking-tight text-slate-900 sm:text-5xl">
              Your personalized path from skills to career
            </h1>
            <p className="mt-5 max-w-xl text-lg text-slate-600">
              PathWise AI identifies skill gaps, builds prerequisite-aware
              learning journeys, and adapts your roadmap using assessments and
              feedback — not generic chatbot guesses.
            </p>
            <Link
              to="/register"
              className="mt-8 inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-3 text-base font-semibold text-white shadow-lg shadow-indigo-200 transition hover:bg-indigo-700"
            >
              Build My Path
              <ArrowRight className="h-5 w-5" />
            </Link>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xl shadow-slate-200/50">
            <div className="mb-4 flex items-center gap-2 text-slate-700">
              <BrainCircuit className="h-5 w-5 text-indigo-600" />
              <h2 className="font-semibold">Core learning loop</h2>
            </div>
            <ol className="space-y-3 text-sm text-slate-600">
              <li className="rounded-lg bg-slate-50 px-3 py-2">
                Profile → Skill gap analysis
              </li>
              <li className="rounded-lg bg-slate-50 px-3 py-2">
                Prerequisite-aware recommendations
              </li>
              <li className="rounded-lg bg-slate-50 px-3 py-2">
                Roadmap → Learn → Assess → Adapt → Explain
              </li>
            </ol>
          </div>
        </section>
      </main>
    </div>
  )
}
