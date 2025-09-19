from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
import re

from .llm_adapters import LLMAdapter
from .image_fetcher import ImageFetcher, ImageResult
from .utils import safe_clean_output


POST_TEMPLATE = (
    "You are a creative social media copywriter. Write a short engaging post for: '{topic}'. "
    "Keep it under 220 characters, add 2-3 relevant hashtags, and a positive CTA."
)


@dataclass
class GeneratorResult:
    topic: str
    variants: List[Dict[str, Optional[str]]]


def build_prompt(topic: str) -> str:
    return POST_TEMPLATE.format(topic=topic.strip())


def generate_posts(
    topic: str,
    variants: int,
    llm: LLMAdapter,
    image_fetcher: ImageFetcher,
    open_links: bool = False,
) -> GeneratorResult:
    results: List[Dict[str, Optional[str]]] = []
    seen_texts: Set[str] = set()

    def normalize_for_uniqueness(text: str) -> str:
        # Remove common stub prefixes like "[Gemini STUB]" for fair deduping
        cleaned = re.sub(r"^\[[^\]]+\]\s*", "", text).strip().lower()
        # Collapse whitespace
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned

    style_cues = [
        "upbeat and witty tone",
        "informative and value-focused tone",
        "playful with emoji",
        "urgent, limited-time offer tone",
        "community-focused, inclusive tone",
        "minimalist, sleek tone",
        "friendly conversational tone",
        "trend-savvy, Gen Z tone",
        "professional, concise tone",
        "storytelling hook in first sentence",
    ]

    def diversify_prompt(topic: str, idx: int, attempt: int) -> str:
        cue = style_cues[idx % len(style_cues)]
        # Add light diversification across attempts as well
        alt = [
            "vary hashtags and CTA",
            "avoid repeating earlier wording",
            "use a different angle or benefit",
            "use different emoji (max 2)",
        ][attempt % 4]
        base = (
            "You are a creative social media copywriter. "
            f"Write a short, unique post about: '{topic.strip()}'. "
            f"Use {cue}; {alt}. Keep it under 220 characters, include 2-3 relevant hashtags, and a positive CTA."
        )
        return base

    # Derive an image query from topic (simple heuristic) and fetch a pool of images once
    image_query = topic
    requested_images = max(1, variants)
    image_pool: List[ImageResult] = image_fetcher.search(image_query, limit=requested_images, open_links=open_links)

    total_images = len(image_pool)

    for idx in range(max(1, variants)):
        # Try up to a few times to obtain a unique variant
        text: str = ""
        for attempt in range(4):
            prompt = diversify_prompt(topic, idx, attempt)
            raw = llm.generate_text(prompt, max_tokens=140)
            candidate = safe_clean_output(raw, max_chars=220)
            norm = normalize_for_uniqueness(candidate)
            if norm and norm not in seen_texts:
                text = candidate
                seen_texts.add(norm)
                break
        if not text:
            # Last-resort diversification: append a subtle variant tag to ensure difference
            fallback = safe_clean_output(llm.generate_text(build_prompt(topic), max_tokens=120), max_chars=210)
            text = f"{fallback} #{idx+1}"
            # don't add to seen_texts yet; we'll run a final uniqueness guard below

        # Assign a distinct image per variant when available; otherwise, fall back or cycle
        if total_images > 0:
            image_choice = image_pool[idx % total_images]
            image_url = image_choice.url
            image_query_out = image_choice.query
        else:
            image_url = None
            image_query_out = image_query

        # Final guard: ensure uniqueness even if the model returned identical text across attempts
        # This avoids duplicate captions when using stub providers.
        norm_text = normalize_for_uniqueness(text)
        if norm_text in seen_texts:
            # Append a short variant tag tied to index until unique
            # Use a bounded number of attempts to prevent infinite loops
            for k in range(1, 5):
                candidate_text = f"{text} · v{idx+1}" if k == 1 else f"{text} · v{idx+1}.{k}"
                norm_candidate = normalize_for_uniqueness(candidate_text)
                if norm_candidate not in seen_texts:
                    text = candidate_text
                    norm_text = norm_candidate
                    break
        seen_texts.add(norm_text)

        results.append({
            "text": text,
            "image_query": image_query_out,
            "image_url": image_url,
        })

    return GeneratorResult(topic=topic, variants=results)


