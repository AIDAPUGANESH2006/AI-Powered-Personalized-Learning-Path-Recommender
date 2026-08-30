"""Assessment submission + adaptive engine trigger."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.adaptive_engine import AdaptationResult, apply_assessment_result
from app.ai.roadmap_generator import RoadmapItem
from app.api.deps import get_current_user
from app.database import get_db
from app.models import Assessment, AssessmentResult, Course, LearningPath, PathItem, User
from app.models.entities import LearningPathStatus, PathItemStatus, PathItemType

router = APIRouter(prefix="/assessment", tags=["assessment"])

# Load assessments from data/assessments.json as reliable source
_DATA_DIR = Path(__file__).resolve().parents[3] / "data"
_DATA_FILE = _DATA_DIR / "assessments.json"

COURSE_TO_ASSESSMENT: dict[str, str] = {
    "course-html-css": "assessment-html-css",
    "course-sql": "assessment-sql",
    "course-python-basics": "assessment-python",
    "course-javascript": "assessment-javascript",
    "course-react": "assessment-react",
    "course-nodejs": "assessment-nodejs",
    "course-cloud": "assessment-cloud",
    "course-docker": "assessment-docker",
    "course-statistics": "assessment-statistics",
    "course-linear-algebra": "assessment-linear-algebra",
    "course-ml-fundamentals": "assessment-ml",
    "course-deep-learning": "assessment-deep-learning",
    "course-nlp": "assessment-nlp",
    "course-llm-apps": "assessment-llm-apps",
    "course-data-analysis": "assessment-data-analysis",
    "course-data-viz": "assessment-data-viz",
    "course-dsa": "assessment-dsa",
    "course-kubernetes": "assessment-kubernetes",
    "course-aws": "assessment-aws",
    "course-cybersec": "assessment-cybersec",
}

SKILL_TO_ASSESSMENT: dict[str, str] = {
    "html_css": "assessment-html-css",
    "sql": "assessment-sql",
    "python": "assessment-python",
    "javascript": "assessment-javascript",
    "react": "assessment-react",
    "nodejs": "assessment-nodejs",
    "rest_apis": "assessment-nodejs",
    "cloud_fundamentals": "assessment-cloud",
    "docker": "assessment-docker",
    "statistics": "assessment-statistics",
    "linear_algebra": "assessment-linear-algebra",
    "machine_learning": "assessment-ml",
    "deep_learning": "assessment-deep-learning",
    "nlp": "assessment-nlp",
    "llms": "assessment-llm-apps",
    "transformers": "assessment-llm-apps",
    "data_analysis": "assessment-data-analysis",
    "data_visualization": "assessment-data-viz",
    "data_structures": "assessment-dsa",
    "kubernetes": "assessment-kubernetes",
    "aws": "assessment-aws",
    "cybersecurity_basics": "assessment-cybersec",
    "networking": "assessment-cybersec",
    "programming_fundamentals": "assessment-python",
}


def _get_static_assessments() -> list[dict]:
    if _DATA_FILE.exists():
        try:
            with open(_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _resolve_assessment_data(db: Session, target_id: str) -> dict | None:
    """Find assessment data by assessment_id, course_id, or skill_id."""
    resolved_id = COURSE_TO_ASSESSMENT.get(target_id) or SKILL_TO_ASSESSMENT.get(target_id) or target_id

    # 1. Check in static dataset
    static_list = _get_static_assessments()
    for item in static_list:
        if item["id"] == resolved_id or item.get("skill_id") == target_id or item["id"] == target_id:
            return item

    # 2. Check in database
    db_assessment = db.get(Assessment, resolved_id) or db.get(Assessment, target_id)
    if not db_assessment:
        clean_skill = target_id.replace("course-", "").replace("assessment-", "").replace("-", "_")
        db_assessment = db.scalar(
            select(Assessment).where(
                (Assessment.id == resolved_id)
                | (Assessment.skill_id == clean_skill)
                | (Assessment.skill_id == target_id)
            )
        )

    if db_assessment:
        return {
            "id": db_assessment.id,
            "title": db_assessment.title,
            "skill_id": db_assessment.skill_id,
            "pass_threshold": db_assessment.pass_threshold,
            "questions": db_assessment.questions or [],
        }

    # 3. Fallback: if target_id is a course in DB
    course = db.get(Course, target_id)
    if course and course.course_skills:
        for cs in course.course_skills:
            if cs.skill_id in SKILL_TO_ASSESSMENT:
                mapped_id = SKILL_TO_ASSESSMENT[cs.skill_id]
                for item in static_list:
                    if item["id"] == mapped_id:
                        return item

    return None


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
    assessment_data = _resolve_assessment_data(db, body.assessment_id)
    if not assessment_data:
        raise HTTPException(404, f"Assessment '{body.assessment_id}' not found.")

    questions = assessment_data.get("questions") or []
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
    passed = score >= assessment_data.get("pass_threshold", 0.6)

    assessment_id = assessment_data.get("id", body.assessment_id)
    skill_id = assessment_data.get("skill_id", "general")

    # Ensure assessment entity exists in DB for foreign key
    db_assessment = db.get(Assessment, assessment_id)
    if not db_assessment:
        try:
            db_assessment = Assessment(
                id=assessment_id,
                title=assessment_data.get("title", assessment_id),
                skill_id=skill_id,
                pass_threshold=assessment_data.get("pass_threshold", 0.6),
                questions=questions,
            )
            db.add(db_assessment)
            db.flush()
        except Exception:
            db.rollback()

    # Persist result if DB assessment exists
    try:
        if db.get(Assessment, assessment_id):
            result = AssessmentResult(
                user_id=current_user.id,
                assessment_id=assessment_id,
                score=score,
                answers=body.answers,
                passed=passed,
            )
            db.add(result)
            db.flush()
    except Exception:
        pass

    # Apply changes to active roadmap
    action = "completed"
    message = f"Score: {round(score * 100)}% ({correct}/{total} correct)"

    active_path = db.scalar(
        select(LearningPath).where(
            LearningPath.user_id == current_user.id,
            LearningPath.status == LearningPathStatus.active,
        )
    )

    if active_path:
        # Match path item by body.assessment_id, resolved assessment_id, course_id, or skill_id
        matched_item = None
        target_ids = {
            body.assessment_id,
            assessment_id,
            skill_id,
            f"course-{skill_id.replace('_', '-')}",
        }
        for k, v in COURSE_TO_ASSESSMENT.items():
            if v == assessment_id:
                target_ids.add(k)

        for pi in active_path.path_items:
            if pi.item_id in target_ids:
                matched_item = pi
                break

        if matched_item:
            matched_item.status = PathItemStatus.complete
            sorted_items = sorted(active_path.path_items, key=lambda x: x.order_index)
            # Unlock next locked item
            for pi in sorted_items:
                if pi.order_index > matched_item.order_index and pi.status == PathItemStatus.locked:
                    pi.status = PathItemStatus.active
                    action = "phase_unlocked"
                    message = f"Passed! Unlocked next step: {pi.title or pi.item_id}"
                    break
        else:
            # If no exact match, complete the currently active item
            active_item = next((pi for pi in active_path.path_items if pi.status == PathItemStatus.active), None)
            if active_item:
                active_item.status = PathItemStatus.complete
                sorted_items = sorted(active_path.path_items, key=lambda x: x.order_index)
                for pi in sorted_items:
                    if pi.order_index > active_item.order_index and pi.status == PathItemStatus.locked:
                        pi.status = PathItemStatus.active
                        action = "phase_unlocked"
                        message = f"Passed! Unlocked next step: {pi.title or pi.item_id}"
                        break

    db.commit()
    return SubmitResponse(
        assessment_id=assessment_id,
        score=score,
        passed=passed,
        correct=correct,
        total=total,
        adaptation_action=action,
        adaptation_message=message,
    )


@router.get("", response_model=list[dict])
@router.get("/list/all", response_model=list[dict])
def list_assessments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    static_list = _get_static_assessments()

    results = db.scalars(
        select(AssessmentResult).where(AssessmentResult.user_id == current_user.id)
    ).all()
    best_scores: dict[str, dict] = {}
    for r in results:
        if r.assessment_id not in best_scores or r.score > best_scores[r.assessment_id]["score"]:
            best_scores[r.assessment_id] = {
                "score": r.score,
                "passed": r.passed,
                "taken_at": r.taken_at.isoformat() if r.taken_at else None,
            }

    out = []
    seen_ids = set()
    for item in static_list:
        a_id = item["id"]
        seen_ids.add(a_id)
        user_res = best_scores.get(a_id)
        skill_name = item.get("skill_id", "").replace("_", " ").title()
        out.append({
            "id": a_id,
            "title": item.get("title", a_id),
            "skill_id": item.get("skill_id", ""),
            "skill_name": skill_name,
            "pass_threshold": item.get("pass_threshold", 0.6),
            "question_count": len(item.get("questions") or []),
            "latest_score": user_res["score"] if user_res else None,
            "passed": user_res["passed"] if user_res else False,
        })

    # Also add any custom DB assessments
    db_assessments = db.scalars(select(Assessment)).all()
    for a in db_assessments:
        if a.id not in seen_ids:
            user_res = best_scores.get(a.id)
            out.append({
                "id": a.id,
                "title": a.title,
                "skill_id": a.skill_id,
                "skill_name": a.skill.name if a.skill else a.skill_id.replace("_", " ").title(),
                "pass_threshold": a.pass_threshold,
                "question_count": len(a.questions or []),
                "latest_score": user_res["score"] if user_res else None,
                "passed": user_res["passed"] if user_res else False,
            })

    return out


@router.get("/{assessment_id}", response_model=dict)
def get_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    assessment_data = _resolve_assessment_data(db, assessment_id)
    if not assessment_data:
        raise HTTPException(404, f"Assessment for '{assessment_id}' not found.")

    # Return questions WITHOUT correct_index to avoid leaking answers
    safe_questions = [
        {"id": q["id"], "question": q["question"], "options": q["options"]}
        for q in (assessment_data.get("questions") or [])
    ]
    return {
        "id": assessment_data["id"],
        "title": assessment_data["title"],
        "skill_id": assessment_data.get("skill_id", ""),
        "pass_threshold": assessment_data.get("pass_threshold", 0.6),
        "questions": safe_questions,
    }
