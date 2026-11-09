"""
Multimodal Creative Inspection (Round 3 · Improvement 1).

Reads the text inside a creative — an image, a PDF deck or a short video — and
runs the same brand checks used for typed copy:

1. Pages: an image is one page; a PDF uses each page's exact text layer (with
   positions) and falls back to OCR for scanned pages; a video is sampled into
   key frames that are OCR'd.
2. OCR words are corrected against the brand vocabulary (every fix is listed).
3. The recovered text goes through ContentAnalyzerService, creating a normal
   submission with findings and ClaimDNA results.
4. Each finding/claim is located back on the page (page number + box) so the
   UI can draw it over the creative.
5. Official logos from the Asset Library are located with Asset Forensics and
   checked for clear space (edges and nearby text) using the organisation's
   configured ratio.

Limits are reported, never hidden: page and frame caps, OCR confidence, and
"no text found" when nothing was readable.
"""
from __future__ import annotations

import datetime
import io
import os
import re
import tempfile
import time
import uuid
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from backend.app.models.asset import BrandAsset
from backend.app.models.brand import ApprovedFact, Organization, TerminologyRule
from backend.app.models.creative import CreativeInspection
from backend.app.models.passport import AgentRun
from backend.app.models.product import Product
from backend.app.models.submission import Finding, Submission
from backend.app.services import filestore, ocr, org_settings
from backend.app.services import forensics as fx

MAX_PDF_PAGES = 10
MAX_OCR_PDF_PAGES = 4        # scanned pages are slow to OCR on a small server
MAX_VIDEO_FRAMES = 6
MAX_BYTES = {"image": 10 * 1024 * 1024, "pdf": 15 * 1024 * 1024, "video": 25 * 1024 * 1024}
VIDEO_EXT = (".mp4", ".mov", ".webm", ".m4v", ".avi")


class CreativeError(ValueError):
    """Bad input (unsupported type, too large, unreadable). Mapped to HTTP 4xx."""


def detect_kind(data: bytes, filename: str) -> Tuple[str, str]:
    name = (filename or "").lower()
    if data[:5] == b"%PDF-":
        return "pdf", "application/pdf"
    if name.endswith(VIDEO_EXT) or data[4:8] in (b"ftyp",) or data[:4] == b"\x1aE\xdf\xa3":
        return "video", "video/webm" if name.endswith(".webm") else "video/mp4"
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(data))
        fmt = (img.format or "").lower()
        mime = {"png": "image/png", "jpeg": "image/jpeg", "webp": "image/webp", "bmp": "image/bmp"}.get(fmt)
        if mime:
            return "image", mime
    except Exception:
        pass
    raise CreativeError("Unsupported file. Upload a PNG, JPEG, WebP or BMP image, a PDF deck, or an MP4/WebM/MOV video.")


def _png(img) -> bytes:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "PNG")
    return buf.getvalue()


# ------------------------------- page sources --------------------------------
def _pdf_pages(data: bytes) -> Tuple[List[Dict], Optional[str]]:
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(data)
    total = len(pdf)
    note = f"Only the first {MAX_PDF_PAGES} of {total} pages were inspected." if total > MAX_PDF_PAGES else None
    pages, ocr_used = [], 0
    for i in range(min(total, MAX_PDF_PAGES)):
        page = pdf[i]
        scale = 1.5
        img = page.render(scale=scale).to_pil()
        pw, ph = page.get_size()
        tp = page.get_textpage()
        lines = []
        for r in range(tp.count_rects()):
            left, bottom, right, top = tp.get_rect(r)
            text = tp.get_text_bounded(left, bottom, right, top).strip()
            if text:
                lines.append({"text": text, "confidence": 1.0, "low_confidence": False,
                              "box": [round(left * scale), round((ph - top) * scale),
                                      round((right - left) * scale), round((top - bottom) * scale)]})
        entry = {"index": i, "label": f"Page {i + 1}", "width": img.width, "height": img.height,
                 "png": _png(img), "lines": lines, "source": "pdf-text"}
        has_image = any(obj.type == pdfium.raw.FPDF_PAGEOBJ_IMAGE for obj in page.get_objects())
        if sum(len(l["text"]) for l in lines) < 15 and has_image:  # little/no text layer but an image: scanned
            if ocr_used < MAX_OCR_PDF_PAGES:
                # OCR a sharper render (keeps word spacing), then map boxes to the display render.
                hi = 2.5
                rec = ocr.recognise(_png(page.render(scale=hi).to_pil()))
                k = scale / hi
                for line in rec["lines"]:
                    line["box"] = [round(v * k) for v in line["box"]]
                entry["lines"], entry["source"] = rec["lines"], "ocr"
                ocr_used += 1
            else:
                entry["source"] = "skipped"
                note = (note + " " if note else "") + f"Scanned pages after the first {MAX_OCR_PDF_PAGES} were not OCR'd."
        pages.append(entry)
    pdf.close()
    return pages, note


