from __future__ import annotations

import argparse
import sys
from typing import Optional

from .config import load_config
from .llm_adapters import build_adapter
from .image_fetcher import UnsplashFetcher, SuggestionFetcher
from .generator import generate_posts
from .utils import to_json


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="VibeWriter: social media post generator")
    parser.add_argument("--topic", required=True, help="Campaign topic or brief")
    parser.add_argument("--variants", type=int, default=3, help="Number of post variants")
    parser.add_argument("--model", default=None, help="LLM model name")
    parser.add_argument("--llm-provider", default=None, help="LLM provider: google|openai|anthropic")
    parser.add_argument("--image-bank", default="unsplash", choices=["unsplash", "suggest"], help="Image source")
    parser.add_argument("--open-links", action="store_true", help="Include image URLs in output JSON")
    parser.add_argument("--output", default=None, help="Output file path (JSON). Defaults to stdout")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    cfg = load_config()

    provider = (args.llm_provider or cfg.llm_provider).strip()
    model = (args.model or cfg.llm_model).strip()

    adapter = build_adapter(
        provider=provider,
        model=model,
        keys={
            "google": cfg.google_api_key,
            "openai": cfg.openai_api_key,
            "anthropic": None,
        },
    )

    if args.image_bank == "unsplash":
        fetcher = UnsplashFetcher(cfg.unsplash_access_key)
    else:
        fetcher = SuggestionFetcher()

    result = generate_posts(
        topic=args.topic,
        variants=args.variants,
        llm=adapter,
        image_fetcher=fetcher,
        open_links=args.open_links,
    )

    payload = {"topic": result.topic, "variants": result.variants}
    text = to_json(payload, pretty=True)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text)

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


