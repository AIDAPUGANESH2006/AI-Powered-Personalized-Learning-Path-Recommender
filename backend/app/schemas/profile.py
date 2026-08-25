from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.entities import LearningStyle


class SkillInput(BaseModel):
    skill_id: str
    level: float = Field(ge=0.0, le=1.0, description="Self-reported proficiency 0–1")


class ProfileCreate(BaseModel):
    education: str | None = None
    experience_level: str | None = None
    goal: str | None = None
    timeline_months: int | None = Field(default=None, ge=1, le=120)
    hours_per_week: float | None = Field(default=None, ge=1.0, le=80.0)
    learning_style: LearningStyle | None = None
    target_career_role_id: str | None = None
    skills: list[SkillInput] = Field(default_factory=list)


class ProfileUpdate(BaseModel):
    education: str | None = None
    experience_level: str | None = None
    goal: str | None = None
    timeline_months: int | None = Field(default=None, ge=1, le=120)
    hours_per_week: float | None = Field(default=None, ge=1.0, le=80.0)
    learning_style: LearningStyle | None = None
    target_career_role_id: str | None = None
    skills: list[SkillInput] | None = None


class SkillOut(BaseModel):
    skill_id: str
    level: float

    model_config = {"from_attributes": True}


class ProfileOut(BaseModel):
    id: int
    education: str | None
    experience_level: str | None
    goal: str | None
    timeline_months: int | None
    hours_per_week: float | None
    learning_style: LearningStyle | None
    target_career_role_id: str | None
    skills: list[SkillOut] = []

    model_config = {"from_attributes": True}
