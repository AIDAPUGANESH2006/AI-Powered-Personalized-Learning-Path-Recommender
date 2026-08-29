"""
Phase 8 — Explainability layer.

explain_recommendation() generates a natural-language "Why this?" paragraph
that cites the learner's ACTUAL profile numbers — not generic advice.

explain_roadmap() produces an overview of the full roadmap plan.
"""
from __future__ import annotations

from app.ai.recommender import ScoreBreakdown
from app.config import settings


from app.ai.gemini_client import call_gemini, get_gemini_api_key

# ── LLM helper (reuse pattern from profile_extractor) ────────────────────────

def _call_llm(system: str, user: str) -> str | None:
    if get_gemini_api_key():
        try:
            res = call_gemini(
                messages=[{"role": "user", "content": user}],
                system_instruction=system,
                temperature=0.3,
                max_tokens=300,
            )
            if res:
                return res
        except Exception:
            pass

    if settings.openai_api_key and not (
        settings.openai_api_key.startswith("AQ.") or settings.openai_api_key.startswith("AIzaSy")
    ):
        try:
            from openai import OpenAI  # type: ignore
            client = OpenAI(api_key=settings.openai_api_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.3,
                max_tokens=300,
            )
            return resp.choices[0].message.content or ""
        except Exception:
            pass

    if settings.anthropic_api_key:
        try:
            import anthropic  # type: ignore
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            resp = client.messages.create(
                model="claude-3-haiku-20240307",
                system=system,
                messages=[{"role": "user", "content": user}],
                max_tokens=300,
            )
            return resp.content[0].text if resp.content else ""
        except Exception:
            pass

    # No API key — return None to fall back to rule-based explanation
    return None


# ── Rule-based fallback (works without any API key) ──────────────────────────

def _rule_based_explanation(
    item_title: str,
    breakdown: ScoreBreakdown,
    learner_context: dict,
) -> str:
    """
    Generate a transparent explanation from the score breakdown numbers alone,
    no LLM required.
    """
    lines: list[str] = [f'We recommend "{item_title}" because:']

    sgm_pct = round(breakdown.skill_gap_match * 100)
    if sgm_pct >= 50:
        lines.append(
            f"• It directly addresses your biggest skill gaps "
            f"(skill-gap match: {sgm_pct}%)."
        )

    gr_pct = round(breakdown.goal_relevance * 100)
    role = learner_context.get("target_career_role", "your target role")
    if gr_pct >= 60:
        lines.append(
            f"• {gr_pct}% of its content is relevant to {role}."
        )

    pf_pct = round(breakdown.prerequisite_fit * 100)
    if pf_pct == 100:
        lines.append("• You have all the prerequisites — you can start it right now.")
    elif pf_pct >= 50:
        lines.append(
            f"• You meet {pf_pct}% of the prerequisites, "
            f"making it achievable with a small bridge step."
        )

    df_pct = round(breakdown.difficulty_fit * 100)
    exp = learner_context.get("experience_level", "your current level")
    if df_pct >= 70:
        lines.append(f"• The difficulty is well-matched to {exp} (fit: {df_pct}%).")

    tf_pct = round(breakdown.time_fit * 100)
    hrs = learner_context.get("hours_per_week", "your available time")
    if tf_pct >= 70:
        lines.append(
            f"• At {hrs} h/wk it fits comfortably within your timeline "
            f"(time fit: {tf_pct}%)."
        )

    if len(lines) == 1:
        lines.append(
            f"• Overall recommendation score: {round(breakdown.total * 100)}%."
        )

    return " ".join(lines) if len(lines) == 1 else "\n".join(lines)


# ── Public API ────────────────────────────────────────────────────────────────

_EXPLAIN_SYSTEM = """\
You are PathWise AI's explanation engine. Given a recommendation and the
learner's profile data, write a concise 2–3 sentence explanation of WHY this
item is recommended. Always cite specific numbers from the provided data.
Never make up facts. Be direct and encouraging. No bullet points.
"""


def explain_recommendation(
    item_title: str,
    item_type: str,
    breakdown: ScoreBreakdown,
    learner_context: dict,
) -> str:
    """
    Returns a natural-language explanation string.
    Uses high-speed rule-based calculation for instant scoring transparency.
    """
    return _rule_based_explanation(item_title, breakdown, learner_context)


_ROADMAP_SYSTEM = """\
You are PathWise AI's roadmap narrator. Given a structured learning plan,
write a motivating 3–4 sentence overview that explains the plan's logic,
references the learner's goal and timeline, and highlights the key milestone
they should focus on first. Be concise and specific — no generic advice.
"""


def explain_roadmap(
    roadmap_summary: dict,
    learner_context: dict,
) -> str:
    """
    roadmap_summary: {total_weeks, pacing_mode, phase_count, first_item_title}
    learner_context: {goal, target_career_role, timeline_months, hours_per_week}
    """
    llm_result = _call_llm(
        _ROADMAP_SYSTEM,
        f"""
Roadmap summary:
  Total weeks: {roadmap_summary.get('total_weeks')}
  Pacing: {roadmap_summary.get('pacing_mode')}
  Number of phases: {roadmap_summary.get('phase_count')}
  First milestone: "{roadmap_summary.get('first_item_title')}"

Learner context:
  Goal: {learner_context.get('goal', 'not specified')}
  Target role: {learner_context.get('target_career_role', 'not specified')}
  Timeline: {learner_context.get('timeline_months')} months
  Hours/week: {learner_context.get('hours_per_week')}

Write the roadmap overview now.
""",
    )
    if llm_result:
        return llm_result.strip()

    # Fallback
    mode = roadmap_summary.get("pacing_mode", "balanced")
    weeks = roadmap_summary.get("total_weeks", "?")
    first = roadmap_summary.get("first_item_title", "the first course")
    role = learner_context.get("target_career_role", "your goal")
    return (
        f"Your personalised roadmap to {role} spans {weeks} weeks on a {mode} schedule. "
        f"Start with '{first}' — it closes your most critical skill gaps and unlocks "
        f"everything downstream. Complete each assessment before moving on; the system "
        f"will adapt your plan based on your results."
    )
