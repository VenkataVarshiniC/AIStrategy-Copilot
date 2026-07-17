"""
Orchestrator: the single entrypoint that runs the entire consulting pipeline
end to end.

  1. generate_issue_tree       -> MECE decomposition
  2. for each branch (CONCURRENT, not sequential — see below):
       run_quant_for_branch    -> optional quantitative model
       test_hypothesis         -> RAG-grounded evidence + LLM judgment
  3. synthesize_recommendation -> answer-first roll-up
  4. run_red_team_review       -> adversarial challenge of the recommendation
  5. analyze_precedents        -> optional comparable-case pattern matching

Concurrency: branches are independent of each other, so they run in a
bounded thread pool instead of one at a time. groq_client's semaphore
(settings.groq_max_concurrent_requests) still caps how many requests
actually hit Groq at once, so this is real wall-clock speedup without
losing the free-tier burst protection. Steps 3-5 stay sequential since each
depends on the prior step's output.
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def _process_branch(branch, quant_params):
    quant_result = run_quant_for_branch(branch, params=quant_params)
    return test_hypothesis(branch, quant_result=quant_result)


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

    logger.info(f"Processing {len(issue_tree.branches)} branches concurrently")
    results_by_id = {}
    with ThreadPoolExecutor(max_workers=settings.groq_max_concurrent_requests) as pool:
        future_to_branch = {
            pool.submit(_process_branch, branch, quant_params): branch for branch in issue_tree.branches
        }
        for future in as_completed(future_to_branch):
            branch = future_to_branch[future]
            finding, branch_warning = future.result()
            results_by_id[branch.id] = finding
            if branch_warning:
                warnings.append(branch_warning)

    # Preserve original branch order in the output regardless of completion order.
    findings = [results_by_id[branch.id] for branch in issue_tree.branches]

    # precedents only depends on issue_tree (already available), not on
    # synthesis/red-team's output — so it runs concurrently with that
    # sequential chain instead of strictly after it, shaving it off the
    # critical path entirely.
    with ThreadPoolExecutor(max_workers=2) as pool:
        precedents_future = pool.submit(analyze_precedents, issue_tree)

        recommendation, synthesis_warning = synthesize_recommendation(issue_tree, findings)
        if synthesis_warning:
            warnings.append(synthesis_warning)
        logger.info(f"Synthesis complete. Headline: {recommendation.headline}")
        _throttle()

        logger.info("Running red-team review")
        red_team = run_red_team_review(issue_tree, findings, recommendation)

        logger.info("Checking for comparable precedents (ran concurrently with synthesis/red-team)")
        precedents = precedents_future.result()

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
