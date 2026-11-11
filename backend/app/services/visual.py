"""
Visual DNA analysis for BRANDVAULT AI (Milestone F).

Honest scope: this performs REAL, deterministic colour measurement on images it
can decode in pure Python (PNG 8-bit RGB/RGBA non-interlaced, and BMP 24/32-bit)
— no OpenCV/Pillow/numpy are available in this environment, so JPEG/WebP/SVG and
exotic PNGs are reported as "unsupported for pixel analysis" rather than faked.

What is MEASURED (deterministic): dominant colour palette, the fraction of
chromatic (non-grayscale) pixels vs the brand's monochrome palette, and a
luminance-contrast proxy. What is NOT available: OCR text extraction (no
Tesseract) — exposed as an unavailable provider seam, never fabricated. The
previous UI invented OCR text and all-"PASSED" checks; this replaces that with
only what can actually be computed.
"""
from __future__ import annotations

import struct
import uuid
import zlib
from typing import Dict, List, Optional, Tuple

Pixel = Tuple[int, int, int]


# --------------------------- decoders (pure Python) ------------------------ #
def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def _decode_png(data: bytes) -> Optional[Dict]:
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    pos = 8
    width = height = bit_depth = color_type = interlace = None
    idat = bytearray()
    try:
        while pos < len(data):
            length = struct.unpack(">I", data[pos:pos + 4])[0]
            ctype = data[pos + 4:pos + 8]
            body = data[pos + 8:pos + 8 + length]
            pos += 12 + length  # 4 len + 4 type + body + 4 crc
            if ctype == b"IHDR":
                width, height, bit_depth, color_type, _comp, _filt, interlace = struct.unpack(">IIBBBBB", body)
            elif ctype == b"IDAT":
                idat += body
            elif ctype == b"IEND":
                break
    except Exception:
        return None
    if None in (width, height) or bit_depth != 8 or interlace != 0 or color_type not in (2, 6):
        return None  # unsupported PNG variant — do not guess
    channels = 3 if color_type == 2 else 4
    try:
        raw = zlib.decompress(bytes(idat))
    except Exception:
        return None
    stride = width * channels
    if len(raw) < (stride + 1) * height:
        return None
    pixels: List[Pixel] = []
    prev = bytearray(stride)
    i = 0
    # Sample at most ~40k pixels for speed; step across scanlines/pixels.
    row_step = max(1, height // 200)
    col_step = max(1, width // 200)
    for y in range(height):
        ftype = raw[i]; i += 1
        line = bytearray(raw[i:i + stride]); i += stride
        if ftype == 1:      # Sub
            for x in range(channels, stride):
                line[x] = (line[x] + line[x - channels]) & 0xFF
        elif ftype == 2:    # Up
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 0xFF
        elif ftype == 3:    # Average
            for x in range(stride):
                a = line[x - channels] if x >= channels else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 0xFF
        elif ftype == 4:    # Paeth
            for x in range(stride):
                a = line[x - channels] if x >= channels else 0
                c = prev[x - channels] if x >= channels else 0
                line[x] = (line[x] + _paeth(a, prev[x], c)) & 0xFF
        prev = line
        if y % row_step == 0:
            for x in range(0, width, col_step):
                off = x * channels
                pixels.append((line[off], line[off + 1], line[off + 2]))
    return {"width": width, "height": height, "format": "png", "pixels": pixels}


def _decode_bmp(data: bytes) -> Optional[Dict]:
    if data[:2] != b"BM":
        return None
    try:
        pixel_offset = struct.unpack("<I", data[10:14])[0]
        width = struct.unpack("<i", data[18:22])[0]
        height = struct.unpack("<i", data[22:26])[0]
        bpp = struct.unpack("<H", data[28:30])[0]
        compression = struct.unpack("<I", data[30:34])[0]
    except Exception:
        return None
    if compression != 0 or bpp not in (24, 32) or width <= 0:
        return None
    channels = bpp // 8
    abs_h = abs(height)
    row_size = ((bpp * width + 31) // 32) * 4  # padded to 4 bytes
    pixels: List[Pixel] = []
    row_step = max(1, abs_h // 200)
    col_step = max(1, width // 200)
    for ry in range(0, abs_h, row_step):
        y = ry if height < 0 else (abs_h - 1 - ry)  # bottom-up unless negative height
        base = pixel_offset + y * row_size
        for x in range(0, width, col_step):
            off = base + x * channels
            if off + 3 > len(data):
                continue
            b, g, r = data[off], data[off + 1], data[off + 2]  # BMP is BGR
            pixels.append((r, g, b))
    return {"width": width, "height": abs_h, "format": "bmp", "pixels": pixels}


def decode_image(data: bytes) -> Optional[Dict]:
    """Decode to sampled RGB pixels, or None if the format is unsupported here."""
    if not data:
        return None
    return _decode_png(data) or _decode_bmp(data) or _decode_pillow(data)


def _decode_pillow(data: bytes) -> Optional[Dict]:
    """JPEG/WebP (and PNG variants the pure-Python path skips) via Pillow, sampled the same way."""
    try:
        import io
        from PIL import Image
        img = Image.open(io.BytesIO(data))
        fmt = (img.format or "").lower()
        if fmt not in ("jpeg", "webp", "png", "bmp"):
            return None
        img = img.convert("RGB")
        w, h = img.size
        small = img.resize((min(w, 200), min(h, 200)))
        return {"width": w, "height": h, "format": fmt, "pixels": list(small.getdata())}
    except Exception:
        return None


# --------------------------- metrics (measured) ---------------------------- #
def _saturation(r: int, g: int, b: int) -> float:
    mx, mn = max(r, g, b), min(r, g, b)
    return 0.0 if mx == 0 else (mx - mn) / mx


def _luminance(r: int, g: int, b: int) -> float:
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def compute_metrics(pixels: List[Pixel]) -> Dict:
    n = len(pixels)
    if n == 0:
        return {"pixels_sampled": 0}
    chromatic = sum(1 for (r, g, b) in pixels if _saturation(r, g, b) >= 0.12)
    lums = [_luminance(r, g, b) for (r, g, b) in pixels]
    # Dominant palette: quantize each channel to 0/128/255 buckets.
    buckets: Dict[Tuple[int, int, int], int] = {}
    def q(v): return 0 if v < 85 else (128 if v < 170 else 255)
    for (r, g, b) in pixels:
        key = (q(r), q(g), q(b))
        buckets[key] = buckets.get(key, 0) + 1
    palette = [
        {"hex": "#%02X%02X%02X" % k, "proportion": round(v / n, 3)}
        for k, v in sorted(buckets.items(), key=lambda kv: -kv[1])[:5]
    ]
    return {
        "pixels_sampled": n,
        "chromatic_fraction": round(chromatic / n, 3),
        "monochrome_fraction": round(1 - chromatic / n, 3),
        "contrast": round((max(lums) - min(lums)) / 255.0, 3),
        "avg_luminance": round(sum(lums) / n / 255.0, 3),
        "dominant_palette": palette,
    }


# --------------------------- OCR seam (honest) ----------------------------- #
class OCRProvider:
    name = "none"
    available = False

    def extract_text(self, data: bytes) -> Optional[str]:
        return None


class NullOCR(OCRProvider):
    """No OCR engine installed. Never fabricates text."""
    reason = "OCR engine not installed in this environment."


class RapidOCRProvider(OCRProvider):
    """Real OCR (services/ocr.py). Returns the recognised lines in reading order."""
    name = "rapidocr-onnx"
    available = True

    def extract_text(self, data: bytes) -> Optional[str]:
        from backend.app.services import ocr as ocr_svc
        try:
            return "\n".join(l["text"] for l in ocr_svc.recognise(data)["lines"]) or None
        except Exception:
            return None


class SkippedOCR(OCRProvider):
    """Visual DNA measures colour and contrast; reading text is Creative Inspection's job.
    Skipping it here keeps a small (512 MB) server from running out of memory."""
    skipped = True
    reason = "Text in images is read in Creative Inspection, which also checks the claims it finds."


def get_ocr_provider() -> OCRProvider:
    from backend.app.core.config import settings
    from backend.app.services import ocr as ocr_svc
    if not settings.VISUAL_DNA_OCR:
        return SkippedOCR()
    return RapidOCRProvider() if ocr_svc.available() else NullOCR()


# --------------------------- persistence / orchestration ------------------- #
def analyze_and_persist(db, org_id: str, filename: str, data: bytes, author_name: str = "Creator") -> Dict:
    """Decode + measure an image, persist a Visual submission with findings and a
    Visual DNA Agent run. Raises ValueError('unsupported') if the image cannot be
    decoded in this environment (caller maps that to HTTP 415)."""
    import time
    import datetime
    from backend.app.models.brand import Organization
    from backend.app.models.submission import Submission, Finding
    from backend.app.models.passport import AgentRun, AuditLog
    from backend.app.services.rag import RagRetriever

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise ValueError("org_not_found")

    decoded = decode_image(data)
    if decoded is None:
        raise ValueError("unsupported")

    start = time.perf_counter()
    metrics = compute_metrics(decoded["pixels"])
    ocr = get_ocr_provider()

    retriever = RagRetriever(db)
    ev = retriever.best(org_id, "brand voice visual palette colour monochrome tone")
    citation = ev["citation"] if ev else "Brand visual guideline (no passage retrieved)"

    submission = Submission(
        id=str(uuid.uuid4()), org_id=org_id,
        title=f"Visual asset: {filename}",
        content=f"[Image asset '{filename}' — {decoded['format'].upper()} {decoded['width']}x{decoded['height']}]",
        status="Analysed", author_name=author_name,
    )
    db.add(submission)

    findings: List[Finding] = []
    deductions = 0
    chromatic = metrics.get("chromatic_fraction", 0.0)
    # Only judge colours against a palette rule this organisation actually has.
    from backend.app.models.brand import BrandRule
    palette_rule = next((r for r in db.query(BrandRule).filter(BrandRule.org_id == org_id, BrandRule.is_active == True,
                                                               BrandRule.is_confirmed == True).all()
                         if "monochrom" in f"{r.title} {r.rule_text}".lower()), None)
    if palette_rule and chromatic > 0.10:
        findings.append(Finding(
            id=str(uuid.uuid4()), submission_id=submission.id,
            issue_category="Visual", severity="WARNING",
            original_text=f"{int(chromatic * 100)}% of sampled pixels are chromatic (non-grayscale)",
            explanation=f"{org.name}'s confirmed palette rule requires monochrome. Measured colour content exceeds the monochrome threshold.",
            rule_reference=palette_rule.title,
            evidence_source=citation,
            confidence=0.9, suggested_correction="Restrict the asset to approved monochrome values (e.g. #0A0A0A, #171717, #FFFFFF).",
            analysis_engine="visual-cv",
        ))
        deductions += 20
    if metrics.get("contrast", 1.0) < 0.20:
        findings.append(Finding(
            id=str(uuid.uuid4()), submission_id=submission.id,
            issue_category="Accessibility", severity="WARNING",
            original_text=f"Low luminance contrast (measured {metrics.get('contrast')})",
            explanation="Low measured luminance spread may fail accessibility contrast guidance.",
            rule_reference="Accessibility contrast (measured)",
            evidence_source=citation,
            confidence=0.8, suggested_correction="Increase contrast between foreground text and background.",
            analysis_engine="visual-cv",
        ))
        deductions += 10

    submission.overall_score = max(5, 100 - deductions)
    submission.findings = findings

    run = AgentRun(
        id=str(uuid.uuid4()), org_id=org_id, agent_name="Visual DNA Agent",
        task_name="Deterministic colour-palette & contrast measurement",
        status="COMPLETED",
        execution_time_ms=round((time.perf_counter() - start) * 1000),
        execution_time_us=max(1, round((time.perf_counter() - start) * 1_000_000)),
        tokens_used=0,
        input_preview=f"{filename} ({decoded['format']} {decoded['width']}x{decoded['height']})",
        output_preview=f"{len(findings)} visual findings; chromatic={chromatic}; contrast={metrics.get('contrast')}.",
        event_details={"metrics": metrics, "ocr_available": ocr.available},
        created_at=datetime.datetime.utcnow(),
    )
    db.add(run)
    db.add(AuditLog(id=str(uuid.uuid4()), org_id=org_id, action="VISUAL_ANALYZED", actor=author_name,
                    details=f"Analyzed image '{filename}' ({decoded['format']}). Findings: {len(findings)}."))
    db.commit()
    db.refresh(submission)

    return {
        "submission": submission,
        "metrics": metrics,
        "format": decoded["format"],
        "dimensions": {"width": decoded["width"], "height": decoded["height"]},
        "ocr": {"available": ocr.available, "text": ocr.extract_text(data) if ocr.available else None,
                "reason": getattr(ocr, "reason", None), "engine": ocr.name, "skipped": getattr(ocr, "skipped", False),
                "note": "Use Creative Inspection to check the claims in this text against your Brand DNA."},
        "palette_rule": palette_rule.title if palette_rule else None,
    }
