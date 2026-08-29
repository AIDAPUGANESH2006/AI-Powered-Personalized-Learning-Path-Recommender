"""Assessment submission + adaptive engine trigger."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.adaptive_engine import AdaptationResult, apply_assessment_result
from app.ai.roadmap_generator import RoadmapItem
from app.api.deps import get_current_user
from app.database import get_db
from app.models import Assessment, AssessmentResult, LearningPath, PathItem, User
from app.models.entities import LearningPathStatus, PathItemStatus, PathItemType

router = APIRouter(prefix="/assessment", tags=["assessment"])


class SubmitRequest(BaseModel):
    assessment_id: str
    answers: dict[str, int] = Field(
        description="{'q1': 2, 'q2': 0, ...} — 0-indexed answer choices"
    )


class SubmitResponse(BaseModel):
    assessment_id: str
    score: float
    passed: bool
    correct: int
    total: int
    adaptation_action: str
    adaptation_message: str


@router.post("/submit", response_model=SubmitResponse)
def submit_assessment(
    body: SubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubmitResponse:
    assessment = db.get(Assessment, body.assessment_id)
    if not assessment:
        raise HTTPException(404, f"Assessment '{body.assessment_id}' not found.")

    questions = assessment.questions or []
    if not questions:
        raise HTTPException(400, "This assessment has no questions.")

    # Grade answers
    correct = 0
    for q in questions:
        q_id = q.get("id")
        if q_id and body.answers.get(q_id) == q.get("correct_index"):
            correct += 1

    total = len(questions)
    score = correct / total
    passed = score >= assessment.pass_threshold

    # Persist result
    result = AssessmentResult(
        user_id=current_user.id,
        assessment_id=assessment.id,
        score=score,
        answers=body.answers,
        passed=passed,
    )
    db.add(result)
    db.flush()

    # Apply adaptive engine to active roadmap
    action = "no_change"
    message = f"Score: {round(score*100)}%"

    active_path = db.scalar(
        select(LearningPath).where(
            LearningPath.user_id == current_user.id,
            LearningPath.status == LearningPathStatus.active,
        )
    )

    if active_path:
        # Build an in-memory Roadmap snapshot for the adaptive engine
        from app.ai.roadmap_generator import Roadmap, RoadmapItem as RI
        items_snapshot = []
        for pi in sorted(active_path.path_items, key=lambda x: x.order_index):
            items_snapshot.append(RI(
                order_index=pi.order_index,
                item_type=pi.item_type.value,  # type: ignore[arg-type]
                item_id=pi.item_id,
                title=pi.title or pi.item_id,
                status=pi.status.value,  # type: ignore[arg-type]
                week_start=pi.week_start or 1,
                week_end=pi.week_end or 1,
                phase_label="",
                duration_hours=1,
            ))
        snapshot = Roadmap(
            user_id=str(current_user.id),
            target_career_role_id=active_path.target_career_role_id,
            pacing_mode=active_path.pacing_mode.value,  # type: ignore[arg-type]
            total_weeks=0,
            items=items_snapshot,
        )

        # Build optional reinforcement item
        reinf_item: RoadmapItem | None = None
        if not passed:
            reinf_item = RI(
                order_index=0,
                item_type="reinforcement",
                item_id=f"reinf-{assessment.skill_id}",
                title=f"Reinforcement: {assessment.skill.name}",
                status="locked",
                week_start=0,
                week_end=0,
                phase_label="Reinforcement",
                skills=[assessment.skill_id],
                duration_hours=5,
            )

        adaptation: AdaptationResult = apply_assessment_result(
            snapshot, assessment.id, score, assessment.pass_threshold, reinf_item
        )
        action = adaptation.action
        message = adaptation.message

        # Sync changes back to DB path_items
        updated_ids = {i.item_id: i.status for i in adaptation.roadmap.items}

        # Mark assessment item complete in DB
        for pi in active_path.path_items:
            new_status = updated_ids.get(pi.item_id)
            if new_status:
                try:
                    pi.status = PathItemStatus[new_status]
                except KeyError:
                    pass

        # Insert reinforcement path_item if needed
        if adaptation.action == "reinforcement_inserted" and reinf_item:
            # Find insertion point — before the next locked item after assessment
            sorted_items = sorted(active_path.path_items, key=lambda x: x.order_index)
            assess_idx = next(
                (i for i, p in enumerate(sorted_items) if p.item_id == assessment.id),
                None,
            )
            if assess_idx is not None:
                # Shift order_index of items after insertion point
                for pi in sorted_items[assess_idx + 1:]:
                    pi.order_index += 1
                db.add(PathItem(
                    learning_path_id=active_path.id,
                    order_index=assess_idx + 1,
                    item_type=PathItemType.reinforcement,
                    item_id=reinf_item.item_id,
                    status=PathItemStatus.active,
                    week_start=reinf_item.week_start,
                    week_end=reinf_item.week_end,
                    title=reinf_item.title,
                ))

    db.commit()
    return SubmitResponse(
        assessment_id=assessment.id,
        score=score,
        passed=passed,
        correct=correct,
        total=total,
        adaptation_action=action,
        adaptation_message=message,
    )


@router.get("/{assessment_id}", response_model=dict)
def get_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, f"Assessment '{assessment_id}' not found.")
    # Return questions WITHOUT correct_index to avoid leaking answers
    safe_questions = [
        {"id": q["id"], "question": q["question"], "options": q["options"]}
        for q in (assessment.questions or [])
    ]
    return {
        "id": assessment.id,
        "title": assessment.title,
        "skill_id": assessment.skill_id,
        "pass_threshold": assessment.pass_threshold,
        "questions": safe_questions,
    }
