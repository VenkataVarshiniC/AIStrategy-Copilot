"""
LLM client — talks to a locally-running Ollama server instead of a cloud API.

No API key, no account, no signup: Ollama runs the model on your own machine
and exposes a plain HTTP endpoint at http://localhost:11434. Every other
module in the pipeline (issue_tree, hypothesis_testing, synthesis) still only
calls `complete()` / `complete_json()`, so this is a drop-in swap — nothing
upstream had to change.

Setup (one-time):
    1. Install Ollama: https://ollama.com/download
    2. Pull a model:   ollama pull llama3.1
    3. That's it — `ollama serve` runs automatically in the background after install.
"""
import json
import re
from typing import Any, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.utils.logger import logger


class OllamaConnectionError(RuntimeError):
    """Raised when the local Ollama server can't be reached."""


@retry(wait=wait_exponential(multiplier=1, min=2, max=20), stop=stop_after_attempt(3))
def _call_ollama(messages: list, max_tokens: int, temperature: float, force_json: bool) -> str:
    url = f"{settings.ollama_base_url}/api/chat"
    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    if force_json:
        payload["format"] = "json"

    try:
        resp = requests.post(url, json=payload, timeout=180)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        raise OllamaConnectionError(
            f"Couldn't reach Ollama at {settings.ollama_base_url}. "
            "Is it installed and running? Try `ollama serve` in a terminal, "
            f"and make sure the model is pulled: `ollama pull {settings.ollama_model}`."
        ) from e

    data = resp.json()
    return data.get("message", {}).get("content", "")


def complete(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = 2000,
    temperature: float = 0.3,
) -> str:
    """Single free-text completion call to the local model."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    return _call_ollama(messages, max_tokens=max_tokens, temperature=temperature, force_json=False)


def complete_json(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = 2000,
    temperature: float = 0.2,
) -> Any:
    """
    Completion that is expected to return strictly parseable JSON.
    Uses Ollama's native `format: "json"` mode (forces valid JSON grammar
    at the decoding level) in addition to an explicit instruction, and
    still strips stray markdown fences defensively.
    """
    json_system = (
        (system or "")
        + "\n\nCRITICAL: Respond with ONLY valid JSON. No markdown fences, no preamble, "
        "no explanation before or after the JSON object."
    )
    messages = [{"role": "system", "content": json_system}, {"role": "user", "content": prompt}]

    raw = _call_ollama(messages, max_tokens=max_tokens, temperature=temperature, force_json=True)
    cleaned = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Ollama response: {e}\nRaw: {raw[:500]}")
        raise
