# PathWise AI

## AI-Powered Personalized Learning Path Recommender

PathWise AI is an AI-powered personalized learning platform developed for the **HCL AMPlified** problem statement.

The system identifies the gap between a learner's current skills and their target career role, recommends relevant learning resources, generates a prerequisite-aware learning roadmap, evaluates the learner through assessments, and adapts the learning journey based on assessment results and feedback.

---

## 🚀 Live Demo

### Frontend

https://pathwise-ai-frontend.onrender.com

### Backend API

https://pathwise-ai-backend-knn1.onrender.com

### Interactive API Documentation

https://pathwise-ai-backend-knn1.onrender.com/docs

> The frontend is deployed on Render and communicates with the FastAPI backend.

---

# 🎯 Problem Statement

Learners often struggle to determine:

- What skills they currently have
- Which skills they are missing
- What they should learn first
- Which courses are relevant to their career goal
- Whether they have achieved sufficient proficiency
- How their learning path should change based on their performance

Traditional learning platforms often provide generic course lists without considering the learner's current skill level, target role, prerequisites, or assessment performance.

### PathWise AI addresses this problem by providing a personalized and adaptive learning journey.

---

# 💡 Solution

PathWise AI creates an individualized learning path using information such as:

- Learner profile
- Current skills
- Target career role
- Skill proficiency
- Skill gaps
- Learning prerequisites
- Assessment performance
- Learner feedback
- Learning progress

The system uses these inputs to recommend learning activities and organize them into a structured roadmap.

---

# ✨ Key Features

## 1. User Registration & Authentication

Users can create an account and securely log in to the application.

Authentication is implemented using:

- JWT tokens
- Password hashing with bcrypt
- FastAPI authentication/dependency mechanisms

---

## 2. Learner Onboarding

The onboarding flow collects information about the learner and their learning goals.

The learner can provide information such as:

- Background
- Current skills
- Experience
- Target career role
- Learning preferences

This information is used to personalize the learning journey.

---

## 3. Skill Gap Analysis

The system compares the learner's current capabilities with the skills required for their target role.

The skill-gap module identifies:

- Existing skills
- Missing skills
- Areas requiring improvement
- Relative proficiency

This allows the platform to focus learning recommendations on the learner's actual needs.

---

## 4. Personalized Recommendations

PathWise AI recommends learning resources based on the learner's skill gaps and target role.

Recommendations consider the learner's current state instead of simply displaying a generic course catalog.

---

## 5. Prerequisite-Aware Learning Roadmap

The platform generates a structured learning roadmap.

Learning items can have prerequisites.

For example:

