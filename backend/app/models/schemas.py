"""
Shared data contracts for the AI Strategy Copilot pipeline.

The pipeline flows:
  BusinessQuestion -> IssueTree -> [HypothesisFinding] -> Recommendation
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class AnalysisRequest(BaseModel):
    question: str = Field(..., description="The business question, e.g. 'Should Acme enter the SEA EV market?'")
    company_name: Optional[str] = Field(None, description="Primary company/client the analysis is about")
    industry: Optional[str] = Field(None, description="Industry / sector context")
    additional_context: Optional[str] = Field(None, description="Any extra context the user wants considered")
    max_branches: int = Field(4, ge=2, le=6, description="Number of MECE branches in the issue tree")


class IngestRequest(BaseModel):
    source_urls: List[str] = Field(default_factory=list, description="URLs to scrape and ingest")
    tags: dict = Field(default_factory=dict, description="Metadata tags to attach to ingested chunks")


# ---------------------------------------------------------------------------
# Core domain objects
# ---------------------------------------------------------------------------

class HypothesisStatus(str, Enum):
    PENDING = "pending"
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    REFUTED = "refuted"
    INCONCLUSIVE = "inconclusive"


class IssueBranch(BaseModel):
    id: str
    title: str = Field(..., description="Short label for the branch, e.g. 'Market Attractiveness'")
    hypothesis: str = Field(..., description="Testable hypothesis statement for this branch")
    analysis_type: str = Field(
        "qualitative", description="One of: market_sizing, financial_analysis, sensitivity, qualitative"
    )
    key_questions: List[str] = Field(default_factory=list)


class IssueTree(BaseModel):
    root_question: str
    restated_question: str = Field(..., description="Consultant's crisp restatement of the ask")
    branches: List[IssueBranch]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Evidence(BaseModel):
    source: str
    snippet: str
    score: float = 0.0
    metadata: dict = Field(default_factory=dict)


class QuantResult(BaseModel):
    method: str
    inputs: dict = Field(default_factory=dict)
    outputs: dict = Field(default_factory=dict)
    narrative: Optional[str] = None


class HypothesisFinding(BaseModel):
    branch_id: str
    branch_title: str
    status: HypothesisStatus
    so_what: str = Field(..., description="The 'so what' synthesis for this branch")
    evidence: List[Evidence] = Field(default_factory=list)
    quant_result: Optional[QuantResult] = None
    confidence: float = Field(0.5, ge=0.0, le=1.0)


class Recommendation(BaseModel):
    headline: str = Field(..., description="Answer-first, single-sentence recommendation")
    executive_summary: str
    supporting_points: List[str]
    risks_and_caveats: List[str]
    confidence: float = Field(..., ge=0.0, le=1.0)


class AnalysisResponse(BaseModel):
    request: AnalysisRequest
    issue_tree: IssueTree
    findings: List[HypothesisFinding]
    recommendation: Recommendation
    warnings: List[str] = Field(
        default_factory=list,
        description=(
            "Technical issues encountered during this run (e.g. Groq rate limits, an empty "
            "knowledge base). Distinct from HypothesisStatus.inconclusive, which reflects a "
            "genuine evidence-based finding, not a failure."
        ),
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)
