from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.analysis import SubmissionResponse
from backend.app.services import visual as visual_svc
from backend.app.services.seed import NOVA_ORG_ID

from backend.app.models.user import User
from backend.app.api.deps import get_current_user, resolve_org, ensure_same_org

router = APIRouter(prefix="/visual", tags=["Visual DNA Inspector"])

ALLOWED_EXT = (".png", ".bmp")
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB


class VisualAnalysisResponse(BaseModel):
    submission: SubmissionResponse
    format: str
    dimensions: Dict[str, int]
    metrics: Dict[str, Any]
    ocr: Dict[str, Any]


@router.post("/analyze", response_model=VisualAnalysisResponse)
async def analyze_image(
    org_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Deterministic colour-palette & contrast analysis of an uploaded image.

    Supports PNG (8-bit RGB/RGBA) and BMP (24/32-bit) — the formats decodable in
    pure Python here. JPEG/WebP/SVG return 415 (not faked). OCR is reported as
    unavailable rather than invented.
    """
    org_id = resolve_org(org_id, current)
    fname = (file.filename or "").lower()
    if not fname.endswith(ALLOWED_EXT):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Pixel analysis supports {', '.join(ALLOWED_EXT)} in this environment (no OpenCV/Pillow). JPEG/WebP/SVG are not analysed here.",
        )
    data = await file.read()
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the 10 MB limit.")

    try:
        result = visual_svc.analyze_and_persist(db, org_id, file.filename, data, author_name=current.full_name)
    except ValueError as e:
        if str(e) == "org_not_found":
            raise HTTPException(status_code=404, detail="Organization not found")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Could not decode this image for pixel analysis (unsupported/corrupt PNG or BMP variant).",
        )

    return VisualAnalysisResponse(
        submission=result["submission"],
        format=result["format"],
        dimensions=result["dimensions"],
        metrics=result["metrics"],
        ocr=result["ocr"],
    )
