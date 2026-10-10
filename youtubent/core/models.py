"""Plain data models + time helpers. No Qt here."""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path


def fmt_time(sec: float, tenths: bool = True) -> str:
    """75.34 -> '1:15.3' ; 3725 -> '1:02:05.0'."""
    sec = max(0.0, float(sec))
    total_tenths = int(round(sec * 10))
    h, rem = divmod(total_tenths, 36000)
    m, rem = divmod(rem, 600)
    s, t = divmod(rem, 10)
    base = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
    return f"{base}.{t}" if tenths else base


def parse_time(text: str) -> float:
    """Accepts '75', '1:15', '1:15.5', '1:02:05', '1h2m5s'. Raises ValueError."""
    text = text.strip().lower()
    if not text:
        raise ValueError("empty time")
    if any(c in text for c in "hms") and ":" not in text:
        total, num = 0.0, ""
        for c in text:
            if c.isdigit() or c == ".":
                num += c
            elif c in "hms" and num:
                total += float(num) * {"h": 3600, "m": 60, "s": 1}[c]
                num = ""
            else:
                raise ValueError(f"bad time: {text}")
        if num:
            total += float(num)
        return total
    parts = text.split(":")
    if len(parts) > 3:
        raise ValueError(f"bad time: {text}")
    total = 0.0
    for p in parts:
        total = total * 60 + float(p)
    if total < 0:
        raise ValueError("negative time")
    return total


def new_id() -> str:
    return uuid.uuid4().hex[:8]


@dataclass
class Point:
    t: float
    caption: str = ""
    include: bool = True
    id: str = field(default_factory=new_id)


@dataclass
class ExportSettings:
    columns: int = 3
    cell_width: int = 480
    gap: int = 12
    theme: str = "dark"  # dark | light | midnight | paper
    title: str = ""
    show_title: bool = True
    show_timestamps: bool = True
    show_captions: bool = True
    mode: str = "frames"  # frames (separate PNGs, default) | storyboard_png | storyboard_pdf
    frame_width: int = 1280  # width of separate PNG frames (0 = original size)


@dataclass
class Project:
    url: str = ""
    video_id: str = ""
    title: str = ""
    duration: float = 0.0
    width: int = 16
    height: int = 9
    points: list[Point] = field(default_factory=list)
    export: ExportSettings = field(default_factory=ExportSettings)

    def sorted_points(self) -> list[Point]:
        return sorted(self.points, key=lambda p: p.t)

    def storyboard_points(self) -> list[Point]:
        """Included points in chronological order."""
        return [p for p in self.sorted_points() if p.include]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_dict(cls, d: dict) -> "Project":
        pts = [Point(**p) for p in d.get("points", [])]
        exp = ExportSettings(**d.get("export", {}))
        rest = {k: v for k, v in d.items() if k not in ("points", "export")}
        return cls(points=pts, export=exp, **rest)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "Project":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
