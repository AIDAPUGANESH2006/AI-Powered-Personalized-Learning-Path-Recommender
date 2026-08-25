const API_URL = import.meta.env.VITE_API_URL ?? ''

// ── helpers ──────────────────────────────────────────────────────────────────

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

// ── health ────────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string
  app: string
  version: string
}

export async function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/health')
}

// ── auth ──────────────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string
  token_type: string
}

export async function register(email: string, password: string): Promise<{ id: string; email: string }> {
  return request('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  // OAuth2 form requires application/x-www-form-urlencoded
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

// ── profile ───────────────────────────────────────────────────────────────────

export type LearningStyle = 'visual' | 'hands_on' | 'reading' | 'mixed'

export interface SkillInput {
  skill_id: string
  level: number
}

export interface ProfilePayload {
  education?: string
  experience_level?: string
  goal?: string
  timeline_months?: number
  hours_per_week?: number
  learning_style?: LearningStyle
  target_career_role_id?: string
  skills?: SkillInput[]
}

export interface ProfileOut {
  id: number
  education: string | null
  experience_level: string | null
  goal: string | null
  timeline_months: number | null
  hours_per_week: number | null
  learning_style: LearningStyle | null
  target_career_role_id: string | null
  skills: SkillInput[]
}

export async function createProfile(payload: ProfilePayload): Promise<ProfileOut> {
  return request('/api/profile', { method: 'POST', body: JSON.stringify(payload) })
}

export async function getProfile(): Promise<ProfileOut> {
  return request('/api/profile')
}

export async function updateProfile(payload: ProfilePayload): Promise<ProfileOut> {
  return request('/api/profile', { method: 'PATCH', body: JSON.stringify(payload) })
}

// ── catalog ───────────────────────────────────────────────────────────────────

export interface SkillBrief {
  id: string
  name: string
  description: string | null
  prerequisites: string[]
}

export interface CareerBrief {
  id: string
  name: string
  description: string | null
  required_skills: Record<string, number>
}

export async function fetchSkills(): Promise<SkillBrief[]> {
  return request('/api/catalog/skills')
}

export async function fetchCareers(): Promise<CareerBrief[]> {
  return request('/api/catalog/careers')
}
