"""Seed demo personas and create sample learning paths."""
from __future__ import annotations

import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from app.database import SessionLocal
from app.models import (
    User,
    Profile,
    UserSkill,
    LearningStyle,
)
from app.services.auth import hash_password

DEMO_PERSONAS = [
    {
        "email": "ganeshaidapu@gmail.com",
        "password": "password123",
        "education": "Computer Science / Engineering",
        "experience_level": "student",
        "goal": "Become an AI/ML Engineer in 8 months",
        "timeline_months": 8,
        "hours_per_week": 15.0,
        "learning_style": LearningStyle.mixed,
        "target_career_role_id": "ai_ml_engineer",
        "skills": {
            "programming_fundamentals": 0.8,
            "python": 0.6,
            "java": 0.5,
            "statistics": 0.4,
            "git": 0.5,
        },
    },
    {
        "email": "rahul@example.com",
        "password": "password123",
        "education": "3rd Year B.Tech CSE",
        "experience_level": "student",
        "goal": "Land an AI Engineer internship and master Deep Learning",
        "timeline_months": 6,
        "hours_per_week": 12.0,
        "learning_style": LearningStyle.hands_on,
        "target_career_role_id": "ai_ml_engineer",
        "skills": {
            "programming_fundamentals": 0.75,
            "python": 0.7,
            "statistics": 0.5,
            "linear_algebra": 0.4,
            "data_structures": 0.6,
        },
    },
    {
        "email": "priya@example.com",
        "password": "password123",
        "education": "B.Com / Information Systems",
        "experience_level": "entry",
        "goal": "Transition into Data Analytics and build SQL dashboards",
        "timeline_months": 4,
        "hours_per_week": 10.0,
        "learning_style": LearningStyle.visual,
        "target_career_role_id": "data_analyst",
        "skills": {
            "programming_fundamentals": 0.5,
            "sql": 0.65,
            "data_analysis": 0.45,
            "python": 0.35,
            "statistics": 0.4,
        },
    },
    {
        "email": "alex@example.com",
        "password": "password123",
        "education": "Bootcamp Graduate",
        "experience_level": "entry",
        "goal": "Become a Full Stack Web Developer building scalable React apps",
        "timeline_months": 6,
        "hours_per_week": 15.0,
        "learning_style": LearningStyle.hands_on,
        "target_career_role_id": "full_stack_developer",
        "skills": {
            "programming_fundamentals": 0.7,
            "html_css": 0.8,
            "javascript": 0.7,
            "react": 0.6,
            "git": 0.6,
        },
    },
    {
        "email": "sarah@example.com",
        "password": "password123",
        "education": "IT Systems",
        "experience_level": "mid",
        "goal": "Master Cloud Infrastructure & AWS Architecture",
        "timeline_months": 6,
        "hours_per_week": 8.0,
        "learning_style": LearningStyle.mixed,
        "target_career_role_id": "cloud_engineer",
        "skills": {
            "networking": 0.7,
            "cloud_fundamentals": 0.6,
            "docker": 0.5,
            "python": 0.4,
        },
    },
]


def seed_personas() -> None:
    session = SessionLocal()
    try:
        for p in DEMO_PERSONAS:
            user = session.scalar(select(User).where(User.email == p["email"]))
            if not user:
                user = User(
                    email=p["email"],
                    password_hash=hash_password(p["password"]),
                )
                session.add(user)
                session.flush()
                print(f"Created user: {p['email']}")
            else:
                user.password_hash = hash_password(p["password"])
                print(f"Updated user password for: {p['email']}")

            # Profile
            profile = user.profile
            if not profile:
                profile = Profile(
                    user_id=user.id,
                    education=p["education"],
                    experience_level=p["experience_level"],
                    goal=p["goal"],
                    timeline_months=p["timeline_months"],
                    hours_per_week=p["hours_per_week"],
                    learning_style=p["learning_style"],
                    target_career_role_id=p["target_career_role_id"],
                )
                session.add(profile)
            else:
                profile.education = p["education"]
                profile.experience_level = p["experience_level"]
                profile.goal = p["goal"]
                profile.timeline_months = p["timeline_months"]
                profile.hours_per_week = p["hours_per_week"]
                profile.learning_style = p["learning_style"]
                profile.target_career_role_id = p["target_career_role_id"]

            session.flush()

            # User skills
            for skill_id, lvl in p["skills"].items():
                existing_skill = session.scalar(
                    select(UserSkill).where(
                        UserSkill.user_id == user.id,
                        UserSkill.skill_id == skill_id,
                    )
                )
                if existing_skill:
                    existing_skill.level = float(lvl)
                else:
                    session.add(
                        UserSkill(
                            user_id=user.id,
                            skill_id=skill_id,
                            level=float(lvl),
                        )
                    )

        session.commit()
        print("\nAll 5 demo personas seeded successfully!")
        print("Default password for all personas: password123")
    except Exception as exc:
        session.rollback()
        print(f"Error seeding personas: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_personas()
