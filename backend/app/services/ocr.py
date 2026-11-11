"""
Optical character recognition for creatives (Round 3 · Improvement 1).

Engine: RapidOCR (PaddleOCR models on ONNX Runtime) — installed with pip, runs
on the CPU, no system binary needed. It is loaded lazily on first use and shared
across requests. When the engine is not installed the caller gets
``OCRUnavailable`` and the UI says so; text is never invented.

After recognition, words are corrected against the organisation's own brand
vocabulary using a small, explicit table of OCR confusions (l/I, 0/O, 1/I, 5/S,
rn/m). Every correction is reported so a reviewer can see exactly what changed.
"""
from __future__ import annotations

import io
import os
import re
import threading
import time
from typing import Dict, Iterable, List, Optional, Tuple

ENGINE_NAME = "rapidocr-onnx"
MAX_SIDE = int(os.getenv("OCR_MAX_SIDE", "1600"))  # downscale very large creatives; boxes are mapped back
UPSCALE_BELOW = int(os.getenv("OCR_UPSCALE_BELOW", "0"))  # small creatives are enlarged 2x: better word spacing
DET_MAX_SIDE = int(os.getenv("OCR_DET_MAX_SIDE", "960"))  # memory cap for text detection (see _get_engine)
# Run each OCR in a short-lived child process. If an image ever needs more memory than the
# server has, only the child is stopped (the user gets a clear error) and the server keeps
# running; when it finishes, all OCR memory (engine included) is returned at once.
IN_SUBPROCESS = os.getenv("OCR_IN_SUBPROCESS", "true").lower() != "false"
CHILD_TIMEOUT = int(os.getenv("OCR_TIMEOUT_SECONDS", "180"))
MIN_CONFIDENCE = 0.5     # lines below this are kept but flagged as low confidence

_lock = threading.Lock()
# One OCR at a time: two at once would double the peak memory on a small server.
_run_lock = threading.Lock()
_engine = None
_load_error: Optional[str] = None


class OCRUnavailable(RuntimeError):
    """The OCR engine is not installed or failed to load."""


def _get_engine():
    global _engine, _load_error
    if _engine is not None:
        return _engine
    with _lock:
        if _engine is None and _load_error is None:
            try:
                from rapidocr_onnxruntime import RapidOCR  # heavy import, done once
                # Text detection runs on a copy at most DET_MAX_SIDE on its longer side; text
                # is still read from the full-size image. Without this cap one banner can need
                # 0.5-1 GB at peak, which crashes a 512 MB server.
                _engine = RapidOCR(det_model_path=None, det_limit_side_len=DET_MAX_SIDE, det_limit_type="max")
            except Exception as exc:  # pragma: no cover - depends on the host
                _load_error = f"{type(exc).__name__}: {exc}"
    if _engine is None:
        raise OCRUnavailable(f"OCR engine unavailable ({_load_error}).")
    return _engine


def _installed() -> bool:
    import importlib.util
    return importlib.util.find_spec("rapidocr_onnxruntime") is not None


def available() -> bool:
    if IN_SUBPROCESS:
        return _installed()
    try:
        _get_engine()
        return True
    except OCRUnavailable:
        return False


def _child_ocr(png: bytes, det_max_side: int) -> list:
    """Runs in the child process: load the engine, read the image, return plain data."""
    from rapidocr_onnxruntime import RapidOCR
    engine = RapidOCR(det_model_path=None, det_limit_side_len=det_max_side, det_limit_type="max")
    result, _ = engine(png)
    return [([[float(x), float(y)] for x, y in box], str(text), float(conf)) for box, text, conf in (result or [])]


def _run_in_child(png: bytes) -> list:
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor
    from concurrent.futures.process import BrokenProcessPool
    ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=1, mp_context=ctx) as pool:
        try:
            return pool.submit(_child_ocr, png, DET_MAX_SIDE).result(timeout=CHILD_TIMEOUT)
        except BrokenProcessPool:
            raise OCRUnavailable("Reading the text in this image needed more memory than this server has. "
                                 "Try a smaller image (under 1600 pixels on the longer side).")
        except TimeoutError:
            raise OCRUnavailable("Reading the text in this image took too long. Try a smaller image.")


