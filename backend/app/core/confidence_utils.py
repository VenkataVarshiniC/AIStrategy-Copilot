"""
Robust confidence-value parsing.

Claude reliably returns confidence as a clean float in [0.0, 1.0] when asked.
Open-weight models served via Groq (Llama 3.3, etc.) are generally good at this
too, but can still occasionally return "70" or "70%" (percent scale instead of
0-1), a string like "0.8" with stray whitespace, or a word like "high"/"medium"/"low".

This parser normalizes all of those into a valid float in [0.0, 1.0] instead
of letting a raw `float(x)` crash and silently zero out an otherwise-valid
finding (which is what was happening before: a confidence-parsing failure
was forcing the whole branch to `inconclusive` / `0%`).
"""
import re
from typing import Any, Optional

from app.utils.logger import logger

_WORD_SCALE = {
    "very low": 0.15,
    "low": 0.3,
    "medium": 0.5,
    "moderate": 0.5,
    "high": 0.75,
    "very high": 0.9,
}


def parse_confidence(raw: Any, default: float = 0.4) -> float:
    """Parse a confidence value from an LLM response into a clamped [0.0, 1.0] float."""
    if raw is None:
        return round(default, 2)

    # Already numeric
    if isinstance(raw, (int, float)):
        value = float(raw)
        return _normalize_scale(value, default)

    if isinstance(raw, str):
        cleaned = raw.strip().lower()

        # Word-scale ("high", "medium", "low", ...)
        if cleaned in _WORD_SCALE:
            return _WORD_SCALE[cleaned]

        # Strip a trailing "%" if present
        had_percent_sign = cleaned.endswith("%")
        cleaned = cleaned.rstrip("%").strip()

        match = re.search(r"-?\d+(\.\d+)?", cleaned)
        if match:
            value = float(match.group())
            if had_percent_sign:
                value = value / 100
            return _normalize_scale(value, default)

    logger.warning(f"Couldn't parse confidence value '{raw}' — using default {default}")
    return round(default, 2)


def _normalize_scale(value: float, default: float) -> float:
    """
    Handles the ways local models drift from a clean 0.0-1.0 float:
      - <= 1.0            : already correct, use as-is
      - 1.0 < x <= 1.5     : almost certainly a minor overflow on a 0-1 scale
                             (e.g. rounding artifact) -> clamp to 1.0
      - 1.5 < x <= 100     : clearly a 0-100 percent scale -> divide by 100
      - > 100 or NaN        : nonsensical -> fall back to default
    """
    if value != value:  # NaN check
        logger.warning(f"Confidence value is NaN — using default {default}")
        return round(default, 2)
    if value < 0.0:
        logger.warning(f"Confidence value {value} is negative — using default {default}")
        return round(default, 2)
    if value <= 1.0:
        return round(value, 2)
    if value <= 1.5:
        return 1.0
    if value <= 100:
        return round(value / 100, 2)
    logger.warning(f"Confidence value {value} out of any reasonable range — using default {default}")
    return round(default, 2)


def average_confidence(values: list, default: float = 0.4) -> float:
    """Simple mean of a list of confidence floats, used as a synthesis fallback."""
    values = [v for v in values if isinstance(v, (int, float))]
    if not values:
        return round(default, 2)
    return round(sum(values) / len(values), 2)