def _video_pages(data: bytes, suffix: str) -> Tuple[List[Dict], Optional[str]]:
    import cv2
    from PIL import Image
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            raise CreativeError("This video could not be decoded.")
        count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        if count <= 0:
            raise CreativeError("This video has no readable frames.")
        n = min(MAX_VIDEO_FRAMES, count)
        idxs = sorted({int(count * (k + 0.5) / n) for k in range(n)})
        pages = []
        for k, fi in enumerate(idxs):
            cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
            ok, frame = cap.read()
            if not ok:
                continue
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            png = _png(img)
            rec = ocr.recognise(png)
            pages.append({"index": k, "label": f"Frame at {fi / fps:.1f}s", "width": img.width, "height": img.height,
                          "png": png, "lines": rec["lines"], "source": "ocr"})
        cap.release()
        note = f"{len(pages)} key frames sampled from {count / fps:.1f}s of video; text that appears only between samples can be missed."
        return pages, note
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def _image_pages(data: bytes) -> Tuple[List[Dict], Optional[str]]:
    rec = ocr.recognise(data)
    return [{"index": 0, "label": "Image", "width": rec["width"], "height": rec["height"], "png": None,
             "lines": rec["lines"], "source": "ocr"}], None


# ------------------------------ text + regions -------------------------------
def _vocabulary(db: Session, org_id: str) -> set:
    texts = [o.name for o in db.query(Organization).filter(Organization.id == org_id).all()]
    texts += [p.name for p in db.query(Product).filter(Product.org_id == org_id).all()]
    for f in db.query(ApprovedFact).filter(ApprovedFact.org_id == org_id).all():
        texts += [f.fact_key, f.fact_value]
    for t in db.query(TerminologyRule).filter(TerminologyRule.org_id == org_id).all():
        texts += [t.prohibited_term, t.preferred_term]
    return ocr.brand_vocabulary(texts)


def _currency(db: Session, org_id: str) -> Optional[str]:
    """The currency symbol used in this organisation's approved prices (only ₹ is restored today)."""
    for f in db.query(ApprovedFact).filter(ApprovedFact.org_id == org_id).all():
        if "₹" in (f.fact_value or ""):
            return "₹"
    return None


_NORM = re.compile(r"[^a-z0-9₹%]+")


def _norm(s: str) -> str:
    return _NORM.sub(" ", (s or "").lower().replace("’", "'")).strip()


def unique_lines(pages: List[Dict]) -> List[str]:
    """Each distinct line once, in reading order. Lines that differ only in spacing (common
    across video frames) count as one; the best-spaced reading is kept."""
    best: Dict[str, str] = {}
    order: List[str] = []
    for p in pages:
        for line in p["lines"]:
            key = _norm(line["text"]).replace(" ", "")
            if not key:
                continue
            if key not in best:
                best[key] = line["text"]
                order.append(key)
            elif line["text"].count(" ") > best[key].count(" "):
                best[key] = line["text"]
    return [best[k] for k in order]


def locate(snippet: str, pages: List[Dict]) -> List[Dict]:
    """Find where a snippet appears: lines that contain it, or lines covering most of its words."""
    target = _norm(snippet)
    if not target:
        return []
    words = set(target.split())
    hits = []
    for p in pages:
        for line in p["lines"]:
            ln = _norm(line["text"])
            if not ln:
                continue
            overlap = len(words & set(ln.split())) / max(1, len(words))
            if target in ln or ln in target and len(ln) > 3 or overlap >= 0.6:
                hits.append({"page": p["index"], "box": line["box"], "text": line["text"]})
    return hits[:6]


# ---------------------------------- logos ------------------------------------
def _logo_refs(db: Session, org_id: str) -> List[dict]:
    from backend.app.api.v1.assets import _is_current  # local import avoids a cycle
    now = datetime.datetime.utcnow()
    refs = []
    for a in db.query(BrandAsset).filter(BrandAsset.org_id == org_id, BrandAsset.kind == "logo").all():
        try:
            rgb, _, alpha = fx.load_image(filestore.read(db, a.file_path, org_id))
        except (OSError, ValueError):
            continue
        refs.append({"id": a.id, "name": a.name, "kind": a.kind, "version_label": a.version_label, "status": a.status,
                     "current": _is_current(a, now), "rgb": rgb, "alpha": alpha, "sha256": a.sha256,
                     "phash": a.phash, "dhash": a.dhash, "replacement": None})
    return refs