def status() -> Dict:
    """Whether OCR can run, without loading the engine (it takes about 85 MB of memory,
    which a small server should only spend when someone actually inspects a creative)."""
    if _engine is not None:
        return {"available": True, "engine": ENGINE_NAME, "loaded": True}
    if _load_error is not None:
        return {"available": False, "engine": None, "reason": f"OCR engine unavailable ({_load_error})."}
    import importlib.util
    if importlib.util.find_spec("rapidocr_onnxruntime") is None:
        return {"available": False, "engine": None, "reason": "OCR engine unavailable (rapidocr_onnxruntime is not installed)."}
    return {"available": True, "engine": ENGINE_NAME, "loaded": False}


def _prepare(image_bytes: bytes) -> Tuple[bytes, float, int, int]:
    """Return (png bytes for the engine, scale back to original, width, height)."""
    from PIL import Image
    img = Image.open(io.BytesIO(image_bytes))
    img.load()
    if img.mode not in ("RGB", "L"):
        bg = Image.new("RGB", img.size, "white")
        bg.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[-1])
        img = bg
    w, h = img.size
    scale = 1.0
    if max(w, h) > MAX_SIDE:
        scale = max(w, h) / MAX_SIDE
        img = img.resize((round(w / scale), round(h / scale)))
    elif max(w, h) <= UPSCALE_BELOW:
        scale = 0.5
        img = img.resize((w * 2, h * 2), Image.LANCZOS)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "PNG")
    return buf.getvalue(), scale, w, h


def recognise(image_bytes: bytes) -> Dict:
    """OCR one image. Returns lines with text, confidence and box [x, y, w, h] in original pixels."""
    t0 = time.perf_counter()
    with _run_lock:
        png, scale, w, h = _prepare(image_bytes)
        if IN_SUBPROCESS:
            if not _installed():
                raise OCRUnavailable("OCR engine unavailable (rapidocr_onnxruntime is not installed).")
            result = _run_in_child(png)
        else:
            result, _ = _get_engine()(png)
        del png
    lines = []
    for box, text, conf in (result or []):
        xs = [p[0] * scale for p in box]
        ys = [p[1] * scale for p in box]
        x0, y0 = max(0, min(xs)), max(0, min(ys))
        lines.append({
            "text": str(text).strip(),
            "confidence": round(float(conf), 3),
            "box": [round(x0), round(y0), round(min(w, max(xs)) - x0), round(min(h, max(ys)) - y0)],
            "low_confidence": float(conf) < MIN_CONFIDENCE,
        })
    # reading order: top-to-bottom, then left-to-right
    lines.sort(key=lambda l: (round(l["box"][1] / 12), l["box"][0]))
    return {"width": w, "height": h, "lines": [l for l in lines if l["text"]],
            "elapsed_ms": round((time.perf_counter() - t0) * 1000), "engine": ENGINE_NAME}


# ----------------------------- brand vocabulary ------------------------------
_CONFUSIONS = [("l", "I"), ("I", "l"), ("0", "O"), ("O", "0"), ("1", "I"), ("I", "1"),
               ("5", "S"), ("S", "5"), ("rn", "m"), ("|", "I")]
_TOKEN = re.compile(r"[A-Za-z0-9|][A-Za-z0-9|'’\-]*")


def brand_vocabulary(texts: Iterable[str]) -> set:
    vocab = set()
    for t in texts:
        for tok in _TOKEN.findall(t or ""):
            if len(tok) >= 2:
                vocab.add(tok)
    return vocab


def _variants(token: str) -> List[str]:
    out = []
    for a, b in _CONFUSIONS:
        start = token.find(a)
        while start != -1:
            out.append(token[:start] + b + token[start + len(a):])
            start = token.find(a, start + 1)
    return out


def _vocab_word(piece: str, by_lower: Dict[str, str]) -> Optional[str]:
    if piece.lower() in by_lower:
        return by_lower[piece.lower()]
    for cand in _variants(piece):
        if cand.lower() in by_lower:
            return by_lower[cand.lower()]
    return None


