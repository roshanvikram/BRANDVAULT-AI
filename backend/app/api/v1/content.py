from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.submission import Submission
from backend.app.schemas.analysis import (
    ContentAnalyzeRequest,
    ApplyCorrectionRequest,
    SubmissionResponse
)
from backend.app.services.analyzer import ContentAnalyzerService
from backend.app.services.seed import NOVA_ORG_ID

router = APIRouter(prefix="/content", tags=["Content Intelligence"])

@router.post("/analyze", response_model=SubmissionResponse)
def analyze_content(payload: ContentAnalyzeRequest, db: Session = Depends(get_db)):
    service = ContentAnalyzerService(db)
    submission = service.analyze_submission(
        org_id=payload.org_id,
        title=payload.title,
        content=payload.content,
        submission_id=payload.submission_id,
        author_name=payload.author_name or "Creator"
    )
    return submission

@router.get("/submissions", response_model=List[SubmissionResponse])
def get_submissions(org_id: str = NOVA_ORG_ID, db: Session = Depends(get_db)):
    return db.query(Submission).filter(Submission.org_id == org_id).order_by(Submission.updated_at.desc()).all()

@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
def get_submission_detail(submission_id: str, db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission

@router.post("/apply-correction", response_model=SubmissionResponse)
def apply_correction(payload: ApplyCorrectionRequest, db: Session = Depends(get_db)):
    service = ContentAnalyzerService(db)
    submission = service.apply_correction(
        submission_id=payload.submission_id,
        finding_id=payload.finding_id,
        target_text=payload.target_text,
        replacement_text=payload.replacement_text
    )
    return submission
