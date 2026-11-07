"""
Campaign integrity verification (Campaign DNA Fingerprint).

Given campaign text (typed or from an uploaded .txt/.md file), decide whether it
is exactly an approved version, an approved campaign that was edited after
approval, a known but unapproved version, or something new. Text is compared
after canonical normalisation (Unicode NFC + whitespace), so line-ending or
spacing differences do not count as a modification, while any change to the
words does.

Images: a byte-level SHA-256 identifies an identical file only. A resized or
re-compressed image has a different hash with the same visual content, so
image files are answered "Unable to Verify" here and pointed to Brand Asset
Forensics, which measures visual similarity.
"""
from __future__ import annotations

import datetime
import difflib
import hashlib
import uuid
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from backend.app.models.integrity import (
    CampaignIntegrityCheck, VERIFIED, MODIFIED, UNKNOWN_VERSION, NEW_UNAPPROVED, UNABLE,
)
from backend.app.models.passport import BrandPassport
from backend.app.models.submission import Submission, Revision
from backend.app.services.passport_service import normalise_content, content_sha256

MODIFIED_THRESHOLD = 0.6  # word-level similarity to call it "the same campaign, edited"


def _ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.split(), b.split(), autojunk=False).ratio()


def word_diff(approved: str, candidate: str) -> List[dict]:
    """Word-level changes from the approved text to the candidate."""
    a, b = approved.split(), candidate.split()
    ops = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        ops.append({"change": tag, "approved": " ".join(a[i1:i2]), "submitted": " ".join(b[j1:j2])})
    return ops[:30]


def _fingerprint(p: BrandPassport) -> dict:
    data = p.passport_data or {}
    fp = dict(data.get("fingerprint") or {})
    if not fp:  # passports issued before fingerprints were recorded
        fp = {"campaign_id": p.submission_id, "brand_id": p.submission.org_id if p.submission else None,
              "content_sha256": content_sha256(data.get("content", "")), "version_bound_hash": p.content_hash,
              "asset_hashes": [], "approved_version": data.get("version"), "guideline_version": p.guideline_version,
              "approval_reference": None, "approver": data.get("approved_by"),
              "timestamp": data.get("certified_timestamp"), "revision_number": None, "reconstructed": True}
    return fp


def verify_campaign(db: Session, org_id: str, *, text: Optional[str], file_name: Optional[str],
                    file_bytes: Optional[bytes], checked_by: str) -> CampaignIntegrityCheck:
    kind = "file" if file_bytes is not None else "text"
    raw_sha = hashlib.sha256(file_bytes if file_bytes is not None else (text or "").encode("utf-8")).hexdigest()

    def record(result: str, explanation: str, similarity=None, passport=None, submission_id=None, details=None):
        row = CampaignIntegrityCheck(
            id=str(uuid.uuid4()), org_id=org_id, checked_by=checked_by, input_kind=kind, input_name=file_name,
            input_sha256=raw_sha, result=result, similarity=similarity,
            matched_passport_number=passport.passport_number if passport else None,
            matched_submission_id=submission_id or (passport.submission_id if passport else None),
            explanation=explanation, details=details or {}, created_at=datetime.datetime.utcnow())
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    if file_bytes is not None:
        name = (file_name or "").lower()
        if name.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")):
            return record(UNABLE, "This is an image. A file hash only proves an identical file; resized or compressed "
                                  "copies differ byte-for-byte. Use Brand Asset Forensics to compare it visually.",
                          details={"hint": "visual-forensics"})
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return record(UNABLE, "The file is not readable text (supported: .txt, .md).")

    candidate = normalise_content(text or "")
    if len(candidate) < 3:
        return record(UNABLE, "No campaign text to verify.")
    cand_sha = content_sha256(candidate)

    passports = (db.query(BrandPassport).join(Submission, BrandPassport.submission_id == Submission.id)
                 .filter(Submission.org_id == org_id).all())

    # 1) Exact match with an approved version.
    best: Tuple[float, Optional[BrandPassport]] = (0.0, None)
    for p in passports:
        approved = normalise_content((p.passport_data or {}).get("content", ""))
        fp = _fingerprint(p)
        if content_sha256(approved) == cand_sha:
            if p.verification_status == "SUPERSEDED":
                return record(UNKNOWN_VERSION, "This exactly matches an approved version that has since been superseded "
                                               "by an edit. It is no longer the approved campaign.",
                              1.0, p, details={"fingerprint": fp})
            return record(VERIFIED, f"Identical to the approved campaign in passport {p.passport_number}.",
                          1.0, p, details={"fingerprint": fp})
        r = _ratio(approved, candidate)
        if r > best[0]:
            best = (r, p)

    # 2) Known submission/revision that was never approved.
    for sub in db.query(Submission).filter(Submission.org_id == org_id).all():
        texts = [sub.content] + [rv.content for rv in db.query(Revision).filter(Revision.submission_id == sub.id).all()]
        if any(content_sha256(t) == cand_sha for t in texts):
            approved_now = sub.passport is not None and sub.passport.verification_status != "SUPERSEDED" and \
                content_sha256((sub.passport.passport_data or {}).get("content", "")) == cand_sha
            if not approved_now:
                return record(UNKNOWN_VERSION, f"This matches a version of “{sub.title}” in BrandVault, but that version "
                                               f"was never approved (current status: {sub.status}).",
                              1.0, sub.passport, submission_id=sub.id)

    # 3) Close to an approved campaign -> edited after approval.
    ratio, p = best
    if p is not None and ratio >= MODIFIED_THRESHOLD:
        approved = normalise_content((p.passport_data or {}).get("content", ""))
        return record(MODIFIED, f"{round(ratio * 100)}% similar to the approved campaign in passport {p.passport_number}, "
                                "but the wording differs. The edit has not been approved.",
                      round(ratio, 4), p, details={"diff": word_diff(approved, candidate), "fingerprint": _fingerprint(p)})

    return record(NEW_UNAPPROVED, "No approved campaign or known version matches this text.",
                  round(ratio, 4) if p else None, None)


def integrity_dict(c: CampaignIntegrityCheck) -> dict:
    return {"id": c.id, "result": c.result, "explanation": c.explanation, "similarity": c.similarity,
            "input_kind": c.input_kind, "input_name": c.input_name, "input_sha256": c.input_sha256,
            "matched_passport_number": c.matched_passport_number, "matched_submission_id": c.matched_submission_id,
            "checked_by": c.checked_by, "details": c.details or {},
            "created_at": c.created_at.isoformat() if c.created_at else None}


def fingerprint_for(p: BrandPassport) -> dict:
    return _fingerprint(p)
