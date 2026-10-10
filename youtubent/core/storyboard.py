"""Compose the storyboard image with Pillow and export PNG / JPG / PDF."""
from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw, ImageFont

from .models import ExportSettings, Project, fmt_time

THEMES = {
    "dark": {"bg": (27, 28, 31), "fg": (230, 231, 234), "sub": (150, 152, 160), "badge": (0, 0, 0), "accent": (255, 77, 94)},
    "midnight": {"bg": (10, 14, 28), "fg": (225, 232, 255), "sub": (130, 145, 190), "badge": (0, 0, 0), "accent": (90, 160, 255)},
    "light": {"bg": (244, 244, 246), "fg": (30, 31, 35), "sub": (110, 112, 120), "badge": (0, 0, 0), "accent": (230, 40, 60)},
    "paper": {"bg": (250, 243, 224), "fg": (60, 45, 30), "sub": (130, 110, 85), "badge": (60, 45, 30), "accent": (200, 80, 40)},
}


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = (
        ["Helvetica.ttc", "Arial Bold.ttf", "DejaVuSans-Bold.ttf", "arialbd.ttf"]
        if bold
        else ["Helvetica.ttc", "Arial.ttf", "DejaVuSans.ttf", "arial.ttf"]
    )
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size)
    except TypeError:  # very old Pillow
        return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    lines: list[str] = []
    for para in text.splitlines() or [""]:
        words, cur = para.split(), ""
        for w in words:
            test = f"{cur} {w}".strip()
            if draw.textlength(test, font=font) <= max_w or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def render(project: Project, frames: dict[str, Image.Image], s: ExportSettings | None = None) -> Image.Image:
    """frames: point.id -> PIL image. Points without a frame are skipped."""
    s = s or project.export
    th = THEMES.get(s.theme, THEMES["dark"])
    pts = [p for p in project.storyboard_points() if p.id in frames]
    if not pts:
        raise ValueError("Nothing to render: no included points with frames.")

    cols = max(1, min(s.columns, len(pts)))
    cw = s.cell_width
    first = frames[pts[0].id]
    ch = round(cw * first.height / first.width)  # all cells share the first frame's aspect (Shorts = tall)
    gap = s.gap
    pad = gap * 2
    cap_font, ts_font, title_font = _font(max(14, cw // 22)), _font(max(12, cw // 28), True), _font(max(24, cw // 10), True)

    meas = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    # caption heights per cell -> row heights
    cap_lines: dict[str, list[str]] = {}
    for p in pts:
        cap_lines[p.id] = _wrap(meas, p.caption.strip(), cap_font, cw - 8) if (s.show_captions and p.caption.strip()) else []
    line_h = cap_font.size + 4 if hasattr(cap_font, "size") else 16
    rows = [pts[i : i + cols] for i in range(0, len(pts), cols)]
    row_caps = [max(len(cap_lines[p.id]) for p in r) * line_h + (8 if any(cap_lines[p.id] for p in r) else 0) for r in rows]

    total_w = cols * cw + (cols - 1) * gap + pad * 2
    title_h = 0
    title_lines: list[str] = []
    if s.show_title and (s.title or project.title):
        title_lines = _wrap(meas, s.title or project.title, title_font, total_w - pad * 2)
        title_h = len(title_lines) * (title_font.size + 6) + pad if hasattr(title_font, "size") else 60
    total_h = pad * 2 + title_h + sum(ch + c for c in row_caps) + gap * (len(rows) - 1)

    img = Image.new("RGB", (total_w, total_h), th["bg"])
    d = ImageDraw.Draw(img)
    y = pad
    for ln in title_lines:
        d.text((pad, y), ln, font=title_font, fill=th["fg"])
        y += title_font.size + 6
    if title_lines:
        y += pad - 6

    for r, rh in zip(rows, row_caps):
        # centre a short last row
        row_w = len(r) * cw + (len(r) - 1) * gap
        x0 = pad + (total_w - pad * 2 - row_w) // 2
        for i, p in enumerate(r):
            x = x0 + i * (cw + gap)
            fr = frames[p.id].resize((cw, ch), Image.LANCZOS)
            img.paste(fr, (x, y))
            if s.show_timestamps:
                label = fmt_time(p.t, tenths=False)
                tw = d.textlength(label, font=ts_font)
                bh = ts_font.size + 8 if hasattr(ts_font, "size") else 20
                d.rounded_rectangle((x + 8, y + ch - bh - 8, x + 8 + tw + 14, y + ch - 8), radius=6, fill=th["badge"])
                d.text((x + 15, y + ch - bh - 4), label, font=ts_font, fill=(255, 255, 255))
            cy = y + ch + 6
            for ln in cap_lines[p.id]:
                d.text((x + 4, cy), ln, font=cap_font, fill=th["fg"])
                cy += line_h
        y += ch + rh + gap
    return img


def save(img: Image.Image, path: str | Path, fmt: str | None = None) -> Path:
    path = Path(path)
    fmt = (fmt or path.suffix.lstrip(".") or "png").lower()
    if fmt == "jpeg":
        fmt = "jpg"
    if path.suffix.lower().lstrip(".") != fmt:
        path = path.with_suffix("." + fmt)
    if fmt == "png":
        img.save(path, "PNG")
    elif fmt == "jpg":
        img.save(path, "JPEG", quality=92)
    elif fmt == "pdf":
        img.save(path, "PDF", resolution=150.0)  # one tall page: fits the whole story
    else:
        raise ValueError(f"unknown format {fmt}")
    return path
