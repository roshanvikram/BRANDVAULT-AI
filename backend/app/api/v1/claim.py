from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.submission import ClaimVerification
from backend.app.schemas.analysis import ClaimVerificationResponse, SubmissionResponse
from backend.app.services.analyzer import ContentAnalyzerService
from backend.app.services.seed import NOVA_ORG_ID

router = APIRouter(prefix="/claim", tags=["ClaimDNA"])

@router.get("/verifications", response_model=List[ClaimVerificationResponse])
def get_verifications(submission_id: str, db: Session = Depends(get_db)):
    return db.query(ClaimVerification).filter(ClaimVerification.submission_id == submission_id).all()

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
