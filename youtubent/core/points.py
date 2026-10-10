import random

from .models import Point


def generate_points(duration: float, count: int, mode: str = "even", rng: random.Random | None = None) -> list[Point]:
    """Even: centre of each of `count` equal slices. Random: one random time per slice (stays chronological)."""
    if duration <= 0 or count <= 0:
        return []
    rng = rng or random.Random()
    slice_len = duration / count
    out = []
    for i in range(count):
        if mode == "random":
            t = (i + rng.random()) * slice_len
        else:
            t = (i + 0.5) * slice_len
        out.append(Point(t=round(clamp(t, duration), 1)))
    return out


def clamp(t: float, duration: float) -> float:
    """Keep inside the video (a hair before the end so ffmpeg can still grab a frame)."""
    return max(0.0, min(t, max(0.0, duration - 0.1)))
