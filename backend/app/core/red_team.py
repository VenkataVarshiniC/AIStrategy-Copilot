"""
Red-team / devil's advocate agent.

Runs after synthesis, as a distinct pass with its own persona: given the
final recommendation and all branch findings, actively argue AGAINST the
recommendation rather than summarize it. This mirrors the pressure-testing
every real recommendation goes through before it reaches a client — and is
the single biggest thing distinguishing this from a one-shot RAG answer.

Deliberately a separate LLM call with an adversarial system prompt, not a
follow-up question in the same context — a model asked "now critique your
own answer" tends to hedge/agree with itself. A fresh call with an explicit
adversarial persona and no self-authorship produces sharper challenges.
"""
from typing import List

from app.core.confidence_utils import parse_confidence
from app.llm.groq_client import GroqAuthError, GroqConnectionError, GroqRateLimitError, complete_json
from app.models.schemas import HypothesisFinding, IssueTree, Recommendation, RedTeamCritique, RedTeamVerdict
from app.utils.logger import logger

RED_TEAM_SYSTEM_PROMPT = """You are a skeptical McKinsey partner reviewing a
case team's recommendation before it goes to the client. Your job is to find
the holes, NOT to validate the work. You will be given the recommendation and
the underlying branch findings.

Rules:
- Identify the SINGLE strongest objection to the recommendation — not a laundry
  list, the one argument that would actually worry a client. Be specific and concrete.
- List 2-3 assumptions the analysis is quietly relying on that haven't been proven.
- List 1-3 risks the recommendation doesn't adequately address.
- Decide a verdict: "holds" (recommendation survives scrutiny), "weakened"
  (still directionally right, but materially less certain than it claimed), or
  "reversed" (the objection is serious enough to flip the recommendation).
- Give an adjusted confidence (0.0-1.0) reflecting the recommendation's strength
  AFTER your challenge — this will usually be equal to or lower than the original.
- Be substantive, not performative — do not manufacture an objection just to have one
  if the analysis is genuinely well-grounded; "holds" is a legitimate verdict.
- Keep it concise — under 150 words total.

Respond with ONLY this compact JSON shape, nothing else:
{"strongest_objection": "...", "challenged_assumptions": ["...", "..."], "unresolved_risks": ["...", "..."], "verdict": "holds | weakened | reversed", "adjusted_confidence": 0.0}
"""


def run_red_team_review(
    issue_tree: IssueTree, findings: List[HypothesisFinding], recommendation: Recommendation
) -> RedTeamCritique:
    findings_block = "\n".join(
        f"- {f.branch_title} [{f.status.value}, confidence {f.confidence}]: {f.so_what}" for f in findings
    )

    prompt = (
        f"Question: {issue_tree.restated_question}\n\n"
        f"Recommendation: {recommendation.headline}\n"
        f"Summary: {recommendation.executive_summary}\n"
        f"Stated confidence: {recommendation.confidence}\n\n"
        f"Branch findings:\n{findings_block}"
    )

    try:
        data = complete_json(prompt, system=RED_TEAM_SYSTEM_PROMPT, max_tokens=700)
        try:
            verdict = RedTeamVerdict(data.get("verdict", "holds"))
        except ValueError:
            logger.warning(f"Unrecognized red-team verdict '{data.get('verdict')}' — defaulting to 'weakened'")
            verdict = RedTeamVerdict.WEAKENED

        return RedTeamCritique(
            strongest_objection=data.get("strongest_objection") or "No specific objection surfaced.",
            challenged_assumptions=data.get("challenged_assumptions", []),
            unresolved_risks=data.get("unresolved_risks", []),
            verdict=verdict,
            adjusted_confidence=parse_confidence(data.get("adjusted_confidence"), default=recommendation.confidence),
        )

    except (GroqRateLimitError, GroqAuthError, GroqConnectionError) as e:
        reason = type(e).__name__.replace("Groq", "").replace("Error", "").lower()
        logger.error(f"Red-team review failed due to a Groq API {reason} issue: {e}")
        return RedTeamCritique(
            strongest_objection=f"Red-team review could not run due to a Groq API {reason} issue — not a finding.",
            challenged_assumptions=[],
            unresolved_risks=["Red-team review did not complete; recommendation is unreviewed."],
            verdict=RedTeamVerdict.WEAKENED,
            adjusted_confidence=recommendation.confidence * 0.8,
        )

    except Exception as e:
        logger.error(f"Red-team review failed unexpectedly: {e}")
        return RedTeamCritique(
            strongest_objection="Red-team review could not run due to an internal error — not a finding.",
            challenged_assumptions=[],
            unresolved_risks=["Red-team review did not complete; recommendation is unreviewed."],
            verdict=RedTeamVerdict.WEAKENED,
            adjusted_confidence=recommendation.confidence * 0.8,
        )
