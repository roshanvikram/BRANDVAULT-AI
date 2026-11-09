"""Brand Asset Library + Brand Asset Forensics API."""
import datetime
import os
import time
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles
from backend.app.core.config import settings
from backend.app.core.ratelimit import rate_limit
from backend.app.db.session import get_db
from backend.app.models.asset import BrandAsset, AssetInvestigation, ASSET_KINDS, ASSET_STATUSES, CURRENT_STATUSES
from backend.app.models.passport import AgentRun, AuditLog
from backend.app.models.user import User, ROLE_ADMIN
from backend.app.services import forensics as fx
from backend.app.services import filestore

router = APIRouter(prefix="/assets", tags=["Brand Asset Library & Forensics"])

STORAGE_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "storage")
MAX_BYTES = 10 * 1024 * 1024
_EXT = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/bmp": ".bmp"}


def _save(db: Session, org_id: str, folder: str, data: bytes, mime: str) -> str:
    """Store an upload durably (database-backed; survives container restarts)."""
    if mime not in _EXT:
        raise HTTPException(status_code=415, detail="Unsupported image type.")
    return filestore.put(db, org_id, folder, data, mime)


async def _read_image(file: UploadFile) -> bytes:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="The file is empty.")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the 10 MB limit.")
    return data


def _is_current(a: BrandAsset, now: datetime.datetime) -> bool:
    return a.status in CURRENT_STATUSES and (a.valid_until is None or a.valid_until > now) \
        and (a.effective_from is None or a.effective_from <= now)


def _replacement(db: Session, a: BrandAsset, now: datetime.datetime) -> Optional[dict]:
    """The approved, currently valid asset that should be used instead."""
    if _is_current(a, now):
        return None
    cands = [x for x in db.query(BrandAsset).filter(BrandAsset.org_id == a.org_id, BrandAsset.kind == a.kind,
                                                     BrandAsset.name == a.name).all() if _is_current(x, now)]
    if not cands and a.superseded_by_id:
        nxt = db.query(BrandAsset).filter(BrandAsset.id == a.superseded_by_id).first()
        cands = [nxt] if nxt and _is_current(nxt, now) else []
    if not cands:
        return None
    c = max(cands, key=lambda x: x.created_at or now)
    return {"id": c.id, "name": c.name, "version_label": c.version_label}


def _asset_out(db: Session, a: BrandAsset) -> dict:
    now = datetime.datetime.utcnow()
    return {"id": a.id, "name": a.name, "kind": a.kind, "version_label": a.version_label, "status": a.status,
            "current": _is_current(a, now), "width": a.width, "height": a.height, "mime": a.mime, "sha256": a.sha256,
            "phash": a.phash, "colours": a.colours, "supersedes_id": a.supersedes_id,
            "superseded_by_id": a.superseded_by_id, "valid_until": a.valid_until.isoformat() if a.valid_until else None,
            "uploaded_by": a.uploaded_by, "approved_by": a.approved_by,
            "created_at": a.created_at.isoformat() if a.created_at else None, "replacement": _replacement(db, a, now)}


def _own_asset(db: Session, asset_id: str, user: User) -> BrandAsset:
    a = db.query(BrandAsset).filter(BrandAsset.id == asset_id).first()
    if a is None or a.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Asset not found")
    return a


