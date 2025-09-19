from __future__ import annotations

"""
Streamlit frontend for VibeWriter.

This app integrates with existing backend modules:
- generator.generate_posts
- llm_adapters.build_adapter
- image_fetcher.UnsplashFetcher, image_fetcher.SuggestionFetcher
- utils.to_json

Features:
- Topic input, model/provider selection
- API keys via inputs or environment
- Image bank selection (Unsplash or Suggestion)
- Variant count selection
- JSON output with download
- Visual cards for each generated post
"""

import json
import os
from dataclasses import asdict
from typing import Dict, Optional

import streamlit as st
from dotenv import load_dotenv

# Ensure project root is on sys.path so "src" package imports work under Streamlit
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.generator import generate_posts
from src.llm_adapters import build_adapter
from src.image_fetcher import UnsplashFetcher, SuggestionFetcher
from src.utils import to_json
from src.streamlit_ui.cards import render_post_cards


def get_env_value(key: str, fallback: str | None = None) -> Optional[str]:
    """Return environment variable value if set and non-empty, otherwise fallback."""
    value = os.getenv(key)
    if value is not None and value.strip() != "":
        return value.strip()
    return fallback


def page_config() -> None:
    st.set_page_config(
        page_title="VibeWriter",
        page_icon="🧪",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def sidebar_inputs() -> Dict[str, Optional[str]]:
    """Render sidebar controls and return a dictionary of parameters."""
    with st.sidebar:
        st.header("Controls")

        topic = st.text_input(
            label="Topic / keywords",
            value="Black Friday discount for coffee shop",
            placeholder="e.g., Summer smoothie launch",
        )

        variants = st.number_input(
            label="Variants",
            min_value=1,
            max_value=20,
            value=3,
            step=1,
        )

        provider = st.selectbox(
            label="LLM Provider",
            options=["google", "openai"],
            index=0,
            help="Default is Google Gemini (stub available without key).",
        )

        default_model = "gemini-2.0-flash" if provider == "google" else "gpt-4o-mini"
        model = st.text_input(
            label="Model",
            value=get_env_value("LLM_MODEL", default_model) or default_model,
            help="Override model name if needed.",
        )

        st.subheader("API Keys")
        google_key = st.text_input(
            label="Google Gemini API Key",
            value=get_env_value("GOOGLE_API_KEY", ""),
            type="password",
            help="Optional for stubbed Gemini; required for real calls.",
        )
        openai_key = st.text_input(
            label="OpenAI API Key",
            value=get_env_value("OPENAI_API_KEY", ""),
            type="password",
        )
        unsplash_key = st.text_input(
            label="Unsplash Access Key",
            value=get_env_value("UNSPLASH_ACCESS_KEY", ""),
            type="password",
            help="Required for Unsplash image fetching.",
        )

        image_source = st.radio(
            label="Image source",
            options=["unsplash", "suggest"],
            index=0,
            help="Unsplash requires a key; Suggestion returns queries without image URLs.",
        )

        submit = st.button("Generate Posts", type="primary")

    return {
        "topic": topic,
        "variants": int(variants),
        "provider": provider,
        "model": model,
        "google_key": google_key,
        "openai_key": openai_key,
        "unsplash_key": unsplash_key,
        "image_source": image_source,
        "submit": submit,
    }


def validate_inputs(params: Dict[str, Optional[str]]) -> Optional[str]:
    """Return an error message if inputs are invalid, else None."""
    if not params.get("topic") or params["topic"].strip() == "":
        return "Please enter a topic or keywords."
    provider = params.get("provider") or "google"
    if provider == "openai" and not (params.get("openai_key") or os.getenv("OPENAI_API_KEY")):
        return "OpenAI selected but no OpenAI API key provided."
    if params.get("image_source") == "unsplash" and not (params.get("unsplash_key") or os.getenv("UNSPLASH_ACCESS_KEY")):
        return "Unsplash selected but no Unsplash access key provided."
    return None


def main() -> None:
    load_dotenv(override=False)
    page_config()

    st.title("🧪 VibeWriter")
    st.caption("Generate on-brand social captions and image prompts in seconds")

    params = sidebar_inputs()

    if params["submit"]:
        error = validate_inputs(params)
        if error:
            st.error(error)
            return

        # Build LLM adapter
        provider = (params.get("provider") or "google").strip()
        model = (params.get("model") or "").strip()
        keys = {
            "google": (params.get("google_key") or os.getenv("GOOGLE_API_KEY") or None),
            "openai": (params.get("openai_key") or os.getenv("OPENAI_API_KEY") or None),
            "anthropic": None,
        }

        try:
            adapter = build_adapter(provider=provider, model=model, keys=keys)
        except Exception as exc:  # defensive: adapter building should be safe
            st.error(f"Failed to build LLM adapter: {exc}")
            return

        # Build Image fetcher
        image_source = params.get("image_source") or "unsplash"
        if image_source == "unsplash":
            fetcher = UnsplashFetcher(params.get("unsplash_key") or os.getenv("UNSPLASH_ACCESS_KEY") or "")
        else:
            fetcher = SuggestionFetcher()

        # Generate posts with progress feedback
        with st.spinner("Generating posts..."):
            try:
                result = generate_posts(
                    topic=str(params.get("topic")),
                    variants=int(params.get("variants") or 3),
                    llm=adapter,
                    image_fetcher=fetcher,
                    open_links=True,
                )
            except Exception as exc:
                st.error(f"Generation failed: {exc}")
                return

        payload = {"topic": result.topic, "variants": result.variants}

        # JSON expander and download
        with st.expander("Raw JSON output", expanded=False):
            st.code(to_json(payload, pretty=True), language="json")
            st.download_button(
                label="Download JSON",
                file_name="posts.json",
                mime="application/json",
                data=json.dumps(payload, ensure_ascii=False, indent=2),
            )

        # Visual cards
        render_post_cards(payload)

    else:
        st.info("Enter a topic and click Generate Posts to get started.")


if __name__ == "__main__":  # pragma: no cover
    main()


