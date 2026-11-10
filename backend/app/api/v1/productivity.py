"""Time savers: check many pieces at once, fix everything fixable in one click,
decide on many reviews at once, a fast paged review list, and CSV export.

Safety rules stay the same as for single actions:
* only Reviewers and Administrators make approval decisions, each recorded
  separately in the audit trail under their own name;
* bulk approval skips anything with an unresolved critical finding: those need
  a person to look at them one by one;
* every decision is version-locked, so nothing changed since it was listed is approved.
"""
from __future__ import annotations

import csv
import io
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.app.api.deps import ensure_same_org, get_current_user
from backend.app.core.config import settings
from backend.app.core.ratelimit import rate_limit
from backend.app.db.session import get_db
from backend.app.models.job import Job
from backend.app.models.submission import Finding, Submission
from backend.app.models.user import ROLE_ADMIN, ROLE_REVIEWER, User
from backend.app.schemas.analysis import SubmissionResponse
from backend.app.services import bulk, events
from backend.app.services import jobs as jobs_svc
from backend.app.services.analyzer import ContentAnalyzerService
from backend.app.services.passport_service import PassportService

router = APIRouter(tags=["Productivity"])
AI_LIMIT = [Depends(rate_limit("ai", settings.RATE_LIMIT_AI_PER_MIN))]


# ------------------------------------------------------------ bulk check
class BulkItem(BaseModel):
    title: str = ""
    content: str
    department: str = ""


class BulkIn(BaseModel):
    items: List[BulkItem] = Field(min_length=1)


@router.post("/content/bulk/parse")
async def bulk_parse(files: List[UploadFile] = File(...), current: User = Depends(get_current_user)):
    """Read uploaded files into a list of pieces to check (nothing is saved yet)."""
    items, errors = [], []
    for f in files[:50]:
        data = await f.read(10_000_001)
        if len(data) > 10_000_000:
            errors.append(f"{f.filename}: larger than 10 MB")
            continue
        try:
            items += bulk.parse_file(f.filename or "file", data)
        except bulk.BulkError as e:
            errors.append(str(e))
    return {"items": items[:bulk.MAX_ITEMS], "truncated": max(0, len(items) - bulk.MAX_ITEMS), "errors": errors,
            "max_items": bulk.MAX_ITEMS}


