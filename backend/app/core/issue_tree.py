"""
Issue tree generation: takes a raw business question and produces a
consultant-style MECE decomposition — a crisp restatement plus N mutually
exclusive, collectively exhaustive branches, each with a testable hypothesis.

This is the step that most distinguishes this system from a generic
"chatbot that answers business questions" — it forces structured thinking
before any evidence is gathered.
"""
from app.llm.groq_client import complete_json
from app.models.schemas import IssueBranch, IssueTree

ISSUE_TREE_SYSTEM_PROMPT = """You are a senior McKinsey engagement manager known for
crisp, MECE problem structuring. Given a business question, you:
1. Restate the question precisely (what is actually being decided?)
2. Break it into 3-5 mutually exclusive, collectively exhaustive (MECE) branches
   that together fully answer the question, following classic consulting frameworks
   (e.g. market attractiveness / competitive position / operational feasibility / financial viability,
   or an issue-tree structure appropriate to the specific question).
3. For each branch, write ONE testable hypothesis (a specific, falsifiable claim,
   not a vague topic) and 2-3 key questions that must be answered to test it.
4. Tag each branch with the type of analysis it most needs: one of
   "market_sizing", "financial_analysis", "sensitivity", or "qualitative".

Respond with ONLY this JSON shape:
{
  "restated_question": "...",
  "branches": [
    {
      "id": "branch_1",
      "title": "...",
      "hypothesis": "...",
      "analysis_type": "market_sizing | financial_analysis | sensitivity | qualitative",
      "key_questions": ["...", "..."]
    }
  ]
}
"""


def generate_issue_tree(
    question: str,
    company_name: str = None,
    industry: str = None,
    additional_context: str = None,
    max_branches: int = 4,
) -> IssueTree:
    context_lines = [f"Business question: {question}"]
    if company_name:
        context_lines.append(f"Company: {company_name}")
    if industry:
        context_lines.append(f"Industry: {industry}")
    if additional_context:
        context_lines.append(f"Additional context: {additional_context}")
    context_lines.append(f"Produce exactly {max_branches} MECE branches.")

    prompt = "\n".join(context_lines)

    data = complete_json(prompt, system=ISSUE_TREE_SYSTEM_PROMPT, max_tokens=1200)

    branches = [
        IssueBranch(
            id=b.get("id", f"branch_{i+1}"),
            title=b["title"],
            hypothesis=b["hypothesis"],
            analysis_type=b.get("analysis_type", "qualitative"),
            key_questions=b.get("key_questions", []),
        )
        for i, b in enumerate(data["branches"][:max_branches])
    ]

    return IssueTree(
        root_question=question,
        restated_question=data["restated_question"],
        branches=branches,
    )
