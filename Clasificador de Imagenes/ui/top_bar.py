"""Barra superior: título, carpeta destino, exportación y marcadores."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QWidget


class TopBar(QFrame):
    """Barra superior con acciones globales de la aplicación."""

    destination_folder_requested = Signal()
    export_json_requested = Signal()
    auto_next_toggled = Signal(bool)
    bookmark_selected = Signal(int)  # índice de frame elegido en el combo

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TopBar")

        title = QLabel("Clasificador de Dataset — Ejercicios Físicos")
        title.setObjectName("TopBarTitle")

        self._destination_label = QLabel("Carpeta destino: (sin definir)")

        destination_button = QPushButton("Elegir carpeta destino")
        destination_button.clicked.connect(self.destination_folder_requested.emit)

        export_button = QPushButton("Exportar metadata (JSON)")
        export_button.clicked.connect(self.export_json_requested.emit)

        self._auto_next_button = QPushButton("Auto-siguiente video")
        self._auto_next_button.setCheckable(True)
        self._auto_next_button.toggled.connect(self.auto_next_toggled.emit)

        self._bookmarks_combo = QComboBox()
        self._bookmarks_combo.setMinimumWidth(160)
        self._bookmarks_combo.addItem("Marcadores…")
        self._bookmarks_combo.activated.connect(self._handle_bookmark_activated)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.addWidget(title)
        layout.addStretch(1)
        layout.addWidget(self._destination_label)
        layout.addWidget(destination_button)
        layout.addWidget(export_button)
        layout.addWidget(self._auto_next_button)
        layout.addWidget(self._bookmarks_combo)

    def set_destination_text(self, text: str) -> None:
        """Actualiza la etiqueta que muestra la carpeta destino actual."""
        self._destination_label.setText(f"Carpeta destino: {text}")

    def set_bookmarks(self, frame_indices: list[int]) -> None:
        """Reemplaza las entradas del combo de marcadores para el video actual."""
        self._bookmarks_combo.blockSignals(True)
        self._bookmarks_combo.clear()
        self._bookmarks_combo.addItem("Marcadores…")
        for index in frame_indices:
            self._bookmarks_combo.addItem(f"Frame {index}", index)
        self._bookmarks_combo.blockSignals(False)

    def _handle_bookmark_activated(self, combo_index: int) -> None:
        if combo_index <= 0:
            return
        frame_index = self._bookmarks_combo.itemData(combo_index)
        if frame_index is not None:
            self.bookmark_selected.emit(int(frame_index))
        self._bookmarks_combo.setCurrentIndex(0)