@router.post("/content/bulk", dependencies=AI_LIMIT)
def bulk_start(body: BulkIn, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    """Check up to 200 pieces in one background job. Poll GET /content/bulk/{job_id}."""
    try:
        items = bulk.clean([i.model_dump() for i in body.items])
    except bulk.BulkError as e:
        raise HTTPException(status_code=422, detail=str(e))
    job, _ = jobs_svc.create_job(db, org_id=current.org_id, kind="bulk_analysis", created_by=current.id,
                                 input_data={"items": items, "results": [], "author_name": current.full_name},
                                 max_attempts=3)
    return {"job_id": job.id, "count": len(items)}


def _bulk_out(job: Job) -> dict:
    data = job.input_data or {}
    results = data.get("results") or []
    ok = [r for r in results if "error" not in r]
    out = jobs_svc.job_to_dict(job)
    out.update({"total": len(data.get("items") or []), "done": len(results), "results": results,
                "summary": {"checked": len(ok), "failed": len(results) - len(ok),
                            "with_critical": sum(1 for r in ok if r["critical"]),
                            "clean": sum(1 for r in ok if not r["findings"]),
                            "average_score": round(sum(r["score"] for r in ok) / len(ok)) if ok else None}})
    return out


def _own_bulk(db: Session, job_id: str, user: User) -> Job:
    job = db.query(Job).filter(Job.id == job_id, Job.kind == "bulk_analysis").first()
    if job is None or job.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Batch not found")
    return job


@router.get("/content/bulk/{job_id}")
def bulk_status(job_id: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return _bulk_out(_own_bulk(db, job_id, current))


@router.get("/content/bulk")
def bulk_list(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    """Recent batches in this workspace."""
    rows = (db.query(Job).filter(Job.org_id == current.org_id, Job.kind == "bulk_analysis")
            .order_by(Job.created_at.desc()).limit(20).all())
    return [{k: v for k, v in _bulk_out(j).items() if k != "results"} for j in rows]


def _csv_response(rows: List[list], name: str) -> Response:
    buf = io.StringIO()
    csv.writer(buf).writerows(rows)
    # BOM so Excel opens ₹ and other characters correctly.
    return Response("﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})


@router.get("/content/bulk/{job_id}/export.csv")
def bulk_export(job_id: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    job = _own_bulk(db, job_id, current)
    rows = [["#", "Title", "Score", "Critical", "Warnings", "Findings", "Status", "Error"]]
    for r in (job.input_data or {}).get("results") or []:
        rows.append([r["index"] + 1, r["title"], r.get("score", ""), r.get("critical", ""), r.get("warnings", ""),
                     r.get("findings", ""), r.get("status", ""), r.get("error", "")])
    return _csv_response(rows, f"brandvault-batch-{job_id[:8]}.csv")


# ------------------------------------------------------------ fix all
class FixAllIn(BaseModel):
    submission_id: str
    expected_version: Optional[int] = None


@router.post("/content/fix-all", dependencies=AI_LIMIT)
def fix_all(body: FixAllIn, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    """Apply every suggested fix that is a direct word replacement, then re-check once."""
    sub = db.query(Submission).filter(Submission.id == body.submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    ensure_same_org(current, sub.org_id)
    if body.expected_version is not None and body.expected_version != sub.version:
        raise HTTPException(status_code=409, detail=f"This content changed to version {sub.version}. Reload it first.")
    result, applied, skipped = ContentAnalyzerService(db).fix_all(sub.id, actor_name=current.full_name)
    return {"submission": SubmissionResponse.model_validate(result).model_dump(mode="json"),
            "applied": applied, "skipped": skipped}


# ------------------------------------------------------------ review list
SORTS = {"newest": Submission.updated_at.desc(), "oldest": Submission.updated_at.asc(),
         "score_low": Submission.overall_score.asc(), "score_high": Submission.overall_score.desc()}


@router.get("/content/queue")
def review_queue(status: Optional[str] = None, q: Optional[str] = None, department: Optional[str] = None,
                 sort: Literal["newest", "oldest", "score_low", "score_high"] = "newest",
                 limit: int = 50, offset: int = 0, db: Session = Depends(get_db),
                 current: User = Depends(get_current_user)):
    """A light, paged list for big workspaces: no full text or findings, just what a list needs."""
    base = db.query(Submission).filter(Submission.org_id == current.org_id)
    if status:
        base = base.filter(Submission.status.in_([s.strip() for s in status.split(",") if s.strip()]))
    if department:
        base = base.filter(Submission.department == department)
    if q and q.strip():
        like = f"%{q.strip()}%"
        base = base.filter(or_(Submission.title.ilike(like), Submission.author_name.ilike(like)))
    total = base.count()
    rows = base.order_by(SORTS[sort]).offset(max(0, offset)).limit(max(1, min(limit, 200))).all()
    counts = {}
    if rows:
        for sid, sev, n in (db.query(Finding.submission_id, Finding.severity, func.count())
                            .filter(Finding.submission_id.in_([r.id for r in rows]), Finding.is_applied == False)  # noqa: E712
                            .group_by(Finding.submission_id, Finding.severity)):
            counts.setdefault(sid, {})[sev] = n
    statuses = dict(db.query(Submission.status, func.count()).filter(Submission.org_id == current.org_id)
                    .group_by(Submission.status).all())
    return {"total": total, "limit": limit, "offset": offset, "status_counts": statuses,
            "items": [{"id": r.id, "title": r.title, "status": r.status, "version": r.version, "score": r.overall_score,
                       "author_name": r.author_name, "department": r.department,
                       "critical": counts.get(r.id, {}).get("CRITICAL", 0), "warnings": counts.get(r.id, {}).get("WARNING", 0),
                       "suggestions": counts.get(r.id, {}).get("SUGGESTION", 0),
                       "updated_at": r.updated_at.isoformat() + "Z" if r.updated_at else None} for r in rows]}


@router.get("/content/export.csv")
def export_reviews(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    """Every review in the workspace as a spreadsheet (for reports)."""
    subs = db.query(Submission).filter(Submission.org_id == current.org_id).order_by(Submission.updated_at.desc()).all()
    counts = {}
    for sid, sev, n in (db.query(Finding.submission_id, Finding.severity, func.count())
                        .join(Submission, Submission.id == Finding.submission_id)
                        .filter(Submission.org_id == current.org_id, Finding.is_applied == False)  # noqa: E712
                        .group_by(Finding.submission_id, Finding.severity)):
        counts.setdefault(sid, {})[sev] = n
    rows = [["Title", "Status", "Score", "Version", "Critical", "Warnings", "Suggestions", "Author", "Department", "Updated (UTC)"]]
    for s in subs:
        c = counts.get(s.id, {})
        rows.append([s.title, s.status, s.overall_score, s.version, c.get("CRITICAL", 0), c.get("WARNING", 0),
                     c.get("SUGGESTION", 0), s.author_name, s.department or "",
                     s.updated_at.strftime("%Y-%m-%d %H:%M") if s.updated_at else ""])
    return _csv_response(rows, "brandvault-reviews.csv")


# ------------------------------------------------------------ bulk decisions
class BulkDecisionItem(BaseModel):
    submission_id: str
    expected_version: int


class BulkDecisionIn(BaseModel):
    items: List[BulkDecisionItem] = Field(min_length=1, max_length=100)
    decision: Literal["Approved", "Rejected", "Revision Requested", "Pending Review"]
    comments: str = Field(min_length=3, max_length=2000)


@router.post("/approval/bulk")
def bulk_decide(body: BulkDecisionIn, request: Request, db: Session = Depends(get_db),
                current: User = Depends(get_current_user)):
    """Decide on many reviews at once. Each one is checked and recorded on its own."""
    if body.decision != "Pending Review" and current.role not in (ROLE_REVIEWER, ROLE_ADMIN):
        raise HTTPException(status_code=403, detail="Only Reviewers and Administrators can approve, reject or request revisions.")
    service = PassportService(db)
    done, skipped = [], []
    for it in body.items:
        sub = db.query(Submission).filter(Submission.id == it.submission_id, Submission.org_id == current.org_id).first()
        if not sub:
            skipped.append({"submission_id": it.submission_id, "reason": "not found"})
            continue
        if sub.version != it.expected_version:
            skipped.append({"submission_id": sub.id, "title": sub.title,
                            "reason": f"changed to version {sub.version} since you listed it"})
            continue
        if body.decision == "Approved":
            crit = sum(1 for f in sub.findings if f.severity == "CRITICAL" and not f.is_applied)
            if crit:
                skipped.append({"submission_id": sub.id, "title": sub.title,
                                "reason": f"{crit} critical finding(s): review it on its own"})
                continue
        sub = service.submit_review_decision(submission_id=sub.id, decision=body.decision, comments=body.comments,
                                             reviewer_name=current.full_name, reviewer_role=current.role)
        done.append({"submission_id": sub.id, "title": sub.title, "status": sub.status,
                     "passport": sub.passport.passport_number if body.decision == "Approved" and sub.passport else None})
    if done:
        events.emit(db, current.org_id, "review.decided",
                    {"decision": body.decision, "count": len(done), "reviewer": current.full_name, "bulk": True},
                    title=f"{body.decision}: {len(done)} item(s)", link="/approval-hub",
                    body=f"{current.full_name} ({current.role}) — {body.comments[:200]}")
    return {"decided": done, "skipped": skipped}
