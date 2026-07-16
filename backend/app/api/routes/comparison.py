"""Scenario comparison endpoint: run two strategic options head-to-head."""
from fastapi import APIRouter, HTTPException

from app.core.scenario_comparison import compare_scenarios
from app.models.schemas import ComparisonRequest, ComparisonResponse
from app.utils.logger import logger

router = APIRouter()


@router.post("/run", response_model=ComparisonResponse)
def run_comparison(request: ComparisonRequest):
    try:
        analysis_a, analysis_b, verdict = compare_scenarios(request)
        return ComparisonResponse(
            request=request,
            option_a_analysis=analysis_a,
            option_b_analysis=analysis_b,
            verdict=verdict,
        )
    except Exception as e:
        logger.exception("Scenario comparison pipeline failed")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {e}")
