"""Seed catalog data from JSON files into PostgreSQL."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select

from app.database import SessionLocal, engine

from app.models import (
    Assessment,
    Base,
    CareerRole,
    CareerRoleSkill,
    Course,
    CoursePrerequisite,
    CourseSkill,
    Project,
    ProjectSkill,
    Skill,
    SkillPrerequisite,
)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def load_json(filename: str) -> list | dict:
    path = DATA_DIR / filename
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def seed_skills(session) -> None:
    skills_data = load_json("skills.json")
    skill_ids = set()

    for item in skills_data:
        skill_ids.add(item["id"])
        existing = session.get(Skill, item["id"])
        if existing:
            existing.name = item["name"]
            existing.description = item.get("description")
        else:
            session.add(
                Skill(
                    id=item["id"],
                    name=item["name"],
                    description=item.get("description"),
                )
            )

    session.flush()

    for item in skills_data:
        for prereq_id in item.get("prerequisites", []):
            if prereq_id not in skill_ids:
                print(f"Warning: unknown prerequisite '{prereq_id}' for {item['id']}")
                continue
            exists = session.scalar(
                select(SkillPrerequisite.id).where(
                    SkillPrerequisite.skill_id == item["id"],
                    SkillPrerequisite.prerequisite_skill_id == prereq_id,
                )
            )
            if not exists:
                session.add(
                    SkillPrerequisite(
                        skill_id=item["id"],
                        prerequisite_skill_id=prereq_id,
                    )
                )


def seed_careers(session) -> None:
    careers_data = load_json("careers.json")

    for item in careers_data:
        existing = session.get(CareerRole, item["id"])
        if existing:
            existing.name = item["name"]
            existing.description = item.get("description")
        else:
            session.add(
                CareerRole(
                    id=item["id"],
                    name=item["name"],
                    description=item.get("description"),
                )
            )

    session.flush()

    for item in careers_data:
        for skill_id, required_level in item.get("required_skills", {}).items():
            skill = session.get(Skill, skill_id)
            if not skill:
                print(f"Warning: unknown skill '{skill_id}' for career {item['id']}")
                continue
            exists = session.scalar(
                select(CareerRoleSkill.id).where(
                    CareerRoleSkill.career_role_id == item["id"],
                    CareerRoleSkill.skill_id == skill_id,
                )
            )
            if exists:
                role_skill = session.get(CareerRoleSkill, exists)
                if role_skill:
                    role_skill.required_level = float(required_level)
            else:
                session.add(
                    CareerRoleSkill(
                        career_role_id=item["id"],
                        skill_id=skill_id,
                        required_level=float(required_level),
                    )
                )


def seed_courses(session) -> None:
    courses_data = load_json("courses.json")
    course_ids = {item["id"] for item in courses_data}

    for item in courses_data:
        existing = session.get(Course, item["id"])
        if existing:
            existing.title = item["title"]
            existing.description = item.get("description")
            existing.level = item.get("level")
            existing.duration_hours = item.get("duration_hours", 0)
            existing.difficulty = item.get("difficulty", 1)
            existing.type = item.get("type", "course")
            existing.provider = item.get("provider")
        else:
            session.add(
                Course(
                    id=item["id"],
                    title=item["title"],
                    description=item.get("description"),
                    level=item.get("level"),
                    duration_hours=item.get("duration_hours", 0),
                    difficulty=item.get("difficulty", 1),
                    type=item.get("type", "course"),
                    provider=item.get("provider"),
                )
            )

    session.flush()

    for item in courses_data:
        for skill_id in item.get("skills", []):
            if not session.get(Skill, skill_id):
                print(f"Warning: unknown skill '{skill_id}' for course {item['id']}")
                continue
            exists = session.scalar(
                select(CourseSkill.id).where(
                    CourseSkill.course_id == item["id"],
                    CourseSkill.skill_id == skill_id,
                )
            )
            if not exists:
                session.add(CourseSkill(course_id=item["id"], skill_id=skill_id))

        for prereq_id in item.get("prerequisites", []):
            if prereq_id not in course_ids:
                print(
                    f"Warning: unknown course prerequisite '{prereq_id}' "
                    f"for {item['id']}"
                )
                continue
            exists = session.scalar(
                select(CoursePrerequisite.id).where(
                    CoursePrerequisite.course_id == item["id"],
                    CoursePrerequisite.prerequisite_course_id == prereq_id,
                )
            )
            if not exists:
                session.add(
                    CoursePrerequisite(
                        course_id=item["id"],
                        prerequisite_course_id=prereq_id,
                    )
                )


def seed_projects(session) -> None:
    projects_data = load_json("projects.json")

    for item in projects_data:
        existing = session.get(Project, item["id"])
        if existing:
            existing.title = item["title"]
            existing.description = item.get("description")
            existing.difficulty = item.get("difficulty", 1)
            existing.duration_hours = item.get("duration_hours", 0)
        else:
            session.add(
                Project(
                    id=item["id"],
                    title=item["title"],
                    description=item.get("description"),
                    difficulty=item.get("difficulty", 1),
                    duration_hours=item.get("duration_hours", 0),
                )
            )

    session.flush()

    for item in projects_data:
        for skill_id in item.get("skills", []):
            if not session.get(Skill, skill_id):
                print(f"Warning: unknown skill '{skill_id}' for project {item['id']}")
                continue
            exists = session.scalar(
                select(ProjectSkill.id).where(
                    ProjectSkill.project_id == item["id"],
                    ProjectSkill.skill_id == skill_id,
                )
            )
            if not exists:
                session.add(ProjectSkill(project_id=item["id"], skill_id=skill_id))


def seed_assessments(session) -> None:
    assessments_data = load_json("assessments.json")

    for item in assessments_data:
        if not session.get(Skill, item["skill_id"]):
            print(f"Warning: unknown skill '{item['skill_id']}' for {item['id']}")
            continue
        existing = session.get(Assessment, item["id"])
        if existing:
            existing.title = item["title"]
            existing.skill_id = item["skill_id"]
            existing.pass_threshold = item.get("pass_threshold", 0.6)
            existing.questions = item.get("questions", [])
        else:
            session.add(
                Assessment(
                    id=item["id"],
                    title=item["title"],
                    skill_id=item["skill_id"],
                    pass_threshold=item.get("pass_threshold", 0.6),
                    questions=item.get("questions", []),
                )
            )


def print_summary(session) -> None:
    tables = [
        ("skills", Skill),
        ("skill_prerequisites", SkillPrerequisite),
        ("career_roles", CareerRole),
        ("career_role_skills", CareerRoleSkill),
        ("courses", Course),
        ("course_skills", CourseSkill),
        ("course_prerequisites", CoursePrerequisite),
        ("projects", Project),
        ("project_skills", ProjectSkill),
        ("assessments", Assessment),
    ]
    print("\nSeed summary:")
    for label, model in tables:
        count = session.scalar(select(func.count()).select_from(model))
        print(f"  {label}: {count}")


def run_seed() -> None:
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Data directory not found: {DATA_DIR}")

    session = SessionLocal()
    try:
        seed_skills(session)
        seed_careers(session)
        seed_courses(session)
        seed_projects(session)
        seed_assessments(session)
        session.commit()
        print_summary(session)
        print("\nSeed completed successfully.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    run_seed()
