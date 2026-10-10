import random
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QIcon, QImage, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
                               QProgressBar, QPushButton, QSpinBox, QSplitter, QTabWidget, QVBoxLayout, QWidget)

from youtubent.core import captions, downloader, export, frames, settings
from youtubent.core.models import Point, Project, fmt_time
from youtubent.core.points import clamp, generate_points
from youtubent.core.urls import extract_video_id

from . import theme, workers
from .gallery import Gallery
from .preview import Preview
from .side_panels import ExportPanel, PointPanel
from .timeline import Timeline

LOADING = ["Asking YouTube nicely…", "Skipping the boring parts…", "Finding the good frames…", "Pretending to watch…"]


def pil_to_pixmap(im) -> QPixmap:
    im = im.convert("RGB")
    q = QImage(im.tobytes(), im.width, im.height, im.width * 3, QImage.Format_RGB888).copy()
    return QPixmap.fromImage(q)


def _thumb_job(video, pid, t, progress=None):
    return pid, t, frames.grab_frame(video, t, max_width=320)


def _preview_job(video, token, t, progress=None):
    return token, t, frames.grab_frame(video, t, max_width=1280)


def _export_job(video, project, target, progress=None):
    pts = project.storyboard_points()
    mw = (project.export.frame_width or None) if project.export.mode == "frames" else project.export.cell_width * 2
    got = {}
    for i, p in enumerate(pts):
        progress(i / len(pts), f"Grabbing frame {i + 1}/{len(pts)}…")
        got[p.id] = frames.grab_frame(video, p.t, max_width=mw)
    progress(0.95, "Composing…")
    return export.export(project, got, target)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Youtuben't")
        self.resize(1280, 860)
        self.project = Project()
        self.video: Path | None = None
        self.sel: str | None = None
        self.thumb_t: dict[str, float] = {}
        self._token = 0
        self._busy = 0
        self._spin = 0
        self._project_path: Path | None = None

        root = QWidget(); root.setObjectName("root"); self.setCentralWidget(root)
        v = QVBoxLayout(root); v.setContentsMargins(14, 12, 14, 8); v.setSpacing(10)
        v.addLayout(self._topbar())

        self.preview, self.timeline, self.gallery = Preview(), Timeline(), Gallery()
        self.tabs = QTabWidget(); self.tabs.setFixedWidth(310)
        self.point_panel, self.export_panel = PointPanel(), ExportPanel()
        self.tabs.addTab(self.point_panel, theme.icon("clock"), "Point")
        self.tabs.addTab(self.export_panel, theme.icon("export"), "Export")
        self.export_panel.load(self.project.export)

        mid = QHBoxLayout(); mid.setSpacing(12)
        left = QVBoxLayout(); left.setSpacing(10)
        left.addWidget(self.preview, 1); left.addWidget(self.timeline); left.addWidget(self.gallery)
        self.gallery.setFixedHeight(150)
        mid.addLayout(left, 1); mid.addWidget(self.tabs)
        v.addLayout(mid, 1)

        # status bar
        sb = self.statusBar()
        self.spinner = QLabel(); self.spinner.setFixedSize(20, 20); self.spinner.setScaledContents(True)
        self.bar = QProgressBar(); self.bar.setFixedWidth(160); self.bar.setRange(0, 100); self.bar.hide()
        self.msg = QLabel("Ready. Paste a YouTube link to start.")
        sb.addWidget(self.spinner); sb.addWidget(self.msg, 1); sb.addPermanentWidget(self.bar)
        self.spin_timer = QTimer(self, interval=90); self.spin_timer.timeout.connect(self._tick_spin)
        self.pv_timer = QTimer(self, singleShot=True, interval=120); self.pv_timer.timeout.connect(self._request_preview)
        self.pv_t = 0.0

        self._wire()
        self._menus()
        self._shortcuts()
        QTimer.singleShot(0, self._restore_last)

    # ---------- layout bits
    def _topbar(self):
        h = QHBoxLayout(); h.setSpacing(8)
        logo = QLabel(); logo.setPixmap(theme.pixmap("app/logo_small.png")); h.addWidget(logo)
        self.url = QLineEdit(); self.url.setPlaceholderText("Paste a YouTube video or Shorts link…")
        self.url.setMinimumHeight(36)
        self.url.returnPressed.connect(self.load_url)
        h.addWidget(self.url, 1)
        self.load_btn = QPushButton(" Load"); self.load_btn.setObjectName("primary"); self.load_btn.setIcon(theme.icon("load"))
        self.load_btn.setMinimumHeight(36); self.load_btn.clicked.connect(self.load_url)
        h.addWidget(self.load_btn)
        h.addSpacing(10)
        h.addWidget(self._dim("Shots"))
        self.count = QSpinBox(); self.count.setRange(1, 60); self.count.setValue(9); h.addWidget(self.count)
        self.mode = QComboBox(); self.mode.addItem(theme.icon("even"), "Evenly spaced", "even"); self.mode.addItem(theme.icon("dice"), "Random", "random")
        h.addWidget(self.mode)
        self.gen_btn = QPushButton(" Generate"); self.gen_btn.setIcon(theme.icon("generate", "_accent"))
        self.gen_btn.setMinimumHeight(36); self.gen_btn.clicked.connect(self.generate); self.gen_btn.setEnabled(False)
        h.addWidget(self.gen_btn)
        return h

    @staticmethod
    def _dim(t):
        l = QLabel(t); l.setObjectName("dim"); return l

    def _wire(self):
        tl, g, pp, ep = self.timeline, self.gallery, self.point_panel, self.export_panel
        tl.selected.connect(self.select)
        tl.moving.connect(self._moving)
        tl.moved.connect(self._moved)
        tl.scrubbed.connect(self._scrubbed)
        tl.add_at.connect(self.add_point)
        g.selected.connect(self.select)
        g.delete_requested.connect(self.delete_point)
        g.include_changed.connect(self._include)
        pp.time_changed.connect(lambda t: self.set_time(self.sel, t))
        pp.nudged.connect(lambda d: self.sel and self.set_time(self.sel, self._sel_point().t + d))
        pp.caption_changed.connect(self._caption)
        pp.include_changed.connect(lambda b: self._include(self.sel, b))
        pp.delete.connect(lambda: self.sel and self.delete_point(self.sel))
        pp.add.connect(lambda: self.add_point(None))
        pp.joke.connect(self._joke)
        ep.changed.connect(lambda: ep.store(self.project.export))
        ep.export.connect(self.do_export)

    def _menus(self):
        m = self.menuBar().addMenu("File")
        for text, key, fn in (("Open project…", "Ctrl+O", self.open_project), ("Save project…", "Ctrl+S", self.save_project),
                              ("Export…", "Ctrl+E", self.do_export)):
            a = QAction(text, self); a.setShortcut(QKeySequence(key)); a.triggered.connect(fn); m.addAction(a)

    def _shortcuts(self):
        def sc(key, fn):
            QShortcut(QKeySequence(key), self, activated=fn)
        sc("Space", lambda: self.add_point(None))
        sc("Delete", lambda: self.sel and self.delete_point(self.sel))
        sc("Left", lambda: self._step(-1)); sc("Right", lambda: self._step(1))
        sc("Shift+Left", lambda: self.sel and self.set_time(self.sel, self._sel_point().t - 1))
        sc("Shift+Right", lambda: self.sel and self.set_time(self.sel, self._sel_point().t + 1))

    # ---------- busy / status
    def say(self, text):
        self.msg.setText(text)

    def _busy_on(self):
        self._busy += 1
        self.spin_timer.start()

    def _busy_off(self):
        self._busy = max(0, self._busy - 1)
        if not self._busy:
            self.spin_timer.stop(); self.spinner.clear(); self.bar.hide()

    def _tick_spin(self):
        self._spin = (self._spin + 1) % 8
        self.spinner.setPixmap(theme.pixmap(f"sprites/spinner_{self._spin}.png"))

    def _progress(self, f, m=""):
        self.bar.show(); self.bar.setValue(int(f * 100))
        if m:
            self.say(m)

    def _fail(self, err):
        self._busy_off()
        self.say("😬 " + err)

    # ---------- loading
    def load_url(self, keep_points: Project | None = None):
        url = self.url.text().strip()
        if not extract_video_id(url):
            self.say("😬 That doesn't look like a YouTube link.")
            return
        self._busy_on()
        self.load_btn.setEnabled(False)
        self.say(random.choice(LOADING))
        keep = keep_points if isinstance(keep_points, Project) else None
        workers.run(downloader.fetch, url, done=lambda info: self._loaded(info, url, keep), failed=self._load_failed, progress=self._progress)

    def _load_failed(self, err):
        self.load_btn.setEnabled(True)
        self._fail(err)

    def _loaded(self, info, url, keep: Project | None):
        self._busy_off()
        self.load_btn.setEnabled(True)
        export_settings = (keep or self.project).export
        if keep:
            self.project = keep
        else:
            self.project = Project(export=export_settings)
        pr = self.project
        pr.url, pr.video_id, pr.title, pr.duration, pr.width, pr.height = url, info.video_id, info.title, info.duration, info.width, info.height
        self.video = info.path
        self.gallery.set_aspect(info.width, info.height)
        self.gallery.thumbs.clear(); self.thumb_t.clear()
        self.gen_btn.setEnabled(True)
        self.setWindowTitle(f"Youtuben't — {info.title}")
        self.export_panel.title.setPlaceholderText(info.title)
        if keep and keep.points:
            self.say(f"Loaded “{info.title}” ({fmt_time(info.duration, False)})")
            self.select(keep.sorted_points()[0].id)
            self._refresh()
        else:
            self.say(f"Loaded “{info.title}” ({fmt_time(info.duration, False)}). Generating shots…")
            self._generate(confirm=False)

    # ---------- points
    def generate(self):
        self._generate(confirm=True)

    def _generate(self, confirm=True):
        if not self.video:
            return
        if confirm and self.project.points and QMessageBox.question(self, "Regenerate?", "Replace all current points?") != QMessageBox.Yes:
            return
        self.project.points = generate_points(self.project.duration, self.count.value(), self.mode.currentData())
        self.gallery.thumbs.clear(); self.thumb_t.clear()
        self.sel = self.project.sorted_points()[0].id if self.project.points else None
        self._refresh()
        if self.sel:
            self.select(self.sel)
        self.say(f"{len(self.project.points)} shots ready. Drag, add or delete to taste.")

    def _sel_point(self) -> Point | None:
        return next((p for p in self.project.points if p.id == self.sel), None)

    def _get(self, pid):
        return next((p for p in self.project.points if p.id == pid), None)

    def _refresh(self):
        pr = self.project
        pts = pr.sorted_points()
        self.timeline.set_data(pr.duration, pr.points, self.sel)
        self.gallery.refresh(pts, self.sel)
        sp = self._sel_point()
        idx = pts.index(sp) + 1 if sp else 0
        self.point_panel.show_point(sp, idx, len(pts))
        for p in pts:
            if self.thumb_t.get(p.id) != p.t and self.video:
                self.thumb_t[p.id] = p.t
                workers.run(_thumb_job, self.video, p.id, p.t, done=self._thumb_done)

    def _thumb_done(self, res):
        pid, t, im = res
        p = self._get(pid)
        if p and abs(p.t - t) < 0.001:
            self.gallery.thumbs[pid] = pil_to_pixmap(im)
            for i in range(self.gallery.count()):
                it = self.gallery.item(i)
                if it.data(256) == pid:
                    it.setIcon(QIcon(self.gallery.thumbs[pid]))

    def select(self, pid):
        p = self._get(pid)
        if not p:
            return
        self.sel = pid
        self.timeline.playhead = p.t
        self._refresh()
        self._show_at(p.t)

    def _step(self, d):
        pts = self.project.sorted_points()
        if not pts:
            return
        i = next((i for i, p in enumerate(pts) if p.id == self.sel), -1)
        self.select(pts[max(0, min(len(pts) - 1, i + d))].id)

    def set_time(self, pid, t):
        p = self._get(pid)
        if not p:
            return
        p.t = round(clamp(t, self.project.duration), 1)
        self.timeline.playhead = p.t
        self._refresh()
        self._show_at(p.t)

    def _moving(self, pid, t):
        self.point_panel.time.setText(fmt_time(t))
        self._show_at(t)

    def _moved(self, pid, t):
        self.set_time(pid, t)

    def _scrubbed(self, t):
        self._show_at(t)

    def add_point(self, t):
        if not self.video:
            return
        t = self.timeline.playhead if t is None else t
        p = Point(t=round(clamp(t, self.project.duration), 1))
        self.project.points.append(p)
        self.sel = p.id
        self.timeline.playhead = p.t
        self._refresh()
        self._show_at(p.t)
        self.say(f"Added a shot at {fmt_time(p.t)}")

    def delete_point(self, pid):
        pts = self.project.sorted_points()
        i = next((i for i, p in enumerate(pts) if p.id == pid), None)
        if i is None:
            return
        self.project.points = [p for p in self.project.points if p.id != pid]
        rest = self.project.sorted_points()
        self.sel = rest[min(i, len(rest) - 1)].id if rest else None
        self._refresh()
        if self.sel:
            self._show_at(self._sel_point().t)
            self.timeline.playhead = self._sel_point().t
            self.timeline.update()

    def _include(self, pid, on):
        p = self._get(pid)
        if p and p.include != on:
            p.include = on
            self._refresh()

    def _caption(self, text):
        p = self._sel_point()
        if p:
            p.caption = text
            self.gallery.refresh(self.project.sorted_points(), self.sel)

    def _joke(self):
        p = self._sel_point()
        if p:
            p.caption = captions.random_caption(avoid=p.caption)
            self.point_panel.caption.setText(p.caption)
            self.gallery.refresh(self.project.sorted_points(), self.sel)

    # ---------- preview
    def _show_at(self, t):
        self.pv_t = t
        self.preview.set_busy(True) if self.preview.pix else None
        self.pv_timer.start()

    def _request_preview(self):
        if not self.video:
            return
        self._token += 1
        workers.run(_preview_job, self.video, self._token, self.pv_t, done=self._preview_done,
                    failed=lambda e: (self.preview.set_busy(False), self.say("😬 " + e)))

    def _preview_done(self, res):
        token, t, im = res
        if token == self._token:
            self.preview.set_frame(pil_to_pixmap(im), fmt_time(t))

    # ---------- export / projects
    def do_export(self):
        if not self.video or not self.project.storyboard_points():
            self.say("😬 Nothing to export yet. Load a video first.")
            return
        self.export_panel.store(self.project.export)
        pr = self.project
        start = str(Path(settings.load().get("last_dir", str(Path.home() / "Pictures"))))
        if pr.export.mode == "frames":
            d = QFileDialog.getExistingDirectory(self, "Where should the frames go? (a subfolder is created)", start)
            if not d:
                return
            target = Path(d) / export.short_name(pr)
        else:
            ext = "pdf" if pr.export.mode == "storyboard_pdf" else "png"
            f, _ = QFileDialog.getSaveFileName(self, "Save storyboard", str(Path(start) / export.suggested_name(pr)), f"{ext.upper()} (*.{ext})")
            if not f:
                return
            target = Path(f)
        s = settings.load(); s["last_dir"] = str(target.parent); settings.save(s)
        self._busy_on()
        self.say("Building your masterpiece…")
        workers.run(_export_job, self.video, pr, target, done=lambda out: self._exported(out, target), failed=self._fail, progress=self._progress)

    def _exported(self, out, target):
        self._busy_off()
        self.say(f"✅ Saved {len(out)} file(s) to {target}")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target if target.is_dir() else target.parent)))

    def save_project(self):
        self.export_panel.store(self.project.export)
        f, _ = QFileDialog.getSaveFileName(self, "Save project", str(self._project_path or Path.home() / "story.ytb"), "Youtuben't project (*.ytb)")
        if f:
            self.project.save(f); self._project_path = Path(f); self.say(f"Saved {f}")

    def open_project(self):
        f, _ = QFileDialog.getOpenFileName(self, "Open project", str(Path.home()), "Youtuben't project (*.ytb)")
        if f:
            self._open(Path(f))

    def _open(self, path: Path):
        try:
            pr = Project.load(path)
        except Exception as e:
            self.say(f"😬 Couldn't open project: {e}")
            return
        self._project_path = path
        self.url.setText(pr.url)
        self.export_panel.load(pr.export)
        self.sel = None
        self.load_url(keep_points=pr)

    def _restore_last(self):
        f = settings.data_dir() / "last.ytb"
        if f.exists():
            try:
                if Project.load(f).url:
                    self._open(f)
            except Exception:
                pass

    def closeEvent(self, e):
        try:
            if self.project.url:
                self.export_panel.store(self.project.export)
                self.project.save(settings.data_dir() / "last.ytb")
        finally:
            super().closeEvent(e)
