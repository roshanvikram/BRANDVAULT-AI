from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.submission import ApprovalRecord, Revision, Submission
from backend.app.models.user import User, ROLE_ADMIN, ROLE_REVIEWER
from backend.app.schemas.approval import ApprovalActionRequest, ApprovalRecordResponse, RevisionResponse
from backend.app.schemas.analysis import SubmissionResponse
from backend.app.services.passport_service import PassportService
from backend.app.api.deps import get_current_user, ensure_same_org

router = APIRouter(prefix="/approval", tags=["Approval Hub"])

# Authoritative governance decisions — only a human Reviewer/Administrator may make these.
AUTHORITATIVE_DECISIONS = {"Approved", "Rejected", "Revision Requested"}


@router.post("/decide", response_model=SubmissionResponse)
def submit_decision(
    payload: ApprovalActionRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Record a review decision.

    Security (Milestone D): authentication is required; only Reviewer/Administrator
    may issue an authoritative decision (Approved/Rejected/Revision Requested);
    the decision is attributed to the authenticated user, never to client-supplied
    names (prevents forged approvals); and the user's org must match the
    submission's (tenant isolation). AI agents hold no token, so they cannot
    approve.
    """
    submission = db.query(Submission).filter(Submission.id == payload.submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    ensure_same_org(current, submission.org_id)

    if payload.decision in AUTHORITATIVE_DECISIONS and current.role not in (ROLE_REVIEWER, ROLE_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{current.role}' cannot approve, reject, or request revision. A Reviewer or Administrator is required.",
        )

    service = PassportService(db)
    submission = service.submit_review_decision(
        submission_id=payload.submission_id,
        decision=payload.decision,
        comments=payload.comments,
        # Attribution comes from the authenticated identity, not the request body.
        reviewer_name=current.full_name,
        reviewer_role=current.role,
    )
    return submission

@router.get("/history/{submission_id}", response_model=List[ApprovalRecordResponse])
def get_approval_history(submission_id: str, db: Session = Depends(get_db)):
    return db.query(ApprovalRecord).filter(ApprovalRecord.submission_id == submission_id).order_by(ApprovalRecord.created_at.desc()).all()

@router.get("/revisions/{submission_id}", response_model=List[RevisionResponse])
def get_revisions(submission_id: str, db: Session = Depends(get_db)):
    return db.query(Revision).filter(Revision.submission_id == submission_id).order_by(Revision.created_at.desc()).all()

