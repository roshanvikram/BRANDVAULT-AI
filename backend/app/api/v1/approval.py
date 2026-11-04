from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.submission import ApprovalRecord, Revision
from backend.app.schemas.approval import ApprovalActionRequest, ApprovalRecordResponse, RevisionResponse
from backend.app.schemas.analysis import SubmissionResponse
from backend.app.services.passport_service import PassportService

router = APIRouter(prefix="/approval", tags=["Approval Hub"])

@router.post("/decide", response_model=SubmissionResponse)
def submit_decision(payload: ApprovalActionRequest, db: Session = Depends(get_db)):
    service = PassportService(db)
    submission = service.submit_review_decision(
        submission_id=payload.submission_id,
        decision=payload.decision,
        comments=payload.comments,
        reviewer_name=payload.reviewer_name,
        reviewer_role=payload.reviewer_role
    )
    return submission

@router.get("/history/{submission_id}", response_model=List[ApprovalRecordResponse])
def get_approval_history(submission_id: str, db: Session = Depends(get_db)):
    return db.query(ApprovalRecord).filter(ApprovalRecord.submission_id == submission_id).order_by(ApprovalRecord.created_at.desc()).all()

@router.get("/revisions/{submission_id}", response_model=List[RevisionResponse])
def get_revisions(submission_id: str, db: Session = Depends(get_db)):
    return db.query(Revision).filter(Revision.submission_id == submission_id).order_by(Revision.created_at.desc()).all()

