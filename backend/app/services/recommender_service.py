"""
Bridge between the DB session and the pure AI functions.
Loads catalog + user data from Postgres, calls the logic, returns results.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.ai.recommender import ItemInput, RankedItem, score_items
from app.ai.roadmap_generator import (
    PacingMode,
    Roadmap,
    RoadmapItem,
    build_roadmap,
)
from app.ai.skill_gap import (
    SkillGap,
    career_readiness_percent,
    compute_skill_gaps,
    full_prerequisite_plan,
)
from app.models import (
    Assessment,
    AssessmentResult,
    CareerRole,
    Course,
    Feedback,
    LearningPath,
    PathItem,
    Project,
    Skill,
    User,
    UserSkill,
)
from app.models.entities import LearningPathStatus, PathItemStatus, PathItemType


# ── helpers ───────────────────────────────────────────────────────────────────

def _user_skill_map(db: Session, user_id: uuid.UUID) -> dict[str, float]:
    rows = db.scalars(select(UserSkill).where(UserSkill.user_id == user_id)).all()
    return {r.skill_id: r.level for r in rows}


def _role_requirement_map(db: Session, role_id: str) -> dict[str, float]:
    role = db.scalar(
        select(CareerRole)
        .where(CareerRole.id == role_id)
        .options(selectinload(CareerRole.required_skills))
    )
    if not role:
        return {}
    return {rs.skill_id: rs.required_level for rs in role.required_skills}


def _skill_name_map(db: Session) -> dict[str, str]:
    rows = db.scalars(select(Skill)).all()
    return {s.id: s.name for s in rows}


def _feedback_map(db: Session, user_id: uuid.UUID) -> dict[str, float]:
    """Aggregate per-item feedback into a [-1, +1] float."""
    rows = db.scalars(
        select(Feedback).where(Feedback.user_id == user_id, Feedback.item_id.isnot(None))
    ).all()
    totals: dict[str, list[int]] = {}
    for fb in rows:
        totals.setdefault(fb.item_id, []).append(fb.rating)
    return {
        item_id: sum(1 if r > 0 else -1 for r in ratings) / max(len(ratings), 1)
        for item_id, ratings in totals.items()
    }


def _completed_items(db: Session, user_id: uuid.UUID) -> set[str]:
    paths = db.scalars(
        select(LearningPath)
        .where(
            LearningPath.user_id == user_id,
            LearningPath.status == LearningPathStatus.active,
        )
        .options(selectinload(LearningPath.path_items))
    ).all()
    done: set[str] = set()
    for lp in paths:
        for pi in lp.path_items:
            if pi.status == PathItemStatus.complete:
                done.add(pi.item_id)
    return done


# ── public service functions ──────────────────────────────────────────────────

def get_skill_gaps(
    db: Session, user_id: uuid.UUID, role_id: str
) -> tuple[list[SkillGap], float]:
    """Returns (gaps, career_readiness_pct)."""
    user_skills = _user_skill_map(db, user_id)
    role_reqs = _role_requirement_map(db, role_id)
    skill_names = _skill_name_map(db)
    gaps = compute_skill_gaps(user_skills, role_reqs, skill_names)
    readiness = career_readiness_percent(user_skills, role_reqs)
    return gaps, readiness


def get_recommendations(
    db: Session,
    user_id: uuid.UUID,
    role_id: str,
    experience_level: str,
    learning_style: str,
    hours_per_week: float,
    timeline_months: int,
    top_n: int = 10,
) -> list[RankedItem]:
    user_skills = _user_skill_map(db, user_id)
    role_reqs = _role_requirement_map(db, role_id)
    skill_names = _skill_name_map(db)
    feedback = _feedback_map(db, user_id)
    completed = _completed_items(db, user_id)

    gaps = compute_skill_gaps(user_skills, role_reqs, skill_names)
    gap_skill_ids = [g.skill_id for g in gaps]
    gap_sizes = {g.skill_id: g.gap_size for g in gaps}
    role_skill_ids = set(role_reqs.keys())

    # Build skill prerequisite graph
    skill_graph: dict[str, list[str]] = {}
    skills = db.scalars(
        select(Skill).options(selectinload(Skill.prerequisites))
    ).all()
    for skill in skills:
        skill_graph[skill.id] = [p.prerequisite_skill_id for p in skill.prerequisites]

    items: list[ItemInput] = []

    courses = db.scalars(
        select(Course).options(
            selectinload(Course.course_skills),
            selectinload(Course.prerequisites),
        )
    ).all()
    for course in courses:
        items.append(ItemInput(
            id=course.id,
            item_type="course",
            title=course.title,
            skills=[cs.skill_id for cs in course.course_skills],
            difficulty=course.difficulty,
            duration_hours=course.duration_hours,
            level=course.level or "intermediate",
            prerequisites=[cp.prerequisite_course_id for cp in course.prerequisites],
        ))

    projects = db.scalars(
        select(Project).options(selectinload(Project.project_skills))
    ).all()
    for project in projects:
        items.append(ItemInput(
            id=project.id,
            item_type="project",
            title=project.title,
            skills=[ps.skill_id for ps in project.project_skills],
            difficulty=project.difficulty,
            duration_hours=project.duration_hours,
        ))

    timeline_weeks = int(timeline_months * 4.33)

    return score_items(
        items=items,
        gap_skill_ids=gap_skill_ids,
        gap_sizes=gap_sizes,
        role_skill_ids=role_skill_ids,
        completed_item_ids=completed,
        experience_level=experience_level,
        learning_style=learning_style,
        available_hours_per_week=hours_per_week,
        timeline_weeks=timeline_weeks,
        user_feedback=feedback,
        top_n=top_n,
    )


def generate_roadmap(
    db: Session,
    user: User,
    role_id: str,
    pacing_mode: PacingMode,
) -> Roadmap:
    profile = user.profile
    hrs = profile.hours_per_week if profile else 10.0
    months = profile.timeline_months if profile else 6
    exp = profile.experience_level or "entry" if profile else "entry"
    style = (profile.learning_style.value if profile and profile.learning_style
             else "mixed")

    ranked = get_recommendations(
        db, user.id, role_id, exp, style, hrs or 10.0, months or 6, top_n=20
    )
    gaps, _ = get_skill_gaps(db, user.id, role_id)

    # Build item_meta dict for roadmap generator
    item_meta: dict[str, dict] = {}
    courses = db.scalars(
        select(Course).options(selectinload(Course.course_skills))
    ).all()
    for course in courses:
        item_meta[course.id] = {
            "title": course.title,
            "duration_hours": course.duration_hours,
            "difficulty": course.difficulty,
            "skills": [cs.skill_id for cs in course.course_skills],
        }
    projects = db.scalars(
        select(Project).options(selectinload(Project.project_skills))
    ).all()
    for project in projects:
        item_meta[project.id] = {
            "title": project.title,
            "duration_hours": project.duration_hours,
            "difficulty": project.difficulty,
            "skills": [ps.skill_id for ps in project.project_skills],
        }

    # Assessment maps
    assessments = db.scalars(select(Assessment)).all()
    assessment_map = {a.skill_id: a.id for a in assessments}
    assessment_titles = {a.id: a.title for a in assessments}

    completed = _completed_items(db, user.id)

    return build_roadmap(
        ranked_items=ranked,
        skill_gaps=gaps,
        item_meta=item_meta,
        assessment_map=assessment_map,
        assessment_titles=assessment_titles,
        pacing_mode=pacing_mode,
        hrs_per_week=hrs,
        user_id=str(user.id),
        target_career_role_id=role_id,
        completed_item_ids=completed,
    )


def persist_roadmap(db: Session, user: User, roadmap: Roadmap) -> LearningPath:
    """Save a Roadmap dataclass to the DB, archiving any previous active path."""
    # Archive old paths
    old_paths = db.scalars(
        select(LearningPath).where(
            LearningPath.user_id == user.id,
            LearningPath.status == LearningPathStatus.active,
        )
    ).all()
    for op in old_paths:
        op.status = LearningPathStatus.archived

    # Get max version
    all_paths = db.scalars(
        select(LearningPath).where(LearningPath.user_id == user.id)
    ).all()
    version = max((lp.version for lp in all_paths), default=0) + 1

    lp = LearningPath(
        user_id=user.id,
        target_career_role_id=roadmap.target_career_role_id,
        pacing_mode=roadmap.pacing_mode,
        version=version,
        status=LearningPathStatus.active,
    )
    db.add(lp)
    db.flush()

    for ri in roadmap.items:
        item_type_map = {
            "course": PathItemType.course,
            "project": PathItemType.project,
            "assessment": PathItemType.assessment,
            "reinforcement": PathItemType.reinforcement,
        }
        db.add(PathItem(
            learning_path_id=lp.id,
            order_index=ri.order_index,
            item_type=item_type_map.get(ri.item_type, PathItemType.course),
            item_id=ri.item_id,
            status=PathItemStatus[ri.status],
            week_start=ri.week_start,
            week_end=ri.week_end,
            title=ri.title,
        ))

    db.commit()
    db.refresh(lp)
    return lp
