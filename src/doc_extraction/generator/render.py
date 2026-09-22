"""Renders a list of text lines into a document-like image, then applies
noise/rotation/low-resolution degradation to simulate scanned/photographed documents."""

import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH = 900
MARGIN = 50
LINE_HEIGHT = 34

_FONT_CANDIDATES = [
    "arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = _FONT_CANDIDATES
    if bold:
        candidates = ["arialbd.ttf", "C:/Windows/Fonts/arialbd.ttf", *candidates]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def render_document(title: str, lines: list[str]) -> Image.Image:
    height = MARGIN * 2 + LINE_HEIGHT * (len(lines) + 3)
    img = Image.new("RGB", (WIDTH, height), color="white")
    draw = ImageDraw.Draw(img)

    title_font = _load_font(28, bold=True)
    body_font = _load_font(20)

    y = MARGIN
    draw.text((MARGIN, y), title, fill="black", font=title_font)
    y += LINE_HEIGHT * 2
    draw.line([(MARGIN, y - 10), (WIDTH - MARGIN, y - 10)], fill="gray", width=1)

    for line in lines:
        draw.text((MARGIN, y), line, fill="black", font=body_font)
        y += LINE_HEIGHT

    return img


def degrade(img: Image.Image, *, seed: int | None = None) -> Image.Image:
    """Apply random rotation, noise, and resolution loss to simulate a
    photographed/scanned document rather than a clean render."""
    rng = random.Random(seed)

    angle = rng.uniform(-3.5, 3.5)
    img = img.rotate(angle, expand=True, fillcolor="white")

    if rng.random() < 0.6:
        img = img.filter(ImageFilter.GaussianBlur(radius=rng.uniform(0.3, 1.2)))

    if rng.random() < 0.5:
        w, h = img.size
        scale = rng.uniform(0.35, 0.7)
        small = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.BILINEAR)
        img = small.resize((w, h), Image.BILINEAR)

    return img.convert("RGB")
