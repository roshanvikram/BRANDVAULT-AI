from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.submission import Submission, Finding
from backend.app.models.user import User
from backend.app.schemas.analysis import (
    ContentAnalyzeRequest,
    ApplyCorrectionRequest,
    SubmissionResponse
)
from backend.app.core.config import settings
from backend.app.core.ratelimit import rate_limit
from backend.app.api.deps import get_current_user, resolve_org, ensure_same_org
from backend.app.services.analyzer import ContentAnalyzerService
from backend.app.services import jobs as jobs_svc
from backend.app.models.job import Job

router = APIRouter(prefix="/content", tags=["Content Intelligence"])


def _own_submission(db: Session, submission_id: str, user: User) -> Submission:
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    ensure_same_org(user, submission.org_id)
    return submission


@router.post("/analyze-async", dependencies=[Depends(rate_limit("ai", settings.RATE_LIMIT_AI_PER_MIN))])
def analyze_async(
    payload: ContentAnalyzeRequest,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Start a durable background analysis job and return its id to poll.

    State is stored in the database, so it survives refreshes and restarts.
    Sending the same Idempotency-Key again returns the existing job.
    """
    org_id = resolve_org(payload.org_id, current)
    if payload.submission_id:
        _own_submission(db, payload.submission_id, current)
    job, created = jobs_svc.create_job(
        db, org_id=org_id, kind="content_analysis", created_by=current.id,
        idempotency_key=idempotency_key,
        input_data={"title": payload.title, "content": payload.content,
                    "submission_id": payload.submission_id, "author_name": current.full_name},
    )
    out = jobs_svc.job_to_dict(job)
    out["job_id"] = job.id
    out["reused"] = not created
    return out


@router.get("/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    job = db.query(Job).filter(Job.id == job_id).first()
    # 404 (not 403) for other orgs' jobs, so job ids can't be probed.
    if job is None or job.org_id != current.org_id:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs_svc.job_to_dict(job)


@router.post("/analyze", response_model=SubmissionResponse,
             dependencies=[Depends(rate_limit("ai", settings.RATE_LIMIT_AI_PER_MIN))])
def analyze_content(payload: ContentAnalyzeRequest, db: Session = Depends(get_db),
                    current: User = Depends(get_current_user)):
    org_id = resolve_org(payload.org_id, current)
    if payload.submission_id:
        _own_submission(db, payload.submission_id, current)
    service = ContentAnalyzerService(db)
    submission = service.analyze_submission(
        org_id=org_id,
        title=payload.title,
        content=payload.content,
        submission_id=payload.submission_id,
        # Attribution comes from the authenticated identity.
        author_name=current.full_name,
    )
    if payload.department is not None:
        submission.department = payload.department.strip()[:100] or None
        db.commit()
        db.refresh(submission)
    return submission

@router.get("/submissions", response_model=List[SubmissionResponse])
def get_submissions(org_id: Optional[str] = None, db: Session = Depends(get_db),
                    current: User = Depends(get_current_user)):
    org_id = resolve_org(org_id, current)
    return db.query(Submission).filter(Submission.org_id == org_id).order_by(Submission.updated_at.desc()).all()

@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
def get_submission_detail(submission_id: str, db: Session = Depends(get_db),
                          current: User = Depends(get_current_user)):
    return _own_submission(db, submission_id, current)

@router.post("/apply-correction", response_model=SubmissionResponse)
def apply_correction(payload: ApplyCorrectionRequest, db: Session = Depends(get_db),
                     current: User = Depends(get_current_user)):
    _own_submission(db, payload.submission_id, current)
    finding = db.query(Finding).filter(Finding.id == payload.finding_id).first()
    if not finding or finding.submission_id != payload.submission_id:
        raise HTTPException(status_code=404, detail="Finding not found for this submission")
    service = ContentAnalyzerService(db)
    submission = service.apply_correction(
        submission_id=payload.submission_id,
        finding_id=payload.finding_id,
        target_text=payload.target_text,
        replacement_text=payload.replacement_text,
        actor_name=current.full_name,
    )
    return submission


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    """Cancel a queued job. A job already processing is not interrupted."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None or job.org_id != current.org_id:
        raise HTTPException(status_code=404, detail="Job not found")
    if not jobs_svc.cancel_job(db, job):
        raise HTTPException(status_code=409, detail=f"Job is already {job.status}; only queued jobs can be cancelled.")
    return jobs_svc.job_to_dict(job)
