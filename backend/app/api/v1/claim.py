from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.submission import ClaimVerification, Submission
from backend.app.schemas.analysis import ClaimVerificationResponse, SubmissionResponse
from backend.app.services.analyzer import ContentAnalyzerService
from backend.app.services.seed import NOVA_ORG_ID

router = APIRouter(prefix="/claim", tags=["ClaimDNA"])

# Map the 5-status truth model to an evidence state, which distinguishes
# MISSING evidence (unsupported) from CONTRADICTORY evidence (PART 02.3).
_EVIDENCE_STATE = {
    "Supported": "supported",
    "Contradicted": "contradicted",
    "Unsupported": "missing",
    "Outdated": "outdated",
    "Needs Human Review": "review",
}


@router.get("/verifications", response_model=List[ClaimVerificationResponse])
def get_verifications(submission_id: str, db: Session = Depends(get_db)):
    return db.query(ClaimVerification).filter(ClaimVerification.submission_id == submission_id).all()


@router.get("/evidence-map")
def evidence_map(org_id: str = NOVA_ORG_ID, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Claim-to-evidence relationships across the org, with the evidence state,
    source reliability and freshness for each claim (R2-7)."""
    claims = (
        db.query(ClaimVerification)
        .join(ClaimVerification.submission)
        .filter(Submission.org_id == org_id)
        .order_by(ClaimVerification.created_at.desc())
        .limit(60)
        .all()
    )
    # Reliability/freshness reflect the evidence STATE (not merely whether a
    # reference string exists): an unsupported claim has no supporting evidence
    # even if the finding cites the policy that requires verification.
    reliability = {
        "supported": "Approved internal source",
        "contradicted": "Contradicts an approved fact",
        "missing": "No supporting evidence found",
        "outdated": "Approved source has lapsed",
        "review": "Needs human verification",
    }
    freshness = {"supported": "Current", "contradicted": "Current", "outdated": "Outdated"}

    summary = {"supported": 0, "contradicted": 0, "missing": 0, "outdated": 0, "review": 0}
    items = []
    for c in claims:
        state = _EVIDENCE_STATE.get(c.status, "review")
        summary[state] = summary.get(state, 0) + 1
        has_evidence = state in ("supported", "contradicted", "outdated")
        items.append({
            "id": c.id,
            "claim_text": c.claim_text,
            "status": c.status,
            "category": c.category,
            "confidence": c.confidence,
            "explanation": c.explanation,
            "evidence_text": c.evidence_text if has_evidence else None,
            "source_reference": c.source_reference if has_evidence else None,
            "evidence_state": state,
            "source": {
                "present": has_evidence,
                "reliability": reliability.get(state, "Needs human verification"),
                "freshness": freshness.get(state, "—"),
            },
        })
    return {"items": items, "summary": summary, "total": len(items)}

@router.post("/test-sample", response_model=SubmissionResponse)
def run_sample_nova_test(db: Session = Depends(get_db)):
    """
    Executes the standard test example from specification:
    Brand: NOVA TECH
    Approved price: ₹79,999
    Submitted copy:
    'Introducing the world's fastest AI laptop! 10x faster than every competitor. Now only ₹69,999!'
    """
    service = ContentAnalyzerService(db)
    test_content = "Introducing the world's fastest AI laptop! 10x faster than every competitor. Now only ₹69,999!"
    return service.analyze_submission(
        org_id=NOVA_ORG_ID,
        title="NovaBook AI Pro 16 Launch Campaign (Test Submission)",
        content=test_content,
        author_name="Marketing Launch Specialist"
    )

