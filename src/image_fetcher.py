from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import quote_plus

import requests


@dataclass
class ImageResult:
    query: str
    url: Optional[str]


class ImageFetcher:
    def search(self, query: str, limit: int = 1, open_links: bool = False) -> List[ImageResult]:
        raise NotImplementedError


@dataclass
class UnsplashFetcher(ImageFetcher):
    access_key: Optional[str]

    def search(self, query: str, limit: int = 1, open_links: bool = False) -> List[ImageResult]:  # pragma: no cover - network
        if not self.access_key:
            # behave like suggest mode when key missing
            return SuggestionFetcher().search(query, limit=limit, open_links=open_links)

        url = "https://api.unsplash.com/search/photos"
        params = {
            "query": query,
            "per_page": max(1, min(limit, 5)),
            "orientation": "landscape",
        }
        headers = {"Accept-Version": "v1", "Authorization": f"Client-ID {self.access_key}"}
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("results", [])[:limit]:
                # Prefer full URL if open_links; otherwise provide None
                img_url = item.get("urls", {}).get("regular") if open_links else None
                results.append(ImageResult(query=query, url=img_url))
            if not results:
                return SuggestionFetcher().search(query, limit=limit, open_links=open_links)
            return results
        except Exception:
            return SuggestionFetcher().search(query, limit=limit, open_links=open_links)


class SuggestionFetcher(ImageFetcher):
    SUGGESTIONS = [
        "product flatlay",
        "happy customers",
        "lifestyle coffee shop",
        "discount banner",
        "seasonal promo graphic",
        "close-up espresso"
    ]

    def search(self, query: str, limit: int = 1, open_links: bool = False) -> List[ImageResult]:
        random.seed(hash(query) % (2**32))
        picks = random.sample(self.SUGGESTIONS, k=min(limit, len(self.SUGGESTIONS)))
        # If open_links is requested (e.g., Streamlit UI), return a placeholder image URL
        # that does not require API keys. Otherwise keep URLs as None.
        if open_links:
            results: List[ImageResult] = []
            for pick in picks:
                # Use Picsum for placeholder images by deterministic seed; no API key required.
                encoded = quote_plus(pick)
                placeholder_url = f"https://picsum.photos/seed/{encoded}/800/600"
                results.append(ImageResult(query=pick, url=placeholder_url))
            return results
        return [ImageResult(query=pick, url=None) for pick in picks]


