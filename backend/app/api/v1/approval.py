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


def _check_submission_org(db: Session, submission_id: str, user: User) -> None:
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    ensure_same_org(user, sub.org_id)


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

    # Version lock: refuse a decision made against a version the reviewer did not see.
    if payload.expected_version is not None and payload.expected_version != submission.version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Submission changed to version {submission.version} after you opened it (you reviewed version {payload.expected_version}). Reload and review the current version.",
        )

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
    from backend.app.services import events
    events.emit(db, submission.org_id, "review.decided",
                {"submission_id": submission.id, "title": submission.title, "decision": payload.decision,
                 "version": submission.version, "reviewer": current.full_name},
                title=f"{payload.decision}: {submission.title}", link="/approval-hub",
                body=f"{current.full_name} ({current.role}) — {payload.comments[:200] if payload.comments else 'no comment'}")
    if payload.decision == "Approved" and submission.passport is not None:
        events.emit(db, submission.org_id, "passport.issued",
                    {"submission_id": submission.id, "passport_number": submission.passport.passport_number,
                     "content_hash": submission.passport.content_hash},
                    title=f"Brand Passport {submission.passport.passport_number} issued", link="/brand-passport",
                    body=f"“{submission.title}” version {submission.version} is approved for publishing.")
    return submission

@router.get("/history/{submission_id}", response_model=List[ApprovalRecordResponse])
def get_approval_history(submission_id: str, db: Session = Depends(get_db),
                         current: User = Depends(get_current_user)):
    _check_submission_org(db, submission_id, current)
    return db.query(ApprovalRecord).filter(ApprovalRecord.submission_id == submission_id).order_by(ApprovalRecord.created_at.desc()).all()

@router.get("/revisions/{submission_id}", response_model=List[RevisionResponse])
def get_revisions(submission_id: str, db: Session = Depends(get_db),
                  current: User = Depends(get_current_user)):
    _check_submission_org(db, submission_id, current)
    return db.query(Revision).filter(Revision.submission_id == submission_id).order_by(Revision.created_at.desc()).all()

