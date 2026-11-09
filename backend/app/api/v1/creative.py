"""Creative Inspection API (Improvement 1) and organisation settings."""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles
from backend.app.core.config import settings
from backend.app.core.ratelimit import rate_limit
from backend.app.db.session import get_db
from backend.app.models.creative import CreativeInspection
from backend.app.models.submission import Submission
from backend.app.models.user import ROLE_ADMIN, User
from backend.app.services import creative, filestore, ocr, org_settings

router = APIRouter(tags=["Creative Inspection"])
AI_LIMIT = [Depends(rate_limit("ai", settings.RATE_LIMIT_AI_PER_MIN))]


def _out(db: Session, i: CreativeInspection, full: bool = True) -> Dict[str, Any]:
    out = {"id": i.id, "file_name": i.file_name, "kind": i.kind, "mime": i.mime, "score": i.score,
           "text_found": i.text_found, "engine": i.engine, "elapsed_ms": i.elapsed_ms, "note": i.note,
           "submission_id": i.submission_id, "created_by": i.created_by,
           "created_at": i.created_at.isoformat() if i.created_at else None,
           "page_count": len(i.pages or []), "logo_count": len(i.logo_checks or [])}
    if not full:
        return out
    out.update({"pages": [{k: v for k, v in p.items() if k != "image_ref"} | {"has_image": bool(p.get("image_ref"))}
                          for p in (i.pages or [])],
                "corrections": i.corrections or [], "regions": i.regions or [], "logo_checks": i.logo_checks or []})
    sub = db.query(Submission).filter(Submission.id == i.submission_id).first() if i.submission_id else None
    if sub:
        out["submission"] = {
            "id": sub.id, "title": sub.title, "status": sub.status, "overall_score": sub.overall_score,
            "content": sub.content,
            "findings": [{"id": f.id, "category": f.issue_category, "severity": f.severity, "text": f.original_text,
                          "explanation": f.explanation, "rule": f.rule_reference, "evidence": f.evidence_source,
                          "suggestion": f.suggested_correction, "engine": f.analysis_engine or "heuristic"}
                         for f in sub.findings],
            "claims": [{"id": c.id, "text": c.claim_text, "status": c.status, "category": c.category,
                        "explanation": c.explanation} for c in sub.claim_verifications],
        }
    return out


@router.get("/creative/status")
def creative_status(current: User = Depends(get_current_user)):
    return {"ocr": ocr.status(), "limits": {"pdf_pages": creative.MAX_PDF_PAGES, "ocr_pdf_pages": creative.MAX_OCR_PDF_PAGES,
                                            "video_frames": creative.MAX_VIDEO_FRAMES,
                                            "max_mb": {k: v // (1024 * 1024) for k, v in creative.MAX_BYTES.items()}}}


@router.post("/creative/inspect", dependencies=AI_LIMIT)
async def inspect_creative(file: UploadFile = File(...), department: Optional[str] = Form(default=None),
                           db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="The file is empty.")
    try:
        insp = creative.inspect(db, current.org_id, file.filename or "creative", data,
                                author=f"{current.full_name}", department=(department or None))
    except creative.CreativeError as e:
        raise HTTPException(status_code=415, detail=str(e))
    except ocr.OCRUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    return _out(db, insp)


@router.get("/creative/inspections")
def list_inspections(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    rows = (db.query(CreativeInspection).filter(CreativeInspection.org_id == current.org_id)
            .order_by(CreativeInspection.created_at.desc()).limit(30).all())
    return [_out(db, i, full=False) for i in rows]


def _own(db: Session, iid: str, user: User) -> CreativeInspection:
    i = db.query(CreativeInspection).filter(CreativeInspection.id == iid).first()
    if i is None or i.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return i


@router.get("/creative/inspections/{iid}")
def get_inspection(iid: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return _out(db, _own(db, iid, current))


@router.get("/creative/inspections/{iid}/pages/{index}/image")
def page_image(iid: str, index: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    i = _own(db, iid, current)
    page = next((p for p in (i.pages or []) if p.get("index") == index), None)
    if not page or not page.get("image_ref"):
        raise HTTPException(status_code=404, detail="Page image not available")
    mime = i.mime if page["image_ref"] == i.file_ref else "image/png"
    return filestore.response(db, page["image_ref"], mime, current.org_id)


# ------------------------------ organisation settings -------------------------
@router.get("/workspace/settings")
def read_settings(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return {"settings": org_settings.get(db, current.org_id), "defaults": org_settings.DEFAULTS,
            "editable": current.role == ROLE_ADMIN}


@router.put("/workspace/settings")
def write_settings(changes: Dict[str, Any], db: Session = Depends(get_db),
                   current: User = Depends(require_roles(ROLE_ADMIN))):
    try:
        return {"settings": org_settings.update(db, current.org_id, changes, f"{current.full_name} ({current.role})")}
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=422, detail=str(e))
