"""
LLM client — talks to Groq's cloud API instead of a local Ollama server.

Why the switch: Ollama runs inference on your own CPU/GPU, which was adding
noticeable latency to every request. Groq runs open-weight models (Llama,
etc.) on custom LPU hardware and is dramatically faster — often 300-1000+
tokens/second — while still being free for prototyping (rate-limited, no
credit card required).

IMPORTANT — free tier rate limits: the free tier caps both requests/minute
and tokens/minute. This pipeline fires several sequential LLM calls per
analysis run (issue tree, then one call per branch, then synthesis), which
can burst past the tokens-per-minute budget partway through a single run if
calls aren't paced. Two things protect against that:
  1. This module honors the `Retry-After` header Groq returns on a 429 and
     waits exactly that long before retrying, instead of guessing.
  2. The orchestrator adds a small fixed delay between calls
     (settings.groq_request_delay_seconds) to avoid bursting in the first place.
If you still see rate-limit errors, either raise groq_request_delay_seconds
in .env or switch GROQ_MODEL to a lighter model with a higher free-tier budget.

Groq's API is OpenAI-compatible, so this is a plain HTTP client against
https://api.groq.com/openai/v1/chat/completions — no SDK dependency needed.
Every other module in the pipeline (issue_tree, hypothesis_testing, synthesis)
still only calls `complete()` / `complete_json()`, so this swap is isolated
to this one file.

Setup (one-time, no credit card):
    1. Sign up at https://console.groq.com
    2. Create an API key under Settings -> API Keys
    3. Set GROQ_API_KEY in your .env file
"""
import json
import re
import time
from typing import Any, Optional

import requests

from app.config import settings
from app.utils.logger import logger

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
MAX_ATTEMPTS = 5
DEFAULT_RATE_LIMIT_WAIT_SECONDS = 8.0
DEFAULT_CONNECTION_RETRY_WAIT_SECONDS = 3.0


class GroqAuthError(RuntimeError):
    """Raised when GROQ_API_KEY is missing or rejected. Never retried — a bad key won't fix itself."""


class GroqRateLimitError(RuntimeError):
    """Raised when Groq's free-tier rate limit is hit (HTTP 429) and all retries are exhausted."""


class GroqConnectionError(RuntimeError):
    """Raised when Groq can't be reached at all after retries (network issue, outage, etc.)."""


def _call_groq(messages: list, max_tokens: int, temperature: float, force_json: bool) -> str:
    if not settings.groq_api_key:
        raise GroqAuthError(
            "GROQ_API_KEY is not set. Get a free key at https://console.groq.com "
            "(Settings -> API Keys) and add it to your .env file."
        )

    payload = {
        "model": settings.groq_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if force_json:
        payload["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }

    last_connection_error: Optional[Exception] = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = requests.post(GROQ_CHAT_URL, json=payload, headers=headers, timeout=60)
        except requests.exceptions.ConnectionError as e:
            last_connection_error = e
            if attempt == MAX_ATTEMPTS:
                raise GroqConnectionError(
                    f"Couldn't reach Groq's API after {MAX_ATTEMPTS} attempts: {e}"
                ) from e
            wait = DEFAULT_CONNECTION_RETRY_WAIT_SECONDS * attempt
            logger.warning(f"Groq connection error (attempt {attempt}/{MAX_ATTEMPTS}) — retrying in {wait:.0f}s")
            time.sleep(wait)
            continue

        # Fail fast on auth errors — retrying a bad key wastes time and
        # burns rate-limit budget on requests that can never succeed.
        if resp.status_code == 401:
            raise GroqAuthError("Groq rejected the API key — double check GROQ_API_KEY in your .env file.")

        if resp.status_code == 429:
            retry_after = float(resp.headers.get("Retry-After", DEFAULT_RATE_LIMIT_WAIT_SECONDS))
            if attempt == MAX_ATTEMPTS:
                raise GroqRateLimitError(
                    f"Groq free-tier rate limit hit and retries exhausted (waited up to {retry_after:.0f}s "
                    "each time). This usually means the pipeline's sequential calls burst past the "
                    "tokens-per-minute budget for this model. Try raising GROQ_REQUEST_DELAY_SECONDS in "
                    ".env, switching to a lighter GROQ_MODEL, or simply waiting a minute and retrying. "
                    "See https://console.groq.com/settings/limits for your current usage."
                )
            logger.warning(
                f"Groq rate limit hit (attempt {attempt}/{MAX_ATTEMPTS}) — "
                f"waiting {retry_after:.0f}s (server-specified via Retry-After header)"
            )
            time.sleep(retry_after)
            continue

        resp.raise_for_status()

        data = resp.json()
        choice = data["choices"][0]

        if choice.get("finish_reason") == "length":
            logger.warning(
                f"Groq response was cut off at the {max_tokens}-token limit — "
                "consider raising max_tokens for this call if you see JSON parse errors."
            )

        return choice["message"]["content"]

    # Should be unreachable — every branch above either returns or raises —
    # but keep a clear error rather than an implicit `None` if it ever isn't.
    raise GroqConnectionError(f"Groq request failed after {MAX_ATTEMPTS} attempts: {last_connection_error}")


def complete(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = 2000,
    temperature: float = 0.3,
) -> str:
    """Single free-text completion call to Groq."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    return _call_groq(messages, max_tokens=max_tokens, temperature=temperature, force_json=False)


def _attempt_json_repair(raw: str) -> Optional[Any]:
    """
    Best-effort recovery for malformed/truncated JSON. Groq's models are
    generally reliable at valid JSON, but this stays in as a safety net —
    truncation can still happen on tight token budgets.
    """
    stripped = raw.strip()
    start = stripped.find("{")
    if start == -1:
        return None

    def _strip_trailing_commas(text: str) -> str:
        return re.sub(r",\s*([}\]])", r"\1", text)

    end = stripped.rfind("}")
    if end > start:
        candidate = _strip_trailing_commas(stripped[start : end + 1])
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    candidate = stripped[start:]
    if candidate.count('"') % 2 == 1:
        candidate += '"'
    candidate = candidate.rstrip().rstrip(",")
    candidate = _strip_trailing_commas(candidate)
    open_braces = candidate.count("{") - candidate.count("}")
    open_brackets = candidate.count("[") - candidate.count("]")
    candidate += "]" * max(open_brackets, 0)
    candidate += "}" * max(open_braces, 0)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def complete_json(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = 2000,
    temperature: float = 0.2,
) -> Any:
    """
    Completion that is expected to return strictly parseable JSON.
    Uses Groq/OpenAI's native `response_format: {"type": "json_object"}` mode
    in addition to an explicit instruction, with a repair fallback for the
    rare case of truncated output.
    """
    json_system = (
        (system or "")
        + "\n\nCRITICAL: Respond with ONLY valid JSON. No markdown fences, no preamble, "
        "no explanation before or after the JSON object."
    )
    messages = [{"role": "system", "content": json_system}, {"role": "user", "content": prompt}]

    raw = _call_groq(messages, max_tokens=max_tokens, temperature=temperature, force_json=True)
    cleaned = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        repaired = _attempt_json_repair(raw)
        if repaired is not None:
            logger.warning("Groq returned malformed/truncated JSON — recovered via repair.")
            return repaired
        logger.error(f"Failed to parse JSON from Groq response: {e}\nRaw: {raw[:500]}")
        raise
