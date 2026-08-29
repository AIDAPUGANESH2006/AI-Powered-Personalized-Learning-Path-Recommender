"""
Phase 7 — Free-text profile extraction via LLM + Pydantic validation.

Calls the LLM once to extract structured JSON from natural language input.
On parse failure, retries once with an error-correction prompt.
Falls back gracefully if the API key is missing.
"""
from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field, ValidationError

from app.config import settings

# ── Output schema ─────────────────────────────────────────────────────────────

class SkillEntry(BaseModel):
    name: str
    level: float = Field(ge=0.0, le=1.0, description="0 = beginner, 1 = expert")


class ExtractedProfile(BaseModel):
    education: str | None = None
    experience_level: str | None = None          # student/entry/mid/senior
    skills: list[SkillEntry] = Field(default_factory=list)
    goal: str | None = None
    timeline_months: int | None = Field(default=None, ge=1, le=120)
    target_career_role: str | None = None        # natural language, e.g. "AI engineer"


# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM = """\
You are a career profiling assistant. Extract structured information from the
user's free-text description and return ONLY valid JSON that matches this schema:

{
  "education": "<string or null>",
  "experience_level": "<student|entry|mid|senior or null>",
  "skills": [{"name": "<string>", "level": <0.0-1.0>}],
  "goal": "<string or null>",
  "timeline_months": <integer 1-120 or null>,
  "target_career_role": "<string or null>"
}

Rules:
- Return ONLY the JSON object, no markdown fences, no commentary.
- Infer skill level from context: "know Python" → 0.5, "expert in Python" → 0.9,
  "heard of" → 0.1. Default to 0.4 when level is unclear.
- experience_level: choose one of student/entry/mid/senior from context clues.
- timeline_months: convert "6 months" → 6, "a year" → 12, "8 months" → 8.
"""

_CORRECTION = """\
Your previous response could not be parsed as valid JSON.
Error: {error}
Previous response: {previous}

