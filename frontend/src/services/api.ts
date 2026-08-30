const API_URL = import.meta.env.VITE_API_URL ?? ''

// ── helpers ────────────────────────────────────────────────────────────────

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('pathwise_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    ...init,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error((body as { detail?: string }).detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

// ── health ─────────────────────────────────────────────────────────────────

export interface HealthResponse { status: string; app: string; version: string }
export const fetchHealth = () => request<HealthResponse>('/api/health')

// ── auth ───────────────────────────────────────────────────────────────────

export interface TokenResponse { access_token: string; token_type: string }
export const register = (email: string, password: string) =>
  request<{ id: string; email: string }>('/api/auth/register', {
    method: 'POST', body: JSON.stringify({ email, password }),
  })

export async function login(email: string, password: string): Promise<TokenResponse> {
  const res = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ username: email, password }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error((body as { detail?: string }).detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

// ── profile ────────────────────────────────────────────────────────────────

export type LearningStyle = 'visual' | 'hands_on' | 'reading' | 'mixed'

export interface SkillInput { skill_id: string; level: number }

export interface ProfilePayload {
  education?: string; experience_level?: string; goal?: string
  timeline_months?: number; hours_per_week?: number
  learning_style?: LearningStyle; target_career_role_id?: string
  skills?: SkillInput[]
}

export interface ProfileOut {
  id: number; education: string | null; experience_level: string | null
  goal: string | null; timeline_months: number | null
  hours_per_week: number | null; learning_style: LearningStyle | null
  target_career_role_id: string | null; skills: SkillInput[]
}

export const createProfile = (p: ProfilePayload) =>
  request<ProfileOut>('/api/profile', { method: 'POST', body: JSON.stringify(p) })
export const getProfile = () => request<ProfileOut>('/api/profile')
export const updateProfile = (p: ProfilePayload) =>
  request<ProfileOut>('/api/profile', { method: 'PATCH', body: JSON.stringify(p) })

// ── catalog ────────────────────────────────────────────────────────────────

export interface SkillBrief { id: string; name: string; description: string | null; prerequisites: string[] }
export interface CareerBrief { id: string; name: string; description: string | null; required_skills: Record<string, number> }

export const fetchSkills  = () => request<SkillBrief[]>('/api/catalog/skills')
export const fetchCareers = () => request<CareerBrief[]>('/api/catalog/careers')

// ── skill gap ──────────────────────────────────────────────────────────────

export interface SkillGapItem {
  skill_id: string; skill_name: string; current_level: number
  required_level: number; gap_size: number; priority: 'HIGH' | 'MEDIUM' | 'LOW'
}

export interface SkillGapResponse {
  career_readiness_pct: number
  gaps: SkillGapItem[]
  biggest_opportunity: string | null
}

export const fetchSkillGap = (roleId: string) =>
  request<SkillGapResponse>(`/api/recommendations/skill-gap?role_id=${roleId}`)

// ── recommendations ────────────────────────────────────────────────────────

export interface ScoreBreakdown {
  skill_gap_match: number; goal_relevance: number; prerequisite_fit: number
  difficulty_fit: number; learning_pref_fit: number; time_fit: number
  user_feedback_adjustment: number; total: number
}

export interface RecommendationItem {
  rank: number; id: string; item_type: string; title: string
  total_score: number; breakdown: ScoreBreakdown; explanation: string | null
}

export const fetchRecommendations = (roleId: string, withExplanations = true, topN = 10) =>
  request<RecommendationItem[]>(
    `/api/recommendations/generate?role_id=${roleId}&with_explanations=${withExplanations}&top_n=${topN}`
  )

export const analyzeProfileText = (text: string) =>
  request<{ education: string | null; experience_level: string | null; skills: SkillInput[]; goal: string | null; timeline_months: number | null; target_career_role: string | null }>(
    '/api/recommendations/profile/analyze', { method: 'POST', body: JSON.stringify({ text }) }
  )

// ── roadmap ────────────────────────────────────────────────────────────────

export interface RoadmapItem {
  order_index: number; item_type: string; item_id: string; title: string
  status: 'locked' | 'active' | 'complete'; week_start: number; week_end: number
  phase_label: string; skills: string[]; score: number; duration_hours: number | null
}

export interface RoadmapOut {
  id: number; version: number; pacing_mode: string
  target_career_role_id: string; total_weeks: number
  items: RoadmapItem[]; narrative: string | null
}

export const generateRoadmap = (roleId: string, pacingMode = 'balanced') =>
  request<RoadmapOut>('/api/roadmap', {
    method: 'POST',
    body: JSON.stringify({ role_id: roleId, pacing_mode: pacingMode }),
  })

export const getRoadmap = () => request<RoadmapOut>('/api/roadmap')

export const adjustPacing = (pacingMode: string) =>
  request<RoadmapOut>('/api/roadmap/pacing', {
    method: 'PATCH', body: JSON.stringify({ pacing_mode: pacingMode }),
  })

export const markItemComplete = (itemId: string) =>
  request<RoadmapOut>(`/api/roadmap/item/${itemId}/complete`, { method: 'POST' })

// ── assessment ─────────────────────────────────────────────────────────────

export interface AssessmentQuestion { id: string; question: string; options: string[] }

export interface AssessmentSummary {
  id: string
  title: string
  skill_id: string
  skill_name: string
  pass_threshold: number
  question_count: number
  latest_score: number | null
  passed: boolean
}

export interface AssessmentOut {
  id: string; title: string; skill_id: string
  pass_threshold: number; questions: AssessmentQuestion[]
}

export interface AssessmentSubmitResult {
  assessment_id: string; score: number; passed: boolean
  correct: number; total: number
  adaptation_action: string; adaptation_message: string
}

export const fetchAssessments = () => request<AssessmentSummary[]>('/api/assessment')

export const fetchAssessment = (id: string) => request<AssessmentOut>(`/api/assessment/${id}`)

export const submitAssessment = (assessmentId: string, answers: Record<string, number>) =>
  request<AssessmentSubmitResult>('/api/assessment/submit', {
    method: 'POST', body: JSON.stringify({ assessment_id: assessmentId, answers }),
  })


// ── feedback ───────────────────────────────────────────────────────────────

export const submitFeedback = (
  itemId: string, itemType: string, rating: 1 | -1, reason?: string
) =>
  request('/api/feedback', {
    method: 'POST',
    body: JSON.stringify({ item_id: itemId, item_type: itemType, rating, reason }),
  })

// ── chat ───────────────────────────────────────────────────────────────────

export interface ChatMsg { role: 'user' | 'assistant'; content: string }

export const sendChatMessage = (message: string, history: ChatMsg[]) =>
  request<{ reply: string }>('/api/chat', {
    method: 'POST', body: JSON.stringify({ message, history }),
  })
