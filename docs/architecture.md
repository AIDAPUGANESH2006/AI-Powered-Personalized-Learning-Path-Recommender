# PathWise AI — Architecture

> Phase 1: project scaffold only. This document will be updated as each phase lands.

## Overview

PathWise AI is a hybrid learning-path system: deterministic engines (skill gaps, prerequisites, scoring, adaptation) do the core reasoning; the LLM explains, extracts profile data, and powers scoped tutoring.

## Core loop

```
PROFILE → SKILL GAP → PREREQUISITE-AWARE RECOMMENDATION → ROADMAP
  → LEARN → ASSESS → ADAPT → EXPLAIN
```

## Components (planned)

| Component | Responsibility | LLM? |
|-----------|----------------|------|
| Profile service | Learner goals, skills, preferences | Extraction only |
| Skill gap engine | Rank gaps vs target role | No |
| Prerequisite resolver | Ordered missing skill chain | No |
| Recommender | Weighted course/project scoring | No |
| Roadmap generator | Phased timeline + pacing modes | No |
| Adaptive engine | Reinforce / unlock on assessment | No |
| RAG + explanation | Retrieve + cite profile numbers | Yes |
| AI tutor | Scoped chat grounded in profile | Yes |

## Phase 1 deliverables

- Monorepo layout (`frontend/`, `backend/`, `data/`, `docs/`)
- Docker Compose Postgres (pgvector image)
- FastAPI health endpoint: `GET /api/health`
- React landing page with API connectivity indicator
