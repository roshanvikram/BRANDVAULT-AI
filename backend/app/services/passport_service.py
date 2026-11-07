import hashlib
import json
import uuid
import datetime
from sqlalchemy.orm import Session
from backend.app.models.submission import Submission, ApprovalRecord, Revision
from backend.app.models.passport import BrandPassport, AuditLog
from backend.app.models.brand import BrandGuideline

def content_fingerprint(submission: Submission) -> str:
    """SHA-256 over content + version + org — the value an approval is locked to."""
    hasher = hashlib.sha256()
    hasher.update(submission.content.encode("utf-8"))
    hasher.update(str(submission.version).encode("utf-8"))
    hasher.update(submission.org_id.encode("utf-8"))
    return hasher.hexdigest()


def normalise_content(text: str) -> str:
    """Canonical form for integrity hashing: Unicode NFC, unified whitespace."""
    import unicodedata
    import re as _re
    return _re.sub(r"\s+", " ", unicodedata.normalize("NFC", text or "")).strip()


def content_sha256(text: str) -> str:
    return hashlib.sha256(normalise_content(text).encode("utf-8")).hexdigest()


def guideline_version_for(db: Session, org_id: str) -> str:
    """The guideline actually in force: the most recently uploaded document."""
    g = (db.query(BrandGuideline).filter(BrandGuideline.org_id == org_id)
         .order_by(BrandGuideline.created_at.desc()).first())
    if g is None:
        return "No guideline on record"
    return f"{g.filename} (uploaded {g.created_at:%Y-%m-%d})" if g.created_at else g.filename


class PassportService:
    def __init__(self, db: Session):
        self.db = db

    def supersede_for_submission(self, submission: Submission) -> None:
        """Content changed: a passport issued for an earlier version no longer
        certifies this submission. It is kept (history) but marked SUPERSEDED."""
        passport = self.db.query(BrandPassport).filter(BrandPassport.submission_id == submission.id).first()
        if passport and passport.verification_status != "SUPERSEDED":
            passport.verification_status = "SUPERSEDED"
            self.db.add(AuditLog(
                id=str(uuid.uuid4()), org_id=submission.org_id, action="PASSPORT_SUPERSEDED", actor="System",
                details=f"Passport {passport.passport_number} superseded: '{submission.title}' changed to version {submission.version}.",
            ))

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
            comments=comments,
            submission_version=submission.version,
            content_hash=content_fingerprint(submission),
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
            self.db.flush()
            self.generate_brand_passport(submission, reviewer_name, approval_id=approval.id)

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

    def generate_brand_passport(self, submission: Submission, reviewer_name: str,
                                approval_id: str | None = None) -> BrandPassport:
        existing = self.db.query(BrandPassport).filter(BrandPassport.submission_id == submission.id).first()
        content_hash = content_fingerprint(submission)
        if existing and existing.content_hash == content_hash and existing.verification_status != "SUPERSEDED":
            return existing  # already certifies exactly this version

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
        guideline_version = guideline_version_for(self.db, submission.org_id)
        passport_data["fingerprint"] = {
            "campaign_id": submission.id,
            "brand_id": submission.org_id,
            "content_sha256": content_sha256(submission.content),
            "version_bound_hash": content_hash,
            "asset_hashes": [],  # text campaign: no files attached
            "approved_version": submission.version,
            "guideline_version": guideline_version,
            "approval_reference": approval_id,
            "approver": reviewer_name,
            "timestamp": passport_data["certified_timestamp"],
            "revision_number": len(submission.revisions),
        }

        org = submission.organization
        brand_name = org.name if org else "Unknown organisation"
        verification_status = "PASSED" if submission.overall_score >= 80 else "CONDITIONALLY_PASSED"

        if existing:
            # A newer version was approved: re-issue, keeping the earlier issue in history.
            history = list((existing.passport_data or {}).get("previous_issues", []))
            history.append({
                "passport_number": existing.passport_number,
                "version": (existing.passport_data or {}).get("version"),
                "content_hash": existing.content_hash,
                "issued_at": existing.issued_at.isoformat() + "Z" if existing.issued_at else None,
            })
            passport_data["previous_issues"] = history
            existing.passport_number = passport_num
            existing.brand_name = brand_name
            existing.content_title = submission.title
            existing.content_hash = content_hash
            existing.verification_status = verification_status
            existing.final_score = submission.overall_score
            existing.audited_by = f"Reviewer: {reviewer_name} (BRANDVAULT Governance)"
            existing.guideline_version = guideline_version
            existing.passport_data = passport_data
            existing.issued_at = datetime.datetime.utcnow()
            return existing

        passport = BrandPassport(
            id=str(uuid.uuid4()),
            passport_number=passport_num,
            submission_id=submission.id,
            brand_name=brand_name,
            content_title=submission.title,
            content_hash=content_hash,
            guideline_version=guideline_version,
            verification_status=verification_status,
            final_score=submission.overall_score,
            audited_by=f"Reviewer: {reviewer_name} (BRANDVAULT Governance)",
            passport_data=passport_data,
            issued_at=datetime.datetime.utcnow()
        )
        self.db.add(passport)
        return passport

