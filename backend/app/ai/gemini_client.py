"""Google Gemini LLM client supporting official SDK and REST API."""
from __future__ import annotations

import logging
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GEMINI_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-flash-latest",
]


def get_gemini_api_key() -> str | None:
    """Return Gemini/Google API key from config or environment."""
    if settings.gemini_api_key:
        return settings.gemini_api_key.strip()
    if settings.google_api_key:
        return settings.google_api_key.strip()
    # If user put Gemini key into OPENAI_API_KEY field
    if settings.openai_api_key and (
        settings.openai_api_key.startswith("AQ.")
        or settings.openai_api_key.startswith("AIzaSy")
    ):
        return settings.openai_api_key.strip()
    return None


def call_gemini(
    messages: list[dict],
    system_instruction: str | None = None,
    temperature: float = 0.4,
    max_tokens: int = 800,
) -> str | None:
    """
    Send messages to Google Gemini API.

    messages: list of {"role": "user"|"assistant", "content": str}
    system_instruction: optional system prompt
    """
    api_key = get_gemini_api_key()
    if not api_key:
        return None

    # 1. Try official google-genai SDK first
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        for model in GEMINI_MODELS:
            try:
                # Format contents for SDK
                contents = []
                for m in messages:
                    role = "user" if m.get("role") == "user" else "model"
                    contents.append(
                        types.Content(
                            role=role,
                            parts=[types.Part.from_text(text=m.get("content", ""))]
                        )
                    )

                config = types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    system_instruction=system_instruction,
                )

                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
                if response.text:
                    return response.text.strip()
            except Exception as model_err:
                logger.debug("SDK call failed for model %s: %s", model, model_err)
                continue
    except Exception as sdk_err:
        logger.debug("google-genai SDK init failed: %s", sdk_err)

    # 2. REST API fallback
    contents = []
    for m in messages:
        role = "user" if m.get("role") == "user" else "model"
        text = m.get("content", "")
        if text:
            contents.append({
                "role": role,
                "parts": [{"text": text}],
            })

    if not contents:
        return None

    payload: dict = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }

    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }

    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }

    for model in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        try:
            with httpx.Client(timeout=12.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            return parts[0]["text"].strip()
                elif resp.status_code == 404:
                    continue
                else:
                    logger.warning("Gemini REST error %s: %s", resp.status_code, resp.text[:200])
        except Exception as exc:
            logger.warning("Gemini REST request failed for model %s: %s", model, exc)
            continue

    return None
