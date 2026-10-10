from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from youtubent.core.models import Point, fmt_time

from . import theme

PAD = 28
TRACK_Y = 62


class Timeline(QWidget):
    """Horizontal timeline. Click/drag empty space = move playhead. Drag a marker = change its time.
    Double-click = add point there."""

    selected = Signal(str)          # point id
    moved = Signal(str, float)      # point id, new t (on release)
    moving = Signal(str, float)     # live while dragging
    scrubbed = Signal(float)        # playhead moved
    add_at = Signal(float)

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(110)
        self.setMouseTracking(True)
        self.duration = 0.0
        self.points: list[Point] = []
        self.sel: str | None = None
        self.playhead = 0.0
        self.marker = theme.pixmap("sprites/marker.png")
        self.head = theme.pixmap("sprites/playhead.png")
        self._drag: str | None = None
        self._scrub = False

    def set_data(self, duration, points, sel=None, playhead=None):
        self.duration, self.points, self.sel = duration, points, sel
        if playhead is not None:
            self.playhead = playhead
        self.update()

    # t <-> x
    def _x(self, t):
        w = max(1, self.width() - 2 * PAD)
        return PAD + (t / self.duration if self.duration else 0) * w

    def _t(self, x):
        w = max(1, self.width() - 2 * PAD)
        return max(0.0, min(self.duration, (x - PAD) / w * self.duration))

    def _hit(self, pos):
        best, bd = None, 14
        for p in self.points:
            d = abs(self._x(p.t) - pos.x())
            if d < bd and pos.y() > 20:
                best, bd = p, d
        return best

    def paintEvent(self, _):
        g = QPainter(self)
        g.setRenderHint(QPainter.Antialiasing)
        g.setBrush(QColor(theme.PANEL)); g.setPen(QColor(theme.BORDER))
        g.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 10, 10)
        if not self.duration:
            g.setPen(QColor(theme.DIM)); g.drawText(self.rect(), Qt.AlignCenter, "Timeline appears when a video is loaded")
            return
        # ticks
        step = next((s for s in (1, 2, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800, 3600) if self.duration / s <= max(2, (self.width() - 2 * PAD) / 80)), 7200)
        g.setPen(QColor(theme.DIM))
        t = 0
        while t <= self.duration:
            x = self._x(t)
            g.drawLine(QPointF(x, TRACK_Y + 8), QPointF(x, TRACK_Y + 14))
            g.drawText(QRectF(x - 30, TRACK_Y + 16, 60, 16), Qt.AlignCenter, fmt_time(t, False))
            t += step
        # track
        g.setPen(Qt.NoPen); g.setBrush(QColor("#3a3c44"))
        g.drawRoundedRect(QRectF(PAD, TRACK_Y - 3, self.width() - 2 * PAD, 6), 3, 3)
        # markers
        for p in self.points:
            x = self._x(p.t)
            g.setOpacity(1.0 if p.include else 0.35)
            if p.id == self.sel:
                g.setPen(QPen(QColor(theme.ACCENT), 2)); g.drawLine(QPointF(x, 24), QPointF(x, TRACK_Y))
            g.drawPixmap(int(x - 12), 26, self.marker.scaledToWidth(24 if p.id != self.sel else 28, Qt.SmoothTransformation))
            g.setOpacity(1.0)
        # playhead
        x = self._x(self.playhead)
        g.setPen(QPen(QColor(theme.FG), 2)); g.drawLine(QPointF(x, 14), QPointF(x, TRACK_Y + 8))
        g.drawPixmap(int(x - 8), 2, self.head.scaledToWidth(16, Qt.SmoothTransformation))
        g.setPen(QColor(theme.FG)); g.drawText(QRectF(x + 10, 2, 80, 14), Qt.AlignLeft | Qt.AlignVCenter, fmt_time(self.playhead))

    def mousePressEvent(self, e):
        if not self.duration or e.button() != Qt.LeftButton:
            return
        hit = self._hit(e.position())
        if hit:
            self._drag = hit.id
            self.sel = hit.id
            self.selected.emit(hit.id)
        else:
            self._scrub = True
            self.playhead = self._t(e.position().x())
            self.scrubbed.emit(self.playhead)
        self.update()

    def mouseMoveEvent(self, e):
        if self._drag:
            t = round(self._t(e.position().x()), 1)
            for p in self.points:
                if p.id == self._drag:
                    p.t = t
            self.playhead = t
            self.moving.emit(self._drag, t)
        elif self._scrub:
            self.playhead = self._t(e.position().x())
            self.scrubbed.emit(self.playhead)
        else:
            self.setCursor(Qt.OpenHandCursor if self._hit(e.position()) else Qt.ArrowCursor)
        self.update()

    def mouseReleaseEvent(self, e):
        if self._drag:
            p = next((p for p in self.points if p.id == self._drag), None)
            if p:
                self.moved.emit(p.id, p.t)
        self._drag, self._scrub = None, False

    def mouseDoubleClickEvent(self, e):
        if self.duration and not self._hit(e.position()):
            self.add_at.emit(round(self._t(e.position().x()), 1))
