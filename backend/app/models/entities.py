import enum
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class LearningStyle(str, enum.Enum):
    visual = "visual"
    hands_on = "hands_on"
    reading = "reading"
    mixed = "mixed"


class PacingMode(str, enum.Enum):
    fast_track = "fast_track"
    balanced = "balanced"
    relaxed = "relaxed"


class PathItemType(str, enum.Enum):
    course = "course"
    project = "project"
    assessment = "assessment"
    reinforcement = "reinforcement"


class PathItemStatus(str, enum.Enum):
    locked = "locked"
    active = "active"
    complete = "complete"


class LearningPathStatus(str, enum.Enum):
    active = "active"
    archived = "archived"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    profile: Mapped["Profile | None"] = relationship(back_populates="user")
    user_skills: Mapped[list["UserSkill"]] = relationship(back_populates="user")
    learning_paths: Mapped[list["LearningPath"]] = relationship(back_populates="user")
    progress_records: Mapped[list["UserProgress"]] = relationship(back_populates="user")
    assessment_results: Mapped[list["AssessmentResult"]] = relationship(
        back_populates="user"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="user")
    feedback_entries: Mapped[list["Feedback"]] = relationship(back_populates="user")
    chat_messages: Mapped[list["ChatHistory"]] = relationship(back_populates="user")


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    education: Mapped[str | None] = mapped_column(String(255), nullable=True)
    experience_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    timeline_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hours_per_week: Mapped[float | None] = mapped_column(Float, nullable=True)
    learning_style: Mapped[LearningStyle | None] = mapped_column(
        Enum(LearningStyle, name="learning_style"), nullable=True
    )
    target_career_role_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("career_roles.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="profile")
    target_career_role: Mapped["CareerRole | None"] = relationship(
        back_populates="profiles"
    )


class UserSkill(Base):
    __tablename__ = "user_skills"
    __table_args__ = (UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    skill_id: Mapped[str] = mapped_column(String(64), ForeignKey("skills.id"))
    level: Mapped[float] = mapped_column(Float, default=0.0)

    user: Mapped["User"] = relationship(back_populates="user_skills")
    skill: Mapped["Skill"] = relationship(back_populates="user_skills")


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    user_skills: Mapped[list["UserSkill"]] = relationship(back_populates="skill")
    career_role_skills: Mapped[list["CareerRoleSkill"]] = relationship(
        back_populates="skill"
    )
    course_skills: Mapped[list["CourseSkill"]] = relationship(back_populates="skill")
    project_skills: Mapped[list["ProjectSkill"]] = relationship(back_populates="skill")
    assessments: Mapped[list["Assessment"]] = relationship(back_populates="skill")
    prerequisites: Mapped[list["SkillPrerequisite"]] = relationship(
        back_populates="skill",
        foreign_keys="SkillPrerequisite.skill_id",
    )
    required_by: Mapped[list["SkillPrerequisite"]] = relationship(
        back_populates="prerequisite_skill",
        foreign_keys="SkillPrerequisite.prerequisite_skill_id",
    )


class SkillPrerequisite(Base):
    __tablename__ = "skill_prerequisites"
    __table_args__ = (
        UniqueConstraint(
            "skill_id", "prerequisite_skill_id", name="uq_skill_prerequisite"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_id: Mapped[str] = mapped_column(String(64), ForeignKey("skills.id"))
    prerequisite_skill_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("skills.id")
    )

    skill: Mapped["Skill"] = relationship(
        back_populates="prerequisites", foreign_keys=[skill_id]
    )
    prerequisite_skill: Mapped["Skill"] = relationship(
        back_populates="required_by", foreign_keys=[prerequisite_skill_id]
    )


class CareerRole(Base):
    __tablename__ = "career_roles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    required_skills: Mapped[list["CareerRoleSkill"]] = relationship(
        back_populates="career_role"
    )
    profiles: Mapped[list["Profile"]] = relationship(back_populates="target_career_role")
    learning_paths: Mapped[list["LearningPath"]] = relationship(
        back_populates="target_career_role"
    )


class CareerRoleSkill(Base):
    __tablename__ = "career_role_skills"
    __table_args__ = (
        UniqueConstraint("career_role_id", "skill_id", name="uq_career_role_skill"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    career_role_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("career_roles.id")
    )
    skill_id: Mapped[str] = mapped_column(String(64), ForeignKey("skills.id"))
    required_level: Mapped[float] = mapped_column(Float, nullable=False)

    career_role: Mapped["CareerRole"] = relationship(back_populates="required_skills")
    skill: Mapped["Skill"] = relationship(back_populates="career_role_skills")


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    duration_hours: Mapped[int] = mapped_column(Integer, default=0)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    type: Mapped[str] = mapped_column(String(50), default="course")
    provider: Mapped[str | None] = mapped_column(String(255), nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)

    course_skills: Mapped[list["CourseSkill"]] = relationship(back_populates="course")
    prerequisites: Mapped[list["CoursePrerequisite"]] = relationship(
        back_populates="course",
        foreign_keys="CoursePrerequisite.course_id",
    )
    required_by: Mapped[list["CoursePrerequisite"]] = relationship(
        back_populates="prerequisite_course",
        foreign_keys="CoursePrerequisite.prerequisite_course_id",
    )


class CourseSkill(Base):
    __tablename__ = "course_skills"
    __table_args__ = (
        UniqueConstraint("course_id", "skill_id", name="uq_course_skill"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[str] = mapped_column(String(64), ForeignKey("courses.id"))
    skill_id: Mapped[str] = mapped_column(String(64), ForeignKey("skills.id"))

    course: Mapped["Course"] = relationship(back_populates="course_skills")
    skill: Mapped["Skill"] = relationship(back_populates="course_skills")


class CoursePrerequisite(Base):
    __tablename__ = "course_prerequisites"
    __table_args__ = (
        UniqueConstraint(
            "course_id", "prerequisite_course_id", name="uq_course_prerequisite"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[str] = mapped_column(String(64), ForeignKey("courses.id"))
    prerequisite_course_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("courses.id")
    )

    course: Mapped["Course"] = relationship(
        back_populates="prerequisites", foreign_keys=[course_id]
    )
    prerequisite_course: Mapped["Course"] = relationship(
        back_populates="required_by", foreign_keys=[prerequisite_course_id]
    )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    duration_hours: Mapped[int] = mapped_column(Integer, default=0)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)

    project_skills: Mapped[list["ProjectSkill"]] = relationship(back_populates="project")


class ProjectSkill(Base):
    __tablename__ = "project_skills"
    __table_args__ = (
        UniqueConstraint("project_id", "skill_id", name="uq_project_skill"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"))
    skill_id: Mapped[str] = mapped_column(String(64), ForeignKey("skills.id"))

    project: Mapped["Project"] = relationship(back_populates="project_skills")
    skill: Mapped["Skill"] = relationship(back_populates="project_skills")


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    skill_id: Mapped[str] = mapped_column(String(64), ForeignKey("skills.id"))
    pass_threshold: Mapped[float] = mapped_column(Float, default=0.6)
    questions: Mapped[list] = mapped_column(JSONB, default=list)

    skill: Mapped["Skill"] = relationship(back_populates="assessments")
    results: Mapped[list["AssessmentResult"]] = relationship(back_populates="assessment")


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    target_career_role_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("career_roles.id")
    )
    pacing_mode: Mapped[PacingMode] = mapped_column(
        Enum(PacingMode, name="pacing_mode"), default=PacingMode.balanced
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[LearningPathStatus] = mapped_column(
        Enum(LearningPathStatus, name="learning_path_status"),
        default=LearningPathStatus.active,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="learning_paths")
    target_career_role: Mapped["CareerRole"] = relationship(
        back_populates="learning_paths"
    )
    path_items: Mapped[list["PathItem"]] = relationship(
        back_populates="learning_path", order_by="PathItem.order_index"
    )


class PathItem(Base):
    __tablename__ = "path_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    learning_path_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("learning_paths.id", ondelete="CASCADE")
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    item_type: Mapped[PathItemType] = mapped_column(
        Enum(PathItemType, name="path_item_type"), nullable=False
    )
    item_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[PathItemStatus] = mapped_column(
        Enum(PathItemStatus, name="path_item_status"),
        default=PathItemStatus.locked,
    )
    week_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    week_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    learning_path: Mapped["LearningPath"] = relationship(back_populates="path_items")
    progress_records: Mapped[list["UserProgress"]] = relationship(
        back_populates="path_item"
    )


class UserProgress(Base):
    __tablename__ = "user_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    path_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("path_items.id", ondelete="CASCADE")
    )
    status: Mapped[PathItemStatus] = mapped_column(
        Enum(PathItemStatus, name="path_item_status"),
        default=PathItemStatus.active,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="progress_records")
    path_item: Mapped["PathItem"] = relationship(back_populates="progress_records")


class AssessmentResult(Base):
    __tablename__ = "assessment_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    assessment_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("assessments.id")
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    answers: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    taken_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="assessment_results")
    assessment: Mapped["Assessment"] = relationship(back_populates="results")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    item_id: Mapped[str] = mapped_column(String(64), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    score_breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="recommendations")
    feedback_entries: Mapped[list["Feedback"]] = relationship(
        back_populates="recommendation"
    )


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    recommendation_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("recommendations.id", ondelete="SET NULL"), nullable=True
    )
    item_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    item_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="feedback_entries")
    recommendation: Mapped["Recommendation | None"] = relationship(
        back_populates="feedback_entries"
    )


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="chat_messages")
