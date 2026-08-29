"""Feedback endpoint — thumbs up/down + reason chip."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import Feedback, User

router = APIRouter(prefix="/feedback", tags=["feedback"])

VALID_REASONS = {"too_hard", "too_easy", "not_relevant", "too_long", "great"}


class FeedbackRequest(BaseModel):
    item_id: str
    item_type: str
    rating: int = Field(description="1 = thumbs up, -1 = thumbs down")
    reason: str | None = Field(default=None, description="One of: too_hard, too_easy, not_relevant, too_long, great")
    recommendation_id: int | None = None


class FeedbackResponse(BaseModel):
    id: int
    item_id: str
    rating: int
    reason: str | None


@router.post("", response_model=FeedbackResponse, status_code=201)
def submit_feedback(
    body: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FeedbackResponse:
    fb = Feedback(
        user_id=current_user.id,
        recommendation_id=body.recommendation_id,
        item_type=body.item_type,
        item_id=body.item_id,
        rating=body.rating,
        reason=body.reason,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return FeedbackResponse(id=fb.id, item_id=fb.item_id, rating=fb.rating, reason=fb.reason)
