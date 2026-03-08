import os
import json
import re
import logging
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv()
logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
DEFAULT_BUSINESS_CONTEXT = "You are writing responses for a real estate business."


def _read_prompt_template(filename: str) -> str:
    template_path = PROMPTS_DIR / filename
    if not template_path.exists():
        raise RuntimeError(f"Prompt template not found: {template_path}")
    return template_path.read_text(encoding="utf-8")


def _render_prompt(template_name: str, **kwargs) -> str:
    template = _read_prompt_template(template_name)
    return template.format(**kwargs)


def _format_previous_versions(previous_versions: list[dict]) -> str:
    if not previous_versions:
        return "No previous versions available."

    chunks = []
    for item in previous_versions:
        version = item.get("version", "?")
        response_text = item.get("response_text", "")
        context = item.get("context") or "none"
        chunks.append(
            f"Version {version}:\n"
            f"generated response: {response_text}\n"
            f"context or notes: {context}"
        )
    return "\n\n".join(chunks)


def _extract_json_object(raw_text: str) -> dict:
    text = raw_text.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    if text.lower().startswith("json"):
        text = text[4:].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", raw_text)
        if not match:
            raise
        return json.loads(match.group(0))


def _build_fallback_post(review: str, tone: str, owner_improvement: str = "", is_revision: bool = False) -> str:
    review_has_issue = any(word in review.lower() for word in ["not", "issue", "problem", "bad", "delay", "complaint"])

    if tone == "apologetic" or review_has_issue:
        opening = "Thank you for sharing your feedback. We are sorry your experience did not fully meet expectations."
    elif tone == "friendly":
        opening = "Thank you so much for your review. We really appreciate your support and kind words."
    else:
        opening = "Thank you for your feedback and for taking the time to share your experience with us."

    if is_revision:
        if "short" in owner_improvement.lower():
            closing = "We appreciate your trust and look forward to serving you again."
        else:
            closing = "Your input helps us improve, and we remain committed to excellent service."
    else:
        closing = "We appreciate your trust and remain committed to delivering excellent service."

    return f"{opening} {closing}"


def _call_gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    client = genai.Client(api_key=api_key)
    result = client.models.generate_content(model=model_name, contents=prompt)
    text = getattr(result, "text", None)
    if not text:
        raise RuntimeError("Gemini returned an empty response")
    return text.strip()


def generate_structured_response(
    review: str,
    tone: str,
    next_version: int,
    previous_versions: list[dict] | None = None,
    owner_improvement: str = "",
) -> dict:
    previous_versions = previous_versions or []
    business_context = os.getenv("BUSINESS_CONTEXT") or DEFAULT_BUSINESS_CONTEXT

    is_revision = bool(previous_versions)
    latest_previous_text = ""
    if previous_versions:
        latest_previous_text = str(previous_versions[-1].get("response_text", "")).strip()

    prompt = _render_prompt(
        "system_prompt.md",
        business_context=business_context,
        review=review,
        previous_versions=_format_previous_versions(previous_versions),
        owner_improvement=owner_improvement or "No owner improvement notes provided.",
        tone=tone,
    )

    try:
        parsed = _extract_json_object(_call_gemini(prompt))
        business_post = str(parsed.get("business_post", "")).strip()
        out_tone = str(parsed.get("tone", tone)).strip() or tone
        if not business_post:
            business_post = _build_fallback_post(
                review=review,
                tone=out_tone,
                owner_improvement=owner_improvement,
                is_revision=is_revision,
            )
        # If revision output is identical to previous text, force a revised fallback.
        if is_revision and latest_previous_text and business_post == latest_previous_text:
            business_post = _build_fallback_post(
                review=review,
                tone=out_tone,
                owner_improvement=owner_improvement,
                is_revision=True,
            )
    except Exception:
        logger.exception("Gemini generation failed; using fallback response")
        business_post = _build_fallback_post(
            review=review,
            tone=tone,
            owner_improvement=owner_improvement,
            is_revision=is_revision,
        )
        out_tone = tone

    return {
        "version": next_version,
        "tone": out_tone,
        "business_post": business_post,
    }
