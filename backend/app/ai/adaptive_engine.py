"""
Phase 9 — Adaptive Engine.

After an assessment result is recorded:
  score < threshold → insert a reinforcement module before the next locked
                      phase and keep that phase locked.
  score ≥ threshold → unlock the next locked item immediately.

Works on the in-memory Roadmap dataclass; the caller is responsible for
persisting the updated path_items to the database.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from app.ai.roadmap_generator import Roadmap, RoadmapItem


@dataclass
class AdaptationResult:
    action: str          # "reinforcement_inserted" | "phase_unlocked" | "no_change"
    message: str         # human-readable message shown to the learner
    roadmap: Roadmap     # updated (possibly mutated) roadmap


def apply_assessment_result(
    roadmap: Roadmap,
    assessment_id: str,
    score: float,
    pass_threshold: float,
    reinforcement_item: RoadmapItem | None = None,
) -> AdaptationResult:
    """
    Mutate the roadmap in response to an assessment score.

    Args:
        roadmap: the learner's current Roadmap (will be deep-copied internally).
        assessment_id: the assessment that was just completed.
        score: raw score 0.0–1.0.
        pass_threshold: minimum passing fraction (e.g. 0.6).
        reinforcement_item: a pre-built RoadmapItem to insert on failure.
                            If None and score < threshold, only a warning is returned.
    """
    roadmap = deepcopy(roadmap)

    # Mark the assessment itself as complete
    for item in roadmap.items:
        if item.item_id == assessment_id and item.item_type == "assessment":
            item.status = "complete"
            break

    # Find the next locked item after the assessment
    assessment_idx = next(
        (i for i, it in enumerate(roadmap.items) if it.item_id == assessment_id),
        None,
    )
    next_locked_idx: int | None = None
    if assessment_idx is not None:
        for i in range(assessment_idx + 1, len(roadmap.items)):
            if roadmap.items[i].status == "locked":
                next_locked_idx = i
                break

    passed = score >= pass_threshold
    pct = round(score * 100)
    threshold_pct = round(pass_threshold * 100)

    if passed:
        # Unlock the next item
        if next_locked_idx is not None:
            roadmap.items[next_locked_idx].status = "active"
            unlocked_title = roadmap.items[next_locked_idx].title
            _reindex(roadmap)
            return AdaptationResult(
                action="phase_unlocked",
                message=(
                    f"Great work — you scored {pct}% (threshold {threshold_pct}%). "
                    f'"{unlocked_title}" is now unlocked.'
                ),
                roadmap=roadmap,
            )
        _reindex(roadmap)
        return AdaptationResult(
            action="no_change",
            message=f"You scored {pct}% — all remaining items are already unlocked.",
            roadmap=roadmap,
        )
    else:
        # Insert reinforcement before the next locked item
        if reinforcement_item is not None and next_locked_idx is not None:
            reinforcement_item.status = "active"
            roadmap.items.insert(next_locked_idx, reinforcement_item)
            locked_title = roadmap.items[next_locked_idx + 1].title
            _reindex(roadmap)
            return AdaptationResult(
                action="reinforcement_inserted",
                message=(
                    f"You scored {pct}% (threshold {threshold_pct}%). "
                    f'A reinforcement module has been added before '
                    f'"{locked_title}" to help you strengthen the foundations.'
                ),
                roadmap=roadmap,
            )
        _reindex(roadmap)
        return AdaptationResult(
            action="reinforcement_inserted",
            message=(
                f"You scored {pct}% (threshold {threshold_pct}%). "
                f"We recommend revisiting the material before moving on — "
                f"the next phase remains locked until you're ready."
            ),
            roadmap=roadmap,
        )


def _reindex(roadmap: Roadmap) -> None:
    """Re-assign order_index after insertions."""
    for i, item in enumerate(roadmap.items):
        item.order_index = i
