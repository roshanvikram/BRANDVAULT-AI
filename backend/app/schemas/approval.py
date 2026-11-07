from pydantic import BaseModel
from typing import Optional, List
import datetime

class ApprovalActionRequest(BaseModel):
    submission_id: str
    reviewer_name: str = "Lead Brand Reviewer"
    reviewer_role: str = "Reviewer"
    decision: str # Approved, Rejected, Revision Requested
    comments: str
    # Optional version lock: the version the reviewer actually looked at.
    expected_version: Optional[int] = None

class ApprovalRecordResponse(BaseModel):
    id: str
    submission_id: str
    reviewer_name: str
    reviewer_role: str
    decision: str
    comments: str
    submission_version: Optional[int] = None
    content_hash: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class RevisionResponse(BaseModel):
    id: str
    submission_id: str
    version: int
    content: str
    change_summary: str
    created_by: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

