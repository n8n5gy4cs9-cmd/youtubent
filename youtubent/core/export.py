"""Export entry point. Modes:
  frames          -> separate numbered PNGs (default):  <shortname>_001.png ...
  storyboard_png  -> one stylized storyboard PNG
  storyboard_pdf  -> one stylized storyboard PDF
"""
from __future__ import annotations

import re
from pathlib import Path

from PIL import Image

from . import storyboard
from .models import Project

MODES = {
    "frames": "Separate PNG frames",
    "storyboard_png": "Storyboard (PNG)",
    "storyboard_pdf": "Storyboard (PDF)",
}


def short_name(project: Project, max_len: int = 24) -> str:
    """'My Super Long Video Title!!' -> 'my_super_long_video'."""
    base = re.sub(r"[^a-z0-9]+", "_", (project.title or project.video_id or "video").lower()).strip("_")
    base = base[:max_len].strip("_") or "video"
    return base


def suggested_name(project: Project) -> str:
    """Default file/folder name for the chosen mode."""
    m = project.export.mode
    if m == "frames":
        return short_name(project)
    return short_name(project) + (".pdf" if m == "storyboard_pdf" else ".png")


def export(project: Project, frames: dict[str, Image.Image], target: str | Path) -> list[Path]:
    """frames mode: `target` is a folder. storyboard modes: `target` is a file path. Returns written paths."""
    mode = project.export.mode
    pts = [p for p in project.storyboard_points() if p.id in frames]
    if not pts:
        raise ValueError("Nothing to export: no included points with frames.")
    target = Path(target)
    if mode == "frames":
        target.mkdir(parents=True, exist_ok=True)
        name, width, out = short_name(project), project.export.frame_width, []
        for i, p in enumerate(pts, 1):
            im = frames[p.id]
            if width and im.width > width:
                im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
            path = target / f"{name}_{i:03d}.png"
            im.save(path, "PNG")
            out.append(path)
        return out
    img = storyboard.render(project, frames)
    return [storyboard.save(img, target, "pdf" if mode == "storyboard_pdf" else "png")]
