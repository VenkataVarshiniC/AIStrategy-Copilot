"""
Core financial analysis functions: profitability ratios, NPV/IRR-style
investment appraisal, and breakeven analysis. Used to quantify branches
of the issue tree that hinge on unit economics or investment viability.
"""
from typing import Dict, List

def profitability_ratios(revenue: float, cogs: float, operating_expenses: float, net_income: float) -> Dict[str, float]:
    gross_profit = revenue - cogs
    operating_income = gross_profit - operating_expenses
    return {
        "gross_margin": round(gross_profit / revenue, 4) if revenue else 0.0,
        "operating_margin": round(operating_income / revenue, 4) if revenue else 0.0,
        "net_margin": round(net_income / revenue, 4) if revenue else 0.0,
    }


def npv(discount_rate: float, cash_flows: List[float]) -> float:
    """cash_flows[0] is the initial outlay (negative), followed by future inflows."""
    return round(sum(cf / ((1 + discount_rate) ** t) for t, cf in enumerate(cash_flows)), 2)


def payback_period(cash_flows: List[float]) -> float:
    """cash_flows[0] negative outlay, rest positive inflows. Returns years (fractional)."""
    cumulative = 0.0
    for t, cf in enumerate(cash_flows):
        cumulative += cf
        if cumulative >= 0 and t > 0:
            prev_cumulative = cumulative - cf
            fraction = -prev_cumulative / cf if cf else 0
            return round((t - 1) + fraction, 2)
    return -1.0  # never pays back within horizon


def breakeven_units(fixed_costs: float, price_per_unit: float, variable_cost_per_unit: float) -> float:
    contribution_margin = price_per_unit - variable_cost_per_unit
    if contribution_margin <= 0:
        return float("inf")
    return round(fixed_costs / contribution_margin, 2)