Return ONLY a valid JSON object matching the schema above. No markdown, no prose.
"""


from app.ai.gemini_client import call_gemini, get_gemini_api_key

# ── LLM call ─────────────────────────────────────────────────────────────────

def _call_llm(messages: list[dict]) -> str:
    """Call configured LLM (Gemini, OpenAI, or Anthropic). Returns raw string."""
    # 1. Google Gemini
    if get_gemini_api_key():
        system_text = next(
            (m["content"] for m in messages if m.get("role") == "system"), ""
        )
        user_msgs = [m for m in messages if m.get("role") != "system"]
        res = call_gemini(
            messages=user_msgs,
            system_instruction=system_text,
            temperature=0.0,
            max_tokens=512,
        )
        if res:
            return res

    # 2. OpenAI
    if settings.openai_api_key and not (
        settings.openai_api_key.startswith("AQ.") or settings.openai_api_key.startswith("AIzaSy")
    ):
        from openai import OpenAI  # type: ignore
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.0,
            max_tokens=512,
        )
        return response.choices[0].message.content or ""

    # 3. Anthropic
    if settings.anthropic_api_key:
        import anthropic  # type: ignore
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        system_text = next(
            (m["content"] for m in messages if m["role"] == "system"), ""
        )
        user_msgs = [m for m in messages if m["role"] != "system"]
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            system=system_text,
            messages=user_msgs,
            max_tokens=512,
        )
        return response.content[0].text if response.content else ""

    raise RuntimeError(
        "No LLM API key configured. Set GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY."
    )


def _parse_json_from_text(text: str) -> dict:
    """Strip markdown fences if present, then parse JSON."""
    clean = re.sub(r"^```[a-z]*\n?", "", text.strip(), flags=re.IGNORECASE)
    clean = re.sub(r"\n?```$", "", clean.strip())
    return json.loads(clean)


def _heuristic_extract_profile(text: str) -> ExtractedProfile:
    """Deterministic heuristic extraction when LLM API key is not present."""
    lower = text.lower()
    
    # Experience level
    exp = None
    if any(w in lower for w in ["student", "college", "university", "undergrad", "3rd year", "4th year", "2nd year", "1st year", "btech", "b.tech", "cse"]):
        exp = "student"
    elif any(w in lower for w in ["junior", "entry", "beginner", "fresher", "graduate"]):
        exp = "entry"
    elif any(w in lower for w in ["senior", "lead", "architect", "5+ years", "10 years"]):
        exp = "senior"
    elif any(w in lower for w in ["mid", "intermediate", "2 years", "3 years"]):
        exp = "mid"

    # Timeline months
    timeline = None
    m = re.search(r'(\d+)\s*(?:months?|mo)', lower)
    if m:
        timeline = int(m.group(1))
    elif "year" in lower:
        m2 = re.search(r'(\d+)\s*(?:years?|yr)', lower)
        if m2:
            timeline = int(m2.group(1)) * 12
        else:
            timeline = 12

    # Target career role
    role = None
    if any(k in lower for k in ["ai", "machine learning", "ml", "deep learning", "llm", "artificial intelligence"]):
        role = "AI/ML Engineer"
    elif any(k in lower for k in ["data scientist", "data science"]):
        role = "Data Scientist"
    elif any(k in lower for k in ["data analyst", "data analysis", "bi analyst", "analytics"]):
        role = "Data Analyst"
    elif any(k in lower for k in ["full stack", "fullstack", "frontend", "backend", "web dev"]):
        role = "Full Stack Developer"
    elif any(k in lower for k in ["cloud", "aws", "azure", "gcp"]):
        role = "Cloud Engineer"
    elif any(k in lower for k in ["devops", "sre", "ci/cd"]):
        role = "DevOps Engineer"
    elif any(k in lower for k in ["cyber", "security", "infosec"]):
        role = "Cybersecurity Engineer"
    elif any(k in lower for k in ["software engineer", "software developer", "swe"]):
        role = "Software Engineer"

    # Skills detection with common aliases
    skill_keywords: dict[str, str] = {
        "python": "Python",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "react": "React",
        "node": "Node.js",
        "sql": "SQL",
        "machine learning": "Machine Learning",
        "ml": "Machine Learning",
        "deep learning": "Deep Learning",
        "statistics": "Statistics",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "aws": "AWS",
        "git": "Git",
        "linux": "Linux",
        "java": "Java",
        "c++": "C++",
        "pytorch": "PyTorch",
        "tensorflow": "TensorFlow",
        "fastapi": "FastAPI",
        "django": "Django",
        "data analysis": "Data Analysis",
        "linear algebra": "Linear Algebra",
        "nlp": "Natural Language Processing",
        "transformers": "Transformers",
    }
    
    extracted_skills: list[SkillEntry] = []
    seen_names: set[str] = set()
    for kw, display_name in skill_keywords.items():
        if re.search(r'\b' + re.escape(kw) + r'\b', lower):
            if display_name in seen_names:
                continue
            seen_names.add(display_name)
            lvl = 0.5
            if any(f"{kw} {adv}" in lower or f"{adv} in {kw}" in lower or f"{adv} {kw}" in lower for adv in ["expert", "advanced", "pro", "master"]):
                lvl = 0.8
            elif any(f"{kw} {bg}" in lower or f"{bg} in {kw}" in lower or f"{bg} {kw}" in lower for bg in ["basic", "beginner", "heard of", "learning", "starter"]):
                lvl = 0.2
            extracted_skills.append(SkillEntry(name=display_name, level=lvl))

    return ExtractedProfile(
        education="Computer Science / Engineering" if any(w in lower for w in ["cse", "cs", "computer science", "btech", "engineering"]) else None,
        experience_level=exp or "entry",
        skills=extracted_skills,
        goal=text.strip()[:150],
        timeline_months=timeline or 6,
        target_career_role=role or "AI/ML Engineer",
    )


# ── Public API ────────────────────────────────────────────────────────────────

def extract_profile(free_text: str) -> ExtractedProfile:
    """
    Parse free-text learner input into a structured ExtractedProfile.

    Uses LLM when API keys are available, falling back gracefully to heuristic parsing.
    """
    if not (get_gemini_api_key() or settings.openai_api_key or settings.anthropic_api_key):
        return _heuristic_extract_profile(free_text)

    messages: list[dict] = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": free_text},
    ]

    try:
        raw = _call_llm(messages)
    except Exception:
        return _heuristic_extract_profile(free_text)

    error_msg: str | None = None

    # First attempt
    try:
        data = _parse_json_from_text(raw)
        return ExtractedProfile(**data)
    except (json.JSONDecodeError, ValidationError, TypeError) as exc:
        error_msg = str(exc)

    # Retry with correction prompt
    correction_messages = messages + [
        {"role": "assistant", "content": raw},
        {
            "role": "user",
            "content": _CORRECTION.format(error=error_msg, previous=raw),
        },
    ]
    try:
        raw2 = _call_llm(correction_messages)
        data2 = _parse_json_from_text(raw2)
        return ExtractedProfile(**data2)
    except Exception:
        return _heuristic_extract_profile(free_text)
