"""Read-only catalog endpoints: skills, career roles, courses."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import CareerRole, Skill

router = APIRouter(prefix="/catalog", tags=["catalog"])


class SkillBrief(BaseModel):
    id: str
    name: str
    description: str | None
    prerequisites: list[str]

    model_config = {"from_attributes": True}


class CareerBrief(BaseModel):
    id: str
    name: str
    description: str | None
    required_skills: dict[str, float]

    model_config = {"from_attributes": True}


@router.get("/skills", response_model=list[SkillBrief])
def list_skills(db: Session = Depends(get_db)) -> list[SkillBrief]:
    skills = db.scalars(
        select(Skill).options(selectinload(Skill.prerequisites))
    ).all()
    return [
        SkillBrief(
            id=s.id,
            name=s.name,
            description=s.description,
            prerequisites=[p.prerequisite_skill_id for p in s.prerequisites],
        )
        for s in skills
    ]


@router.get("/careers", response_model=list[CareerBrief])
def list_careers(db: Session = Depends(get_db)) -> list[CareerBrief]:
    careers = db.scalars(
        select(CareerRole).options(selectinload(CareerRole.required_skills))
    ).all()
    return [
        CareerBrief(
            id=c.id,
            name=c.name,
            description=c.description,
            required_skills={rs.skill_id: rs.required_level for rs in c.required_skills},
        )
        for c in careers
    ]
