"""
Phase 5 — Hybrid Recommendation Engine.

Pure function: score_items() takes plain dicts and returns ranked results with
a per-factor breakdown so explanation.py can cite real numbers.

Score formula (weights sum to 1.0):
  0.30 × skill_gap_match
  0.20 × goal_relevance
  0.15 × prerequisite_fit
  0.10 × difficulty_fit
  0.10 × learning_pref_fit
  0.10 × time_fit
  0.05 × user_feedback_adjustment
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

WEIGHTS = {
    "skill_gap_match": 0.30,
    "goal_relevance": 0.20,
    "prerequisite_fit": 0.15,
    "difficulty_fit": 0.10,
    "learning_pref_fit": 0.10,
    "time_fit": 0.10,
    "user_feedback_adjustment": 0.05,
}

assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "Weights must sum to 1"

ItemType = Literal["course", "project"]


@dataclass
class ItemInput:
    """Descriptor for a course or project to be scored."""
    id: str
    item_type: ItemType
    title: str
    skills: list[str]                   # skill_ids taught / practiced
    difficulty: int                     # 1–5
    duration_hours: int
    level: str = "intermediate"         # beginner / intermediate / advanced
    prerequisites: list[str] = field(default_factory=list)  # course prereq ids


@dataclass
class ScoreBreakdown:
    skill_gap_match: float
    goal_relevance: float
    prerequisite_fit: float
    difficulty_fit: float
    learning_pref_fit: float
    time_fit: float
    user_feedback_adjustment: float
    total: float


@dataclass
class RankedItem:
    rank: int
    id: str
    item_type: ItemType
    title: str
    total_score: float
    breakdown: ScoreBreakdown


# ── Individual factor calculators ─────────────────────────────────────────────

def _skill_gap_match(
    item_skills: list[str],
    gap_skill_ids: list[str],       # skills the learner still needs
    gap_sizes: dict[str, float],    # skill_id -> gap_size (0–1)
) -> float:
    """How directly does this item address the learner's gaps?"""
    if not item_skills or not gap_skill_ids:
        return 0.0
    gap_set = set(gap_skill_ids)
    matching = [s for s in item_skills if s in gap_set]
    if not matching:
        return 0.0
    # Weight each match by its gap size so high-priority gaps score more
    total_gap = sum(gap_sizes.get(s, 0.5) for s in matching)
    max_possible = sum(sorted(gap_sizes.values(), reverse=True)[: len(item_skills)])
    if max_possible == 0:
        return len(matching) / len(item_skills)
    return min(1.0, total_gap / max(max_possible, 1.0))


def _goal_relevance(
    item_skills: list[str],
    role_skill_ids: set[str],       # all skills needed for target career
) -> float:
    """Fraction of item skills that are relevant to the target career."""
    if not item_skills:
        return 0.0
    relevant = sum(1 for s in item_skills if s in role_skill_ids)
    return relevant / len(item_skills)


def _prerequisite_fit(
    item_prereqs: list[str],         # course prerequisite course-ids
    completed_item_ids: set[str],    # course/project ids already done
) -> float:
    """
    1.0  → all prerequisites met (or none required)
    0.5  → some missing
    0.0  → no prerequisites met at all
    """
    if not item_prereqs:
        return 1.0
    met = sum(1 for p in item_prereqs if p in completed_item_ids)
    return met / len(item_prereqs)


def _difficulty_fit(
    item_difficulty: int,   # 1–5
    experience_level: str,  # student / entry / mid / senior
) -> float:
    """Score is highest when difficulty matches experience."""
    level_map = {"student": 1.5, "entry": 2.0, "mid": 3.0, "senior": 4.5}
    target = level_map.get(experience_level, 2.5)
    distance = abs(item_difficulty - target)
    # Max distance is 4 (1 vs 5); map 0→1.0, 4→0.0 linearly
    return max(0.0, 1.0 - distance / 4.0)


