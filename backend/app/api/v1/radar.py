from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.db.session import get_db
from backend.app.models.submission import Submission, Finding, ClaimVerification, ApprovalRecord
from backend.app.services.seed import NOVA_ORG_ID

router = APIRouter(prefix="/radar", tags=["Brand Risk Radar"])

@router.get("/metrics")
def get_risk_metrics(org_id: str = NOVA_ORG_ID, db: Session = Depends(get_db)) -> Dict[str, Any]:
    submissions = db.query(Submission).filter(Submission.org_id == org_id).all()
    total_submissions = len(submissions)
    
    # Findings by category
    findings = db.query(Finding).join(Finding.submission).filter(Submission.org_id == org_id).all()
    category_counts: Dict[str, int] = {}
    severity_counts: Dict[str, int] = {"CRITICAL": 0, "WARNING": 0, "SUGGESTION": 0}
    top_repeated_violations: Dict[str, int] = {}

    for f in findings:
        category_counts[f.issue_category] = category_counts.get(f.issue_category, 0) + 1
        if f.severity in severity_counts:
            severity_counts[f.severity] += 1
        top_repeated_violations[f.original_text] = top_repeated_violations.get(f.original_text, 0) + 1

    # Claims status breakdown
    claims = db.query(ClaimVerification).join(ClaimVerification.submission).filter(Submission.org_id == org_id).all()
    claims_breakdown = {
        "Supported": sum(1 for c in claims if c.status == "Supported"),
        "Unsupported": sum(1 for c in claims if c.status == "Unsupported"),
        "Contradicted": sum(1 for c in claims if c.status == "Contradicted"),
        "Outdated": sum(1 for c in claims if c.status == "Outdated"),
        "Needs Human Review": sum(1 for c in claims if c.status == "Needs Human Review")
    }

    # Approvals breakdown
    approvals = db.query(ApprovalRecord).join(ApprovalRecord.submission).filter(Submission.org_id == org_id).all()
    approval_counts = {
        "Approved": sum(1 for a in approvals if a.decision == "Approved"),
        "Revision Requested": sum(1 for a in approvals if a.decision == "Revision Requested"),
        "Rejected": sum(1 for a in approvals if a.decision == "Rejected")
    }

    avg_score = sum(s.overall_score for s in submissions) // max(1, total_submissions) if total_submissions > 0 else 100

    sorted_repeated = sorted(top_repeated_violations.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "organization_id": org_id,
        "brand_health_index": avg_score,
        "total_campaign_submissions": total_submissions,
        "findings_by_severity": severity_counts,
        "findings_by_category": category_counts,
        "claims_risk_breakdown": claims_breakdown,
        "approvals_summary": approval_counts,
        "top_repeated_violations": [{"phrase": item[0], "occurrences": item[1]} for item in sorted_repeated],
        "risk_level": "HIGH" if severity_counts["CRITICAL"] > 3 else ("MEDIUM" if severity_counts["CRITICAL"] > 0 else "LOW")
    }
