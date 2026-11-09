"""Generate test creatives (images, PDFs, videos) with known text — no binary fixtures in git."""
from __future__ import annotations

import io
import os
import tempfile
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

_WIN_FONTS = ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf",
              "C:/Windows/Fonts/verdana.ttf", "C:/Windows/Fonts/georgia.ttf", "C:/Windows/Fonts/calibri.ttf"]
_NIX_FONTS = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]


def font(size: int, variant: int = 0):
    paths = [p for p in _WIN_FONTS + _NIX_FONTS if os.path.exists(p)]
    if paths:
        return ImageFont.truetype(paths[variant % len(paths)], size)
    return ImageFont.load_default(size=size)  # Pillow >= 10.1 bundles a TrueType default


def banner(lines: List[str], size: Tuple[int, int] = (1200, 628), bg=(255, 255, 255), fg=(15, 23, 42),
           font_size: int = 44, variant: int = 0, logo: Optional[Image.Image] = None, logo_at=(0, 0), fmt: str = "PNG") -> bytes:
    img = Image.new("RGB", size, bg)
    d = ImageDraw.Draw(img)
    y = 70
    for i, text in enumerate(lines):
        d.text((60, y), text, fill=fg, font=font(font_size if i == 0 else int(font_size * 0.72), variant))
        y += int(font_size * 1.6)
    if logo is not None:
        img.paste(logo, logo_at, logo if logo.mode == "RGBA" else None)
    buf = io.BytesIO()
    img.save(buf, fmt)
    return buf.getvalue()


def text_pdf(pages: List[List[str]]) -> bytes:
    """A minimal valid PDF whose pages carry a real text layer (Helvetica)."""
    objs: List[bytes] = []
    page_ids = []
    font_id = 3 + 2 * len(pages)
    for pi, lines in enumerate(pages):
        content_id, page_id = 3 + 2 * pi + 1, 3 + 2 * pi
        page_ids.append(page_id)
        ops = ["BT", "/F1 22 Tf"]
        y = 760
        for text in lines:
            safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            ops.append(f"1 0 0 1 60 {y} Tm ({safe}) Tj")
            y -= 40
        ops.append("ET")
        stream = "\n".join(ops).encode("latin-1")
        objs.append((page_id, f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>".encode()))
        objs.append((content_id, b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream"))
    objs.append((1, b"<< /Type /Catalog /Pages 2 0 R >>"))
    objs.append((2, ("<< /Type /Pages /Kids [%s] /Count %d >>" % (" ".join(f"{p} 0 R" for p in page_ids), len(pages))).encode()))
    objs.append((font_id, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"))
    objs.sort(key=lambda o: o[0])
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = {}
    for num, body in objs:
        offsets[num] = out.tell()
        out.write(b"%d 0 obj\n" % num + body + b"\nendobj\n")
    xref = out.tell()
    n = max(offsets) + 1
    out.write(b"xref\n0 %d\n0000000000 65535 f \n" % n)
    for i in range(1, n):
        out.write(b"%010d 00000 n \n" % offsets[i])
    out.write(b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (n, xref))
    return out.getvalue()


def image_pdf(lines: List[str]) -> bytes:
    """A 'scanned' PDF: the page is an image, no text layer."""
    img = Image.open(io.BytesIO(banner(lines, size=(1240, 1754), font_size=52)))
    buf = io.BytesIO()
    img.save(buf, "PDF", resolution=150)
    return buf.getvalue()


def video(frames_text: List[List[str]], seconds_each: float = 1.0, fps: int = 10) -> bytes:
    import cv2
    import numpy as np
    w, h = 960, 540
    fd, path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)
    try:
        vw = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
        for lines in frames_text:
            frame = Image.open(io.BytesIO(banner(lines, size=(w, h), font_size=40))).convert("RGB")
            arr = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
            for _ in range(int(seconds_each * fps)):
                vw.write(arr)
        vw.release()
        with open(path, "rb") as fh:
            return fh.read()
    finally:
        os.remove(path)
