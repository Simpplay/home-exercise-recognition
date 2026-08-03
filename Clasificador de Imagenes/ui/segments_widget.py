"""Panel para delimitar y administrar segmentos (ejercicios) dentro de un video largo."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.data_models import VideoSegment

_SEGMENT_ROLE = Qt.ItemDataRole.UserRole


class SegmentsPanel(QFrame):
    """Lista los segmentos delimitados en el video actual y permite crear más.

    Pensado para videos de varios minutos que contienen varios ejercicios
    seguidos de una misma persona: el usuario navega hasta el inicio de un
    ejercicio, pulsa "Marcar inicio", navega hasta el final y pulsa
    "Marcar fin…" para asignarle Ejercicio/Ángulo. A partir de ahí, guardar
    un frame dentro de ese rango usa automáticamente esa metadata.
    """

    mark_start_clicked = Signal()
    mark_end_clicked = Signal()
    segment_jump_requested = Signal(VideoSegment)
    segment_delete_requested = Signal(VideoSegment)
    segment_edit_requested = Signal(VideoSegment)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SegmentsPanel")

        title = QLabel("SEGMENTOS DEL VIDEO")
        title.setObjectName("SectionTitle")

        self._status_label = QLabel(self._IDLE_TEXT)
        self._status_label.setWordWrap(True)

        self._start_button = QPushButton("Marcar inicio")
        self._start_button.clicked.connect(self.mark_start_clicked.emit)

        self._end_button = QPushButton("Marcar fin…")
        self._end_button.setObjectName("PrimaryButton")
        self._end_button.setEnabled(False)
        self._end_button.clicked.connect(self.mark_end_clicked.emit)

        buttons_row = QHBoxLayout()
        buttons_row.addWidget(self._start_button)
        buttons_row.addWidget(self._end_button)

        self._list_widget = QListWidget()
        self._list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self._list_widget.itemDoubleClicked.connect(self._handle_double_click)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(title)
        layout.addWidget(self._status_label)
        layout.addLayout(buttons_row)
        layout.addWidget(self._list_widget, stretch=1)

    _IDLE_TEXT = "Video con varios ejercicios: marca cada tramo."

    def set_pending_start(self, frame_index: int | None) -> None:
        """Refleja si hay un inicio de segmento pendiente de cerrar."""
        if frame_index is None:
            self._status_label.setText(self._IDLE_TEXT)
            self._end_button.setEnabled(False)
        else:
            self._status_label.setText(
                f"Inicio marcado en frame {frame_index}. Ve al final del ejercicio y marca el fin."
            )
            self._end_button.setEnabled(True)

    def set_segments(self, segments: list[VideoSegment]) -> None:
        """Reemplaza la lista de segmentos mostrados para el video actual."""
        self._list_widget.clear()
        for segment in segments:
            item = QListWidgetItem(segment.label())
            item.setData(_SEGMENT_ROLE, segment)
            self._list_widget.addItem(item)

    def _handle_double_click(self, item: QListWidgetItem) -> None:
        self.segment_jump_requested.emit(item.data(_SEGMENT_ROLE))

    def _show_context_menu(self, position) -> None:
        item = self._list_widget.itemAt(position)
        if item is None:
            return
        segment: VideoSegment = item.data(_SEGMENT_ROLE)

        menu = QMenu(self)
        jump_action = menu.addAction("Ir al inicio")
        edit_action = menu.addAction("Editar ejercicio/ángulo")
        delete_action = menu.addAction("Eliminar segmento")
        chosen = menu.exec(self._list_widget.mapToGlobal(position))

        if chosen == jump_action:
            self.segment_jump_requested.emit(segment)
        elif chosen == edit_action:
            self.segment_edit_requested.emit(segment)
        elif chosen == delete_action:
            self.segment_delete_requested.emit(segment)
