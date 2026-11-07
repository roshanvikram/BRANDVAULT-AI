"""
Brand Asset Forensics — find official assets inside an uploaded image and
measure how they were changed.

Deterministic computer vision (OpenCV + numpy), no generative model:
  * identical file       SHA-256
  * near-duplicate       64-bit perceptual hash (DCT pHash) + difference hash
  * logo localisation    ORB features + RANSAC homography; edge-based
                         multi-scale template matching as a fallback for flat
                         logos with few corners
  * modifications        rotation, non-uniform scale (stretch), cropping at the
                         image border, recolouring (mean CIE76 ΔE in Lab over the
                         logo's own pixels), outdated version (match is a
                         superseded asset)

Every finding carries a measurement and a confidence. Similarity is evidence,
not proof of unauthorised use — results say "suspected" and recommend review.
"""
from __future__ import annotations

import hashlib
import io
import math
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageOps

MAX_SIDE = 1600  # analysis resolution cap (keeps ORB fast and deterministic)
ALLOWED_FORMATS = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp", "BMP": "image/bmp"}


# ----------------------------------------------------------------------------
# Decoding + fingerprints
# ----------------------------------------------------------------------------
def load_image(data: bytes) -> Tuple[np.ndarray, str, np.ndarray]:
    """Decode bytes -> (RGB uint8 array, mime, alpha mask 0/255).
    Raises ValueError for anything that is not a real supported image."""
    try:
        img = Image.open(io.BytesIO(data))
        fmt = img.format
        img.verify()  # structural check
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"Not a readable image: {e}") from e
    if fmt not in ALLOWED_FORMATS:
        raise ValueError(f"Unsupported image format {fmt}. Use PNG, JPEG, WebP or BMP.")
    if img.width * img.height > 40_000_000:
        raise ValueError("Image is too large (over 40 megapixels).")
    rgba = img.convert("RGBA")
    arr = np.array(rgba)
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]
    # Flatten transparency onto white, like a page would render it.
    a = (alpha.astype(np.float32) / 255.0)[:, :, None]
    rgb = (rgb.astype(np.float32) * a + 255.0 * (1 - a)).astype(np.uint8)
    return rgb, ALLOWED_FORMATS[fmt], alpha


def _bits_to_hex(bits: np.ndarray) -> str:
    v = 0
    for b in bits.flatten():
        v = (v << 1) | int(b)
    return f"{v:016x}"


