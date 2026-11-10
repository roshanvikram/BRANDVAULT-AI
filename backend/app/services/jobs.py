"""
Durable background jobs (Phase 1a, replaces the R2-6 in-memory store).

Job state is persisted in the `jobs` table, so a page refresh or a backend
restart never loses it. Every status the API reports is one the worker really
wrote: queued -> processing -> completed | failed, or queued -> cancelled.

- Idempotency: a repeated request with the same (org, idempotency_key) returns
  the existing job instead of starting a second one.
- Retries: a handler that raises is retried up to `max_attempts`, then marked
  failed with the error.
- Restart recovery: on startup, jobs left queued/processing by a previous
  process are re-run if they have attempts left, otherwise marked failed.
- Cancellation: only a queued job can be cancelled. A job already processing
  is not interrupted mid-write, and the API says so.

Execution uses a daemon thread per job. A production deployment would swap
`_dispatch` for a real queue worker (RQ/Celery) without changing callers.
"""
from __future__ import annotations

import datetime
import threading
import uuid
from typing import Callable, Dict, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.db.session import SessionLocal
from backend.app.models.job import (
    Job, JOB_QUEUED, JOB_PROCESSING, JOB_COMPLETED, JOB_FAILED, JOB_CANCELLED,
)

# Session factory used by worker threads (tests point this at their own DB).
session_factory = SessionLocal

# kind -> handler(db, job) returning a result reference (e.g. a submission id)
_HANDLERS: Dict[str, Callable[[Session, Job], Optional[str]]] = {}


def register_handler(kind: str):
    def deco(fn):
        _HANDLERS[kind] = fn
        return fn
    return deco


def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


def job_to_dict(job: Job) -> dict:
    return {
        "id": job.id,
        "kind": job.kind,
        "status": job.status,
        "stage": job.stage,
        "attempts": job.attempts,
        "max_attempts": job.max_attempts,
        # Kept for the existing content-analysis caller.
        "submission_id": job.result_ref if job.kind == "content_analysis" else None,
        "result_ref": job.result_ref,
        "error": job.error,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }


def create_job(db: Session, *, org_id: str, kind: str, input_data: dict,
               created_by: Optional[str] = None, idempotency_key: Optional[str] = None,
               max_attempts: int = 2, dispatch: bool = True) -> tuple[Job, bool]:
    """Create (or reuse, by idempotency key) a job. Returns (job, created)."""
    if kind not in _HANDLERS:
        raise ValueError(f"Unknown job kind '{kind}'")
    if idempotency_key:
        existing = db.query(Job).filter(Job.org_id == org_id, Job.idempotency_key == idempotency_key).first()
        if existing:
            return existing, False
    job = Job(
        id=uuid.uuid4().hex, org_id=org_id, kind=kind, status=JOB_QUEUED, stage="Queued",
        idempotency_key=idempotency_key, attempts=0, max_attempts=max(1, max_attempts),
        input_data=input_data, created_by=created_by, created_at=_now(), updated_at=_now(),
    )
    db.add(job)
    try:
        db.commit()
    except IntegrityError:  # concurrent request with the same key won the race
        db.rollback()
        existing = db.query(Job).filter(Job.org_id == org_id, Job.idempotency_key == idempotency_key).first()
        return existing, False
    db.refresh(job)
    if dispatch:
        _dispatch(job.id)
    return job, True


def cancel_job(db: Session, job: Job) -> bool:
    """Cancel a queued job. Returns False if it already started or finished."""
    updated = (
        db.query(Job)
        .filter(Job.id == job.id, Job.status == JOB_QUEUED)
        .update({"status": JOB_CANCELLED, "stage": "Cancelled", "finished_at": _now(), "updated_at": _now()},
                synchronize_session=False)
    )
    db.commit()
    db.refresh(job)
    return bool(updated)


def _set(db: Session, job: Job, **fields) -> None:
    for k, v in fields.items():
        setattr(job, k, v)
    job.updated_at = _now()
    db.commit()


