import sys
from pathlib import Path

from PySide6.QtGui import QIcon, QPixmap

BG, PANEL, PANEL2, BORDER = "#1b1c1f", "#25262b", "#2e3036", "#3a3c44"
FG, DIM, ACCENT = "#e6e7ea", "#8d8f98", "#ff4d5e"


def assets() -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base / "assets"


_cache: dict = {}


def icon(name: str, variant: str = "") -> QIcon:
    key = (name, variant)
    if key not in _cache:
        _cache[key] = QIcon(str(assets() / "sprites" / f"{name}{variant}.png"))
    return _cache[key]


def pixmap(rel: str) -> QPixmap:
    return QPixmap(str(assets() / rel))


QSS = f"""
* {{ font-size: 13px; color: {FG}; }}
QMainWindow, QWidget#root {{ background: {BG}; }}
QWidget {{ background: transparent; }}
QFrame#panel, QWidget#panel {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 10px; }}
QLineEdit, QSpinBox, QComboBox, QDoubleSpinBox {{
    background: {PANEL2}; border: 1px solid {BORDER}; border-radius: 8px; padding: 6px 8px; min-height: 18px;
    selection-background-color: {ACCENT}; }}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border-color: {ACCENT}; }}
QComboBox QAbstractItemView {{ background: {PANEL2}; border: 1px solid {BORDER}; selection-background-color: {ACCENT}; }}
QPushButton {{ background: {PANEL2}; border: 1px solid {BORDER}; border-radius: 8px; padding: 6px 12px; }}
QPushButton:hover {{ background: #3a3c44; }}
QPushButton:pressed {{ background: #45474f; }}
QPushButton:disabled {{ color: #666; }}
QPushButton#primary {{ background: {ACCENT}; border: none; color: white; font-weight: 600; }}
QPushButton#primary:hover {{ background: #ff6674; }}
QPushButton#primary:disabled {{ background: #6b3a40; color: #aaa; }}
QToolButton {{ background: transparent; border: none; border-radius: 6px; padding: 4px; }}
QToolButton:hover {{ background: {PANEL2}; }}
QLabel#dim {{ color: {DIM}; }}
QLabel#h {{ font-size: 15px; font-weight: 700; }}
QTabWidget::pane {{ border: none; }}
QTabBar::tab {{ background: transparent; padding: 8px 14px; color: {DIM}; border-bottom: 2px solid transparent; }}
QTabBar::tab:selected {{ color: {FG}; border-bottom: 2px solid {ACCENT}; }}
QListWidget {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 10px; outline: 0; }}
QListWidget::item {{ border-radius: 8px; padding: 4px; color: {DIM}; }}
QListWidget::item:selected {{ background: {PANEL2}; border: 2px solid {ACCENT}; color: {FG}; }}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 4px; border: 1px solid {BORDER}; background: {PANEL2}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
QProgressBar {{ background: {PANEL2}; border: none; border-radius: 4px; max-height: 8px; text-align: center; color: transparent; }}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 4px; }}
QStatusBar {{ background: {BG}; color: {DIM}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; }}
QScrollBar::handle:horizontal {{ background: {BORDER}; border-radius: 5px; min-width: 30px; }}
QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QToolTip {{ background: {PANEL2}; color: {FG}; border: 1px solid {BORDER}; padding: 4px; }}
QMenuBar, QMenu {{ background: {PANEL}; }}
QMenu::item:selected, QMenuBar::item:selected {{ background: {ACCENT}; }}
"""
