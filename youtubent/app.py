import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from youtubent.ui import theme
from youtubent.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Youtuben't")
    app.setStyleSheet(theme.QSS)
    app.setWindowIcon(QIcon(str(theme.assets() / "app" / "icon.png")))
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
