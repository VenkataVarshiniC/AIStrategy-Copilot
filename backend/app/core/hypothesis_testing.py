"""
Hypothesis testing: for a single issue-tree branch, retrieves grounding
evidence via RAG, optionally runs a quantitative model, and asks the model
to judge whether the evidence supports, refutes, or is inconclusive about the
branch's hypothesis — always citing the retrieved sources, never inventing facts.

Two distinct failure modes are handled differently on purpose:
  - Genuinely sparse/absent evidence -> legitimately "inconclusive", per the
    system prompt's own instruction. This is a correct, honest outcome.
  - A Groq API failure (rate limit, auth, connection) -> ALSO marked
    "inconclusive" for schema consistency, but with a so_what that says so
    explicitly, and a warning bubbled up to the orchestrator — this is a
    technical failure, not a finding, and should never be silently confused
    with the former.
"""
from typing import Optional, Tuple

from app.core.confidence_utils import parse_confidence
from app.llm.groq_client import GroqAuthError, GroqConnectionError, GroqRateLimitError, complete_json
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
- Write a tight "so what" in ONE sentence, under 30 words: the business implication,
  not a summary of the evidence. Keep it short — a long answer risks being cut off.
- Assign a confidence score 0.0-1.0 reflecting evidence strength and quantity.
- Keep your entire JSON response compact and under 150 words total.

Respond with ONLY this JSON shape, nothing else:
{"status": "supported | partially_supported | refuted | inconclusive", "so_what": "...", "confidence": 0.0}
"""

# Cap how much evidence text actually goes into the prompt, independent of
# how many chunks retrieval returns — keeps per-call token usage predictable
# against the free-tier tokens-per-minute budget.
MAX_EVIDENCE_ITEMS_IN_PROMPT = 4
MAX_EVIDENCE_SNIPPET_CHARS = 220


def test_hypothesis(
    branch: IssueBranch, quant_result: Optional[QuantResult] = None
) -> Tuple[HypothesisFinding, Optional[str]]:
    """Returns (finding, warning). `warning` is None unless a technical failure occurred."""
    evidence = retrieve_evidence(query=f"{branch.title}: {branch.hypothesis}")

    prompt_evidence = evidence[:MAX_EVIDENCE_ITEMS_IN_PROMPT]
    evidence_block = (
        "\n".join(f"- [{e.source}] {e.snippet[:MAX_EVIDENCE_SNIPPET_CHARS]}" for e in prompt_evidence)
        if prompt_evidence
        else "(no evidence retrieved)"
    )
    quant_block = (
        f"Quant analysis ({quant_result.method}): {quant_result.narrative or quant_result.outputs}"
        if quant_result
        else "(no quantitative analysis run for this branch)"
    )

    prompt = (
        f"Hypothesis: {branch.hypothesis}\n"
        f"Key questions: {', '.join(branch.key_questions)}\n\n"
        f"Evidence:\n{evidence_block}\n\n"
        f"{quant_block}"
    )

    warning: Optional[str] = None

    try:
        data = complete_json(prompt, system=FINDING_SYSTEM_PROMPT, max_tokens=700)
        try:
            status = HypothesisStatus(data.get("status", "inconclusive"))
        except ValueError:
            logger.warning(f"Unrecognized status '{data.get('status')}' — defaulting to inconclusive")
            status = HypothesisStatus.INCONCLUSIVE
        so_what = data.get("so_what") or "Insufficient evidence to draw a conclusion."
        confidence = parse_confidence(data.get("confidence"), default=0.4)

    except (GroqRateLimitError, GroqAuthError, GroqConnectionError) as e:
        # A genuine technical failure, not an evidence-based finding. Say so
        # explicitly rather than silently blending in with real "inconclusive"
        # results — this is the distinction that was previously getting lost.
        reason = type(e).__name__.replace("Groq", "").replace("Error", "").lower()
        logger.error(f"Groq call failed for branch '{branch.title}' ({reason}): {e}")
        status = HypothesisStatus.INCONCLUSIVE
        so_what = (
            f"This branch could not be analyzed due to a Groq API {reason} issue — "
            "this is NOT a conclusion about the evidence. Re-run the analysis."
        )
        confidence = 0.15
        warning = f"Branch '{branch.title}' failed ({reason}): {e}"

    except Exception as e:
        logger.error(f"Hypothesis testing failed for branch '{branch.title}': {e}")
        status = HypothesisStatus.INCONCLUSIVE
        so_what = "Analysis could not be completed due to an internal error; treat this branch as unresolved."
        confidence = 0.15
        warning = f"Branch '{branch.title}' failed unexpectedly: {e}"

    finding = HypothesisFinding(
        branch_id=branch.id,
        branch_title=branch.title,
        status=status,
        so_what=so_what,
        evidence=evidence,
        quant_result=quant_result,
        confidence=round(confidence, 2),
    )
    return finding, warning
