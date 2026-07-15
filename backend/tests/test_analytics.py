"""
Deterministic unit tests — cover the analytics layer only, since those
functions have no external dependency (no LLM, no vector store) and should
be 100% reliable. Orchestrator/LLM-dependent paths are covered separately
via integration tests that require a running local Ollama server (no API key needed).
"""
from app.analytics.financial_analysis import breakeven_units, npv, payback_period, profitability_ratios
from app.analytics.market_sizing import cagr, project_forward, tam_sam_som
from app.analytics.sensitivity import one_way_sensitivity, scenario_table


def test_tam_sam_som():
    result = tam_sam_som(
        total_population=1_000_000,
        addressable_pct=0.5,
        obtainable_pct=0.1,
        avg_revenue_per_user=100,
    )
    assert result["tam"] == 100_000_000
    assert result["sam"] == 50_000_000
    assert result["som"] == 5_000_000


def test_cagr():
    rate = cagr(100, 200, 5)
    assert 0.14 < rate < 0.15


def test_project_forward():
    values = project_forward(100, 0.1, 3)
    assert len(values) == 3
    assert values[0] == 110.0


def test_profitability_ratios():
    ratios = profitability_ratios(revenue=1000, cogs=600, operating_expenses=200, net_income=150)
    assert ratios["gross_margin"] == 0.4
    assert ratios["operating_margin"] == 0.2
    assert ratios["net_margin"] == 0.15


def test_npv_positive_project():
    result = npv(0.1, [-1000, 400, 400, 400, 400])
    assert result > 0


def test_payback_period():
    result = payback_period([-1000, 500, 500, 500])
    assert result == 2.0


def test_breakeven_units():
    result = breakeven_units(fixed_costs=10000, price_per_unit=50, variable_cost_per_unit=30)
    assert result == 500.0


def test_one_way_sensitivity():
    sweep = one_way_sensitivity(lambda x: x * 2, base_value=100, swing_pct=0.2, steps=3)
    assert len(sweep) == 3
    assert sweep[0]["output"] == 160.0
    assert sweep[-1]["output"] == 240.0


def test_scenario_table():
    result = scenario_table(
        lambda multiplier: 100 * multiplier,
        {"worst": {"multiplier": 0.8}, "base": {"multiplier": 1.0}, "best": {"multiplier": 1.2}},
    )
    assert result["worst"] == 80.0
    assert result["best"] == 120.0
