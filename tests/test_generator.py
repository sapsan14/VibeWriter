from __future__ import annotations

from dataclasses import dataclass

from src.generator import generate_posts
from src.image_fetcher import ImageFetcher, ImageResult
from src.llm_adapters import LLMAdapter


@dataclass
class DummyLLM(LLMAdapter):
    def generate_text(self, prompt: str, max_tokens: int = 300, **kwargs) -> str:  # type: ignore[override]
        return "Buy now and save! #Deal #Coffee"


class DummyFetcher(ImageFetcher):
    def search(self, query: str, limit: int = 1, open_links: bool = False):
        return [ImageResult(query="coffee shop", url="http://example.com/img.jpg")]


def test_generate_posts_basic():
    llm = DummyLLM()
    fetcher = DummyFetcher()
    res = generate_posts("black friday discount for coffee shop", variants=2, llm=llm, image_fetcher=fetcher, open_links=True)
    assert res.topic.startswith("black friday")
    assert len(res.variants) == 2
    assert res.variants[0]["text"]
    assert res.variants[0]["image_url"].startswith("http")


