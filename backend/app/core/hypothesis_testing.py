"""
Hypothesis testing: for a single issue-tree branch, retrieves grounding
evidence via RAG, optionally runs a quantitative model, and asks Claude to
judge whether the evidence supports, refutes, or is inconclusive about the
branch's hypothesis — always citing the retrieved sources, never inventing facts.
"""
from typing import Optional

from app.core.confidence_utils import parse_confidence
from app.llm.ollama_client import complete_json
from app.models.schemas import HypothesisFinding, HypothesisStatus, IssueBranch, QuantResult
from app.rag.retriever import retrieve_evidence
from app.utils.logger import logger

FINDING_SYSTEM_PROMPT = """You are a McKinsey engagement team member synthesizing
findings for one branch of an issue tree. You will be given:
- A hypothesis to test
- Retrieved evidence snippets (may be sparse or empty)
- Optionally, a quantitative analysis result

Rules:
- Base your judgment ONLY on the evidence and quant result provided. Never invent facts or figures.
- If evidence is sparse or absent, say so explicitly and mark status as "inconclusive" —
  do not fabricate confidence.
- Write a tight "so what" (1-3 sentences): the business implication, not a summary of the evidence.
- Assign a confidence score 0.0-1.0 reflecting evidence strength and quantity.

Respond with ONLY this JSON shape:
{
  "status": "supported | partially_supported | refuted | inconclusive",
  "so_what": "...",
  "confidence": 0.0
}
"""


def test_hypothesis(branch: IssueBranch, quant_result: Optional[QuantResult] = None) -> HypothesisFinding:
    evidence = retrieve_evidence(query=f"{branch.title}: {branch.hypothesis}")

    evidence_block = (
        "\n".join(f"- [{e.source}] {e.snippet}" for e in evidence) if evidence else "(no evidence retrieved)"
    )
    quant_block = (
        f"Quant analysis ({quant_result.method}): inputs={quant_result.inputs} outputs={quant_result.outputs}"
        if quant_result
        else "(no quantitative analysis run for this branch)"
    )

    prompt = (
        f"Hypothesis: {branch.hypothesis}\n"
        f"Key questions: {', '.join(branch.key_questions)}\n\n"
        f"Evidence:\n{evidence_block}\n\n"
        f"{quant_block}"
    )

    try:
        data = complete_json(prompt, system=FINDING_SYSTEM_PROMPT, max_tokens=800)
        try:
            status = HypothesisStatus(data.get("status", "inconclusive"))
        except ValueError:
            logger.warning(f"Unrecognized status '{data.get('status')}' — defaulting to inconclusive")
            status = HypothesisStatus.INCONCLUSIVE
        so_what = data.get("so_what") or "Insufficient evidence to draw a conclusion."
        confidence = parse_confidence(data.get("confidence"), default=0.4)
    except Exception as e:
        logger.error(f"Hypothesis testing failed for branch {branch.id}: {e}")
        status = HypothesisStatus.INCONCLUSIVE
        so_what = "Analysis could not be completed due to an internal error; treat this branch as unresolved."
        confidence = 0.0

    return HypothesisFinding(
        branch_id=branch.id,
        branch_title=branch.title,
        status=status,
        so_what=so_what,
        evidence=evidence,
        quant_result=quant_result,
        confidence=round(confidence, 2),
    )
