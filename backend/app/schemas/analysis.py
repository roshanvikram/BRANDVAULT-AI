from pydantic import BaseModel
from typing import Optional, List
import datetime

class FindingResponse(BaseModel):
    id: str
    submission_id: str
    issue_category: str
    severity: str
    original_text: str
    explanation: str
    rule_reference: str
    evidence_source: str
    confidence: float
    suggested_correction: str
    is_applied: bool = False
    analysis_engine: str = "heuristic"
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class ClaimVerificationResponse(BaseModel):
    id: str
    submission_id: str
    claim_text: str
    status: str # Supported, Unsupported, Contradicted, Outdated, Needs Human Review
    category: str
    explanation: str
    evidence_text: Optional[str] = None
    source_reference: Optional[str] = None
    confidence: float
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class ContentAnalyzeRequest(BaseModel):
    # Optional: the server scopes to the caller's organisation from the token.
    org_id: Optional[str] = None
    title: str
    content: str
    author_name: Optional[str] = "Marketing Creator"
    submission_id: Optional[str] = None


class ApplyCorrectionRequest(BaseModel):
    submission_id: str
    finding_id: str
    target_text: str
    replacement_text: str


class SubmissionResponse(BaseModel):
    id: str
    org_id: str
    title: str
    content: str
    version: int
    status: str
    author_name: str
    author_role: str
    overall_score: int
    findings: List[FindingResponse] = []
    claim_verifications: List[ClaimVerificationResponse] = []
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

