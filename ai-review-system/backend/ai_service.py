import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

SYSTEM_PROMPT = "You are writing a response for a real estate business."


def _fallback_initial_response(review: str, tone: str) -> str:
    return (
        "Thank you for your feedback. We truly appreciate you taking the time to share your experience with us. "
        f"Your review was: \"{review[:220]}\". "
        f"We are committed to delivering excellent service, and we value your support. (tone: {tone})"
    )


def _fallback_revision_response(review: str, previous_response: str, notes: str) -> str:
    return (
        "Thank you for your review. We appreciate your feedback and support. "
        f"We have updated our response based on your notes: \"{notes[:200]}\". "
        "We remain committed to providing excellent service."
    )


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


def generate_response(review: str, tone: str) -> str:
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Review:\n{review}\n\n"
        f"Tone:\n{tone}\n\n"
        "Write a professional response thanking the reviewer."
    )

    try:
        return _call_gemini(prompt)
    except Exception:
        return _fallback_initial_response(review, tone)


def revise_response(review: str, previous_response: str, notes: str, tone: str) -> str:
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Original Review:\n{review}\n\n"
        f"Previous Response:\n{previous_response}\n\n"
        f"Revision Notes:\n{notes}\n\n"
        f"Keep the response tone: {tone}.\n"
        "Rewrite the response considering the notes."
    )

    try:
        return _call_gemini(prompt)
    except Exception:
        return _fallback_revision_response(review, previous_response, notes)