def clear_space(bbox: List[int], width: int, height: int, ratio: float, lines: List[Dict]) -> Dict:
    """Measure the empty margin around a logo against the required ratio."""
    x, y, w, h = bbox
    required = ratio * min(w, h)
    edges = {"left": x, "top": y, "right": width - (x + w), "bottom": height - (y + h)}
    tight_edges = {k: v for k, v in edges.items() if v < required}
    zone = (x - required, y - required, x + w + required, y + h + required)
    intruding = []
    for line in lines:
        lx, ly, lw, lh = line["box"]
        overlaps_zone = lx < zone[2] and lx + lw > zone[0] and ly < zone[3] and ly + lh > zone[1]
        inside_logo = lx >= x - 2 and ly >= y - 2 and lx + lw <= x + w + 2 and ly + lh <= y + h + 2
        if overlaps_zone and not inside_logo:
            intruding.append(line["text"])
    return {"required_px": round(required), "min_margin_px": round(min(edges.values())),
            "edges": {k: round(v) for k, v in edges.items()}, "tight_edges": sorted(tight_edges),
            "intruding_text": intruding[:5], "ok": not tight_edges and not intruding}


def _check_logos(db: Session, org_id: str, pages: List[Dict], originals: Dict[int, bytes], ratio: float) -> List[Dict]:
    refs = _logo_refs(db, org_id)
    if not refs:
        return []
    out = []
    for p in pages[:3]:  # logos are checked on the first pages/frames only (speed)
        data = originals.get(p["index"]) or p.get("png")
        if not data:
            continue
        res = fx.investigate(data, refs)
        for m in res["matches"]:
            lm = m.get("logo_match")
            if not lm:
                continue
            cs = clear_space(lm["bbox"], p["width"], p["height"], ratio, p["lines"])
            out.append({"page": p["index"], "asset_name": m["asset_name"], "version_label": m["version_label"],
                        "bbox": lm["bbox"], "confidence": lm["confidence"], "clear_space": cs,
                        "findings": [{"type": f["type"], "severity": f["severity"], "title": f["title"],
                                      "measurement": f["measurement"]} for f in m["findings"]]})
    return out


