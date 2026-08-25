# PathWise AI

AI-Powered Personalized Learning Path Recommender for HCL AMPlified.

PathWise AI identifies skill gaps between a learner's profile and their target career role, builds prerequisite-aware learning journeys, and adapts those journeys using assessment results and feedback.

## Project structure

```
pathwise-ai/
  frontend/          React + Vite + TypeScript + Tailwind
  backend/           FastAPI + Pydantic
  data/              Seed JSON datasets (Phase 2)
  docs/              Architecture & methodology docs
  docker-compose.yml Local PostgreSQL with pgvector
```

## Prerequisites

- Node.js 20+
- Python 3.10+
- Docker Desktop (for local Postgres)

## Quick start (Phase 1)

### 1. Environment

```powershell
copy .env.example .env
```

### 2. Start PostgreSQL

```powershell
docker compose up -d
```

Verify Postgres is healthy:

```powershell
docker compose ps
```

### 3. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health check: [http://localhost:8000/api/health](http://localhost:8000/api/health)

Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Frontend

In a new terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). The footer shows API connectivity when the backend is running.

## Phase 1 verification checklist

- [ ] `docker compose ps` shows `pathwise-postgres` as healthy
- [ ] `GET http://localhost:8000/api/health` returns `{"status":"ok",...}`
- [ ] Frontend loads landing page with **Build My Path** CTA
- [ ] Footer shows green **API ok** badge when backend is running

## Build phases

This repo is built incrementally. Phase 1 is scaffold only. Reply **continue to Phase 2** in Cursor to add database schema and seed data.

| Phase | Scope |
|-------|-------|
| 1 | Scaffold (this phase) |
| 2 | Database schema + seed script |
| 3 | Auth + profile onboarding |
| 4 | Skill gap + prerequisite engine |
| 5 | Recommendation scoring |
| 6 | Roadmap generator |
| 7 | LLM profile extraction |
| 8 | Embeddings + RAG |
| 9 | Assessments + adaptive engine |
| 10 | Dashboard + tutor + explainability |
| 11 | Test personas + polish |

## Tech stack

| Layer | Choice |
|-------|--------|
| Frontend | React, Vite, TypeScript, Tailwind, Recharts, Lucide |
| Backend | FastAPI, Pydantic, SQLAlchemy, Alembic |
| Database | PostgreSQL + pgvector |
| AI | LLM API + embeddings (Phase 7+) |
