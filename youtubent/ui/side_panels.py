from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox,
                               QToolButton, QVBoxLayout, QWidget)

from youtubent.core.export import MODES
from youtubent.core.models import ExportSettings, Point, fmt_time, parse_time
from youtubent.core.storyboard import THEMES

from . import theme


class PointPanel(QWidget):
    time_changed = Signal(float)
    nudged = Signal(float)
    caption_changed = Signal(str)
    include_changed = Signal(bool)
    delete = Signal()
    joke = Signal()
    add = Signal()

    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self); v.setSpacing(10)
        self.title = QLabel("No point selected"); self.title.setObjectName("h")
        v.addWidget(self.title)
        v.addWidget(self._dim("Time (mm:ss.s)"))
        self.time = QLineEdit(); self.time.setPlaceholderText("1:23.4")
        self.time.editingFinished.connect(self._time_done)
        v.addWidget(self.time)
        row = QHBoxLayout()
        for lab, d in (("−1s", -1), ("−0.1", -0.1), ("+0.1", 0.1), ("+1s", 1)):
            b = QPushButton(lab); b.clicked.connect(lambda _=False, d=d: self.nudged.emit(d)); row.addWidget(b)
        v.addLayout(row)
        v.addWidget(self._dim("Caption"))
        self.caption = QLineEdit(); self.caption.setPlaceholderText("Say something funny…")
        self.caption.textEdited.connect(self.caption_changed)
        v.addWidget(self.caption)
        j = QPushButton(" Random joke"); j.setIcon(theme.icon("dice")); j.clicked.connect(self.joke); v.addWidget(j)
        self.include = QCheckBox("Include in export"); self.include.toggled.connect(self._inc); v.addWidget(self.include)
        a = QPushButton(" Add point at playhead"); a.setIcon(theme.icon("add")); a.clicked.connect(self.add); v.addWidget(a)
        d = QPushButton(" Delete point"); d.setIcon(theme.icon("delete")); d.clicked.connect(self.delete); v.addWidget(d)
        v.addStretch()
        self._loading = False
        self.setEnabled(False)

    @staticmethod
    def _dim(t):
        l = QLabel(t); l.setObjectName("dim"); return l

    def _inc(self, b):
        if not self._loading:
            self.include_changed.emit(b)

    def _time_done(self):
        if self._loading:
            return
        try:
            self.time_changed.emit(parse_time(self.time.text()))
        except ValueError:
            self.time.setStyleSheet("border-color: #ff4d5e;")
            return
        self.time.setStyleSheet("")

    def show_point(self, p: Point | None, index: int = 0, total: int = 0):
        self._loading = True
        self.setEnabled(p is not None)
        if p is None:
            self.title.setText("No point selected"); self.time.clear(); self.caption.clear()
        else:
            self.title.setText(f"Frame {index} of {total}")
            if not self.time.hasFocus():
                self.time.setText(fmt_time(p.t))
            self.time.setStyleSheet("")
            if not self.caption.hasFocus():
                self.caption.setText(p.caption)
            self.include.setChecked(p.include)
        self._loading = False


class ExportPanel(QWidget):
    changed = Signal()
    export = Signal()

    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self); v.setSpacing(10)
        self.mode = QComboBox()
        for k, label in MODES.items():
            self.mode.addItem(label, k)
        form = QFormLayout(); form.setLabelAlignment(Qt.AlignLeft)
        form.addRow("Export as", self.mode)
        self.frame_w = QComboBox()
        for label, w in (("1280 px", 1280), ("1920 px", 1920), ("Original", 0), ("640 px", 640)):
            self.frame_w.addItem(label, w)
        form.addRow("PNG width", self.frame_w)
        v.addLayout(form)
        self.sb = QWidget(); sbv = QFormLayout(self.sb); sbv.setContentsMargins(0, 0, 0, 0)
        self.title = QLineEdit(); self.title.setPlaceholderText("(video title)")
        sbv.addRow("Title", self.title)
        self.cols = QSpinBox(); self.cols.setRange(1, 6); sbv.addRow("Columns", self.cols)
        self.cell = QSpinBox(); self.cell.setRange(160, 1200); self.cell.setSingleStep(40); sbv.addRow("Frame size", self.cell)
        self.gap = QSpinBox(); self.gap.setRange(0, 60); sbv.addRow("Gap", self.gap)
        self.theme = QComboBox(); self.theme.addItems(list(THEMES)); sbv.addRow("Theme", self.theme)
        self.show_title = QCheckBox("Show title"); self.show_ts = QCheckBox("Timestamps"); self.show_cap = QCheckBox("Captions")
        for c in (self.show_title, self.show_ts, self.show_cap):
            sbv.addRow(c)
        v.addWidget(self.sb)
        self.hint = QLabel(); self.hint.setObjectName("dim"); self.hint.setWordWrap(True); v.addWidget(self.hint)
        self.btn = QPushButton(" Export"); self.btn.setObjectName("primary"); self.btn.setIcon(theme.icon("export"))
        self.btn.setMinimumHeight(38); self.btn.clicked.connect(self.export)
        v.addWidget(self.btn); v.addStretch()
        self._loading = False
        for w in (self.mode, self.frame_w, self.theme):
            w.currentIndexChanged.connect(self._ch)
        for w in (self.cols, self.cell, self.gap):
            w.valueChanged.connect(self._ch)
        self.title.textEdited.connect(self._ch)
        for c in (self.show_title, self.show_ts, self.show_cap):
            c.toggled.connect(self._ch)

    def _ch(self, *_):
        if not self._loading:
            self.changed.emit()
        self._visibility()

    def _visibility(self):
        m = self.mode.currentData()
        self.sb.setVisible(m != "frames")
        self.frame_w.setEnabled(m == "frames")
        self.hint.setText({
            "frames": "Saves a folder of numbered PNGs like name_001.png, name_002.png… No storyboard.",
            "storyboard_png": "One stylized storyboard image, frames in chronological order.",
            "storyboard_pdf": "One stylized storyboard PDF, great for sending to a friend.",
        }[m])

    def load(self, s: ExportSettings):
        self._loading = True
        self.mode.setCurrentIndex(max(0, self.mode.findData(s.mode)))
        self.frame_w.setCurrentIndex(max(0, self.frame_w.findData(s.frame_width)))
        self.title.setText(s.title); self.cols.setValue(s.columns); self.cell.setValue(s.cell_width); self.gap.setValue(s.gap)
        self.theme.setCurrentText(s.theme)
        self.show_title.setChecked(s.show_title); self.show_ts.setChecked(s.show_timestamps); self.show_cap.setChecked(s.show_captions)
        self._loading = False
        self._visibility()

    def store(self, s: ExportSettings):
        s.mode = self.mode.currentData(); s.frame_width = self.frame_w.currentData()
        s.title = self.title.text(); s.columns = self.cols.value(); s.cell_width = self.cell.value(); s.gap = self.gap.value()
        s.theme = self.theme.currentText()
        s.show_title = self.show_title.isChecked(); s.show_timestamps = self.show_ts.isChecked(); s.show_captions = self.show_cap.isChecked()
