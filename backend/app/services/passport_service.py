import hashlib
import json
import uuid
import datetime
from sqlalchemy.orm import Session
from backend.app.models.submission import Submission, ApprovalRecord, Revision
from backend.app.models.passport import BrandPassport, AuditLog

class PassportService:
    def __init__(self, db: Session):
        self.db = db

    def submit_review_decision(self, submission_id: str, decision: str, comments: str, reviewer_name: str = "Lead Reviewer", reviewer_role: str = "Reviewer") -> Submission:
        submission = self.db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            raise ValueError(f"Submission {submission_id} not found.")

        # Create approval record
        approval = ApprovalRecord(
            id=str(uuid.uuid4()),
            submission_id=submission.id,
            reviewer_name=reviewer_name,
            reviewer_role=reviewer_role,
            decision=decision,
            comments=comments
        )
        self.db.add(approval)

        submission.status = decision # "Approved", "Rejected", "Revision Requested"

        # Record revision history
        revision = Revision(
            id=str(uuid.uuid4()),
            submission_id=submission.id,
            version=submission.version,
            content=submission.content,
            change_summary=f"Reviewer Decision: {decision} — {comments[:80]}",
            created_by=reviewer_name
        )
        self.db.add(revision)

        # If approved, generate Brand Passport!
        if decision == "Approved":
            self.generate_brand_passport(submission, reviewer_name)

        # Audit log
        audit = AuditLog(
            id=str(uuid.uuid4()),
            org_id=submission.org_id,
            action=f"REVIEW_DECISION_{decision.upper().replace(' ', '_')}",
            actor=reviewer_name,
            details=f"Submission '{submission.title}' evaluated. Decision: {decision}. Notes: {comments}"
        )
        self.db.add(audit)

        self.db.commit()
        self.db.refresh(submission)
        return submission

    def generate_brand_passport(self, submission: Submission, reviewer_name: str) -> BrandPassport:
        # Check if passport already exists
        existing = self.db.query(BrandPassport).filter(BrandPassport.submission_id == submission.id).first()
        if existing:
            return existing

        # Compute SHA-256 of verified content
        hasher = hashlib.sha256()
        hasher.update(submission.content.encode("utf-8"))
        hasher.update(str(submission.version).encode("utf-8"))
        hasher.update(submission.org_id.encode("utf-8"))
        content_hash = hasher.hexdigest()

        # Generate unique passport number
        passport_num = f"BV-2026-{uuid.uuid4().hex[:6].upper()}"

        passport_data = {
            "passport_number": passport_num,
            "submission_id": submission.id,
            "title": submission.title,
            "author": submission.author_name,
            "content": submission.content,
            "version": submission.version,
            "score": submission.overall_score,
            "findings_count": len(submission.findings),
            "claims_verified": len(submission.claim_verifications),
            "claims_summary": [
                {
                    "claim": c.claim_text,
                    "status": c.status,
                    "source": c.source_reference
                }
                for c in submission.claim_verifications
            ],
            "approved_by": reviewer_name,
            "certified_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "cryptographic_fingerprint": content_hash
        }

        passport = BrandPassport(
            id=str(uuid.uuid4()),
            passport_number=passport_num,
            submission_id=submission.id,
            brand_name="NOVA TECH" if submission.org_id == "nova-tech-org-001" else "Enterprise Brand",
            content_title=submission.title,
            content_hash=content_hash,
            guideline_version="v2.4",
            verification_status="PASSED" if submission.overall_score >= 80 else "CONDITIONALLY_PASSED",
            final_score=submission.overall_score,
            audited_by=f"Reviewer: {reviewer_name} (BRANDVAULT Governance)",
            passport_data=passport_data,
            issued_at=datetime.datetime.utcnow()
        )
        self.db.add(passport)
        return passport

