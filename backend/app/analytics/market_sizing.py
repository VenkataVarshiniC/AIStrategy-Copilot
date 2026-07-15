"""
Market sizing toolkit: TAM/SAM/SOM funnel and forward CAGR projection.
Pure numeric functions — no LLM calls — so results are deterministic and
auditable, which is exactly what a consulting-grade deliverable needs.
"""
from typing import Dict, List

import numpy as np


def tam_sam_som(
    total_population: float,
    addressable_pct: float,
    obtainable_pct: float,
    avg_revenue_per_user: float,
) -> Dict[str, float]:
    """
    total_population: total unit count in the broad market (e.g., total EV buyers)
    addressable_pct: fraction of TAM realistically reachable given product/geography (0-1)
    obtainable_pct: fraction of SAM realistically capturable given competition (0-1)
    avg_revenue_per_user: expected revenue per captured unit
    """
    tam = total_population * avg_revenue_per_user
    sam = tam * addressable_pct
    som = sam * obtainable_pct
    return {
        "tam": round(tam, 2),
        "sam": round(sam, 2),
        "som": round(som, 2),
        "tam_units": round(total_population, 2),
        "sam_units": round(total_population * addressable_pct, 2),
        "som_units": round(total_population * addressable_pct * obtainable_pct, 2),
    }


def cagr(beginning_value: float, ending_value: float, periods: int) -> float:
    if beginning_value <= 0 or periods <= 0:
        return 0.0
    return round((ending_value / beginning_value) ** (1 / periods) - 1, 4)


def project_forward(base_value: float, growth_rate: float, years: int) -> List[float]:
    """Compound a base market value forward by a fixed annual growth rate."""
    return [round(base_value * ((1 + growth_rate) ** y), 2) for y in range(1, years + 1)]


def market_sizing_narrative(result: Dict[str, float], context: str = "") -> str:
    return (
        f"TAM of ${result['tam']:,.0f} narrows to a SAM of ${result['sam']:,.0f} "
        f"({result['sam'] / result['tam']:.0%} of TAM) after applying reachability constraints, "
        f"and a realistically obtainable SOM of ${result['som']:,.0f} "
        f"({result['som'] / result['sam']:.0%} of SAM) given competitive intensity. {context}"
    ).strip()
