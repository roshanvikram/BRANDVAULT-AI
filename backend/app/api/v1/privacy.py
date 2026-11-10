"""Data protection: export the workspace's data, close your account, delete the workspace.

These are the controls a company needs for GDPR / India DPDP requests:
access and portability (export), erasure (account and workspace deletion).
Every action is written to the security log.
"""
from __future__ import annotations

import datetime
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles
from backend.app.core.security import hash_password, verify_password
from backend.app.db.session import get_db
from backend.app.models.brand import Organization
from backend.app.models.user import ROLE_ADMIN, User
from backend.app.services import audit, orgdata
from backend.app.services.analytics import DEMO_ORGS

router = APIRouter(prefix="/privacy", tags=["Data protection"])


def _check_password(user: User, password: Optional[str]) -> None:
    if user.auth_provider == "google" and not password:
        return  # federated account: no local password to confirm with
    if not verify_password(password or "", user.salt or "", user.password_hash or ""):
        raise HTTPException(status_code=400, detail="Your password is not correct.")


@router.get("/summary")
def summary(db: Session = Depends(get_db), current: User = Depends(require_roles(ROLE_ADMIN))):
    """How many records of each kind the workspace holds (what an export or deletion covers)."""
    c = orgdata.counts(db, current.org_id)
    return {"tables": c, "total_records": sum(c.values()), "demo_workspace": current.org_id in DEMO_ORGS}


@router.get("/export")
def export(request: Request, include_files: bool = True, db: Session = Depends(get_db),
           current: User = Depends(require_roles(ROLE_ADMIN))):
    """Download every record the workspace owns as a ZIP (JSON plus uploaded files)."""
    blob = orgdata.export_zip(db, current.org_id, include_files=include_files)
    audit.record(db, "data.exported", org_id=current.org_id, actor=current.email,
                 detail={"bytes": len(blob), "files": include_files}, request=request)
    stamp = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M")
    return Response(blob, media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="brandvault-export-{stamp}.zip"'})


class Confirm(BaseModel):
    password: Optional[str] = None
    confirm: str = ""


@router.post("/delete-account")
def delete_account(body: Confirm, request: Request, db: Session = Depends(get_db),
                   current: User = Depends(get_current_user)):
    """Close your own account. Your name and email are removed; records you created
    (reviews, approvals) stay with the workspace, attributed to "Deleted user"."""
    if body.confirm.strip().upper() != "DELETE":
        raise HTTPException(status_code=400, detail='Type DELETE to confirm.')
    _check_password(current, body.password)
    if current.org_id in DEMO_ORGS and current.email.endswith(".demo"):
        raise HTTPException(status_code=403, detail="The shared demo accounts cannot be deleted.")
    if current.role == ROLE_ADMIN:
        others = db.query(User).filter(User.org_id == current.org_id, User.id != current.id,
                                       User.is_active == True).count()  # noqa: E712
        admins = db.query(User).filter(User.org_id == current.org_id, User.id != current.id,
                                       User.role == ROLE_ADMIN, User.is_active == True).count()  # noqa: E712
        if others and not admins:
            raise HTTPException(status_code=400, detail="You are the only Administrator. Make someone else an Administrator first, or delete the whole workspace.")
    old_email = current.email
    current.email = f"deleted-{uuid.uuid4().hex[:12]}@deleted.invalid"
    current.full_name = "Deleted user"
    current.salt, current.password_hash = hash_password(uuid.uuid4().hex)
    current.mfa_secret, current.mfa_enabled, current.google_sub = None, False, None
    current.is_active = False
    current.token_version = int(current.token_version or 0) + 1
    db.commit()
    audit.record(db, "account.deleted", org_id=current.org_id, actor="(deleted user)",
                 detail={"email_domain": old_email.split("@")[-1]}, request=request)
    return {"deleted": True}


@router.post("/delete-workspace")
def delete_workspace(body: Confirm, request: Request, db: Session = Depends(get_db),
                     current: User = Depends(require_roles(ROLE_ADMIN))):
    """Permanently erase the workspace and everything in it. Cannot be undone."""
    org = db.query(Organization).filter(Organization.id == current.org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    if org.id in DEMO_ORGS:
        raise HTTPException(status_code=403, detail="The shared demo workspace cannot be deleted.")
    if body.confirm.strip() != org.name:
        raise HTTPException(status_code=400, detail="Type the workspace name exactly to confirm.")
    _check_password(current, body.password)
    name, actor = org.name, current.email
    removed = orgdata.erase(db, org.id)
    db.commit()
    db.info.pop("bv_org", None)  # the workspace is gone: log the deletion outside its tenant scope
    audit.record(db, "workspace.deleted", org_id=None, actor=actor, target=name,
                 detail={"records": sum(removed.values())}, request=request)
    return {"deleted": True, "records_removed": sum(removed.values()), "tables": removed}