def run_job(job_id: str) -> None:
    """Execute a job to a terminal state. Safe to call from any thread."""
    db = session_factory()
    try:
        # Claim it atomically: only a queued job moves to processing.
        claimed = (
            db.query(Job)
            .filter(Job.id == job_id, Job.status == JOB_QUEUED)
            .update({"status": JOB_PROCESSING, "updated_at": _now()}, synchronize_session=False)
        )
        db.commit()
        if not claimed:
            return  # cancelled, or another worker has it
        job = db.query(Job).filter(Job.id == job_id).first()
        handler = _HANDLERS[job.kind]
        while True:
            _set(db, job, attempts=job.attempts + 1, started_at=job.started_at or _now(),
                 stage=f"Processing (attempt {job.attempts + 1} of {job.max_attempts})")
            try:
                result = handler(db, job)
                _set(db, job, status=JOB_COMPLETED, stage="Completed", result_ref=result,
                     error=None, finished_at=_now())
                return
            except Exception as e:  # noqa: BLE001 - record any handler failure
                db.rollback()
                job = db.query(Job).filter(Job.id == job_id).first()
                if job.attempts >= job.max_attempts:
                    _set(db, job, status=JOB_FAILED, stage="Failed", error=str(e)[:500], finished_at=_now())
                    return
                _set(db, job, error=f"Attempt {job.attempts} failed: {str(e)[:300]}; retrying")
    finally:
        db.close()


def _dispatch(job_id: str) -> None:
    threading.Thread(target=run_job, args=(job_id,), daemon=True).start()


def resume_unfinished(db: Session, dispatch: bool = True) -> int:
    """Startup recovery for jobs a previous process left unfinished."""
    resumed = 0
    for job in db.query(Job).filter(Job.status.in_([JOB_QUEUED, JOB_PROCESSING])).all():
        if job.attempts >= job.max_attempts:
            _set(db, job, status=JOB_FAILED, stage="Failed",
                 error="Interrupted by a server restart with no attempts left.", finished_at=_now())
            continue
        _set(db, job, status=JOB_QUEUED, stage="Re-queued after server restart")
        if dispatch:
            _dispatch(job.id)
        resumed += 1
    return resumed


# ------------------------------- handlers --------------------------------- #
@register_handler("content_analysis")
def _content_analysis(db: Session, job: Job) -> Optional[str]:
    from backend.app.services.analyzer import ContentAnalyzerService
    data = job.input_data or {}
    _set(db, job, stage="Analysing content against your brand DNA")
    sub = ContentAnalyzerService(db).analyze_submission(
        org_id=job.org_id, title=data["title"], content=data["content"],
        submission_id=data.get("submission_id"), author_name=data.get("author_name") or "Creator",
    )
    return sub.id


@register_handler("bulk_analysis")
def _bulk_analysis(db: Session, job: Job) -> Optional[str]:
    """Check many pieces of copy in one job. Results are saved after every item, so a
    restart continues where it stopped instead of starting again."""
    from backend.app.services.analyzer import ContentAnalyzerService
    data = dict(job.input_data or {})
    items = data.get("items") or []
    results = list(data.get("results") or [])
    service = ContentAnalyzerService(db)
    for i in range(len(results), len(items)):
        it = items[i]
        _set(db, job, stage=f"Checking {i + 1} of {len(items)}: {it['title'][:80]}")
        try:
            sub = service.analyze_submission(org_id=job.org_id, title=it["title"], content=it["content"],
                                             author_name=data.get("author_name") or "Creator")
            if it.get("department"):
                sub.department = it["department"][:100]
            crit = sum(1 for f in sub.findings if f.severity == "CRITICAL")
            results.append({"index": i, "title": it["title"], "submission_id": sub.id, "score": sub.overall_score,
                            "critical": crit, "warnings": sum(1 for f in sub.findings if f.severity == "WARNING"),
                            "findings": len(sub.findings), "status": sub.status})
        except Exception as exc:  # noqa: BLE001 - one bad item must not stop the batch
            db.rollback()
            results.append({"index": i, "title": it["title"], "error": f"{type(exc).__name__}: {str(exc)[:200]}"})
        data["results"] = results
        job = db.query(Job).filter(Job.id == job.id).first()
        job.input_data = dict(data)  # reassign so the JSON column is saved
        db.commit()
    done = sum(1 for r in results if "error" not in r)
    _set(db, job, stage=f"Checked {done} of {len(items)}")
    return None
