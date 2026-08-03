"""Punto de entrada de la aplicación Clasificador de Dataset de Imágenes."""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow, apply_application_style


def main() -> int:
    """Inicializa Qt, construye la ventana principal y arranca el loop de eventos."""
    app = QApplication(sys.argv)
    app.setApplicationName("Clasificador de Dataset de Imágenes")
    apply_application_style(app)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
