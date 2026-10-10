import random
import subprocess

import pytest
from PIL import Image

from youtubent.core import frames, points, storyboard
from youtubent.core.models import Point, Project, fmt_time, parse_time
from youtubent.core.urls import extract_video_id

ID = "dQw4w9WgXcQ"


@pytest.mark.parametrize("u", [
    f"https://www.youtube.com/watch?v={ID}&t=5s", f"https://youtu.be/{ID}?si=x", f"https://youtube.com/shorts/{ID}",
    f"m.youtube.com/watch?v={ID}", f"https://www.youtube.com/embed/{ID}", ID,
])
def test_ids(u):
    assert extract_video_id(u) == ID


@pytest.mark.parametrize("u", ["https://example.com/watch?v=" + ID, "hello", "https://youtube.com/", ""])
def test_bad_ids(u):
    assert extract_video_id(u) is None


def test_time_roundtrip():
    assert fmt_time(75.34) == "1:15.3"
    assert fmt_time(3725) == "1:02:05.0"
    assert parse_time("1:15.5") == 75.5
    assert parse_time("1h2m5s") == 3725
    assert parse_time("90") == 90
    with pytest.raises(ValueError):
        parse_time("abc")


def test_points_even_random():
    ev = points.generate_points(100, 4)
    assert [p.t for p in ev] == [12.5, 37.5, 62.5, 87.5]
    rnd = points.generate_points(100, 10, "random", random.Random(1))
    ts = [p.t for p in rnd]
    assert ts == sorted(ts) and all(0 <= t < 100 for t in ts)
    assert points.generate_points(0, 5) == []


def test_project_roundtrip(tmp_path):
    pr = Project(url="u", duration=10, points=[Point(2, "hi"), Point(1, include=False)])
    f = tmp_path / "a.ytb"
    pr.save(f)
    back = Project.load(f)
    assert back.points[0].caption == "hi" and back.points[1].include is False
    assert [p.t for p in back.storyboard_points()] == [2]


@pytest.fixture(scope="module")
def video(tmp_path_factory):
    p = tmp_path_factory.mktemp("v") / "t.mp4"
    subprocess.run([frames.ffmpeg_exe(), "-v", "error", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=10:duration=5",
                    "-pix_fmt", "yuv420p", str(p)], check=True)
    return p


def test_grab_and_storyboard(video, tmp_path):
    im = frames.grab_frame(video, 2.0, max_width=200)
    assert im.width == 200
    with pytest.raises(frames.FrameError):
        frames.grab_frame(tmp_path / "nope.mp4", 1)
    pr = Project(title="Test", duration=5, points=[Point(t, f"cap {t}") for t in (0.5, 1.5, 2.5, 3.5)])
    fr = {p.id: frames.grab_frame(video, p.t) for p in pr.points}
    img = storyboard.render(pr, fr)
    for ext in ("png", "jpg", "pdf"):
        out = storyboard.save(img, tmp_path / f"o.{ext}")
        assert out.exists() and out.stat().st_size > 1000
    assert Image.open(tmp_path / "o.png").width > 3 * 480
    pr.points[0].include = False
    assert storyboard.render(pr, fr).height > 0
