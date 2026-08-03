"""Panel lateral izquierdo: lista de videos de la sesión con soporte drag & drop."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.video_player import VideoPlayer

_PATH_ROLE = Qt.ItemDataRole.UserRole


class VideoListSidebar(QFrame):
    """Lista los videos disponibles para revisar y permite abrir/soltar nuevos.

    Emite ``video_selected`` cuando el usuario elige un video de la lista
    (doble clic) y ``open_video_requested`` / ``open_folder_requested``
    cuando se pulsan los botones correspondientes.
    """

    video_selected = Signal(Path)
    open_video_requested = Signal()
    open_folder_requested = Signal()
    videos_dropped = Signal(list)  # list[Path]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setAcceptDrops(True)
        self.setMinimumWidth(220)
        self.setMaximumWidth(320)

        title = QLabel("VIDEOS")
        title.setObjectName("SectionTitle")

        self._list_widget = QListWidget()
        self._list_widget.itemDoubleClicked.connect(self._handle_item_double_clicked)

        open_video_button = QPushButton("Abrir video")
        open_video_button.clicked.connect(self.open_video_requested.emit)

        open_folder_button = QPushButton("Abrir carpeta")
        open_folder_button.clicked.connect(self.open_folder_requested.emit)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(open_video_button)
        buttons_layout.addWidget(open_folder_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(title)
        layout.addWidget(self._list_widget, stretch=1)
        layout.addLayout(buttons_layout)

    def set_videos(self, paths: list[Path]) -> None:
        """Reemplaza la lista completa de videos mostrados."""
        self._list_widget.clear()
        for path in paths:
            self._add_item(path)

    def add_video_if_missing(self, path: Path) -> None:
        """Agrega un video a la lista si aún no está presente."""
        if self._find_item(path) is None:
            self._add_item(path)

    def select_video(self, path: Path) -> None:
        """Marca visualmente un video como el actualmente seleccionado."""
        item = self._find_item(path)
        if item is not None:
            self._list_widget.setCurrentItem(item)

    def update_saved_count(self, path: Path, count: int) -> None:
        """Actualiza el contador de frames guardados mostrado junto a un video."""
        item = self._find_item(path)
        if item is not None:
            item.setText(self._item_label(path, count))

    def next_video_after(self, path: Path) -> Path | None:
        """Devuelve el video siguiente al indicado en la lista, si existe."""
        item = self._find_item(path)
        if item is None:
            return None
        row = self._list_widget.row(item)
        if row + 1 < self._list_widget.count():
            return self._list_widget.item(row + 1).data(_PATH_ROLE)
        return None

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        video_paths = self._resolve_dropped_paths(paths)
        if video_paths:
            self.videos_dropped.emit(video_paths)
        event.acceptProposedAction()

    def _resolve_dropped_paths(self, paths: list[Path]) -> list[Path]:
        """Expande carpetas soltadas a la lista de videos que contienen."""
        resolved: list[Path] = []
        for path in paths:
            if path.is_dir():
                resolved.extend(sorted(p for p in path.iterdir() if VideoPlayer.is_supported_video(p)))
            elif VideoPlayer.is_supported_video(path):
                resolved.append(path)
        return resolved

    def _handle_item_double_clicked(self, item: QListWidgetItem) -> None:
        path = item.data(_PATH_ROLE)
        if path is not None:
            self.video_selected.emit(path)

    def _add_item(self, path: Path) -> None:
        item = QListWidgetItem(self._item_label(path, 0))
        item.setData(_PATH_ROLE, path)
        item.setToolTip(str(path))
        self._list_widget.addItem(item)

    def _find_item(self, path: Path) -> QListWidgetItem | None:
        for row in range(self._list_widget.count()):
            item = self._list_widget.item(row)
            if item.data(_PATH_ROLE) == path:
                return item
        return None

    @staticmethod
    def _item_label(path: Path, count: int) -> str:
        suffix = f"  ·  {count} guardados" if count else ""
        return f"{path.name}{suffix}"