# --------------------------------- pipeline ----------------------------------
def inspect(db: Session, org_id: str, filename: str, data: bytes, author: str, analyzer=None,
            department: Optional[str] = None) -> CreativeInspection:
    kind, mime = detect_kind(data, filename)
    if len(data) > MAX_BYTES[kind]:
        raise CreativeError(f"File too large for a {kind} ({len(data) // (1024 * 1024)} MB); the limit is {MAX_BYTES[kind] // (1024 * 1024)} MB.")
    t0 = time.perf_counter()
    if kind == "image":
        pages, note = _image_pages(data)
        originals = {0: data}
    elif kind == "pdf":
        pages, note = _pdf_pages(data)
        originals = {}
    else:
        pages, note = _video_pages(data, os.path.splitext(filename or "")[1] or ".mp4")
        originals = {}

    vocab = _vocabulary(db, org_id)
    currency = _currency(db, org_id)
    corrections: List[Dict] = []
    for p in pages:
        for line in p["lines"]:
            if p["source"] == "ocr":
                fixed, fx_list = ocr.correct(line["text"], vocab)
                if currency:
                    fixed, cur_fixes = ocr.restore_currency(fixed, currency)
                    fx_list += cur_fixes
                if fx_list:
                    line["ocr_text"] = line["text"]
                    line["text"] = fixed
                    corrections += [dict(c, page=p["index"]) for c in fx_list]

    ordered = unique_lines(pages)
    text = "\n".join(ordered)

    file_ref = filestore.put(db, org_id, "creatives", data, mime)
    for p in pages:  # rendered PDF pages / video frames are kept for the overlay view
        png = p.pop("png", None)
        p["image_ref"] = file_ref if kind == "image" else (filestore.put(db, org_id, "creative-pages", png, "image/png") if png else None)
        if kind != "image" and png:
            originals[p["index"]] = png

    ratio = org_settings.get(db, org_id)["logo_clear_space_ratio"]
    logo_checks = _check_logos(db, org_id, pages, originals, ratio)

    insp = CreativeInspection(id=str(uuid.uuid4()), org_id=org_id, file_name=filename or "creative", file_ref=file_ref,
                              mime=mime, kind=kind, pages=pages, corrections=corrections, logo_checks=logo_checks,
                              text_found=bool(text.strip()), engine=ocr.ENGINE_NAME if any(p["source"] == "ocr" for p in pages) else "pdf-text",
                              note=note, created_by=author)
    db.add(insp)
    db.commit()

    regions: List[Dict] = []
    sub: Optional[Submission] = None
    if text.strip():
        from backend.app.services.analyzer import ContentAnalyzerService
        svc = analyzer or ContentAnalyzerService(db)
        sub = svc.analyze_submission(org_id, f"Creative: {filename}", text, author_name=author)
        sub.department = department
        extra, deduction = [], 0
        for lc in logo_checks:
            cs = lc["clear_space"]
            if not cs["ok"]:
                why = []
                if cs["tight_edges"]:
                    why.append(f"only {cs['min_margin_px']}px to the {', '.join(cs['tight_edges'])} edge")
                if cs["intruding_text"]:
                    why.append(f"text inside the clear zone (“{cs['intruding_text'][0]}”)")
                extra.append(Finding(id=str(uuid.uuid4()), submission_id=sub.id, issue_category="Logo", severity="WARNING",
                                     original_text=f"{lc['asset_name']} clear space: {'; '.join(why)}",
                                     explanation=f"The logo needs at least {cs['required_px']}px of empty space around it "
                                                 f"({ratio:g} × its shorter side).",
                                     rule_reference="Logo clear-space rule (organisation setting)",
                                     evidence_source=f"Measured on {pages[lc['page']]['label'] if lc['page'] < len(pages) else 'page'}",
                                     confidence=round(float(lc["confidence"]), 2),
                                     suggested_correction="Move nearby text or the logo so the full clear space is empty.",
                                     analysis_engine="visual-cv"))
                deduction += 10
            for f in lc["findings"]:
                if f["severity"] == "high":
                    extra.append(Finding(id=str(uuid.uuid4()), submission_id=sub.id, issue_category="Logo", severity="CRITICAL",
                                         original_text=f"{lc['asset_name']}: {f['title']}", explanation=f["measurement"],
                                         rule_reference="Official logo usage (Asset Library)", evidence_source="Asset Forensics",
                                         confidence=round(float(lc["confidence"]), 2),
                                         suggested_correction="Use the current official logo file without modification.",
                                         analysis_engine="visual-cv"))
                    deduction += 20
        for f in extra:
            db.add(f)
        if deduction:
            sub.overall_score = max(5, sub.overall_score - deduction)
        db.commit()
        db.refresh(sub)
        for f in sub.findings:
            for hit in locate(f.original_text, pages):
                regions.append({"kind": "finding", "id": f.id, "severity": f.severity, "category": f.issue_category,
                                "label": f.original_text[:80], **hit})
        for c in sub.claim_verifications:
            for hit in locate(c.claim_text, pages):
                regions.append({"kind": "claim", "id": c.id, "severity": c.status, "category": c.category,
                                "label": c.claim_text[:80], **hit})
        for lc in logo_checks:
            regions.append({"kind": "logo", "id": lc["asset_name"], "severity": "OK" if lc["clear_space"]["ok"] else "WARNING",
                            "category": "Logo", "label": f"{lc['asset_name']} {lc['version_label']}", "page": lc["page"],
                            "box": lc["bbox"], "text": ""})
        insp.submission_id = sub.id
        insp.score = sub.overall_score
    insp.regions = regions
    insp.elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
    db.add(AgentRun(id=str(uuid.uuid4()), org_id=org_id, agent_name="Creative Inspection Agent",
                    task_name=f"Read and check a {kind} creative ({len(pages)} page(s))", status="COMPLETED",
                    execution_time_ms=round(insp.elapsed_ms), execution_time_us=max(1, round(insp.elapsed_ms * 1000)),
                    tokens_used=0, input_preview=f"{insp.file_name} ({kind})",
                    output_preview=(f"{len(ordered)} text line(s), score {insp.score}" if text.strip() else "No readable text"),
                    event_details={"pages": len(pages), "corrections": len(corrections), "logos": len(logo_checks)},
                    created_at=datetime.datetime.utcnow()))
    db.commit()
    db.refresh(insp)
    return insp
