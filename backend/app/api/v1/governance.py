"""Phase 2 governance APIs: launch readiness, asset lifecycle, consistency
analytics and reviewer intelligence."""
import datetime
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles, resolve_org, ensure_same_org
from backend.app.db.session import get_db
from backend.app.models.brand import BrandRule
from backend.app.models.governance import LaunchReadinessReport
from backend.app.models.passport import AgentRun, AuditLog
from backend.app.models.submission import Submission
from backend.app.models.user import User, ROLE_ADMIN
from backend.app.services import analytics, launch_readiness as lr, lifecycle, reviewer_intel

router = APIRouter(tags=["Governance Intelligence"])


def _audit(db: Session, org_id: str, action: str, user: User, details: str) -> None:
    db.add(AuditLog(id=str(uuid.uuid4()), org_id=org_id, action=action,
                    actor=f"{user.full_name} ({user.role})", details=details))


# ------------------------------------------------------------ launch readiness
@router.get("/launch/checks")
def launch_checks(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    cfg = lr.get_config(db, current.org_id)
    return {"checks": [{"key": k, "label": v, "mandatory": k in (cfg.mandatory or [])} for k, v in lr.CHECKS],
            "approval_validity_days": cfg.approval_validity_days,
            "updated_by": cfg.updated_by, "updated_at": cfg.updated_at.isoformat() if cfg.updated_at else None}


class LaunchConfigIn(BaseModel):
    mandatory: List[str]
    approval_validity_days: int = Field(default=90, ge=1, le=730)


@router.put("/launch/config")
def set_launch_config(payload: LaunchConfigIn, db: Session = Depends(get_db),
                      current: User = Depends(require_roles(ROLE_ADMIN))):
    unknown = [k for k in payload.mandatory if k not in lr.CHECK_LABELS]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown checks: {', '.join(unknown)}")
    cfg = lr.get_config(db, current.org_id)
    cfg.mandatory = sorted(set(payload.mandatory))
    cfg.approval_validity_days = payload.approval_validity_days
    cfg.updated_by, cfg.updated_at = current.full_name, datetime.datetime.utcnow()
    _audit(db, current.org_id, "LAUNCH_POLICY_UPDATED", current,
           f"Mandatory checks: {', '.join(cfg.mandatory) or 'none'}; approvals valid {cfg.approval_validity_days} days.")
    db.commit()
    return launch_checks(db, current)


def _own_sub(db: Session, submission_id: str, user: User) -> Submission:
    s = db.query(Submission).filter(Submission.id == submission_id).first()
    if s is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    ensure_same_org(user, s.org_id)
    return s


@router.post("/launch/{submission_id}/check")
def run_launch_check(submission_id: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    s = _own_sub(db, submission_id, current)
    t0 = datetime.datetime.utcnow()
    report = lr.evaluate(db, s, actor=f"{current.full_name} ({current.role})")
    el = (datetime.datetime.utcnow() - t0).total_seconds()
    db.add(AgentRun(id=str(uuid.uuid4()), org_id=s.org_id, agent_name="Launch Readiness Agent",
                    task_name="Evaluate the pre-launch governance checklist", status="COMPLETED",
                    execution_time_ms=round(el * 1000), execution_time_us=max(1, round(el * 1_000_000)), tokens_used=0,
                    input_preview=s.title[:120], output_preview=f"{report['state']} · {report['counts']}",
                    event_details={"submission_id": s.id, "version": s.version}, created_at=datetime.datetime.utcnow()))
    db.commit()
    return report


@router.get("/launch/{submission_id}/reports")
def launch_reports(submission_id: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    _own_sub(db, submission_id, current)
    rows = (db.query(LaunchReadinessReport).filter(LaunchReadinessReport.submission_id == submission_id)
            .order_by(LaunchReadinessReport.created_at.desc()).limit(20).all())
    return [{"id": r.id, "state": r.state, "version": r.submission_version, "created_by": r.created_by,
             "created_at": r.created_at.isoformat() if r.created_at else None} for r in rows]


# ------------------------------------------------------------ asset lifecycle
@router.get("/governance/lifecycle")
def asset_lifecycle(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return lifecycle.lifecycle(db, current.org_id)


# ------------------------------------------------------------ consistency analytics
@router.get("/analytics/consistency")
def consistency(date_from: Optional[str] = None, date_to: Optional[str] = None, severity: Optional[str] = None,
                category: Optional[str] = None, product: Optional[str] = None, department: Optional[str] = None,
                org_id: Optional[str] = None, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    org_id = resolve_org(org_id, current)
    try:
        r = analytics.consistency(db, org_id, date_from=date_from, date_to=date_to, severity=severity,
                                  category=category, product=product, department=department)
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be YYYY-MM-DD.")
    if r is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return r


# ------------------------------------------------------------ reviewer intelligence
@router.get("/governance/reviewer-intelligence")
def reviewer_intelligence(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return reviewer_intel.analyse(db, current.org_id)


class ProposalIn(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    rule_text: str = Field(min_length=10, max_length=2000)
    category: str = Field(default="Guideline Rule", max_length=100)


@router.post("/governance/reviewer-intelligence/propose")
def propose_rule(payload: ProposalIn, db: Session = Depends(get_db), current: User = Depends(require_roles(ROLE_ADMIN))):
    """Turn a suggestion into a DRAFT rule. It stays unconfirmed (not enforced)
    until an administrator confirms it in Brand DNA Studio."""
    r = BrandRule(id=str(uuid.uuid4()), org_id=current.org_id, category=payload.category, title=payload.title.strip(),
                  rule_text=payload.rule_text.strip(), severity="WARNING", source_document="Reviewer Intelligence proposal",
                  is_active=True, is_confirmed=False)
    db.add(r)
    _audit(db, current.org_id, "RULE_PROPOSED", current, f"Draft rule '{r.title}' from Reviewer Intelligence (unconfirmed).")
    db.commit()
    return {"id": r.id, "title": r.title, "is_confirmed": r.is_confirmed}
