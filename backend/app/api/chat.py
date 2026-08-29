"""AI Tutor chat endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.skill_gap import career_readiness_percent, compute_skill_gaps
from app.ai.tutor import chat
from app.api.deps import get_current_user
from app.database import get_db
from app.models import CareerRole, ChatHistory, LearningPath, PathItem, User, UserSkill
from app.models.entities import LearningPathStatus, PathItemStatus
from app.services.recommender_service import _role_requirement_map, _user_skill_map

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str   # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str


@router.post("", response_model=ChatResponse)
def tutor_chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    profile = current_user.profile

    # Build learner context
    learner_ctx: dict = {
        "goal": profile.goal if profile else None,
        "experience_level": profile.experience_level if profile else None,
        "hours_per_week": profile.hours_per_week if profile else None,
        "timeline_months": profile.timeline_months if profile else None,
    }

    if profile and profile.target_career_role_id:
        role = db.get(CareerRole, profile.target_career_role_id)
        learner_ctx["target_career_role"] = role.name if role else profile.target_career_role_id

        user_skills = _user_skill_map(db, current_user.id)
        role_reqs = _role_requirement_map(db, profile.target_career_role_id)
        from app.ai.skill_gap import compute_skill_gaps
        gaps = compute_skill_gaps(user_skills, role_reqs)
        learner_ctx["top_skill_gaps"] = [g.skill_id for g in gaps[:6]]
        learner_ctx["current_skill_levels"] = user_skills
    
    # Build roadmap snapshot
    roadmap_snapshot: dict | None = None
    active_path = db.scalar(
        select(LearningPath).where(
            LearningPath.user_id == current_user.id,
            LearningPath.status == LearningPathStatus.active,
        )
    )
    if active_path:
        sorted_items = sorted(active_path.path_items, key=lambda x: x.order_index)
        current_item = next((i for i in sorted_items if i.status == PathItemStatus.active), None)
        next_item = next(
            (i for i in sorted_items if i.status == PathItemStatus.locked), None
        )
        completed_count = sum(1 for i in sorted_items if i.status == PathItemStatus.complete)
        roadmap_snapshot = {
            "current_item_title": current_item.title if current_item else None,
            "next_item_title": next_item.title if next_item else None,
            "completed_count": completed_count,
            "total_items": len(sorted_items),
        }

    # Persist user message
    db.add(ChatHistory(user_id=current_user.id, role="user", content=body.message))

    # Build history list for LLM
    messages = [{"role": m.role, "content": m.content} for m in body.history]
    messages.append({"role": "user", "content": body.message})

    reply = chat(messages, learner_ctx, roadmap_snapshot)

    # Persist assistant reply
    db.add(ChatHistory(user_id=current_user.id, role="assistant", content=reply))
    db.commit()

    return ChatResponse(reply=reply)
