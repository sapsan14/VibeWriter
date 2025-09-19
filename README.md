## VibeWriter

Generate on-brand social captions and image prompts using a pluggable LLM adapter system. Defaults to Google Gemini (stub) and includes a working OpenAI adapter. Images are fetched from Unsplash or suggested as search queries.

### Quick Start

1) Create and populate your environment file:

```bash
cp env.example .env  # if .env.example creation is blocked in your environment
# Or create .env manually. Add keys from the list below
```

2) Install dependencies (Python 3.10+):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

3) Run the CLI:

```bash
python -m src.cli --topic "black friday discount for coffee shop" --variants 3 --model gemini-1 --llm-provider google --image-bank unsplash --output sample_runs/out.json
```

Or use suggestion mode (no Unsplash API key required):

```bash
python -m src.cli --topic "summer smoothie launch" --variants 2 --image-bank suggest --open-links
```

### CLI Options

- `--topic` (required): Topic/brief for the campaign
- `--variants` (default 3): Number of post variants to generate
- `--model` (default from env `LLM_MODEL`, fallback `gemini-1`)
- `--llm-provider` (default from env `LLM_PROVIDER`, fallback `google`)
- `--image-bank` (`unsplash` or `suggest`)
- `--open-links` (flag): include image URLs in JSON
- `--output` (path): write JSON to file; when omitted prints to stdout

### Environment Variables

- `GOOGLE_API_KEY` (for Gemini; stub included by default)
- `OPENAI_API_KEY` (optional, for OpenAI adapter)
- `UNSPLASH_ACCESS_KEY` (for Unsplash)
- `LLM_PROVIDER` (default `google`)
- `LLM_MODEL` (default `gemini-1`)

Use `.env` (loaded automatically) or export in your shell.

### LLM Adapters

- `GeminiAdapter` (default): Stubbed implementation with clear comments and placeholders where to wire Google Generative AI / Vertex AI SDK. Returns a safe placeholder response for local testing without a key.
- `OpenAIAdapter`: Implemented with `openai` SDK (Responses API). Requires `OPENAI_API_KEY` and a model name (e.g., `gpt-4o-mini`).
- `AnthropicAdapter`: Stub showing how to extend.

To switch providers, pass `--llm-provider openai --model gpt-4o-mini` or set `LLM_PROVIDER` and `LLM_MODEL` in env.

### Unsplash Integration

- `UnsplashFetcher` fetches photo results via the Unsplash API (search endpoint). Requires `UNSPLASH_ACCESS_KEY`.
- `SuggestionFetcher` is a fallback that returns 1–3 image search query suggestions when the API key is missing or `--image-bank suggest` is used.

### Data Shape

The CLI outputs JSON in the following structure:

```json
{
  "topic": "...",
  "variants": [
    { "text": "...", "image_query": "...", "image_url": "..." }
  ]
}
```

When `--open-links` is not specified or not applicable, `image_url` may be `null`.

### Development

Run tests:

```bash
pytest -q
```

### Implementing Real Gemini Calls

- In `src/llm_adapters.py`, find `GeminiAdapter`. Replace the stub `generate_text` with calls to the Google Generative AI SDK or Vertex AI. You will need to:
  - Install the SDK (e.g., `google-generativeai`)
  - Initialize the client with `GOOGLE_API_KEY`
  - Call generate with your model name (default `gemini-1`) and prompt
  - Return the generated text string

Comments and placeholders are included in the code to guide you.

### GDPR/PII Notes

- The prototype includes a minimal profanity filter and a simple scrubbing step. You are responsible for ensuring compliance when handling user data and generated content. Avoid including personal data or unique identifiers in prompts or outputs.


