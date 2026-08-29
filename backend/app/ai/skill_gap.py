"""
Phase 4 — Skill Gap Engine + Prerequisite Resolver.

Pure functions: no database sessions, no LLM calls.
All inputs are plain dicts/lists so they are trivially unit-testable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class GapPriority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class SkillGap:
    skill_id: str
    skill_name: str
    current_level: float        # 0-1  (0 = no knowledge)
    required_level: float       # 0-1
    gap_size: float             # required - current  (clamped >= 0)
    priority: GapPriority


@dataclass
class PrerequisiteChain:
    target_skill_id: str
    ordered_missing: list[str]  # topological order — earliest first


# ── Skill-gap calculation ─────────────────────────────────────────────────────

def compute_skill_gaps(
    user_skills: dict[str, float],
    role_requirements: dict[str, float],
    skill_names: dict[str, str] | None = None,
) -> list[SkillGap]:
    """Return a list of SkillGap objects, sorted descending by gap_size."""
    names = skill_names or {}
    gaps: list[SkillGap] = []

    for skill_id, required in role_requirements.items():
        current = user_skills.get(skill_id, 0.0)
        gap = max(0.0, round(required - current, 4))
        if gap <= 0:
            continue

        if gap >= 0.5:
            priority = GapPriority.HIGH
        elif gap >= 0.25:
            priority = GapPriority.MEDIUM
        else:
            priority = GapPriority.LOW

        gaps.append(SkillGap(
            skill_id=skill_id,
            skill_name=names.get(skill_id, skill_id),
            current_level=round(current, 4),
            required_level=round(required, 4),
            gap_size=gap,
            priority=priority,
        ))

    gaps.sort(key=lambda g: g.gap_size, reverse=True)
    return gaps


def skill_gap_summary(gaps: list[SkillGap]) -> dict:
    if not gaps:
        return {"total_gaps": 0, "high": 0, "medium": 0, "low": 0, "biggest_opportunity": None}
    return {
        "total_gaps": len(gaps),
        "high":   sum(1 for g in gaps if g.priority == GapPriority.HIGH),
        "medium": sum(1 for g in gaps if g.priority == GapPriority.MEDIUM),
        "low":    sum(1 for g in gaps if g.priority == GapPriority.LOW),
        "biggest_opportunity": gaps[0].skill_id,
    }


def career_readiness_percent(
    user_skills: dict[str, float],
    role_requirements: dict[str, float],
) -> float:
    """Overall readiness as a percentage (0-100), weighted by required level."""
    if not role_requirements:
        return 0.0
    total_weight = sum(role_requirements.values())
    if total_weight == 0:
        return 0.0
    achieved = sum(
        min(user_skills.get(sid, 0.0), req)
        for sid, req in role_requirements.items()
    )
    return round((achieved / total_weight) * 100, 1)


# ── Prerequisite resolver ─────────────────────────────────────────────────────

def resolve_prerequisites(
    target_skill_id: str,
    skill_graph: dict[str, list[str]],
    user_skills: dict[str, float],
    mastery_threshold: float = 0.4,
) -> PrerequisiteChain:
    """Walk the prerequisite graph; return ordered chain of missing skills."""
    visited: set[str] = set()
    ordered: list[str] = []

    def _dfs(skill_id: str) -> None:
        if skill_id in visited:
            return
        visited.add(skill_id)
        for prereq in skill_graph.get(skill_id, []):
            _dfs(prereq)
        if user_skills.get(skill_id, 0.0) < mastery_threshold:
            ordered.append(skill_id)

    _dfs(target_skill_id)
    missing = [s for s in ordered if s != target_skill_id]
    return PrerequisiteChain(target_skill_id=target_skill_id, ordered_missing=missing)


def full_prerequisite_plan(
    gap_skills: list[str],
    skill_graph: dict[str, list[str]],
    user_skills: dict[str, float],
    mastery_threshold: float = 0.4,
) -> list[str]:
    """De-duplicated ordered list of ALL skills the learner needs to acquire."""
    seen: set[str] = set()
    plan: list[str] = []

    for skill_id in gap_skills:
        chain = resolve_prerequisites(skill_id, skill_graph, user_skills, mastery_threshold)
        for s in chain.ordered_missing:
            if s not in seen:
                seen.add(s)
                plan.append(s)
        if skill_id not in seen:
            seen.add(skill_id)
            plan.append(skill_id)

    return plan
