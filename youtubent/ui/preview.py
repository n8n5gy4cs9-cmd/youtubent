from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from . import theme


class Preview(QWidget):
    """Big frame viewer. Shows the empty-state illustration until a frame arrives."""

    def __init__(self):
        super().__init__()
        self.setMinimumSize(320, 180)
        self.pix: QPixmap | None = None
        self.label = ""
        self.busy = False
        self.empty = theme.pixmap("illustrations/empty.png")
        self.empty_text = "Paste a link. Skip the video."

    def set_frame(self, pix: QPixmap | None, label: str = ""):
        self.pix, self.label, self.busy = pix, label, False
        self.update()

    def set_busy(self, b: bool):
        self.busy = b
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(0, 0, -1, -1)
        p.setBrush(QColor("#121316"))
        p.setPen(QColor(theme.BORDER))
        p.drawRoundedRect(r, 10, 10)
        if self.pix is None:
            e = self.empty.scaledToWidth(min(360, r.width() - 40), Qt.SmoothTransformation)
            p.drawPixmap((r.width() - e.width()) // 2, (r.height() - e.height()) // 2 - 20, e)
            p.setPen(QColor(theme.DIM))
            f = p.font(); f.setPointSize(15); p.setFont(f)
            p.drawText(r.adjusted(0, r.height() // 2 + e.height() // 2 - 5, 0, 0), Qt.AlignHCenter | Qt.AlignTop, self.empty_text)
            return
        s = self.pix.size().scaled(r.size() - QSize(16, 16), Qt.KeepAspectRatio)
        x, y = (r.width() - s.width()) // 2, (r.height() - s.height()) // 2
        p.setOpacity(0.5 if self.busy else 1.0)
        p.drawPixmap(x, y, s.width(), s.height(), self.pix)
        p.setOpacity(1.0)
        if self.label:
            f = p.font(); f.setBold(True); f.setPointSize(14); p.setFont(f)
            w = p.fontMetrics().horizontalAdvance(self.label) + 20
            p.setBrush(QColor(0, 0, 0, 170)); p.setPen(Qt.NoPen)
            p.drawRoundedRect(x + 10, y + s.height() - 38, w, 28, 8, 8)
            p.setPen(Qt.white)
            p.drawText(x + 20, y + s.height() - 18, self.label)
