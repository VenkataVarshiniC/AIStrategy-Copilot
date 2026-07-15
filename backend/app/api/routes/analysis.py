"""
Analysis endpoints: the core product surface. POST a business question,
get back a full issue tree, evidence-grounded findings, and an answer-first
recommendation.
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.orchestrator import run_analysis
from app.models.schemas import AnalysisRequest, AnalysisResponse
from app.utils.logger import logger

router = APIRouter()


class AnalysisRequestWithParams(AnalysisRequest):
    quant_params: Optional[Dict[str, Any]] = None


@router.post("/run", response_model=AnalysisResponse)
def run_full_analysis(request: AnalysisRequestWithParams):
    try:
        response = run_analysis(request, quant_params=request.quant_params)
        return response
    except Exception as e:
        logger.exception("Analysis pipeline failed")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
