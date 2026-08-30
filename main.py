"""Ponto de entrada do DocJoin — une múltiplos PDFs em um único arquivo."""

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from src.gui.brand_logo import ceasaminas_mark_pixmap
from src.gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("DocJoin")
    app.setOrganizationName("CEASAMINAS")
    app.setWindowIcon(QIcon(ceasaminas_mark_pixmap(128)))

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
