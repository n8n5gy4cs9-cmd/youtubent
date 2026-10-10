"""Offscreen smoke test: fake a cached video so no network is needed."""
import json
import os
import subprocess

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

VID = "abcdefghijk"


def _wait(app, cond, ms=15000):
    import time
    end = time.time() + ms / 1000
    while time.time() < end and not cond():
        app.processEvents()
        time.sleep(0.01)
    assert cond(), getattr(app, "dbg", lambda: "")()


def test_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setattr("sys.platform", "linux")
    from youtubent.core import frames, settings
    cache = settings.cache_dir()
    subprocess.run([frames.ffmpeg_exe(), "-v", "error", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=10:duration=20",
                    "-pix_fmt", "yuv420p", str(cache / f"{VID}.mp4")], check=True)
    (cache / f"{VID}.json").write_text(json.dumps({"title": "Smoke Test Vid", "duration": 20.0, "width": 320, "height": 180}))

    from PySide6.QtWidgets import QApplication
    from youtubent.ui import theme
    from youtubent.ui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(theme.QSS)
    w = MainWindow()
    w.resize(1280, 860); w.show()
    w.url.setText(f"https://youtu.be/{VID}")
    w.load_url()
    app.dbg = lambda: (w.msg.text(), len(w.project.points), len(w.gallery.thumbs), w.preview.pix)
    _wait(app, lambda: len(w.project.points) == 9 and len(w.gallery.thumbs) == 9 and w.preview.pix is not None)
    n = len(w.project.points)
    w.add_point(5.0); assert len(w.project.points) == n + 1
    w.set_time(w.sel, 7.3); assert w._sel_point().t == 7.3
    w.delete_point(w.sel); assert len(w.project.points) == n
    w._joke(); assert w._sel_point() is None or w._sel_point().caption
    w.grab().save(str(tmp_path / "shot.png"))
    # export frames (default) directly via job
    from youtubent.core import export
    from youtubent.ui.main_window import _export_job
    out = _export_job(w.video, w.project, tmp_path / "out", progress=lambda *a: None)
    assert len(out) == n and out[0].name.endswith("_001.png")
    w.project.export.mode = "storyboard_pdf"
    assert _export_job(w.video, w.project, tmp_path / "s.pdf", progress=lambda *a: None)[0].suffix == ".pdf"
    w.close()
    import shutil
    shutil.copy(tmp_path / "shot.png", os.environ.get("SHOT_OUT", str(tmp_path / "keep.png")))
