"""yt-dlp wrapper: fetch video info and download a small video-only copy for frame grabbing."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import settings
from .urls import extract_video_id, watch_url

# Video only (no audio needed), capped at 720p: small + plenty sharp for a storyboard.
FORMAT = "bv*[height<=720]/b[height<=720]/b"


class DownloadError(Exception):
    pass


@dataclass
class VideoInfo:
    video_id: str
    title: str
    duration: float
    width: int
    height: int
    path: Path


def _find_cached(video_id: str) -> Path | None:
    for p in settings.cache_dir().glob(f"{video_id}.*"):
        if p.suffix not in (".part", ".ytdl", ".json"):
            return p
    return None


def fetch(url: str, progress: Callable[[float, str], None] | None = None) -> VideoInfo:
    """Resolve + download (cached). progress(fraction 0..1, message)."""
    import yt_dlp

    vid = extract_video_id(url)
    if not vid:
        raise DownloadError("That doesn't look like a YouTube link.")
    progress = progress or (lambda f, m: None)

    def hook(d):
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            if total:
                progress(d["downloaded_bytes"] / total, "Downloading video…")

    opts = {
        "format": FORMAT,
        "outtmpl": str(settings.cache_dir() / "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "progress_hooks": [hook],
        "retries": 3,
    }
    cached = _find_cached(vid)
    meta = settings.cache_dir() / f"{vid}.json"
    if cached and meta.exists():  # works offline
        try:
            m = json.loads(meta.read_text())
            progress(1.0, "Loaded from cache")
            return VideoInfo(vid, m["title"], m["duration"], m["width"], m["height"], cached)
        except Exception:
            pass
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            progress(0.0, "Asking YouTube nicely…")
            info = ydl.extract_info(watch_url(vid), download=cached is None)
    except Exception as e:  # yt-dlp raises many types
        raise DownloadError(_friendly(e)) from e

    path = _find_cached(vid)
    if path is None:
        raise DownloadError("Download finished but the file is missing.")
    progress(1.0, "Got it!")
    vi = VideoInfo(
        video_id=vid,
        title=info.get("title") or vid,
        duration=float(info.get("duration") or 0),
        width=int(info.get("width") or 16),
        height=int(info.get("height") or 9),
        path=path,
    )
    meta.write_text(json.dumps({"title": vi.title, "duration": vi.duration, "width": vi.width, "height": vi.height}))
    return vi


def _friendly(e: Exception) -> str:
    msg = str(e)
    low = msg.lower()
    if "private" in low:
        return "This video is private."
    if "unavailable" in low or "not available" in low:
        return "This video is unavailable."
    if "sign in" in low or "age" in low:
        return "YouTube wants a login for this one (age/members only)."
    if "urlopen" in low or "network" in low or "resolve" in low or "timed out" in low:
        return "Can't reach YouTube. Check your internet."
    return msg.replace("ERROR: ", "")[:300]
