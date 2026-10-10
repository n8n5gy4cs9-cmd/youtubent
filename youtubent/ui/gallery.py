from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QListView, QListWidget, QListWidgetItem

from youtubent.core.models import Point, fmt_time

THUMB_W = 150


class Gallery(QListWidget):
    """Thumbnail strip, chronological. Click = select, checkbox = include in export."""

    selected = Signal(str)
    include_changed = Signal(str, bool)
    delete_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.setViewMode(QListView.IconMode)
        self.setFlow(QListView.LeftToRight)
        self.setWrapping(False)
        self.setMovement(QListView.Static)
        self.setResizeMode(QListView.Adjust)
        self.setIconSize(QSize(THUMB_W, int(THUMB_W * 9 / 16)))
        self.setSpacing(6)
        self.setHorizontalScrollMode(QListWidget.ScrollPerPixel)
        self.thumbs: dict[str, QPixmap] = {}
        self._busy = False
        self.currentItemChanged.connect(self._cur)
        self.itemChanged.connect(self._chk)

    def set_aspect(self, w: int, h: int):
        ih = int(THUMB_W * h / max(1, w))
        self.setIconSize(QSize(THUMB_W, min(ih, 220)))

    def refresh(self, points: list[Point], sel: str | None):
        self._busy = True
        self.clear()
        for p in sorted(points, key=lambda p: p.t):
            it = QListWidgetItem(self._label(p))
            it.setData(Qt.UserRole, p.id)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Checked if p.include else Qt.Unchecked)
            pm = self.thumbs.get(p.id)
            if pm:
                it.setIcon(QIcon(pm))
            it.setToolTip(p.caption or fmt_time(p.t))
            self.addItem(it)
            if p.id == sel:
                self.setCurrentItem(it)
        self._busy = False

    @staticmethod
    def _label(p: Point) -> str:
        return fmt_time(p.t, False) + (f"  {p.caption[:14]}" if p.caption else "")

    def _cur(self, it, _prev):
        if it and not self._busy:
            self.selected.emit(it.data(Qt.UserRole))

    def _chk(self, it):
        if not self._busy:
            self.include_changed.emit(it.data(Qt.UserRole), it.checkState() == Qt.Checked)

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Delete, Qt.Key_Backspace) and self.currentItem():
            self.delete_requested.emit(self.currentItem().data(Qt.UserRole))
        else:
            super().keyPressEvent(e)
