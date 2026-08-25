"""Profile endpoints: create/read/update learner profile + skills."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import Profile, Skill, User, UserSkill
from app.schemas.profile import ProfileCreate, ProfileOut, ProfileUpdate, SkillOut

router = APIRouter(prefix="/profile", tags=["profile"])


def _sync_skills(db: Session, user: User, skills_input: list) -> None:
    """Upsert user_skills rows from a list of SkillInput."""
    for s in skills_input:
        skill = db.get(Skill, s.skill_id)
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown skill_id: '{s.skill_id}'",
            )
        existing = db.scalar(
            select(UserSkill).where(
                UserSkill.user_id == user.id,
                UserSkill.skill_id == s.skill_id,
            )
        )
        if existing:
            existing.level = s.level
        else:
            db.add(UserSkill(user_id=user.id, skill_id=s.skill_id, level=s.level))


def _profile_to_out(profile: Profile, db: Session) -> ProfileOut:
    user_skills = db.scalars(
        select(UserSkill).where(UserSkill.user_id == profile.user_id)
    ).all()
    skills_out = [SkillOut(skill_id=us.skill_id, level=us.level) for us in user_skills]
    return ProfileOut(
        id=profile.id,
        education=profile.education,
        experience_level=profile.experience_level,
        goal=profile.goal,
        timeline_months=profile.timeline_months,
        hours_per_week=profile.hours_per_week,
        learning_style=profile.learning_style,
        target_career_role_id=profile.target_career_role_id,
        skills=skills_out,
    )


@router.post("", response_model=ProfileOut, status_code=status.HTTP_201_CREATED)
def create_profile(
    body: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileOut:
    if current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile already exists. Use PATCH /api/profile to update it.",
        )
    profile = Profile(
        user_id=current_user.id,
        education=body.education,
        experience_level=body.experience_level,
        goal=body.goal,
        timeline_months=body.timeline_months,
        hours_per_week=body.hours_per_week,
        learning_style=body.learning_style,
        target_career_role_id=body.target_career_role_id,
    )
    db.add(profile)
    db.flush()
    _sync_skills(db, current_user, body.skills)
    db.commit()
    db.refresh(profile)
    return _profile_to_out(profile, db)


@router.get("", response_model=ProfileOut)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileOut:
    if not current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No profile found. POST /api/profile to create one.",
        )
    return _profile_to_out(current_user.profile, db)


@router.patch("", response_model=ProfileOut)
def update_profile(
    body: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileOut:
    if not current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No profile found. POST /api/profile to create one.",
        )
    profile = current_user.profile
    for field, value in body.model_dump(exclude_none=True, exclude={"skills"}).items():
        setattr(profile, field, value)

    if body.skills is not None:
        _sync_skills(db, current_user, body.skills)

    db.commit()
    db.refresh(profile)
    return _profile_to_out(profile, db)
