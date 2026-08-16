"""Ponto de entrada do Junta Documentos — une múltiplos PDFs em um único arquivo."""

import sys

from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Junta Documentos")
    app.setOrganizationName("JuntaDocumentos")

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
