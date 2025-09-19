from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency at runtime
    load_dotenv = None  # type: ignore


@dataclass(frozen=True)
class AppConfig:
    """Application configuration loaded from environment variables.

    Environment variables:
    - GOOGLE_API_KEY
    - OPENAI_API_KEY
    - UNSPLASH_ACCESS_KEY
    - LLM_PROVIDER (default 'google')
    - LLM_MODEL (default 'gemini-1')
    """

    google_api_key: Optional[str]
    openai_api_key: Optional[str]
    unsplash_access_key: Optional[str]
    llm_provider: str
    llm_model: str


def load_config() -> AppConfig:
    """Load configuration from .env (if available) and environment variables."""
    if load_dotenv is not None:
        # Silently load .env if present
        load_dotenv()

    google_api_key = os.getenv("GOOGLE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    unsplash_access_key = os.getenv("UNSPLASH_ACCESS_KEY")
    llm_provider = os.getenv("LLM_PROVIDER", "google").strip() or "google"
    llm_model = os.getenv("LLM_MODEL", "gemini-1").strip() or "gemini-1"

    return AppConfig(
        google_api_key=google_api_key,
        openai_api_key=openai_api_key,
        unsplash_access_key=unsplash_access_key,
        llm_provider=llm_provider,
        llm_model=llm_model,
    )