def phash(rgb: np.ndarray) -> str:
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    g = cv2.resize(g, (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32)
    d = cv2.dct(g)[:8, :8]
    med = np.median(d.flatten()[1:])
    return _bits_to_hex(d > med)


def dhash(rgb: np.ndarray) -> str:
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    g = cv2.resize(g, (9, 8), interpolation=cv2.INTER_AREA)
    return _bits_to_hex(g[:, 1:] > g[:, :-1])


def hamming(a: str, b: str) -> int:
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def dominant_colours(rgb: np.ndarray, k: int = 5) -> Dict:
    small = cv2.resize(rgb, (64, 64), interpolation=cv2.INTER_AREA).reshape(-1, 3).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    cv2.setRNGSeed(7)
    _, labels, centers = cv2.kmeans(small, k, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.flatten(), minlength=k)
    order = np.argsort(-counts)
    out = [{"hex": "#{:02X}{:02X}{:02X}".format(*[int(c) for c in centers[i]]),
            "share": round(float(counts[i] / counts.sum()), 3)} for i in order]
    return {"dominant": out}


def fingerprints(data: bytes) -> Dict:
    rgb, mime, _ = load_image(data)
    return {"sha256": hashlib.sha256(data).hexdigest(), "phash": phash(rgb), "dhash": dhash(rgb),
            "width": int(rgb.shape[1]), "height": int(rgb.shape[0]), "mime": mime, "colours": dominant_colours(rgb)}


# ----------------------------------------------------------------------------
# Logo localisation
# ----------------------------------------------------------------------------
def _cap(rgb: np.ndarray) -> Tuple[np.ndarray, float]:
    h, w = rgb.shape[:2]
    s = min(1.0, MAX_SIDE / max(h, w))
    if s < 1.0:
        rgb = cv2.resize(rgb, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return rgb, s


def _foreground_mask(rgb: np.ndarray, alpha: Optional[np.ndarray]) -> np.ndarray:
    """Pixels that belong to the logo (not its transparent/white background)."""
    if alpha is not None and alpha.min() < 250:
        return (alpha > 128).astype(np.uint8)
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    return (g < 235).astype(np.uint8)


@dataclass
class LogoMatch:
    method: str
    confidence: float
    polygon: List[List[float]]          # 4 corners in upload pixel coords
    bbox: List[int]                     # x, y, w, h (clipped to image)
    rotation_deg: float
    scale_x: float
    scale_y: float
    inliers: int = 0
    verification: float = 0.0          # edge agreement with the official logo (0..1)
    out_of_frame: float = 0.0           # fraction of the logo outside the image
    delta_e: Optional[float] = None     # colour difference vs the official logo
    homography: Optional[List[List[float]]] = None


def _poly_metrics(H: np.ndarray, w: int, h: int) -> Tuple[List[List[float]], float, float, float]:
    corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
    proj = cv2.perspectiveTransform(corners, H).reshape(-1, 2)
    top = proj[1] - proj[0]
    left = proj[3] - proj[0]
    rot = math.degrees(math.atan2(top[1], top[0]))
    sx = float(np.linalg.norm(top)) / w
    sy = float(np.linalg.norm(left)) / h
    return proj.tolist(), rot, sx, sy


def _out_of_frame(poly: List[List[float]], W: int, H: int) -> Tuple[float, List[int]]:
    pts = np.array(poly, dtype=np.float32)
    area = abs(cv2.contourArea(pts))
    if area < 1:
        return 1.0, [0, 0, 0, 0]
    clip = np.zeros((H, W), np.uint8)
    cv2.fillPoly(clip, [pts.astype(np.int32)], 1)
    inside = float(clip.sum())
    x0, y0 = max(0, int(pts[:, 0].min())), max(0, int(pts[:, 1].min()))
    x1, y1 = min(W, int(math.ceil(pts[:, 0].max()))), min(H, int(math.ceil(pts[:, 1].max())))
    return max(0.0, 1.0 - inside / area), [x0, y0, max(0, x1 - x0), max(0, y1 - y0)]


def _orb_match(logo: np.ndarray, scene: np.ndarray) -> Optional[Tuple[np.ndarray, int, int]]:
    orb = cv2.ORB_create(nfeatures=3000, scaleFactor=1.2, nlevels=10)
    g1 = cv2.cvtColor(logo, cv2.COLOR_RGB2GRAY)
    g2 = cv2.cvtColor(scene, cv2.COLOR_RGB2GRAY)
    k1, d1 = orb.detectAndCompute(g1, None)
    k2, d2 = orb.detectAndCompute(g2, None)
    if d1 is None or d2 is None or len(k1) < 8 or len(k2) < 8:
        return None
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    good = []
    for pair in bf.knnMatch(d1, d2, k=2):
        if len(pair) == 2 and pair[0].distance < 0.75 * pair[1].distance:
            good.append(pair[0])
    if len(good) < 10:
        return None
    src = np.float32([k1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst = np.float32([k2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
    if H is None or mask is None:
        return None
    inl = int(mask.sum())
    if inl < 10:
        return None
    return H, inl, len(good)


def _template_match(logo: np.ndarray, scene: np.ndarray) -> Optional[Tuple[np.ndarray, float]]:
    """Edge-based, colour-independent, multi-scale; handles upright logos at any
    uniform size. Returns (homography, score)."""
    le = cv2.Canny(cv2.cvtColor(logo, cv2.COLOR_RGB2GRAY), 50, 150)
    se = cv2.Canny(cv2.cvtColor(scene, cv2.COLOR_RGB2GRAY), 50, 150)
    se = cv2.dilate(se, np.ones((2, 2), np.uint8))
    h, w = le.shape
    best = (0.0, None, None)
    for s in np.geomspace(0.15, 3.0, 36):
        tw, th = int(w * s), int(h * s)
        if tw < 16 or th < 16 or tw > se.shape[1] or th > se.shape[0]:
            continue
        t = cv2.dilate(cv2.resize(le, (tw, th), interpolation=cv2.INTER_AREA), np.ones((2, 2), np.uint8))
        if t.sum() == 0:
            continue
        r = cv2.matchTemplate(se, t, cv2.TM_CCOEFF_NORMED)
        _, mx, _, loc = cv2.minMaxLoc(r)
        if mx > best[0]:
            best = (mx, s, loc)
    score, s, loc = best
    if s is None or score < 0.45:
        return None
    H = np.array([[s, 0, loc[0]], [0, s, loc[1]], [0, 0, 1]], dtype=np.float64)
    return H, float(score)


def _delta_e(logo_rgb: np.ndarray, logo_mask: np.ndarray, scene_rgb: np.ndarray, H: np.ndarray) -> Optional[float]:
    """Warp the scene back into the logo's frame and compare colours on the
    logo's own (foreground) pixels. Mean CIE76 ΔE; > ~12 is clearly visible."""
    h, w = logo_rgb.shape[:2]
    try:
        Hinv = np.linalg.inv(H)
    except np.linalg.LinAlgError:
        return None
    warped = cv2.warpPerspective(scene_rgb, Hinv, (w, h), flags=cv2.INTER_LINEAR, borderValue=(255, 255, 255))
    valid = cv2.warpPerspective(np.ones(scene_rgb.shape[:2], np.uint8), Hinv, (w, h)) > 0
    m = (logo_mask > 0) & valid
    m = cv2.erode(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0  # ignore anti-aliased edges
    if m.sum() < 50:
        return None
    a = cv2.cvtColor(logo_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    b = cv2.cvtColor(warped, cv2.COLOR_RGB2LAB).astype(np.float32)
    # OpenCV 8-bit Lab: L scaled 0..255, a/b offset by 128
    a[:, :, 0] *= 100 / 255
    b[:, :, 0] *= 100 / 255
    d = np.sqrt(((a - b) ** 2).sum(axis=2))[m]
    return float(np.median(d))


VERIFY_MIN = 0.6  # edge agreement needed to accept a match (calibrated: real >= 0.71, false <= 0.48)


def edge_agreement(logo_rgb: np.ndarray, scene_rgb: np.ndarray, H: np.ndarray) -> float:
    """Colour-independent check that the matched region really has the logo's
    outline: F1 of official vs observed Canny edges after warping the scene
    back into the logo frame (5 px tolerance)."""
    h, w = logo_rgb.shape[:2]
    try:
        Hinv = np.linalg.inv(H)
    except np.linalg.LinAlgError:
        return 0.0
    warped = cv2.warpPerspective(scene_rgb, Hinv, (w, h), borderValue=(255, 255, 255))
    e1 = cv2.Canny(cv2.cvtColor(logo_rgb, cv2.COLOR_RGB2GRAY), 50, 150) > 0
    e2 = cv2.Canny(cv2.cvtColor(warped, cv2.COLOR_RGB2GRAY), 50, 150) > 0
    k = np.ones((5, 5), np.uint8)
    d1 = cv2.dilate(e1.astype(np.uint8), k) > 0
    d2 = cv2.dilate(e2.astype(np.uint8), k) > 0
    rec = (e1 & d2).sum() / max(1, e1.sum())
    prec = (e2 & d1).sum() / max(1, e2.sum())
    return float(2 * rec * prec / max(1e-6, rec + prec))


def locate_logo(logo_rgb: np.ndarray, logo_alpha: Optional[np.ndarray], scene_rgb: np.ndarray) -> Optional[LogoMatch]:
    logo, _ = _cap(logo_rgb)
    scale_logo = logo.shape[1] / logo_rgb.shape[1]
    mask = cv2.resize(_foreground_mask(logo_rgb, logo_alpha), (logo.shape[1], logo.shape[0]), interpolation=cv2.INTER_NEAREST)
    h, w = logo.shape[:2]
    Hs, Ws = scene_rgb.shape[:2]
    match = None
    orb = _orb_match(logo, scene_rgb)
    if orb is not None:
        H, inl, total = orb
        poly, rot, sx, sy = _poly_metrics(H, w, h)
        oof, bbox = _out_of_frame(poly, Ws, Hs)
        # reject degenerate projections (folded / absurd scale)
        ver = edge_agreement(logo, scene_rgb, H)
        if 0.05 < sx < 20 and 0.05 < sy < 20 and abs(cv2.contourArea(np.array(poly, np.float32))) > 64                 and ver >= VERIFY_MIN:
            match = LogoMatch("orb-homography", round(min(0.99, 0.5 * ver + 0.5 * min(1.0, inl / 60)), 2), poly, bbox,
                              rot, sx, sy, inliers=inl, verification=round(ver, 3), out_of_frame=oof,
                              homography=H.tolist())
    if match is None:
        tm = _template_match(logo, scene_rgb)
        if tm is not None:
            H, score = tm
            poly, rot, sx, sy = _poly_metrics(H, w, h)
            oof, bbox = _out_of_frame(poly, Ws, Hs)
            ver = edge_agreement(logo, scene_rgb, H)
            if ver >= VERIFY_MIN:
                match = LogoMatch("edge-template", round(min(0.95, 0.5 * score + 0.5 * ver), 2), poly, bbox, rot, sx, sy,
                                  verification=round(ver, 3), out_of_frame=oof, homography=H.tolist())
    if match is None:
        return None
    match.delta_e = _delta_e(logo, mask, scene_rgb, np.array(match.homography))
    _ = scale_logo
    return match


# ----------------------------------------------------------------------------
# Investigation
# ----------------------------------------------------------------------------
@dataclass
class Finding:
    type: str
    severity: str           # high | medium | low | info
    title: str
    measurement: str
    explanation: str
    recommendation: str
    confidence: float


@dataclass
class AssetComparison:
    asset_id: str
    asset_name: str
    asset_kind: str
    version_label: str
    asset_status: str
    current: bool
    similarity: float            # 0..1 (perceptual)
    phash_distance: int
    identical_file: bool
    logo_match: Optional[dict] = None
    findings: List[dict] = field(default_factory=list)
    replacement: Optional[dict] = None


ROTATION_TOL = 3.0     # degrees
STRETCH_TOL = 0.06     # |sx/sy - 1|
CROP_TOL = 0.04        # fraction outside frame
DELTA_E_TOL = 12.0     # clearly visible colour change


def investigate(upload: bytes, assets: List[dict]) -> dict:
    """`assets`: dicts with id, name, kind, version_label, status, current, rgb,
    alpha, sha256, phash, dhash, replacement (dict or None)."""
    rgb, mime, _ = load_image(upload)
    scene, s = _cap(rgb)
    up_sha = hashlib.sha256(upload).hexdigest()
    up_ph, up_dh = phash(rgb), dhash(rgb)
    comparisons: List[AssetComparison] = []

    located: Dict[str, LogoMatch] = {}
    for a in assets:
        if a["kind"] == "logo" and up_sha != a["sha256"]:
            m = locate_logo(a["rgb"], a.get("alpha"), scene)
            if m is not None:
                located[a["id"]] = m
    # Several versions of a logo can match the same spot; keep the one whose
    # outline agrees best, so an old version is not reported next to the new one.
    def iou(b1, b2):
        x0, y0 = max(b1[0], b2[0]), max(b1[1], b2[1])
        x1, y1 = min(b1[0] + b1[2], b2[0] + b2[2]), min(b1[1] + b1[3], b2[1] + b2[3])
        inter = max(0, x1 - x0) * max(0, y1 - y0)
        union = b1[2] * b1[3] + b2[2] * b2[3] - inter
        return inter / union if union else 0.0
    for aid in sorted(located, key=lambda k: -located[k].verification):
        if aid not in located:
            continue
        for other in list(located):
            if other != aid and iou(located[aid].bbox, located[other].bbox) > 0.3                     and located[other].verification < located[aid].verification:
                del located[other]

    for a in assets:
        d_p = hamming(up_ph, a["phash"])
        d_d = hamming(up_dh, a["dhash"])
        sim = round(1 - (d_p + d_d) / 128, 3)
        comp = AssetComparison(a["id"], a["name"], a["kind"], a["version_label"], a["status"], a["current"],
                               sim, d_p, up_sha == a["sha256"], replacement=a.get("replacement"))
        fs: List[Finding] = []
        if comp.identical_file:
            if a["current"]:
                fs.append(Finding("identical_official", "low", "Identical to an approved official file",
                                  "SHA-256 match", "Byte-for-byte the same file as the official asset.",
                                  "No action needed.", 1.0))
            else:
                fs.append(Finding("identical_outdated", "high", "Identical to an outdated asset version",
                                  f"SHA-256 match · status {a['status']}",
                                  f"This file is version {a['version_label']}, which is {a['status']}.",
                                  "Replace it with the current approved version.", 1.0))
        elif d_p <= 10 and d_d <= 14:
            fs.append(Finding("near_duplicate", "medium" if a["current"] else "high",
                              "Near-duplicate of an official asset" + ("" if a["current"] else " (outdated version)"),
                              f"perceptual distance {d_p}/64, difference-hash distance {d_d}/64",
                              "Visually almost the same image with different bytes — re-saved, resized, compressed or "
                              "lightly edited. This is not proof of misuse.",
                              "Confirm the copy comes from the official library" +
                              ("" if a["current"] else " and replace it with the current version") + ".",
                              round(1 - d_p / 64, 2)))

        if a["kind"] == "logo" and not comp.identical_file:
            m = located.get(a["id"])
            if m is not None:
                # convert back to original upload coordinates
                inv = 1 / s
                m.polygon = [[x * inv, y * inv] for x, y in m.polygon]
                m.bbox = [int(v * inv) for v in m.bbox]
                comp.logo_match = asdict(m)
                comp.logo_match.pop("homography", None)
                aspect = m.scale_x / m.scale_y if m.scale_y else 1
                rot = ((m.rotation_deg + 180) % 360) - 180
                if not a["current"]:
                    fs.append(Finding("outdated_logo", "high", "Outdated logo version detected",
                                      f"matches {a['name']} {a['version_label']} ({a['status']})",
                                      "The logo in this image is a version that is no longer approved.",
                                      "Replace it with the current approved logo.", m.confidence))
                if abs(aspect - 1) > STRETCH_TOL:
                    fs.append(Finding("stretched", "high", "Logo proportions changed (stretched or squashed)",
                                      f"width/height scale ratio {aspect:.2f} (official 1.00)",
                                      "The logo was resized non-uniformly, distorting its proportions.",
                                      "Use the official file and scale it proportionally.", m.confidence))
                if abs(rot) > ROTATION_TOL:
                    fs.append(Finding("rotated", "medium", "Logo rotated",
                                      f"{rot:+.1f}° from upright", "The logo is not shown at its official orientation.",
                                      "Place the logo upright unless a rotated variant is approved.", m.confidence))
                if m.out_of_frame > CROP_TOL:
                    fs.append(Finding("cropped", "medium", "Logo cropped at the image edge",
                                      f"{m.out_of_frame * 100:.0f}% of the logo lies outside the image",
                                      "Part of the logo is cut off.", "Keep the full logo plus its clear space inside the frame.",
                                      m.confidence))
                if m.delta_e is not None and m.delta_e > DELTA_E_TOL:
                    fs.append(Finding("recoloured", "high", "Logo colours changed",
                                      f"median colour difference ΔE {m.delta_e:.1f} (visible above ~{DELTA_E_TOL:.0f})",
                                      "The logo's colours differ clearly from the official file.",
                                      "Use the official colour version of the logo.", m.confidence))
                if a["current"] and not any(f.type in ("stretched", "rotated", "cropped", "recoloured") for f in fs):
                    fs.append(Finding("official_logo", "low", "Official logo found, no modification measured",
                                      f"located by {m.method} · confidence {m.confidence:.2f}",
                                      "The approved logo appears unaltered within the measured tolerances.",
                                      "No action needed.", m.confidence))
        comp.findings = [asdict(f) for f in fs]
        if comp.findings or comp.similarity >= 0.75:
            comparisons.append(comp)

    order = {"high": 0, "medium": 1, "low": 2, "info": 3}
    comparisons.sort(key=lambda c: (min([order[f["severity"]] for f in c.findings] or [3]), -c.similarity))
    all_f = [f for c in comparisons for f in c.findings]
    risk = ("high" if any(f["severity"] == "high" for f in all_f) else
            "medium" if any(f["severity"] == "medium" for f in all_f) else
            "low" if all_f else "none")
    if not comparisons:
        summary = "No official asset was recognised in this image."
    else:
        top = comparisons[0]
        summary = (f"Best match: {top.asset_name} {top.version_label} "
                   f"({', '.join(f['title'].lower() for f in top.findings) or 'visually similar'}).")
    return {"risk": risk, "summary": summary, "sha256": up_sha, "phash": up_ph,
            "width": int(rgb.shape[1]), "height": int(rgb.shape[0]), "mime": mime,
            "matches": [asdict(c) for c in comparisons],
            "note": "Visual similarity and measured modifications are evidence for review, not proof of unauthorised use."}
