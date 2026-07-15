"""
Sensitivity and scenario analysis: one-way sensitivity sweeps and
best/base/worst-case scenario tables. Used when a branch's conclusion
depends heavily on an uncertain assumption (e.g., adoption rate, discount rate).
"""
from typing import Callable, Dict, List

import numpy as np


def one_way_sensitivity(
    model_fn: Callable[[float], float],
    base_value: float,
    swing_pct: float = 0.2,
    steps: int = 5,
) -> List[Dict[str, float]]:
    """
    Sweeps a single input variable from (1-swing_pct) to (1+swing_pct) of its
    base value and records the resulting model output at each step.
    `model_fn` takes the swept variable's value and returns a single output metric.
    """
    low = base_value * (1 - swing_pct)
    high = base_value * (1 + swing_pct)
    values = np.linspace(low, high, steps)
    return [{"input": round(float(v), 4), "output": round(float(model_fn(v)), 4)} for v in values]


def scenario_table(
    model_fn: Callable[..., float],
    scenarios: Dict[str, Dict[str, float]],
) -> Dict[str, float]:
    """
    scenarios: {"worst": {...kwargs}, "base": {...kwargs}, "best": {...kwargs}}
    Runs model_fn(**kwargs) for each named scenario.
    """
    return {name: round(model_fn(**kwargs), 2) for name, kwargs in scenarios.items()}
