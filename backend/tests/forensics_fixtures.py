"""Deterministic synthetic images for forensics tests (no external files)."""
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def _font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # very old Pillow
        return ImageFont.load_default()


def make_logo(variant="v2", w=360, h=160) -> Image.Image:
    """A logo with enough structure for feature matching: mark + wordmark."""
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    if variant == "v2":
        d.rounded_rectangle([8, 20, 128, 140], radius=22, fill=(79, 70, 229, 255))
        d.polygon([(30, 120), (68, 40), (106, 120)], fill=(255, 255, 255, 255))
        d.ellipse([56, 92, 80, 116], fill=(16, 185, 129, 255))
        d.text((142, 42), "Vortexa", font=_font(52), fill=(17, 24, 39, 255))
        d.text((146, 102), "TECHNOLOGIES", font=_font(22), fill=(79, 70, 229, 255))
    else:  # old v1: different mark and wordmark
        d.ellipse([10, 20, 130, 140], fill=(220, 38, 38, 255))
        d.rectangle([48, 58, 92, 102], fill=(255, 255, 255, 255))
        d.text((142, 50), "VORTEX", font=_font(54), fill=(30, 30, 30, 255))
        d.text((146, 110), "tech", font=_font(24), fill=(220, 38, 38, 255))
    return img


def scene(size=(1000, 700), seed=1) -> Image.Image:
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:size[1], 0:size[0]]
    base = np.stack([(x / size[0]) * 120 + 60, (y / size[1]) * 90 + 80, 160 - (x / size[0]) * 60], -1)
    noise = rng.normal(0, 18, base.shape)
    img = Image.fromarray(np.clip(base + noise, 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(img)
    for i in range(14):  # unrelated shapes so the scene has its own features
        x0, y0 = rng.integers(0, size[0] - 120), rng.integers(0, size[1] - 120)
        d.rectangle([x0, y0, x0 + rng.integers(30, 110), y0 + rng.integers(30, 110)],
                    outline=tuple(int(c) for c in rng.integers(0, 255, 3)), width=3)
    d.text((40, 620), "Big Diwali Sale - limited period", font=_font(30), fill=(255, 255, 255))
    return img


def compose(logo: Image.Image, at=(420, 220), size=None, rotate=0, bg=None) -> Image.Image:
    img = (bg or scene()).copy()
    lg = logo.copy()
    if size:
        lg = lg.resize(size, Image.LANCZOS)
    if rotate:
        lg = lg.rotate(rotate, expand=True, resample=Image.BICUBIC)
    plate = Image.new("RGBA", lg.size, (255, 255, 255, 235))  # logos usually sit on a light plate
    plate.alpha_composite(lg)
    img.paste(plate, at, plate)
    return img


def recolour(logo: Image.Image) -> Image.Image:
    arr = np.array(logo).astype(np.int32)
    rgb = arr[:, :, :3]
    arr[:, :, :3] = rgb[:, :, [2, 0, 1]]  # rotate channels: indigo -> orange-ish, etc.
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def png_bytes(img: Image.Image) -> bytes:
    b = io.BytesIO()
    img.save(b, "PNG")
    return b.getvalue()


def jpeg_bytes(img: Image.Image, q=80) -> bytes:
    b = io.BytesIO()
    img.convert("RGB").save(b, "JPEG", quality=q)
    return b.getvalue()
