from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile
from backend.app.models.integrity import CampaignIntegrityCheck
from backend.app.services import integrity
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.passport import BrandPassport
from backend.app.models.submission import Submission
from backend.app.schemas.passport import BrandPassportResponse

from backend.app.models.user import User
from backend.app.api.deps import get_current_user, resolve_org, ensure_same_org

router = APIRouter(prefix="/passport", tags=["Brand Passport"])

@router.get("/list", response_model=List[BrandPassportResponse])
def get_passports(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return db.query(BrandPassport).join(BrandPassport.submission).filter(
        Submission.org_id == current.org_id).order_by(BrandPassport.issued_at.desc()).all()

@router.get("/by-submission/{submission_id}", response_model=BrandPassportResponse)
def get_passport_by_submission(submission_id: str, db: Session = Depends(get_db),
                               current: User = Depends(get_current_user)):
    passport = db.query(BrandPassport).filter(BrandPassport.submission_id == submission_id).first()
    if not passport or passport.submission.org_id != current.org_id:
        raise HTTPException(status_code=404, detail="Brand Passport not yet issued for this submission.")
    return passport

# ------------------------- Campaign DNA Fingerprint -------------------------
MAX_VERIFY_BYTES = 2 * 1024 * 1024


@router.post("/verify")
async def verify_campaign_integrity(
    text: Optional[str] = Form(default=None),
    file: Optional[UploadFile] = File(default=None),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Check whether campaign text (or an uploaded .txt/.md file) is exactly an
    approved version. Every check is written to an append-only log."""
    data = None
    name = None
    if file is not None and file.filename:
        data = await file.read()
        name = file.filename
        if len(data) > MAX_VERIFY_BYTES:
            raise HTTPException(status_code=413, detail="File exceeds the 2 MB limit.")
    elif not (text or "").strip():
        raise HTTPException(status_code=400, detail="Provide campaign text or a file.")
    row = integrity.verify_campaign(db, current.org_id, text=text, file_name=name, file_bytes=data,
                                    checked_by=f"{current.full_name} ({current.role})")
    return integrity.integrity_dict(row)


@router.get("/integrity-checks")
def list_integrity_checks(limit: int = 30, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    rows = (db.query(CampaignIntegrityCheck).filter(CampaignIntegrityCheck.org_id == current.org_id)
            .order_by(CampaignIntegrityCheck.created_at.desc()).limit(max(1, min(limit, 200))).all())
    return [integrity.integrity_dict(r) for r in rows]


@router.get("/{passport_number}/fingerprint")
def get_fingerprint(passport_number: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    passport = db.query(BrandPassport).filter(BrandPassport.passport_number == passport_number).first()
    if not passport or passport.submission.org_id != current.org_id:
        raise HTTPException(status_code=404, detail="Passport not found.")
    return {"passport_number": passport.passport_number, "verification_status": passport.verification_status,
            "fingerprint": integrity.fingerprint_for(passport)}


@router.get("/{passport_number}", response_model=BrandPassportResponse)
def get_passport_by_number(passport_number: str, db: Session = Depends(get_db),
                           current: User = Depends(get_current_user)):
    passport = db.query(BrandPassport).filter(BrandPassport.passport_number == passport_number).first()
    if not passport or passport.submission.org_id != current.org_id:
        raise HTTPException(status_code=404, detail="Passport not found.")
    return passport

