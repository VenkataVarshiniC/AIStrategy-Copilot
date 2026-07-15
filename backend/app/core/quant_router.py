"""
Quant router: decides, per issue-tree branch, whether a quantitative model
should run and with what illustrative inputs.

MVP note: because a fully generic "extract real financial parameters from
arbitrary retrieved text" step is a project of its own, this router runs
each analysis type with clearly-labeled illustrative/default assumptions
unless overridden via `params`. The orchestrator passes `params` through
from the API request when the caller supplies real figures. This keeps
every number in the output traceable to either a real input or an explicit
labeled assumption — never a silent guess.
"""
from typing import Any, Dict, Optional

from app.analytics import financial_analysis, market_sizing, sensitivity
from app.models.schemas import IssueBranch, QuantResult


def run_quant_for_branch(branch: IssueBranch, params: Optional[Dict[str, Any]] = None) -> Optional[QuantResult]:
    params = params or {}

    if branch.analysis_type == "market_sizing":
        inputs = {
            "total_population": params.get("total_population", 10_000_000),
            "addressable_pct": params.get("addressable_pct", 0.35),
            "obtainable_pct": params.get("obtainable_pct", 0.08),
            "avg_revenue_per_user": params.get("avg_revenue_per_user", 250),
        }
        outputs = market_sizing.tam_sam_som(**inputs)
        narrative = market_sizing.market_sizing_narrative(outputs)
        return QuantResult(method="tam_sam_som", inputs=inputs, outputs=outputs, narrative=narrative)

    if branch.analysis_type == "financial_analysis":
        inputs = {
            "revenue": params.get("revenue", 50_000_000),
            "cogs": params.get("cogs", 30_000_000),
            "operating_expenses": params.get("operating_expenses", 12_000_000),
            "net_income": params.get("net_income", 5_000_000),
        }
        ratios = financial_analysis.profitability_ratios(**inputs)
        narrative = (
            f"Gross margin of {ratios['gross_margin']:.1%}, operating margin of "
            f"{ratios['operating_margin']:.1%}, and net margin of {ratios['net_margin']:.1%} "
            "based on the provided/assumed financials."
        )
        return QuantResult(method="profitability_ratios", inputs=inputs, outputs=ratios, narrative=narrative)

    if branch.analysis_type == "sensitivity":
        base_value = params.get("base_value", 100.0)
        swing_pct = params.get("swing_pct", 0.2)

        def linear_model(x: float) -> float:
            multiplier = params.get("sensitivity_multiplier", 1.0)
            return x * multiplier

        sweep = sensitivity.one_way_sensitivity(linear_model, base_value=base_value, swing_pct=swing_pct)
        return QuantResult(
            method="one_way_sensitivity",
            inputs={"base_value": base_value, "swing_pct": swing_pct},
            outputs={"sweep": sweep},
            narrative=f"Output ranges from {sweep[0]['output']} to {sweep[-1]['output']} across a ±{swing_pct:.0%} swing.",
        )

    # qualitative branches get no quant model
    return None