def _split_merged(tok: str, by_lower: Dict[str, str]) -> Optional[List[str]]:
    """Split a run-together OCR token into brand-vocabulary words (all of it, or nothing)."""
    n = len(tok)
    best: List[Optional[List[str]]] = [None] * (n + 1)
    best[0] = []
    for i in range(n):
        if best[i] is None:
            continue
        for j in range(i + 2 if not tok[i].isdigit() else i + 1, n + 1):
            word = _vocab_word(tok[i:j], by_lower)
            if word and (best[j] is None or len(best[i]) + 1 < len(best[j])):
                best[j] = best[i] + [word]
    parts = best[n]
    return parts if parts and len(parts) >= 2 else None


def correct(text: str, vocab: set) -> Tuple[str, List[Dict]]:
    """Fix OCR confusions (l/I, 0/O, ...) and run-together words using the brand vocabulary only."""
    if not vocab:
        return text, []
    lower_vocab = {v.lower() for v in vocab}
    by_lower = {v.lower(): v for v in sorted(vocab, key=len)}
    for v in vocab:  # split multi-part vocabulary entries (e.g. "Pro" from "NovaBook AI Pro 16")
        for part in re.findall(r"[A-Za-z]+|\d+", v):
            by_lower.setdefault(part.lower(), part)
    corrections: List[Dict] = []

    def fix(m: re.Match) -> str:
        tok = m.group(0)
        if tok in vocab or tok.lower() in lower_vocab:
            return tok
        for cand in _variants(tok):
            if cand in vocab:
                corrections.append({"from": tok, "to": cand, "reason": "OCR character confusion"})
                return cand
        if len(tok) >= 8:
            parts = _split_merged(tok, by_lower)
            if parts:
                fixed = " ".join(parts)
                corrections.append({"from": tok, "to": fixed, "reason": "words run together by OCR"})
                return fixed
        return tok

    return _TOKEN.sub(fix, text), corrections


# Price words may be glued to the amount by OCR ("only69,999"), so no word boundary is required.
_BARE_PRICE = re.compile(r"(?i)(only|price|now|at|just|for|mrp|offer|from|starting|alert|pay|deal|sale|today|@)"
                         r"(\s*:?\s*)(\d{1,3}(?:,\d{2,3})+(?:\.\d+)?)(?!\s*%)")
# A number with letters that look like digits inside it: "1ox" (10x), "75,0o0", "2O26".
_DIGITISH = re.compile(r"(?<![A-Za-z0-9])\d[\dOoIl,]*[\dOo](?:[xX×])?(?![A-Za-z0-9])|(?<![A-Za-z0-9])\d[OoIl][xX×](?![A-Za-z0-9])")


def fix_digits(text: str) -> Tuple[str, List[Dict]]:
    """Inside numbers, OCR reads 0 as o/O and 1 as l/I. Fix only tokens that start with a digit."""
    corrections: List[Dict] = []

    def fix(m: re.Match) -> str:
        tok = m.group(0)
        if not re.search(r"[OoIl]", tok):
            return tok
        fixed = tok.translate(str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1"}))
        corrections.append({"from": tok, "to": fixed, "reason": "letter read in place of a digit by OCR"})
        return fixed

    return _DIGITISH.sub(fix, text), corrections
# The ₹ glyph is often read as a capital R directly before an Indian-grouped amount ("R69,999").
_R_AS_RUPEE = re.compile(r"(?<![A-Za-z])R(?=\d{1,3}(?:,\d{2,3})+\b)")


def restore_currency(text: str, symbol: str) -> Tuple[str, List[Dict]]:
    """OCR models often drop the ₹ glyph. Put it back on bare amounts in a clear price context."""
    text, corrections = fix_digits(text)

    def fix(m: re.Match) -> str:
        corrections.append({"from": m.group(3), "to": symbol + m.group(3), "reason": "currency symbol not recognised by OCR"})
        return f"{m.group(1)}{m.group(2)}{symbol}{m.group(3)}"

    if symbol == "₹":
        def fix_r(m: re.Match) -> str:
            corrections.append({"from": "R", "to": "₹", "reason": "₹ read as the letter R by OCR"})
            return "₹"
        text = _R_AS_RUPEE.sub(fix_r, text)
    return _BARE_PRICE.sub(fix, text), corrections
