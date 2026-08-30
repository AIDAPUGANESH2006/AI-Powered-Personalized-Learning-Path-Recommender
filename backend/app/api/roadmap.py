"""Roadmap generation, retrieval, and pacing-adjustment endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.explanation import explain_roadmap
from app.api.deps import get_current_user
from app.database import get_db
from app.models import LearningPath, PathItem, User
from app.models.entities import LearningPathStatus, PathItemStatus
from app.services.recommender_service import (
    generate_roadmap,
    persist_roadmap,
)

router = APIRouter(prefix="/roadmap", tags=["roadmap"])

PACING_MODES = {"fast_track", "balanced", "relaxed"}


# ── schemas ───────────────────────────────────────────────────────────────────

class RoadmapItemOut(BaseModel):
    order_index: int
    item_type: str
    item_id: str
    title: str
    status: str
    week_start: int
    week_end: int
    phase_label: str
    skills: list[str]
    score: float
    duration_hours: int | None


class RoadmapOut(BaseModel):
    id: int
    version: int
    pacing_mode: str
    target_career_role_id: str
    total_weeks: int
    items: list[RoadmapItemOut]
    narrative: str | None = None


class GenerateRequest(BaseModel):
    role_id: str
    pacing_mode: str = "balanced"


class AdjustRequest(BaseModel):
    pacing_mode: str


# ── helpers ───────────────────────────────────────────────────────────────────

def _active_path(db: Session, user: User) -> LearningPath | None:
    return db.scalar(
        select(LearningPath).where(
            LearningPath.user_id == user.id,
            LearningPath.status == LearningPathStatus.active,
        )
    )


def _path_to_out(lp: LearningPath, narrative: str | None = None) -> RoadmapOut:
    items_out: list[RoadmapItemOut] = []
    for pi in sorted(lp.path_items, key=lambda x: x.order_index):
        items_out.append(RoadmapItemOut(
            order_index=pi.order_index,
            item_type=pi.item_type.value,
            item_id=pi.item_id,
            title=pi.title or pi.item_id,
            status=pi.status.value,
            week_start=pi.week_start or 1,
            week_end=pi.week_end or 1,
            phase_label=_infer_phase(pi),
            skills=[],
            score=0.0,
            duration_hours=None,
        ))
    total_weeks = max((i.week_end or 1 for i in lp.path_items), default=1)
    return RoadmapOut(
        id=lp.id,
        version=lp.version,
        pacing_mode=lp.pacing_mode.value,
        target_career_role_id=lp.target_career_role_id,
        total_weeks=total_weeks,
        items=items_out,
        narrative=narrative,
    )


COURSE_PHASES: dict[str, str] = {
    "course-python-basics": "Foundation",
    "course-sql": "Foundation",
    "course-html-css": "Foundation",
    "course-cloud": "Foundation",
    "course-data-viz": "Foundation",
    "course-statistics": "Core Skills",
    "course-linear-algebra": "Core Skills",
    "course-data-analysis": "Core Skills",
    "course-javascript": "Core Skills",
    "course-react": "Core Skills",
    "course-nodejs": "Core Skills",
    "course-docker": "Core Skills",
    "course-aws": "Core Skills",
    "course-cybersec": "Core Skills",
    "course-ml-fundamentals": "Advanced",
    "course-deep-learning": "Advanced",
    "course-nlp": "Advanced",
    "course-llm-apps": "Advanced",
    "course-dsa": "Advanced",
    "course-kubernetes": "Advanced",
}

ASSESSMENT_PHASES: dict[str, str] = {
    "assessment-sql": "Foundation",
    "assessment-python": "Foundation",
    "assessment-statistics": "Core Skills",
    "assessment-react": "Core Skills",
    "assessment-ml": "Advanced",
}


def _infer_phase(pi: PathItem) -> str:
    if pi.item_type.value == "project":
        return "Capstone Projects"
    if pi.item_type.value == "assessment":
        return ASSESSMENT_PHASES.get(pi.item_id, "Core Skills")
    if pi.item_type.value == "reinforcement":
        return "Reinforcement"
    return COURSE_PHASES.get(pi.item_id, "Core Skills")



# ── endpoints ─────────────────────────────────────────────────────────────────

@router.post("", response_model=RoadmapOut, status_code=status.HTTP_201_CREATED)
def create_roadmap(
    body: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoadmapOut:
    if body.pacing_mode not in PACING_MODES:
        raise HTTPException(400, f"pacing_mode must be one of {PACING_MODES}")
    if not current_user.profile:
        raise HTTPException(400, "Complete your profile first.")

    roadmap = generate_roadmap(db, current_user, body.role_id, body.pacing_mode)  # type: ignore[arg-type]
    lp = persist_roadmap(db, current_user, roadmap)

    # Generate narrative explanation
    profile = current_user.profile
    narrative = explain_roadmap(
        {
            "total_weeks": roadmap.total_weeks,
            "pacing_mode": roadmap.pacing_mode,
            "phase_count": len({i.phase_label for i in roadmap.items}),
            "first_item_title": roadmap.items[0].title if roadmap.items else "",
        },
        {
            "goal": profile.goal,
            "target_career_role": body.role_id,
            "timeline_months": profile.timeline_months,
            "hours_per_week": profile.hours_per_week,
        },
    )
    return _path_to_out(lp, narrative)


@router.get("", response_model=RoadmapOut)
def get_roadmap(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoadmapOut:
    lp = _active_path(db, current_user)
    if not lp:
        raise HTTPException(404, "No active roadmap. POST /api/roadmap to generate one.")
    return _path_to_out(lp)


@router.patch("/pacing", response_model=RoadmapOut)
def adjust_pacing(
    body: AdjustRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoadmapOut:
    if body.pacing_mode not in PACING_MODES:
        raise HTTPException(400, f"pacing_mode must be one of {PACING_MODES}")
    lp = _active_path(db, current_user)
    if not lp:
        raise HTTPException(404, "No active roadmap found.")

    from app.models.entities import PacingMode
    lp.pacing_mode = PacingMode[body.pacing_mode]
    db.commit()
    db.refresh(lp)
    return _path_to_out(lp)


@router.post("/item/{item_id}/complete", response_model=RoadmapOut)
def mark_item_complete(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoadmapOut:
    lp = _active_path(db, current_user)
    if not lp:
        raise HTTPException(404, "No active roadmap found.")

    items = sorted(lp.path_items, key=lambda x: x.order_index)
    target = next((i for i in items if i.item_id == item_id), None)
    if not target:
        raise HTTPException(404, f"Item '{item_id}' not in active roadmap.")

    target.status = PathItemStatus.complete

    # Unlock next locked item
    for pi in items:
        if pi.order_index > target.order_index and pi.status == PathItemStatus.locked:
            pi.status = PathItemStatus.active
            break

    db.commit()
    db.refresh(lp)
    return _path_to_out(lp)
