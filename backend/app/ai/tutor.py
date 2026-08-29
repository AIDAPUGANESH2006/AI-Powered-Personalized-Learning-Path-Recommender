"""
Phase 8 — AI Tutor chat.

Every system prompt includes the learner's current profile, skill levels, and
roadmap position so answers are grounded in their actual data.
"""
from __future__ import annotations

from app.config import settings

_BASE_SYSTEM = """\
You are PathWise AI Tutor — a knowledgeable, supportive learning coach.
You answer questions about the learner's personalised roadmap, explain why
specific courses or skills matter for their goals, and provide study guidance.

RULES:
1. Ground every answer in the learner's profile data provided below.
2. Be concise (2–4 sentences unless depth is explicitly asked for).
3. Never invent course titles or claim specific job outcomes.
4. If asked something outside the learner's roadmap, politely redirect.
5. You may suggest skipping a topic only if the learner clearly already has it.
"""


def build_system_prompt(learner_context: dict, roadmap_snapshot: dict | None) -> str:
    """
    Build the system prompt by injecting the learner's live data.

    learner_context keys:
      goal, target_career_role, experience_level, hours_per_week,
      timeline_months, top_skill_gaps (list[str]),
      current_skill_levels (dict[str, float])

    roadmap_snapshot keys (optional):
      current_item_title, current_item_type, next_item_title,
      completed_count, total_items, career_readiness_pct
    """
    lines = [_BASE_SYSTEM, "\n--- LEARNER PROFILE ---"]
    lines.append(f"Goal: {learner_context.get('goal', 'not specified')}")
    lines.append(f"Target role: {learner_context.get('target_career_role', 'not specified')}")
    lines.append(f"Experience: {learner_context.get('experience_level', 'not specified')}")
    lines.append(f"Timeline: {learner_context.get('timeline_months', '?')} months")
    lines.append(f"Hours/week: {learner_context.get('hours_per_week', '?')}")

    gaps = learner_context.get("top_skill_gaps", [])
    if gaps:
        lines.append(f"Top skill gaps: {', '.join(gaps[:6])}")

    levels = learner_context.get("current_skill_levels", {})
    if levels:
        skill_str = ", ".join(
            f"{k}={round(v*100)}%" for k, v in list(levels.items())[:8]
        )
        lines.append(f"Current skill levels: {skill_str}")

    if roadmap_snapshot:
        lines.append("\n--- CURRENT ROADMAP POSITION ---")
        lines.append(
            f"Now studying: {roadmap_snapshot.get('current_item_title', 'not started')}"
        )
        next_t = roadmap_snapshot.get("next_item_title")
        if next_t:
            lines.append(f"Next up: {next_t}")
        comp = roadmap_snapshot.get("completed_count", 0)
        total = roadmap_snapshot.get("total_items", "?")
        lines.append(f"Progress: {comp}/{total} items complete")
        readiness = roadmap_snapshot.get("career_readiness_pct")
        if readiness is not None:
            lines.append(f"Career readiness: {readiness}%")

    return "\n".join(lines)


from app.ai.gemini_client import call_gemini, get_gemini_api_key

def chat(
    messages: list[dict],
    learner_context: dict,
    roadmap_snapshot: dict | None = None,
) -> str:
    """
    Send a chat message to the tutor.

    messages: list of {"role": "user"|"assistant", "content": str}
              — the full conversation history (latest message last).
    Returns the assistant's reply as a plain string.
    """
    system_prompt = build_system_prompt(learner_context, roadmap_snapshot)

    # 1. Google Gemini (Free & native)
    if get_gemini_api_key():
        try:
            gemini_reply = call_gemini(
                messages=messages,
                system_instruction=system_prompt,
                temperature=0.5,
                max_tokens=600,
            )
            if gemini_reply:
                return gemini_reply
        except Exception:
            pass

    # 2. OpenAI
    if settings.openai_api_key and not (
        settings.openai_api_key.startswith("AQ.") or settings.openai_api_key.startswith("AIzaSy")
    ):
        try:
            from openai import OpenAI  # type: ignore
            client = OpenAI(api_key=settings.openai_api_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": system_prompt}] + messages,
                temperature=0.5,
                max_tokens=600,
            )
            return resp.choices[0].message.content or "No response from LLM."
        except Exception:
            pass

    # 3. Anthropic
    if settings.anthropic_api_key:
        try:
            import anthropic  # type: ignore
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            resp = client.messages.create(
                model="claude-3-haiku-20240307",
                system=system_prompt,
                messages=messages,
                max_tokens=600,
            )
            return resp.content[0].text if resp.content else "No response from LLM."
        except Exception:
            pass

    # Fallback when offline or error
    last = messages[-1]["content"] if messages else ""
    return (
        f"(AI Tutor is offline — add GEMINI_API_KEY or OPENAI_API_KEY to .env)\n\n"
        f"Your question: \"{last}\"\n\n"
        f"Based on your profile I can see you're working towards "
        f"{learner_context.get('target_career_role', 'your goal')}. "
        f"Once the AI key is configured I'll give you a personalised answer."
    )

