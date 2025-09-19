from __future__ import annotations

import json
import re
from typing import Any, Dict


PROFANITY_WORDS = {
    "damn",
    "shit",
    "fuck",
}


def minimal_profanity_filter(text: str) -> str:
    """Very small profanity mask. Replace internal letters with asterisks.

    This is intentionally minimal and only for a prototype. For production,
    use a vetted content moderation system.
    """
    def mask(word: str) -> str:
        if len(word) <= 2:
            return "*" * len(word)
        return word[0] + "*" * (len(word) - 2) + word[-1]

    def repl(match: re.Match[str]) -> str:
        original = match.group(0)
        return mask(original)

    for w in PROFANITY_WORDS:
        pattern = re.compile(rf"\b{re.escape(w)}\b", flags=re.IGNORECASE)
        text = pattern.sub(repl, text)
    return text


def truncate_text(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 1)].rstrip() + "…"


def scrub_pii(text: str) -> str:
    """Naive scrubbing of PII-like patterns (emails, phone numbers).

    This is minimal and heuristic-based. For GDPR compliance, ensure data
    minimization, explicit consent, and comprehensive policies.
    """
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[email]", text)
    text = re.sub(r"\b\+?[0-9][0-9\-\s]{6,}[0-9]\b", "[phone]", text)
    return text


def safe_clean_output(text: str, max_chars: int = 500) -> str:
    # Strip leading stub/debug prefixes (e.g., "[Gemini STUB] ... -> Example caption:") if present
    text = re.sub(r"^\[[^\]]+\]\s*", "", text).strip()
    text = re.sub(r"\s*->\s*Example caption:\s*", "", text, flags=re.IGNORECASE)
    text = scrub_pii(text)
    text = minimal_profanity_filter(text)
    text = truncate_text(text, max_chars=max_chars)
    return text


def to_json(data: Dict[str, Any], pretty: bool = True) -> str:
    if pretty:
        return json.dumps(data, ensure_ascii=False, indent=2)
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


