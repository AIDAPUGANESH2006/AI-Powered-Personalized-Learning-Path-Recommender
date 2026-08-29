"""Recommendation + skill-gap + profile-analysis endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.explanation import explain_recommendation
from app.ai.profile_extractor import extract_profile
from app.api.deps import get_current_user
from app.database import get_db
from app.models import User
from app.services.recommender_service import get_recommendations, get_skill_gaps

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


# ── schemas ───────────────────────────────────────────────────────────────────

class ScoreBreakdownOut(BaseModel):
    skill_gap_match: float
    goal_relevance: float
    prerequisite_fit: float
    difficulty_fit: float
    learning_pref_fit: float
    time_fit: float
    user_feedback_adjustment: float
    total: float


class RecommendationOut(BaseModel):
    rank: int
    id: str
    item_type: str
    title: str
    total_score: float
    breakdown: ScoreBreakdownOut
    explanation: str | None = None


class SkillGapOut(BaseModel):
    skill_id: str
    skill_name: str
    current_level: float
    required_level: float
    gap_size: float
    priority: str


class SkillGapResponse(BaseModel):
    career_readiness_pct: float
    gaps: list[SkillGapOut]
    biggest_opportunity: str | None


class ProfileAnalyzeRequest(BaseModel):
    text: str


class ProfileAnalyzeResponse(BaseModel):
    education: str | None
    experience_level: str | None
    skills: list[dict]
    goal: str | None
    timeline_months: int | None
    target_career_role: str | None


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.get("/skill-gap", response_model=SkillGapResponse)
def skill_gap(
    role_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SkillGapResponse:
    gaps, readiness = get_skill_gaps(db, current_user.id, role_id)
    if not gaps and not readiness:
        raise HTTPException(status_code=404, detail=f"Career role '{role_id}' not found.")
    return SkillGapResponse(
        career_readiness_pct=readiness,
        gaps=[
            SkillGapOut(
                skill_id=g.skill_id,
                skill_name=g.skill_name,
                current_level=g.current_level,
                required_level=g.required_level,
                gap_size=g.gap_size,
                priority=g.priority.value,
            )
            for g in gaps
        ],
        biggest_opportunity=gaps[0].skill_id if gaps else None,
    )


@router.get("/generate", response_model=list[RecommendationOut])
@router.post("/generate", response_model=list[RecommendationOut])
def generate_recommendations(
    role_id: str,
    with_explanations: bool = False,
    top_n: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RecommendationOut]:
    profile = current_user.profile
    if not profile:
        raise HTTPException(
            status_code=400,
            detail="Complete your profile first (POST /api/profile).",
        )

    ranked = get_recommendations(
        db=db,
        user_id=current_user.id,
        role_id=role_id,
        experience_level=profile.experience_level or "entry",
        learning_style=(
            profile.learning_style.value if profile.learning_style else "mixed"
        ),
        hours_per_week=profile.hours_per_week or 10.0,
        timeline_months=profile.timeline_months or 6,
        top_n=top_n,
    )

    results: list[RecommendationOut] = []
    for ri in ranked:
        explanation: str | None = None
        if with_explanations:
            learner_ctx = {
                "target_career_role": role_id,
                "experience_level": profile.experience_level or "entry",
                "hours_per_week": profile.hours_per_week,
                "gap_skills": [],
            }
            explanation = explain_recommendation(
                ri.title, ri.item_type, ri.breakdown, learner_ctx
            )
        results.append(
            RecommendationOut(
                rank=ri.rank,
                id=ri.id,
                item_type=ri.item_type,
                title=ri.title,
                total_score=ri.total_score,
                breakdown=ScoreBreakdownOut(**ri.breakdown.__dict__),
                explanation=explanation,
            )
        )
    return results


@router.post("/profile/analyze", response_model=ProfileAnalyzeResponse)
def analyze_profile_text(body: ProfileAnalyzeRequest) -> ProfileAnalyzeResponse:
    """Extract structured profile data from free-text learner input (Phase 7)."""
    try:
        extracted = extract_profile(body.text)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Profile extraction failed: {exc}",
        ) from exc
    return ProfileAnalyzeResponse(
        education=extracted.education,
        experience_level=extracted.experience_level,
        skills=[s.model_dump() for s in extracted.skills],
        goal=extracted.goal,
        timeline_months=extracted.timeline_months,
        target_career_role=extracted.target_career_role,
    )