def _learning_pref_fit(
    item_type: ItemType,
    learning_style: str,    # visual / hands_on / reading / mixed
) -> float:
    """Simple preference alignment."""
    mapping: dict[str, dict[ItemType, float]] = {
        "hands_on": {"project": 1.0, "course": 0.5},
        "visual":   {"course": 0.9, "project": 0.7},
        "reading":  {"course": 1.0, "project": 0.5},
        "mixed":    {"course": 0.75, "project": 0.75},
    }
    return mapping.get(learning_style, {}).get(item_type, 0.7)


def _time_fit(
    item_duration_hours: int,
    available_hours_per_week: float,
    timeline_weeks: int,
) -> float:
    """
    Prefer items whose duration fits within a reasonable portion of remaining
    time.  Items that take >50 % of the total remaining hours score lower.
    """
    total_available = available_hours_per_week * timeline_weeks
    if total_available <= 0:
        return 0.5
    ratio = item_duration_hours / total_available
    if ratio <= 0.1:
        return 1.0
    if ratio <= 0.3:
        return 0.8
    if ratio <= 0.5:
        return 0.6
    return max(0.1, 1.0 - ratio)


def _feedback_adjustment(
    item_id: str,
    user_feedback: dict[str, float],  # item_id -> [-1, +1] cumulative rating
) -> float:
    """Map stored [-1, +1] rating to [0, 1] additive factor."""
    raw = user_feedback.get(item_id, 0.0)
    return (raw + 1.0) / 2.0


# ── Main scoring function ─────────────────────────────────────────────────────

def score_items(
    items: list[ItemInput],
    gap_skill_ids: list[str],
    gap_sizes: dict[str, float],
    role_skill_ids: set[str],
    completed_item_ids: set[str],
    experience_level: str,
    learning_style: str,
    available_hours_per_week: float,
    timeline_weeks: int,
    user_feedback: dict[str, float] | None = None,
    top_n: int = 10,
) -> list[RankedItem]:
    """
    Score and rank all items; return top_n results.

    All inputs are plain Python values — no DB sessions required.
    """
    feedback = user_feedback or {}
    results: list[tuple[float, RankedItem]] = []

    for item in items:
        sgm = _skill_gap_match(item.skills, gap_skill_ids, gap_sizes)
        gr  = _goal_relevance(item.skills, role_skill_ids)
        pf  = _prerequisite_fit(item.prerequisites, completed_item_ids)
        df  = _difficulty_fit(item.difficulty, experience_level)
        lpf = _learning_pref_fit(item.item_type, learning_style)
        tf  = _time_fit(item.duration_hours, available_hours_per_week, timeline_weeks)
        fa  = _feedback_adjustment(item.id, feedback)

        total = (
            WEIGHTS["skill_gap_match"]          * sgm
            + WEIGHTS["goal_relevance"]         * gr
            + WEIGHTS["prerequisite_fit"]       * pf
            + WEIGHTS["difficulty_fit"]         * df
            + WEIGHTS["learning_pref_fit"]      * lpf
            + WEIGHTS["time_fit"]               * tf
            + WEIGHTS["user_feedback_adjustment"] * fa
        )

        breakdown = ScoreBreakdown(
            skill_gap_match=round(sgm, 4),
            goal_relevance=round(gr, 4),
            prerequisite_fit=round(pf, 4),
            difficulty_fit=round(df, 4),
            learning_pref_fit=round(lpf, 4),
            time_fit=round(tf, 4),
            user_feedback_adjustment=round(fa, 4),
            total=round(total, 4),
        )
        results.append(
            (total, RankedItem(rank=0, id=item.id, item_type=item.item_type,
                               title=item.title, total_score=round(total, 4),
                               breakdown=breakdown))
        )

    results.sort(key=lambda x: x[0], reverse=True)
    ranked = []
    for i, (_, item_result) in enumerate(results[:top_n], start=1):
        item_result.rank = i
        ranked.append(item_result)
    return ranked
