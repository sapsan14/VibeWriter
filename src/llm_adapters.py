from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
import os


# OpenAI SDK is optional at runtime depending on provider selection
try:  # pragma: no cover - exercised in integration, mocked in tests
    import openai
except Exception:  # pragma: no cover
    openai = None  # type: ignore


class LLMAdapter(ABC):
    """Abstract interface for pluggable LLM providers."""

    @abstractmethod
    def generate_text(self, prompt: str, max_tokens: int = 300, **kwargs: Any) -> str:
        raise NotImplementedError


@dataclass
class GeminiAdapter(LLMAdapter):
    api_key: Optional[str]
    model: str = "gemini-1.5-flash"

    def generate_text(self, prompt: str, max_tokens: int = 300, **kwargs: Any) -> str:
        """Call Google Gemini if an API key is provided; otherwise return a stub.

        Uses the `google-generativeai` SDK when available. Falls back to a short
        local stub when the key or SDK is missing.
        """
        # Allow env var fallback if api_key wasn't provided by caller
        api_key = self.api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

        # If no key, return a concise stub preserving prior behavior
        if not api_key:
            # Return only an example caption without echoing the prompt
            return "Celebrate savings with our limited-time offer! #Deal #Promo"

        # Try real API; if SDK missing or call fails, surface a clear message
        try:
            import google.generativeai as genai  # type: ignore
        except Exception:
            return "Gemini SDK not installed. Please install `google-generativeai`."

        try:
            genai.configure(api_key=api_key)
            model_name = (self.model or "gemini-1.5-flash").strip()
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt, generation_config={"max_output_tokens": max_tokens})
            text = getattr(response, "text", None)
            if isinstance(text, str) and text.strip():
                return text.strip()
            # Some SDK versions return candidates in a list
            try:
                candidates = getattr(response, "candidates", None) or []
                for c in candidates:
                    parts = getattr(getattr(c, "content", None), "parts", [])
                    for p in parts:
                        t = getattr(p, "text", None)
                        if isinstance(t, str) and t.strip():
                            return t.strip()
            except Exception:
                pass
            # Fallback to stringifying the response if structure changes
            return str(response)
        except Exception as exc:
            return f"Gemini generation failed: {exc}"


@dataclass
class OpenAIAdapter(LLMAdapter):
    api_key: Optional[str]
    model: str

    def generate_text(self, prompt: str, max_tokens: int = 300, **kwargs: Any) -> str:  # pragma: no cover - thin wrapper
        if openai is None:
            return "OpenAI SDK not installed. Please install `openai`."
        if not self.api_key:
            return "OPENAI_API_KEY is missing."

        # Configure API key
        client = openai.OpenAI(api_key=self.api_key)

        # Using Responses API for text generation
        try:
            response = client.responses.create(
                model=self.model,
                input=prompt,
                max_output_tokens=max_tokens,
            )
            # Prefer convenience accessor when available
            text = getattr(response, "output_text", None)
            if isinstance(text, str) and text.strip():
                return text.strip()
            # Fallback if structure changes
            return str(response)
        except Exception as exc:
            return f"OpenAI generation failed: {exc}"


@dataclass
class AnthropicAdapter(LLMAdapter):
    api_key: Optional[str]
    model: str = "claude-3-haiku-20240307"

    def generate_text(self, prompt: str, max_tokens: int = 300, **kwargs: Any) -> str:
        # Stub for Anthropic Claude
        # Example (when implementing):
        # from anthropic import Anthropic
        # client = Anthropic(api_key=self.api_key)
        # resp = client.messages.create(model=self.model, max_tokens=max_tokens, messages=[{"role":"user","content":prompt}])
        # return resp.content[0].text
        if not self.api_key:
            return "[Anthropic STUB] API key missing; returning placeholder."
        return "[Anthropic STUB] Replace with real API call."


def build_adapter(provider: str, model: str, keys: Dict[str, Optional[str]]) -> LLMAdapter:
    provider_lower = (provider or "").lower()
    if provider_lower in {"google", "gemini"}:
        return GeminiAdapter(api_key=keys.get("google"), model=model or "gemini-1")
    if provider_lower in {"openai"}:
        return OpenAIAdapter(api_key=keys.get("openai"), model=model or "gpt-4o-mini")
    if provider_lower in {"anthropic", "claude"}:
        return AnthropicAdapter(api_key=keys.get("anthropic"), model=model or "claude-3-haiku-20240307")
    # Fallback
    return GeminiAdapter(api_key=keys.get("google"), model=model or "gemini-1")


