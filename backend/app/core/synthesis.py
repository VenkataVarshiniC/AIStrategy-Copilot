"""
Synthesis: the final "so what" roll-up. Takes all branch-level findings and
produces a single answer-first recommendation, in the classic consulting
pyramid-principle style: headline first, then supporting points, then caveats.
"""
from typing import List, Optional, Tuple

from app.core.confidence_utils import average_confidence, parse_confidence
from app.llm.groq_client import GroqAuthError, GroqConnectionError, GroqRateLimitError, complete_json
from app.models.schemas import HypothesisFinding, HypothesisStatus, IssueTree, Recommendation
from app.utils.logger import logger

SYNTHESIS_SYSTEM_PROMPT = """You are a McKinsey engagement manager writing the
final recommendation slide for a client. You will be given the original
question and the findings from each MECE branch of the issue tree.

Apply the Pyramid Principle:
- Lead with the answer (headline), not the analysis. Keep the headline to one sentence.
- The executive summary should read like the top of a client deck: 3-4 sentences,
  answer-first, so-what focused. Do not exceed 100 words.
- Supporting points: 2-4 short bullets, each mapping back to a specific branch finding.
- Risks and caveats: 2-4 short bullets. Must explicitly flag any branch marked inconclusive,
  refuted, or based on illustrative/assumed inputs rather than real data.
- Overall confidence should reflect the weighted confidence of all branches
  (lower if key branches are inconclusive).
- Keep the ENTIRE response concise — a long response risks being cut off before it's valid JSON.

Respond with ONLY this compact JSON shape, nothing else:
{"headline": "...", "executive_summary": "...", "supporting_points": ["...", "..."], "risks_and_caveats": ["...", "..."], "confidence": 0.0}
"""


def synthesize_recommendation(
    issue_tree: IssueTree, findings: List[HypothesisFinding]
) -> Tuple[Recommendation, Optional[str]]:
    """Returns (recommendation, warning). `warning` is None unless a technical failure occurred."""
    findings_block = "\n\n".join(
        f"Branch: {f.branch_title}\n"
        f"Status: {f.status.value}\n"
        f"Confidence: {f.confidence}\n"
        f"So-what: {f.so_what}\n"
        f"Quant: {f.quant_result.narrative if f.quant_result else 'none'}"
        for f in findings
    )

    prompt = (
        f"Original question: {issue_tree.root_question}\n"
        f"Restated: {issue_tree.restated_question}\n\n"
        f"Branch findings:\n{findings_block}"
    )

    fallback_confidence = average_confidence([f.confidence for f in findings], default=0.4)

    try:
        data = complete_json(prompt, system=SYNTHESIS_SYSTEM_PROMPT, max_tokens=900)
        recommendation = Recommendation(
            headline=data.get("headline") or "Recommendation unavailable — see executive summary.",
            executive_summary=data.get("executive_summary", ""),
            supporting_points=data.get("supporting_points", []),
            risks_and_caveats=data.get("risks_and_caveats", []),
            confidence=parse_confidence(data.get("confidence"), default=fallback_confidence),
        )
        return recommendation, None

    except (GroqRateLimitError, GroqAuthError, GroqConnectionError) as e:
        reason = type(e).__name__.replace("Groq", "").replace("Error", "").lower()
        logger.error(f"Synthesis failed due to a Groq API {reason} issue: {e}")
        recommendation = _fallback_recommendation(
            findings, f"a Groq API {reason} issue ({e})"
        )
        return recommendation, f"Synthesis failed ({reason}): {e}"

    except Exception as e:
        logger.error(f"Synthesis failed, falling back to a findings-based recommendation: {e}")
        recommendation = _fallback_recommendation(findings, f"an internal error ({e})")
        return recommendation, f"Synthesis failed unexpectedly: {e}"


def _fallback_recommendation(findings: List[HypothesisFinding], reason: str) -> Recommendation:
    """Degrade gracefully instead of 500-ing the whole request: build a plain roll-up directly
    from the findings we already have, and say clearly why the LLM synthesis step didn't run."""
    inconclusive_count = sum(1 for f in findings if f.status == HypothesisStatus.INCONCLUSIVE)
    fallback_confidence = average_confidence([f.confidence for f in findings], default=0.4)
    return Recommendation(
        headline="Synthesis could not be completed automatically — review branch findings below.",
        executive_summary=(
            f"The synthesis step failed due to {reason}, not a data or evidence problem. "
            f"{len(findings)} branch(es) were analyzed, {inconclusive_count} of which were inconclusive. "
            "Review each branch's findings directly, or re-run the analysis."
        ),
        supporting_points=[f"{f.branch_title}: {f.so_what}" for f in findings],
        risks_and_caveats=["Automatic synthesis failed; this recommendation was assembled without LLM roll-up."],
        confidence=fallback_confidence,
    )
