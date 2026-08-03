"""Panel lateral derecho: miniaturas de los frames guardados en la sesión."""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.data_models import FrameRecord
from utils.constants import IMAGE_THUMBNAIL_SIZE

_RECORD_ROLE = Qt.ItemDataRole.UserRole


class ThumbnailsPanel(QFrame):
    """Muestra las miniaturas de los frames guardados y permite eliminarlos."""

    delete_requested = Signal(FrameRecord)
    thumbnail_activated = Signal(FrameRecord)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ThumbnailsPanel")
        self.setMinimumWidth(220)
        self.setMaximumWidth(320)

        title = QLabel("FRAMES GUARDADOS")
        title.setObjectName("SectionTitle")

        self._list_widget = QListWidget()
        self._list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self._list_widget.setIconSize(QSize(IMAGE_THUMBNAIL_SIZE, IMAGE_THUMBNAIL_SIZE))
        self._list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self._list_widget.setMovement(QListWidget.Movement.Static)
        self._list_widget.setSpacing(6)
        self._list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self._list_widget.itemDoubleClicked.connect(self._handle_double_click)

        delete_button = QPushButton("Eliminar seleccionado")
        delete_button.clicked.connect(self._delete_selected)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(title)
        layout.addWidget(self._list_widget, stretch=1)
        layout.addWidget(delete_button)

    def add_record(self, record: FrameRecord) -> None:
        """Agrega una miniatura correspondiente a un frame recién guardado."""
        pixmap = QPixmap(str(record.file_path)).scaled(
            IMAGE_THUMBNAIL_SIZE,
            IMAGE_THUMBNAIL_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        item = QListWidgetItem(QIcon(pixmap), record.file_path.name)
        item.setData(_RECORD_ROLE, record)
        item.setToolTip(f"Frame {record.frame_index} · {record.time_seconds:.2f}s")
        self._list_widget.addItem(item)

    def remove_record(self, record: FrameRecord) -> None:
        """Quita la miniatura asociada a ``record`` de la lista."""
        for row in range(self._list_widget.count()):
            item = self._list_widget.item(row)
            if item.data(_RECORD_ROLE) == record:
                self._list_widget.takeItem(row)
                return

    def clear(self) -> None:
        """Vacía el panel de miniaturas."""
        self._list_widget.clear()

    def _delete_selected(self) -> None:
        item = self._list_widget.currentItem()
        if item is not None:
            self.delete_requested.emit(item.data(_RECORD_ROLE))

    def _handle_double_click(self, item: QListWidgetItem) -> None:
        self.thumbnail_activated.emit(item.data(_RECORD_ROLE))

    def _show_context_menu(self, position) -> None:
        item = self._list_widget.itemAt(position)
        if item is None:
            return
        menu = QMenu(self)
        delete_action = menu.addAction("Eliminar")
        chosen = menu.exec(self._list_widget.mapToGlobal(position))
        if chosen == delete_action:
            self.delete_requested.emit(item.data(_RECORD_ROLE))
