"""
Synthesis: the final "so what" roll-up. Takes all branch-level findings and
produces a single answer-first recommendation, in the classic consulting
pyramid-principle style: headline first, then supporting points, then caveats.
"""
from typing import List

from app.core.confidence_utils import average_confidence, parse_confidence
from app.llm.ollama_client import complete_json
from app.models.schemas import HypothesisFinding, IssueTree, Recommendation

SYNTHESIS_SYSTEM_PROMPT = """You are a McKinsey engagement manager writing the
final recommendation slide for a client. You will be given the original
question and the findings from each MECE branch of the issue tree.

Apply the Pyramid Principle:
- Lead with the answer (headline), not the analysis.
- The executive summary should read like the top of a client deck: 3-5 sentences,
  answer-first, so-what focused.
- Supporting points should each map back to a specific branch finding.
- Risks and caveats must explicitly flag any branch marked inconclusive, refuted,
  or based on illustrative/assumed inputs rather than real data.
- Overall confidence should reflect the weighted confidence of all branches
  (lower if key branches are inconclusive).

Respond with ONLY this JSON shape:
{
  "headline": "...",
  "executive_summary": "...",
  "supporting_points": ["...", "..."],
  "risks_and_caveats": ["...", "..."],
  "confidence": 0.0
}
"""


def synthesize_recommendation(issue_tree: IssueTree, findings: List[HypothesisFinding]) -> Recommendation:
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

    data = complete_json(prompt, system=SYNTHESIS_SYSTEM_PROMPT, max_tokens=1200)

    # If the model omits/mangles the overall confidence, fall back to the
    # average of branch-level confidences rather than a meaningless flat 0.5 —
    # this is what "weighted confidence of all branches" should degrade to.
    fallback_confidence = average_confidence([f.confidence for f in findings], default=0.4)

    return Recommendation(
        headline=data.get("headline") or "Recommendation unavailable — see executive summary.",
        executive_summary=data.get("executive_summary", ""),
        supporting_points=data.get("supporting_points", []),
        risks_and_caveats=data.get("risks_and_caveats", []),
        confidence=parse_confidence(data.get("confidence"), default=fallback_confidence),
    )