```text
HTML & CSS
     ↓
JavaScript
     ↓
React
     ↓
Advanced React

This prevents learners from being directed toward advanced topics before completing important prerequisite concepts.

6. Course Progress Tracking

Course items can be completed using the:

Mark done

action.

The system tracks the learner's progress and uses completion information to determine the next available learning activities.

7. Interactive Assessments

The application includes interactive multiple-choice assessments.

Assessment areas include:

SQL
Python
React
Machine Learning
Statistics

Assessments provide:

Questions
Answer selection
Scoring
Results
Learning feedback

Example assessment routes:

/assessment/assessment-sql
/assessment/assessment-python
/assessment/assessment-react
/assessment/assessment-ml
/assessment/assessment-statistics
8. Adaptive Learning

Assessment results can influence the learner's learning journey.

If a learner performs poorly in a particular skill, the system can identify that area as requiring additional learning.

If the learner demonstrates strong proficiency, the roadmap can progress toward more advanced material.

This creates an adaptive rather than static learning path.

9. AI Tutor

PathWise AI includes an AI-powered tutor.

The tutor can assist learners by providing explanations and learning support related to their learning journey.

The AI functionality is integrated with the Gemini API.

10. Feedback-Based Learning

Learner feedback can be used as an additional signal for improving recommendations and adapting the learning experience.

This allows the system to consider more than just assessment scores.

11. Personalized Dashboard

The dashboard provides a centralized view of the learner's learning journey.

It can present information such as:

Learning progress
Recommended activities
Skill information
Roadmap status
Assessment information
12. Explainable Recommendations

The application includes explanation functionality to help learners understand why particular learning recommendations are relevant to their current learning goals.

🏗️ System Architecture

The project follows a frontend-backend architecture.

                    ┌──────────────────────┐
                    │      Learner         │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   React Frontend     │
                    │ TypeScript + Vite    │
                    │ Tailwind CSS          │
                    └──────────┬───────────┘
                               │
                         HTTP / API
                               │
                               ▼
                    ┌──────────────────────┐
                    │    FastAPI Backend   │
                    │      Python          │
                    └──────────┬───────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │ AI Modules   │  │ PostgreSQL   │  │ Authentication│
     │ Gemini API   │  │ + pgvector   │  │ JWT + bcrypt │
     └──────────────┘  └──────────────┘  └──────────────┘
             │                 │
             └─────────────────┘
📁 Project Structure
AI-Powered-Personalized-Learning-Path-Recommender/
│
├── backend/
│   │
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
│   │   │
│   │   ├── api/
│   │   │   ├── assessment.py
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── feedback.py
│   │   │   ├── recommendations.py
│   │   │   └── roadmap.py
│   │   │
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── scripts/
│   ├── requirements.txt
│   ├── run.py
│   └── runtime.txt
│
├── frontend/
│   │
│   ├── src/
│   │   ├── components/
│   │   │   └── FeedbackControl.tsx
│   │   │
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
│   │   │
│   │   └── ...
│   │
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
🛠️ Technology Stack
Layer	Technology
Frontend	React
Programming Language	TypeScript
Build Tool	Vite
Styling	Tailwind CSS
Backend	FastAPI
Backend Language	Python
Validation	Pydantic
ORM	SQLAlchemy
Database	PostgreSQL
Vector Database	pgvector
Database Hosting	Neon
Authentication	JWT
Password Security	bcrypt
AI	Google Gemini API
HTTP Client	HTTPX
Frontend Deployment	Render
Backend Deployment	Render
🔄 Application Workflow

The overall learning flow is:

User Registration
        ↓
Login
        ↓
Learner Onboarding
        ↓
Career Goal Selection
        ↓
Skill Assessment
        ↓
Skill Gap Analysis
        ↓
Personalized Recommendations
        ↓
Learning Roadmap
        ↓
Courses
        ↓
Assessments
        ↓
Assessment Results
        ↓
Adaptive Learning
        ↓
AI Tutor / Feedback
        ↓
Updated Learning Journey
📋 Roadmap Progression

The roadmap is designed around learning dependencies.

Learning activities can be categorized as:

Course

Courses are learning modules.

They can be completed using:

Mark done
Assessment

Assessments provide interactive quizzes.

They can be accessed using:

Take quiz

The learner progresses through the roadmap as prerequisite learning activities are completed.

🧪 Assessment System

The application contains assessment functionality for different technical skills.

Available assessment examples:

SQL Proficiency Quiz
Python Fundamentals Quiz
React Quiz
Machine Learning Quiz
Statistics Quiz

The frontend assessment routes are:

https://pathwise-ai-frontend.onrender.com/assessment/assessment-sql

https://pathwise-ai-frontend.onrender.com/assessment/assessment-python

https://pathwise-ai-frontend.onrender.com/assessment/assessment-react

https://pathwise-ai-frontend.onrender.com/assessment/assessment-ml

https://pathwise-ai-frontend.onrender.com/assessment/assessment-statistics
🤖 AI Components

The backend contains dedicated AI modules for different parts of the learning system.

backend/app/ai/

Important components include:

Module	Purpose
gemini_client.py	Communication with Gemini API
profile_extractor.py	Learner profile processing
skill_gap.py	Skill gap analysis
recommender.py	Learning recommendations
roadmap_generator.py	Learning roadmap generation
adaptive_engine.py	Adaptive learning logic
tutor.py	AI tutor functionality
explanation.py	Recommendation explanations
🗄️ Database

PathWise AI uses:

PostgreSQL + pgvector

The deployed application uses a PostgreSQL database hosted through Neon.

The database connection is configured through environment variables.

🔐 Environment Variables

Create a local .env file using .env.example.

Example:

DATABASE_URL=your_database_url
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key

Use the exact environment variable names expected by the application.

Important

Never commit the actual .env file containing secrets.

The repository should only contain:

.env.example

with placeholder values.

💻 Local Development
Prerequisites

Install the following:

Git
Node.js 20+
Python 3.12+
PostgreSQL or Neon PostgreSQL
A Gemini API key

Docker is optional if PostgreSQL is being run locally through Docker.

1. Clone the Repository
git clone https://github.com/AIDAPUGANESH2006/AI-Powered-Personalized-Learning-Path-Recommender.git

Enter the project:

cd AI-Powered-Personalized-Learning-Path-Recommender
2. Configure Environment

Create .env from .env.example.

Windows
copy .env.example .env

Then open .env and configure the required values.

3. Backend Setup

Open a terminal and enter:

cd backend

Create a Python virtual environment:

python -m venv .venv

Activate it:

.\.venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

Start the backend:

python run.py

Alternatively:

uvicorn app.main:app --reload --port 8000
4. Backend Verification

Once the backend is running, check:

http://localhost:8000/api/health

The API documentation is available at:

http://localhost:8000/docs

The /docs page provides an interactive Swagger API interface.

5. Frontend Setup

Open another terminal.

From the project root:

cd frontend

Install dependencies:

npm install

Start the development server:

npm run dev

Open the URL displayed by Vite.

Usually:

http://localhost:5173
6. Frontend Production Build

To verify that the frontend can be built for production:

npm run build

The generated production files will be created in the dist directory.

🐳 Optional Local PostgreSQL Using Docker

If you prefer to run PostgreSQL locally and the project Docker configuration is available:

docker compose up -d

Check the containers:

docker compose ps

Stop the containers:

docker compose down
🌐 Deployment

The application is deployed using Render.

Frontend
https://pathwise-ai-frontend.onrender.com
Backend
https://pathwise-ai-backend-knn1.onrender.com
API Documentation
https://pathwise-ai-backend-knn1.onrender.com/docs
🚀 Deployment Configuration
Backend

The backend uses:

Python 3.12
FastAPI
Uvicorn

The production server command is:

uvicorn app.main:app --host 0.0.0.0 --port $PORT

The backend dependencies are defined in:

backend/requirements.txt

Python runtime configuration:

backend/runtime.txt
Frontend

The frontend uses:

React
Vite
TypeScript
Tailwind CSS

Install dependencies:

npm install

Build:

npm run build

The production build is generated in:

dist/
🔗 API Communication

During local development, the frontend communicates with the backend using the Vite configuration.

The API proxy is configured for:

/api

The deployed frontend communicates with the deployed backend.

Backend:

https://pathwise-ai-backend-knn1.onrender.com
🧪 Testing Checklist

After starting the application, verify the following:

Authentication
 Registration works
 Login works
 Invalid credentials are handled correctly
Onboarding
 User can complete onboarding
 Career goal can be selected
 User profile is saved
Learning Path
 Skill-gap information is displayed
 Recommendations are generated
 Roadmap is displayed
 Course completion works
 Prerequisite progression works
Assessments
 Assessment page opens
 Questions are displayed
 Answers can be selected
 Score is calculated
 Results are displayed
AI
 AI-powered features work when Gemini API is configured
 AI Tutor is accessible
 AI explanations/recommendations work
Dashboard
 Progress is displayed
 Learning activities are visible
 User information is displayed
📌 Important Notes
Environment Variables

The project requires environment configuration for services such as the database and Gemini API.

Do not commit real API keys, passwords, or secret values.

Database

Database-dependent functionality requires a valid PostgreSQL database connection.

For local execution, configure:

DATABASE_URL=your_database_url
Gemini API

AI functionality requires a valid Gemini API key.

Configure:

GEMINI_API_KEY=your_gemini_api_key
🔒 Files That Should Not Be Committed

The following should normally remain outside the submitted source package:

.env
.venv/
node_modules/
frontend/dist/
__pycache__/
.git/

The .env.example file should be included so that another developer can understand the required configuration.

📦 Submission Package

The source-code submission should contain:

backend/
frontend/
data/
docs/
.env.example
README.md
docker-compose.yml
start-dev.bat

It should not contain:

.env
.venv/
node_modules/
dist/
.git/
👨‍💻 Project Development

PathWise AI was developed as an HCL AMPlified project to demonstrate an AI-driven approach to personalized learning.

The project combines:

Full-stack web development
REST API development
Authentication
Relational database management
Vector database capabilities
AI integration
Skill-gap analysis
Recommendation systems
Adaptive learning
Interactive assessments
Learning roadmap generation
🎓 Expected User Journey

A typical learner journey is:

1. Open PathWise AI
        ↓
2. Register
        ↓
3. Login
        ↓
4. Complete onboarding
        ↓
5. Define career goal
        ↓
6. Analyze current skills
        ↓
7. Identify skill gaps
        ↓
8. Receive recommendations
        ↓
9. Follow personalized roadmap
        ↓
10. Complete learning modules
        ↓
11. Take assessments
        ↓
12. Review results
        ↓
13. Adapt learning path
        ↓
14. Use AI Tutor
        ↓
15. Track progress
🏆 Project Objective

The primary objective of PathWise AI is to provide learners with a structured, personalized, and adaptive learning experience.

Rather than providing the same learning content to every learner, the platform attempts to determine:

What does the learner know?
            ↓
What does the learner want to become?
            ↓
What skills are missing?
            ↓
What should the learner learn first?
            ↓
What should the learner learn next?
            ↓
How is the learner performing?
            ↓
How should the learning path adapt?

This approach creates a more personalized learning journey based on the learner's goals, skills, progress, and assessment performance.

📞 Project Links
Resource	Link
GitHub Repository	https://github.com/AIDAPUGANESH2006/AI-Powered-Personalized-Learning-Path-Recommender
Live Frontend	https://pathwise-ai-frontend.onrender.com
Backend API	https://pathwise-ai-backend-knn1.onrender.com
API Documentation	https://pathwise-ai-backend-knn1.onrender.com/docs