# ------------------------------- library ------------------------------------
@router.get("")
def list_assets(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    rows = db.query(BrandAsset).filter(BrandAsset.org_id == current.org_id).order_by(BrandAsset.created_at.desc()).all()
    return [_asset_out(db, a) for a in rows]


@router.post("")
async def upload_asset(
    file: UploadFile = File(...),
    name: str = Form(..., min_length=2, max_length=255),
    kind: str = Form("logo"),
    version_label: str = Form("v1", max_length=40),
    supersedes_id: Optional[str] = Form(None),
    valid_until: Optional[datetime.datetime] = Form(None),
    db: Session = Depends(get_db),
    current: User = Depends(require_roles(ROLE_ADMIN)),
):
    """Administrators add an official asset (approved on upload). Optionally it
    supersedes an earlier version, which is kept as history, never deleted."""
    if kind not in ASSET_KINDS:
        raise HTTPException(status_code=400, detail=f"kind must be one of {', '.join(ASSET_KINDS)}")
    data = await _read_image(file)
    try:
        fp = fx.fingerprints(data)
    except ValueError as e:
        raise HTTPException(status_code=415, detail=str(e))
    old = _own_asset(db, supersedes_id, current) if supersedes_id else None
    a = BrandAsset(id=str(uuid.uuid4()), org_id=current.org_id, name=name.strip(), kind=kind,
                   version_label=version_label.strip() or "v1", status="active",
                   file_path=_save(db, current.org_id, "assets", data, fp["mime"]), mime=fp["mime"],
                   width=fp["width"], height=fp["height"], sha256=fp["sha256"], phash=fp["phash"], dhash=fp["dhash"],
                   colours=fp["colours"], supersedes_id=old.id if old else None, valid_until=valid_until,
                   effective_from=datetime.datetime.utcnow(), uploaded_by=current.full_name,
                   approved_by=current.full_name)
    db.add(a)
    if old is not None:
        old.status = "superseded"
        old.superseded_by_id = a.id
    db.add(AuditLog(id=str(uuid.uuid4()), org_id=current.org_id, action="ASSET_UPLOADED",
                    actor=f"{current.full_name} ({current.role})",
                    details=f"{kind} '{a.name}' {a.version_label} (sha256 {fp['sha256'][:12]}…)"
                            + (f"; supersedes {old.version_label}" if old else "")))
    db.commit()
    db.refresh(a)
    return _asset_out(db, a)


class StatusIn(BaseModel):
    status: str


@router.post("/{asset_id}/status")
def set_status(asset_id: str, payload: StatusIn, db: Session = Depends(get_db),
               current: User = Depends(require_roles(ROLE_ADMIN))):
    if payload.status not in ASSET_STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of {', '.join(ASSET_STATUSES)}")
    a = _own_asset(db, asset_id, current)
    prev, a.status = a.status, payload.status
    db.add(AuditLog(id=str(uuid.uuid4()), org_id=a.org_id, action="ASSET_STATUS_CHANGED",
                    actor=f"{current.full_name} ({current.role})", details=f"'{a.name}' {a.version_label}: {prev} → {a.status}"))
    db.commit()
    return _asset_out(db, a)


@router.get("/{asset_id}/file")
def asset_file(asset_id: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    a = _own_asset(db, asset_id, current)
    return filestore.response(db, a.file_path, a.mime, current.org_id)


# ------------------------------- forensics ----------------------------------
def _inv_out(i: AssetInvestigation, full: bool = True) -> dict:
    out = {"id": i.id, "file_name": i.file_name, "risk": i.risk, "summary": i.summary, "width": i.width,
           "height": i.height, "sha256": i.sha256, "investigated_by": i.investigated_by, "elapsed_ms": i.elapsed_ms,
           "created_at": i.created_at.isoformat() if i.created_at else None}
    if full:
        out.update({"matches": (i.result or {}).get("matches", []), "note": (i.result or {}).get("note")})
    return out


@router.post("/investigate", dependencies=[Depends(rate_limit("ai", settings.RATE_LIMIT_AI_PER_MIN))])
async def investigate(file: UploadFile = File(...), db: Session = Depends(get_db),
                      current: User = Depends(get_current_user)):
    data = await _read_image(file)
    try:
        fx.load_image(data)
    except ValueError as e:
        raise HTTPException(status_code=415, detail=str(e))
    now = datetime.datetime.utcnow()
    refs = []
    for a in db.query(BrandAsset).filter(BrandAsset.org_id == current.org_id).all():
        try:
            rgb, _, alpha = fx.load_image(filestore.read(db, a.file_path, current.org_id))
        except (OSError, ValueError):
            continue  # missing/corrupt reference file: skip, never fabricate
        refs.append({"id": a.id, "name": a.name, "kind": a.kind, "version_label": a.version_label, "status": a.status,
                     "current": _is_current(a, now), "rgb": rgb, "alpha": alpha, "sha256": a.sha256,
                     "phash": a.phash, "dhash": a.dhash, "replacement": _replacement(db, a, now)})
    t0 = time.perf_counter()
    result = fx.investigate(data, refs)
    elapsed = (time.perf_counter() - t0) * 1000
    if not refs:
        result["summary"] = "No official assets are in the library yet, so nothing could be compared."
    inv = AssetInvestigation(id=str(uuid.uuid4()), org_id=current.org_id, file_name=file.filename or "upload",
                             file_path=_save(db, current.org_id, "investigations", data, result["mime"]), mime=result["mime"],
                             width=result["width"], height=result["height"], sha256=result["sha256"],
                             phash=result["phash"], risk=result["risk"], summary=result["summary"],
                             result={"matches": result["matches"], "note": result["note"], "compared": len(refs)},
                             elapsed_ms=round(elapsed, 1), investigated_by=f"{current.full_name} ({current.role})")
    db.add(inv)
    db.add(AgentRun(id=str(uuid.uuid4()), org_id=current.org_id, agent_name="Asset Forensics Agent",
                    task_name=f"Compare an uploaded image with {len(refs)} official asset(s)", status="COMPLETED",
                    execution_time_ms=round(elapsed), execution_time_us=max(1, round(elapsed * 1000)), tokens_used=0,
                    input_preview=f"{inv.file_name} ({inv.width}x{inv.height})",
                    output_preview=f"risk {inv.risk}: {inv.summary[:160]}",
                    event_details={"matches": len(result["matches"])}, created_at=now))
    db.commit()
    db.refresh(inv)
    out = _inv_out(inv)
    out["compared"] = len(refs)
    return out


@router.get("/investigations")
def list_investigations(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    rows = (db.query(AssetInvestigation).filter(AssetInvestigation.org_id == current.org_id)
            .order_by(AssetInvestigation.created_at.desc()).limit(30).all())
    return [_inv_out(i, full=False) for i in rows]


def _own_inv(db: Session, inv_id: str, user: User) -> AssetInvestigation:
    i = db.query(AssetInvestigation).filter(AssetInvestigation.id == inv_id).first()
    if i is None or i.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return i


@router.get("/investigations/{inv_id}")
def get_investigation(inv_id: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return _inv_out(_own_inv(db, inv_id, current))


@router.get("/investigations/{inv_id}/file")
def investigation_file(inv_id: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    i = _own_inv(db, inv_id, current)
    return filestore.response(db, i.file_path, i.mime, current.org_id)
