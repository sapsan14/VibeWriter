from __future__ import annotations

from src.image_fetcher import SuggestionFetcher, ImageResult


def test_suggestion_fetcher_returns_queries():
    f = SuggestionFetcher()
    results = f.search("espresso deal", limit=2)
    assert len(results) == 2
    assert all(isinstance(r, ImageResult) for r in results)
    assert all(r.url is None for r in results)


