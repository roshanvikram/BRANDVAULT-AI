from typing import List
from fastapi import APIRouter, Depends, HTTPException
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

@router.get("/{passport_number}", response_model=BrandPassportResponse)
def get_passport_by_number(passport_number: str, db: Session = Depends(get_db),
                           current: User = Depends(get_current_user)):
    passport = db.query(BrandPassport).filter(BrandPassport.passport_number == passport_number).first()
    if not passport or passport.submission.org_id != current.org_id:
        raise HTTPException(status_code=404, detail="Passport not found.")
    return passport

