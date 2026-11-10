"""Load a campaign's related rows in a few batched queries instead of one query per campaign."""
from sqlalchemy.orm import selectinload

from backend.app.models.submission import Submission

FINDINGS = selectinload(Submission.findings)
CLAIMS = selectinload(Submission.claim_verifications)
APPROVALS = selectinload(Submission.approvals)
PASSPORT = selectinload(Submission.passport)
SUBMISSION_FULL = (FINDINGS, CLAIMS, APPROVALS, PASSPORT)
