"""
Orchestrator: the single entrypoint that runs the entire consulting pipeline
end to end.

  1. generate_issue_tree     -> MECE decomposition
  2. for each branch:
       run_quant_for_branch  -> optional quantitative model
       test_hypothesis       -> RAG-grounded evidence + LLM judgment
  3. synthesize_recommendation -> answer-first roll-up

This is intentionally a plain, readable function rather than a class or
graph-framework DAG — for an MVP, explicit and debuggable beats "clever."
"""
from typing import Any, Dict, Optional

from app.core.hypothesis_testing import test_hypothesis
from app.core.issue_tree import generate_issue_tree
from app.core.quant_router import run_quant_for_branch
from app.core.synthesis import synthesize_recommendation
from app.models.schemas import AnalysisRequest, AnalysisResponse
from app.utils.logger import logger


def run_analysis(request: AnalysisRequest, quant_params: Optional[Dict[str, Any]] = None) -> AnalysisResponse:
    logger.info(f"Running analysis for question: '{request.question}'")

    issue_tree = generate_issue_tree(
        question=request.question,
        company_name=request.company_name,
        industry=request.industry,
        additional_context=request.additional_context,
        max_branches=request.max_branches,
    )
    logger.info(f"Generated issue tree with {len(issue_tree.branches)} branches")

    findings = []
    for branch in issue_tree.branches:
        logger.info(f"Processing branch: {branch.title} ({branch.analysis_type})")
        quant_result = run_quant_for_branch(branch, params=quant_params)
        finding = test_hypothesis(branch, quant_result=quant_result)
        findings.append(finding)

    recommendation = synthesize_recommendation(issue_tree, findings)
    logger.info(f"Synthesis complete. Headline: {recommendation.headline}")

    return AnalysisResponse(
        request=request,
        issue_tree=issue_tree,
        findings=findings,
        recommendation=recommendation,
    )
