"""
Orchestrator: the single entrypoint that runs the entire consulting pipeline
end to end.

  1. generate_issue_tree     -> MECE decomposition
  2. for each branch (throttled, see below):
       run_quant_for_branch  -> optional quantitative model
       test_hypothesis       -> RAG-grounded evidence + LLM judgment
  3. synthesize_recommendation -> answer-first roll-up

Throttling: the free Groq tier caps tokens-per-minute, and this pipeline
fires several sequential LLM calls in one request. A small fixed delay
between branch calls (settings.groq_request_delay_seconds) keeps a single
analysis run from bursting past that budget partway through — which is what
was previously causing every later branch in a run to silently fail and get
mislabeled "inconclusive." Any call that still fails is now reported via
`warnings` instead of being silently absorbed.

This is intentionally a plain, readable function rather than a class or
graph-framework DAG — for an MVP, explicit and debuggable beats "clever."
"""
import time
from typing import Any, Dict, Optional

from app.config import settings
from app.core.hypothesis_testing import test_hypothesis
from app.core.issue_tree import generate_issue_tree
from app.core.quant_router import run_quant_for_branch
from app.core.synthesis import synthesize_recommendation
from app.models.schemas import AnalysisRequest, AnalysisResponse
from app.rag.vector_store import get_vector_store
from app.utils.logger import logger


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

    findings = []
    for i, branch in enumerate(issue_tree.branches):
        logger.info(f"Processing branch {i + 1}/{len(issue_tree.branches)}: {branch.title} ({branch.analysis_type})")
        quant_result = run_quant_for_branch(branch, params=quant_params)
        finding, branch_warning = test_hypothesis(branch, quant_result=quant_result)
        findings.append(finding)
        if branch_warning:
            warnings.append(branch_warning)

        # Pace requests to stay under the free tier's tokens-per-minute budget —
        # skip the delay after the last branch, nothing follows it but synthesis.
        if i < len(issue_tree.branches) - 1 and settings.groq_request_delay_seconds > 0:
            time.sleep(settings.groq_request_delay_seconds)

    if settings.groq_request_delay_seconds > 0:
        time.sleep(settings.groq_request_delay_seconds)

    recommendation, synthesis_warning = synthesize_recommendation(issue_tree, findings)
    if synthesis_warning:
        warnings.append(synthesis_warning)
    logger.info(f"Synthesis complete. Headline: {recommendation.headline}")

    if warnings:
        logger.warning(f"Analysis completed with {len(warnings)} warning(s): {warnings}")

    return AnalysisResponse(
        request=request,
        issue_tree=issue_tree,
        findings=findings,
        recommendation=recommendation,
        warnings=warnings,
    )
