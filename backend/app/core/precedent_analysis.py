"""
Precedent / comparable-case analysis.

Alongside the primary evidence layer (which answers "what does the
evidence say about THIS situation"), this queries a separate ingested
collection of prior case studies / analogous company situations and asks
"what happened when something similar was tried before, and what does that
imply here." This is a distinct retrieval index and a distinct reasoning
step on purpose — precedent-matching is genuinely different from
evidence-grounding, and real senior consultants lean on it heavily.

Precedents are optional: if nothing's been ingested into the precedents
collection, this returns an empty list rather than an error — the primary
pipeline still works fine without it.
"""
from typing import List

from app.llm.groq_client import GroqAuthError, GroqConnectionError, GroqRateLimitError, complete_json
from app.models.schemas import IssueTree, PrecedentInsight
from app.rag.retriever import retrieve_precedents
from app.utils.logger import logger

PRECEDENT_SYSTEM_PROMPT = """You are a McKinsey engagement manager pattern-matching
the current question against prior case studies. You will be given the business
question and retrieved snippets describing analogous historical situations.

Rules:
- Base your analysis ONLY on the retrieved snippets. Never invent a precedent
  that isn't in the provided text.
- For each precedent snippet, extract: what the situation/company was, what the
  outcome was, and what it implies for the current question.
- If a snippet doesn't actually describe a comparable situation, skip it —
  don't force a connection that isn't there.
- Keep each field to one concise sentence.

Respond with ONLY this JSON shape, nothing else:
{"precedents": [{"situation": "...", "outcome": "...", "implication": "...", "source": "..."}]}
"""


def analyze_precedents(issue_tree: IssueTree) -> List[PrecedentInsight]:
    retrieved = retrieve_precedents(query=issue_tree.restated_question, top_k=3)
    if not retrieved:
        return []

    snippets_block = "\n".join(f"- [{e.source}] {e.snippet}" for e in retrieved)
    prompt = f"Business question: {issue_tree.restated_question}\n\nRetrieved precedent snippets:\n{snippets_block}"

    try:
        data = complete_json(prompt, system=PRECEDENT_SYSTEM_PROMPT, max_tokens=600)
        insights = []
        for item in data.get("precedents", []):
            try:
                insights.append(
                    PrecedentInsight(
                        situation=item["situation"],
                        outcome=item["outcome"],
                        implication=item["implication"],
                        source=item.get("source", "unknown"),
                    )
                )
            except KeyError:
                continue  # skip malformed entries rather than failing the whole batch
        return insights

    except (GroqRateLimitError, GroqAuthError, GroqConnectionError) as e:
        reason = type(e).__name__.replace("Groq", "").replace("Error", "").lower()
        logger.error(f"Precedent analysis failed due to a Groq API {reason} issue: {e}")
        return []

    except Exception as e:
        logger.error(f"Precedent analysis failed unexpectedly: {e}")
        return []
