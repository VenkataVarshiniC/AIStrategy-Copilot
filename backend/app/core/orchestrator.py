"""
Orchestrator: the single entrypoint that runs the entire consulting pipeline
end to end.

  1. generate_issue_tree       -> MECE decomposition
  2. for each branch (throttled):
       run_quant_for_branch    -> optional quantitative model
       test_hypothesis         -> RAG-grounded evidence + LLM judgment
  3. synthesize_recommendation -> answer-first roll-up
  4. run_red_team_review       -> adversarial challenge of the recommendation
  5. analyze_precedents        -> optional comparable-case pattern matching

Throttling: the free Groq tier caps tokens-per-minute, and this pipeline
fires several sequential LLM calls in one request (now 8+ with red-team and
precedents added). A small fixed delay between calls
(settings.groq_request_delay_seconds) keeps a single analysis run from
bursting past that budget partway through. Any call that still fails is
reported via `warnings` instead of being silently absorbed.
"""
import time
from typing import Any, Dict, Optional

from app.config import settings
from app.core.hypothesis_testing import test_hypothesis
from app.core.issue_tree import generate_issue_tree
from app.core.precedent_analysis import analyze_precedents
from app.core.quant_router import run_quant_for_branch
from app.core.red_team import run_red_team_review
from app.core.synthesis import synthesize_recommendation
from app.models.schemas import AnalysisRequest, AnalysisResponse
from app.rag.vector_store import get_vector_store
from app.utils.logger import logger


def _throttle():
    if settings.groq_request_delay_seconds > 0:
        time.sleep(settings.groq_request_delay_seconds)


def run_analysis(request: AnalysisRequest, quant_params: Optional[Dict[str, Any]] = None) -> AnalysisResponse:
    logger.info(f"Running analysis for question: '{request.question}'")

    warnings: list = []

    if get_vector_store().count() == 0:
        msg = (
            "No documents have been ingested into the knowledge base. Every branch below will "
            "likely be marked inconclusive because there's no evidence to ground findings in — "
            "this is expected behavior, not a bug. Ingest source URLs or a PDF via /api/ingest "
            "before running an analysis for grounded results."
        )
        logger.warning(msg)
        warnings.append(msg)

    issue_tree = generate_issue_tree(
        question=request.question,
        company_name=request.company_name,
        industry=request.industry,
        additional_context=request.additional_context,
        max_branches=request.max_branches,
    )
    logger.info(f"Generated issue tree with {len(issue_tree.branches)} branches")
    _throttle()

    findings = []
    for i, branch in enumerate(issue_tree.branches):
        logger.info(f"Processing branch {i + 1}/{len(issue_tree.branches)}: {branch.title} ({branch.analysis_type})")
        quant_result = run_quant_for_branch(branch, params=quant_params)
        finding, branch_warning = test_hypothesis(branch, quant_result=quant_result)
        findings.append(finding)
        if branch_warning:
            warnings.append(branch_warning)
        _throttle()

    recommendation, synthesis_warning = synthesize_recommendation(issue_tree, findings)
    if synthesis_warning:
        warnings.append(synthesis_warning)
    logger.info(f"Synthesis complete. Headline: {recommendation.headline}")
    _throttle()

    logger.info("Running red-team review")
    red_team = run_red_team_review(issue_tree, findings, recommendation)
    _throttle()

    logger.info("Checking for comparable precedents")
    precedents = analyze_precedents(issue_tree)

    if warnings:
        logger.warning(f"Analysis completed with {len(warnings)} warning(s): {warnings}")

    return AnalysisResponse(
        request=request,
        issue_tree=issue_tree,
        findings=findings,
        recommendation=recommendation,
        red_team=red_team,
        precedents=precedents,
        warnings=warnings,
    )
