"""
Phase 6 — Roadmap Generator.

Combines: skill gaps + prerequisite ordering + recommendation scores
→ ordered phases with week estimates, locked/active/complete states.

Three pacing modes:
  fast_track : 15–20 h/wk  (multiplier 1.0)
  balanced   :  8–12 h/wk  (multiplier 1.5)
  relaxed    :  4–6  h/wk  (multiplier 2.5)

Pure function — no DB, no LLM.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

from app.ai.recommender import RankedItem
from app.ai.skill_gap import SkillGap

PacingMode = Literal["fast_track", "balanced", "relaxed"]

# h/wk assumed for duration maths when the user hasn't stated
_PACING_HRS: dict[PacingMode, float] = {
    "fast_track": 17.5,
    "balanced": 10.0,
    "relaxed": 5.0,
}

# Multiplier applied to raw duration_hours to arrive at elapsed weeks
# (accounts for review, practice, and real-life interruptions)
_PACING_MULTIPLIER: dict[PacingMode, float] = {
    "fast_track": 1.0,
    "balanced": 1.5,
    "relaxed": 2.5,
}


class PhaseLabel(str, Enum):
    FOUNDATION = "Foundation"
    CORE = "Core Skills"
    ADVANCED = "Advanced"
    CAPSTONE = "Capstone Projects"


@dataclass
class RoadmapItem:
    order_index: int
    item_type: Literal["course", "project", "assessment"]
    item_id: str
    title: str
    status: Literal["locked", "active", "complete"]
    week_start: int
    week_end: int
    phase_label: str
    skills: list[str] = field(default_factory=list)
    score: float = 0.0
    # present only for courses/projects — None for assessments
    duration_hours: int | None = None


@dataclass
class Roadmap:
    user_id: str
    target_career_role_id: str
    pacing_mode: PacingMode
    total_weeks: int
    items: list[RoadmapItem]
    version: int = 1


# ── helpers ───────────────────────────────────────────────────────────────────

def _weeks_for_item(duration_hours: int, pacing: PacingMode,
                    hrs_per_week: float | None = None) -> int:
    """Convert content hours to calendar weeks under a given pacing mode."""
    effective_hrs = hrs_per_week if hrs_per_week else _PACING_HRS[pacing]
    raw_weeks = duration_hours / max(effective_hrs, 1.0)
    adjusted = raw_weeks * _PACING_MULTIPLIER[pacing]
    return max(1, math.ceil(adjusted))


def _phase_for_difficulty(difficulty: int) -> str:
    if difficulty <= 2:
        return PhaseLabel.FOUNDATION.value
    if difficulty == 3:
        return PhaseLabel.CORE.value
    return PhaseLabel.ADVANCED.value


# ── main builder ──────────────────────────────────────────────────────────────

def build_roadmap(
    ranked_items: list[RankedItem],
    skill_gaps: list[SkillGap],
    # item metadata keyed by item_id — needed for duration/difficulty
    item_meta: dict[str, dict],          # {id: {duration_hours, difficulty, skills, title}}
    assessment_map: dict[str, str],      # {skill_id: assessment_id}
    assessment_titles: dict[str, str],   # {assessment_id: title}
    pacing_mode: PacingMode,
    hrs_per_week: float | None,
    user_id: str,
    target_career_role_id: str,
    completed_item_ids: set[str] | None = None,
) -> Roadmap:
    """
    Build an ordered roadmap from recommendation scores + prerequisites.

    Strategy:
      1. Insert prerequisite-ordered foundation items first (difficulty ≤ 2).
      2. Add core recommended courses/projects (difficulty 3).
      3. Add advanced items (difficulty ≥ 4).
      4. Sprinkle skill assessments after the course that teaches each skill.
      5. Add capstone projects at the end.
      6. Assign week ranges and locked/active status.
    """
    done = completed_item_ids or set()
    gap_skill_ids = {g.skill_id for g in skill_gaps}

    # Partition items by phase bucket
    foundation: list[RankedItem] = []
    core: list[RankedItem] = []
    advanced: list[RankedItem] = []
    capstone_projects: list[RankedItem] = []

    for ri in ranked_items:
        meta = item_meta.get(ri.id, {})
        diff = meta.get("difficulty", 3)
        if ri.item_type == "project" and diff >= 4:
            capstone_projects.append(ri)
        elif diff <= 2:
            foundation.append(ri)
        elif diff == 3:
            core.append(ri)
        else:
            advanced.append(ri)

    ordered: list[RankedItem] = foundation + core + advanced + capstone_projects

    items: list[RoadmapItem] = []
    current_week = 1
    order_idx = 0
    inserted_assessments: set[str] = set()

    for ri in ordered:
        meta = item_meta.get(ri.id, {})
        duration = meta.get("duration_hours", 10)
        diff = meta.get("difficulty", 3)
        skills = meta.get("skills", [])
        title = meta.get("title", ri.title)

        phase = (
            PhaseLabel.CAPSTONE.value
            if ri.item_type == "project" and diff >= 4
            else _phase_for_difficulty(diff)
        )

        weeks = _weeks_for_item(duration, pacing_mode, hrs_per_week)
        status: Literal["locked", "active", "complete"] = (
            "complete" if ri.id in done
            else "active" if order_idx == 0
            else "locked"
        )

        items.append(RoadmapItem(
            order_index=order_idx,
            item_type=ri.item_type,
            item_id=ri.id,
            title=title,
            status=status,
            week_start=current_week,
            week_end=current_week + weeks - 1,
            phase_label=phase,
            skills=skills,
            score=ri.total_score,
            duration_hours=duration,
        ))
        order_idx += 1
        current_week += weeks

        # Insert a skill assessment right after a course that covers a gap skill
        for skill_id in skills:
            if skill_id in gap_skill_ids and skill_id in assessment_map:
                a_id = assessment_map[skill_id]
                if a_id not in inserted_assessments:
                    inserted_assessments.add(a_id)
                    a_title = assessment_titles.get(a_id, f"Assessment: {skill_id}")
                    a_status: Literal["locked", "active", "complete"] = (
                        "complete" if a_id in done else "locked"
                    )
                    items.append(RoadmapItem(
                        order_index=order_idx,
                        item_type="assessment",
                        item_id=a_id,
                        title=a_title,
                        status=a_status,
                        week_start=current_week,
                        week_end=current_week,
                        phase_label=phase,
                        skills=[skill_id],
                        score=0.0,
                        duration_hours=1,
                    ))
                    order_idx += 1
                    current_week += 1

    # Activate the first non-complete item when nothing is yet active
    active_exists = any(i.status == "active" for i in items)
    if not active_exists:
        for item in items:
            if item.status == "locked":
                item.status = "active"
                break

    return Roadmap(
        user_id=user_id,
        target_career_role_id=target_career_role_id,
        pacing_mode=pacing_mode,
        total_weeks=current_week - 1,
        items=items,
        version=1,
    )


def adjust_pacing(roadmap: Roadmap, new_pacing: PacingMode,
                  hrs_per_week: float | None,
                  item_meta: dict[str, dict]) -> Roadmap:
    """Re-compute week ranges for an existing roadmap under a new pacing mode."""
    current_week = 1
    for item in roadmap.items:
        duration = item.duration_hours or 1
        weeks = _weeks_for_item(duration, new_pacing, hrs_per_week)
        item.week_start = current_week
        item.week_end = current_week + weeks - 1
        current_week += weeks

    roadmap.pacing_mode = new_pacing
    roadmap.total_weeks = current_week - 1
    return roadmap
