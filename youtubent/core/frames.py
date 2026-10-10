"""Grab single frames with ffmpeg (bundled via imageio-ffmpeg, falls back to system ffmpeg)."""
from __future__ import annotations

import io
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image


class FrameError(Exception):
    pass


def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        exe = shutil.which("ffmpeg")
        if not exe:
            raise FrameError("ffmpeg not found (pip install imageio-ffmpeg)")
        return exe


def grab_frame(video: str | Path, t: float, max_width: int | None = None) -> Image.Image:
    """Decode one frame at time `t` seconds. Fast seek (-ss before -i)."""
    cmd = [ffmpeg_exe(), "-v", "error", "-ss", f"{max(0.0, t):.3f}", "-i", str(video), "-frames:v", "1"]
    if max_width:
        cmd += ["-vf", f"scale='min({int(max_width)},iw)':-2"]
    cmd += ["-f", "image2pipe", "-vcodec", "png", "-"]
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=60, creationflags=flags)
    except subprocess.TimeoutExpired as e:
        raise FrameError("ffmpeg timed out") from e
    if r.returncode != 0 or not r.stdout:
        raise FrameError(r.stderr.decode(errors="ignore")[-200:] or "no frame at that time")
    img = Image.open(io.BytesIO(r.stdout))
    img.load()
    return img.convert("RGB")
