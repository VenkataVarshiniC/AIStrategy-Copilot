"""
Scenario comparison: runs the full analysis pipeline independently for two
strategic options against the same decision context, then produces a
comparative verdict — which real case work almost always requires, since
the question is rarely "should we do X" in isolation but "X or Y."

Reuses the existing single-option orchestrator (run_analysis) twice rather
than duplicating pipeline logic, then adds one more LLM call to compare
the two resulting recommendations head to head.
"""
from typing import Tuple

from app.core.confidence_utils import parse_confidence
from app.core.orchestrator import run_analysis
from app.llm.groq_client import GroqAuthError, GroqConnectionError, GroqRateLimitError, complete_json
from app.models.schemas import AnalysisRequest, AnalysisResponse, ComparisonRequest, ComparisonVerdict
from app.utils.logger import logger

COMPARISON_SYSTEM_PROMPT = """You are a McKinsey engagement manager deciding
between two strategic options that were each independently analyzed. You will
be given the decision context and a summary of each option's recommendation.

Rules:
- Decide which option wins on balance, or "neither/hybrid" if a blended approach
  is genuinely better than either pure option.
- Give a concise rationale (2-3 sentences) for the call.
- List 2-4 key trade-offs between the two options — the factors that actually
  drove the decision, not a generic list.
- Give a confidence score 0.0-1.0 for this comparative verdict.

Respond with ONLY this compact JSON shape, nothing else:
{"winning_option": "option_a | option_b | neither/hybrid", "rationale": "...", "key_tradeoffs": ["...", "..."], "confidence": 0.0}
"""


def compare_scenarios(request: ComparisonRequest) -> Tuple[AnalysisResponse, AnalysisResponse, ComparisonVerdict]:
    request_a = AnalysisRequest(
        question=f"{request.decision_context} Specifically: {request.option_a}",
        company_name=request.company_name,
        industry=request.industry,
        additional_context=request.additional_context,
        max_branches=request.max_branches,
    )
    request_b = AnalysisRequest(
        question=f"{request.decision_context} Specifically: {request.option_b}",
        company_name=request.company_name,
        industry=request.industry,
        additional_context=request.additional_context,
        max_branches=request.max_branches,
    )

    logger.info("Running analysis for option A")
    analysis_a = run_analysis(request_a)
    logger.info("Running analysis for option B")
    analysis_b = run_analysis(request_b)

    prompt = (
        f"Decision context: {request.decision_context}\n\n"
        f"Option A: {request.option_a}\n"
        f"Option A recommendation: {analysis_a.recommendation.headline}\n"
        f"Option A confidence: {analysis_a.recommendation.confidence}\n"
        f"Option A key risks: {'; '.join(analysis_a.recommendation.risks_and_caveats)}\n\n"
        f"Option B: {request.option_b}\n"
        f"Option B recommendation: {analysis_b.recommendation.headline}\n"
        f"Option B confidence: {analysis_b.recommendation.confidence}\n"
        f"Option B key risks: {'; '.join(analysis_b.recommendation.risks_and_caveats)}"
    )

    try:
        data = complete_json(prompt, system=COMPARISON_SYSTEM_PROMPT, max_tokens=700)
        verdict = ComparisonVerdict(
            winning_option=data.get("winning_option", "neither/hybrid"),
            rationale=data.get("rationale", ""),
            key_tradeoffs=data.get("key_tradeoffs", []),
            confidence=parse_confidence(data.get("confidence"), default=0.4),
        )
    except (GroqRateLimitError, GroqAuthError, GroqConnectionError) as e:
        reason = type(e).__name__.replace("Groq", "").replace("Error", "").lower()
        logger.error(f"Scenario comparison failed due to a Groq API {reason} issue: {e}")
        verdict = ComparisonVerdict(
            winning_option="neither/hybrid",
            rationale=f"Comparison could not be completed due to a Groq API {reason} issue — review both option analyses directly.",
            key_tradeoffs=[],
            confidence=0.2,
        )
    except Exception as e:
        logger.error(f"Scenario comparison failed unexpectedly: {e}")
        verdict = ComparisonVerdict(
            winning_option="neither/hybrid",
            rationale=f"Comparison could not be completed due to an internal error ({e}) — review both option analyses directly.",
            key_tradeoffs=[],
            confidence=0.2,
        )

    return analysis_a, analysis_b, verdict
