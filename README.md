# PathWise AI 🎯

**AI-Powered Personalized Learning Path Recommender**

PathWise AI identifies the gap between a learner's current skills and their target career role, recommends relevant learning resources, generates a prerequisite-aware roadmap, evaluates learners through assessments, and adapts the journey based on results and feedback.

Built for the **HCL AMPlified** problem statement.

[![Frontend](https://img.shields.io/badge/frontend-live-brightgreen)](https://pathwise-ai-frontend.onrender.com)
[![Backend](https://img.shields.io/badge/backend-live-brightgreen)](https://pathwise-ai-backend-knn1.onrender.com)
[![API Docs](https://img.shields.io/badge/API-docs-blue)](https://pathwise-ai-backend-knn1.onrender.com/docs)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](#license)

---

## 🔗 Quick Links

| Resource | Link |
|---|---|
| Live App | https://pathwise-ai-frontend.onrender.com |
| Backend API | https://pathwise-ai-backend-knn1.onrender.com |
| API Documentation (Swagger) | https://pathwise-ai-backend-knn1.onrender.com/docs |
| Repository | https://github.com/AIDAPUGANESH2006/AI-Powered-Personalized-Learning-Path-Recommender |

---

## 📑 Table of Contents

- [Problem Statement](#-problem-statement)
- [Solution](#-solution)
- [Key Features](#-key-features)
- [System Architecture](#️-system-architecture)
- [Tech Stack](#️-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [AI Components](#-ai-components)
- [Testing Checklist](#-testing-checklist)
- [Deployment](#-deployment)
- [Submission Package](#-submission-package)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Problem Statement

Learners often struggle to determine what skills they have, what they're missing, what to learn first, which courses actually matter for their goal, and whether they're making real progress. Traditional platforms respond with generic course lists that ignore skill level, prerequisites, and performance.

**PathWise AI replaces the generic course list with a personalized, adaptive learning journey.**

## 💡 Solution

PathWise AI builds an individualized path using the learner's profile, current skills, target role, skill gaps, prerequisites, assessment performance, and feedback — then organizes everything into a structured, evolving roadmap.

---

## ✨ Key Features

| # | Feature | Description |
|---|---|---|
| 1 | **Authentication** | JWT-based auth with bcrypt password hashing via FastAPI dependencies |
| 2 | **Learner Onboarding** | Captures background, current skills, experience, target role, and preferences |
| 3 | **Skill Gap Analysis** | Compares current skills vs. target-role requirements to surface gaps and proficiency |
| 4 | **Personalized Recommendations** | Resource suggestions driven by the learner's actual gaps, not a static catalog |
| 5 | **Prerequisite-Aware Roadmap** | Structured path where advanced topics unlock only after prerequisites (e.g. `HTML & CSS → JavaScript → React → Advanced React`) |
| 6 | **Progress Tracking** | Course items tracked via a "Mark done" action, driving what unlocks next |
| 7 | **Interactive Assessments** | MCQ quizzes for SQL, Python, React, ML, and Statistics with scoring and feedback |
| 8 | **Adaptive Learning** | Roadmap shifts based on assessment performance — reinforcement on weak areas, acceleration on strong ones |
| 9 | **AI Tutor** | Gemini-powered assistant for explanations and learning support |
| 10 | **Feedback-Based Learning** | Learner feedback feeds back into recommendations, alongside scores |
| 11 | **Personalized Dashboard** | Central view of progress, recommendations, skills, roadmap, and assessments |
| 12 | **Explainable Recommendations** | Surfaces *why* a recommendation was made, not just what it is |

---

## 🏗️ System Architecture

```
                    ┌──────────────────────┐
                    │       Learner        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   React Frontend     │
                    │ TypeScript + Vite    │
                    │   Tailwind CSS       │
                    └──────────┬───────────┘
                               │
                          HTTP / API
                               │
                               ▼
                    ┌──────────────────────┐
                    │   FastAPI Backend    │
                    │       Python         │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                 │
              ▼                ▼                 ▼
      ┌──────────────┐ ┌──────────────┐ ┌────────────────┐
      │  AI Modules  │ │  PostgreSQL  │ │ Authentication  │
      │  Gemini API  │ │  + pgvector  │ │  JWT + bcrypt   │
      └──────────────┘ └──────────────┘ └────────────────┘
```

**Flow:** Register → Login → Onboarding → Career Goal → Skill Assessment → Skill Gap Analysis → Recommendations → Roadmap → Courses & Assessments → Adaptive Updates → AI Tutor / Feedback

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Backend | FastAPI (Python), Pydantic, SQLAlchemy |
| Database | PostgreSQL + pgvector (hosted on Neon) |
| Auth | JWT, bcrypt |
| AI | Google Gemini API |
| HTTP Client | HTTPX |
| Deployment | Render (frontend + backend) |

---

## 📁 Project Structure

```
AI-Powered-Personalized-Learning-Path-Recommender/
│
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   ├── adaptive_engine.py
│   │   │   ├── explanation.py
│   │   │   ├── gemini_client.py
│   │   │   ├── profile_extractor.py
│   │   │   ├── recommender.py
│   │   │   ├── roadmap_generator.py
│   │   │   ├── skill_gap.py
│   │   │   └── tutor.py
│   │   ├── api/
│   │   │   ├── assessment.py
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── feedback.py
│   │   │   ├── recommendations.py
│   │   │   └── roadmap.py
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── scripts/
│   ├── requirements.txt
│   ├── run.py
│   └── runtime.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── FeedbackControl.tsx
│   │   ├── pages/
│   │   │   ├── AssessmentPage.tsx
│   │   │   ├── CoursesPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── LandingPage.tsx
│   │   │   ├── LoginPage.tsx
│   │   │   ├── OnboardingPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   ├── RoadmapPage.tsx
│   │   │   ├── SkillGapPage.tsx
│   │   │   └── TutorPage.tsx
│   │   └── ...
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.ts
│
├── data/
├── docs/
├── docker-compose.yml
├── .env.example
├── start-dev.bat
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Git
- Node.js 20+
- Python 3.12+
- PostgreSQL (or a Neon PostgreSQL instance)
- A Gemini API key
- Docker *(optional — only if running PostgreSQL locally via container)*

### 1. Clone the repository

```bash
git clone https://github.com/AIDAPUGANESH2006/AI-Powered-Personalized-Learning-Path-Recommender.git
cd AI-Powered-Personalized-Learning-Path-Recommender
```

### 2. Configure environment variables

```bash
copy .env.example .env      # Windows
# cp .env.example .env      # macOS/Linux
```

Then fill in the values — see [Environment Variables](#-environment-variables).

### 3. Backend setup

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Windows PowerShell
pip install -r requirements.txt
python run.py
# or: uvicorn app.main:app --reload --port 8000
```

Verify it's running:
- Health check: `http://localhost:8000/api/health`
- Swagger docs: `http://localhost:8000/docs`

### 4. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (typically `http://localhost:5173`).

To verify a production build:

```bash
npm run build   # outputs to frontend/dist
```

### 5. (Optional) Local PostgreSQL via Docker

```bash
docker compose up -d      # start
docker compose ps         # check status
docker compose down       # stop
```

---

## 🔐 Environment Variables

Copy `.env.example` to `.env` and set:

```
DATABASE_URL=your_database_url
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key
```

> ⚠️ **Never commit your actual `.env` file.** Only `.env.example` (with placeholder values) should be tracked in version control.

---

## 🤖 AI Components

Located in `backend/app/ai/`:

| Module | Purpose |
|---|---|
| `gemini_client.py` | Communication with the Gemini API |
| `profile_extractor.py` | Learner profile processing |
| `skill_gap.py` | Skill gap analysis |
| `recommender.py` | Learning recommendations |
| `roadmap_generator.py` | Roadmap generation |
| `adaptive_engine.py` | Adaptive learning logic |
| `tutor.py` | AI tutor functionality |
| `explanation.py` | Recommendation explanations |

---

## 🧪 Testing Checklist

<details>
<summary>Click to expand manual QA checklist</summary>

**Authentication**
- [ ] Registration works
- [ ] Login works
- [ ] Invalid credentials handled correctly

**Onboarding**
- [ ] User can complete onboarding
- [ ] Career goal can be selected
- [ ] Profile is saved

**Learning Path**
- [ ] Skill-gap info displays correctly
- [ ] Recommendations generate
- [ ] Roadmap displays
- [ ] Course completion works
- [ ] Prerequisite progression works

**Assessments**
- [ ] Assessment page opens
- [ ] Questions display
- [ ] Answers can be selected
- [ ] Score calculates correctly
- [ ] Results display

**AI**
- [ ] AI features work when Gemini API key is configured
- [ ] AI Tutor is accessible
- [ ] AI explanations/recommendations work

**Dashboard**
- [ ] Progress displays
- [ ] Learning activities are visible
- [ ] User info displays

</details>

---

## 🌐 Deployment

Deployed on **Render**:

- **Frontend** — https://pathwise-ai-frontend.onrender.com (React + Vite + TypeScript + Tailwind, built via `npm run build`, served from `dist/`)
- **Backend** — https://pathwise-ai-backend-knn1.onrender.com (Python 3.12 + FastAPI, served via `uvicorn app.main:app --host 0.0.0.0 --port $PORT`)

During local dev, the frontend proxies `/api` requests to the backend via the Vite config. In production, the deployed frontend talks directly to the deployed backend.

---

## 📦 Submission Package

**Include:**
```
backend/  frontend/  data/  docs/  .env.example  README.md  docker-compose.yml  start-dev.bat
```

**Exclude:**
```
.env  .venv/  node_modules/  dist/  .git/  __pycache__/
```

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Push to the branch and open a Pull Request


---

## 👨‍💻 About

PathWise AI was developed as an **HCL AMPlified** project, combining full-stack web development, REST API design, authentication, relational + vector database management, AI integration, skill-gap analysis, recommendation systems, adaptive learning, and interactive assessments into one platform.
