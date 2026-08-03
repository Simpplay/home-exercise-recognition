"""Ventana principal: integra reproductor, controles y paneles laterales."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from core.config import AppConfig
from core.frame_extractor import FrameExtractor
from core.image_processing import apply_preview_adjustments
from core.video_player import VideoLoadError, VideoPlayer
from models.data_models import (
    Bookmark,
    FrameRecord,
    ImageAdjustments,
    SessionMetadata,
    VideoSegment,
    VideoSessionState,
)
from ui.controls_widget import ControlsWidget
from ui.metadata_dialog import MetadataDialog
from ui.segments_widget import SegmentsPanel
from ui.sidebar_widget import VideoListSidebar
from ui.styles import DARK_STYLESHEET
from ui.thumbnails_widget import ThumbnailsPanel
from ui.top_bar import TopBar
from ui.video_view import VideoView
from utils.constants import STEP_LARGE, STEP_SMALL, VIDEO_FILE_FILTER
from utils.image_convert import bgr_to_qpixmap

_SEGMENT_COLORS: tuple[QColor, ...] = (
    QColor("#3a5fd9"),
    QColor("#e0704f"),
    QColor("#4caf7d"),
    QColor("#c26bd1"),
    QColor("#d1a53e"),
    QColor("#4fb8e0"),
)


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación de curación de datasets de video."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Clasificador de Dataset — Ejercicios Físicos")
        self.resize(1440, 900)

        self._config = AppConfig()
        self._video_player = VideoPlayer()
        self._frame_extractor = FrameExtractor()

        self._destination_dir: Path | None = self._config.last_destination_folder
        self._current_video_path: Path | None = None
        self._current_raw_frame = None
        self._is_playing = False
        self._auto_next_enabled = False
        self._pending_segment_start: int | None = None

        self._video_metadata: dict[Path, SessionMetadata] = {}
        self._session_states: dict[Path, VideoSessionState] = {}

        self._playback_timer = QTimer(self)
        self._playback_timer.timeout.connect(self._advance_playback)

        self._build_ui()
        self._connect_signals()
        self._register_shortcuts()
        self._restore_window_state()

        if self._destination_dir is not None:
            self._top_bar.set_destination_text(str(self._destination_dir))

        self._set_video_controls_enabled(False)

    # ------------------------------------------------------------------
    # Construcción de interfaz
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self._top_bar = TopBar()
        self._sidebar = VideoListSidebar()
        self._segments_panel = SegmentsPanel()
        self._video_view = VideoView()
        self._controls = ControlsWidget()
        self._thumbnails_panel = ThumbnailsPanel()

        left_splitter = QSplitter(Qt.Orientation.Vertical)
        left_splitter.addWidget(self._sidebar)
        left_splitter.addWidget(self._segments_panel)
        left_splitter.setStretchFactor(0, 1)
        left_splitter.setStretchFactor(1, 1)

        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        center_layout.addWidget(self._video_view, stretch=1)
        center_layout.addWidget(self._controls)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_splitter)
        splitter.addWidget(center_widget)
        splitter.addWidget(self._thumbnails_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([240, 900, 240])

        root_widget = QWidget()
        root_layout = QVBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._top_bar)
        root_layout.addWidget(splitter, stretch=1)

        self.setCentralWidget(root_widget)
        self.setStatusBar(QStatusBar())

    def _connect_signals(self) -> None:
        self._sidebar.open_video_requested.connect(self._prompt_open_video)
        self._sidebar.open_folder_requested.connect(self._prompt_open_folder)
        self._sidebar.video_selected.connect(self._load_video)
        self._sidebar.videos_dropped.connect(self._handle_videos_dropped)

        self._controls.play_pause_clicked.connect(self._toggle_play_pause)
        self._controls.step_requested.connect(self._step_frames)
        self._controls.seek_requested.connect(self._seek_to_frame)
        self._controls.save_frame_clicked.connect(self._save_current_frame)
        self._controls.bookmark_clicked.connect(self._add_bookmark)
        self._controls.grid_toggled.connect(self._video_view.set_grid_enabled)
        self._controls.adjustments_changed.connect(self._handle_adjustments_changed)

        self._top_bar.destination_folder_requested.connect(self._prompt_destination_folder)
        self._top_bar.export_json_requested.connect(self._export_metadata_json)
        self._top_bar.auto_next_toggled.connect(self._set_auto_next_enabled)
        self._top_bar.bookmark_selected.connect(self._seek_to_frame)

        self._thumbnails_panel.delete_requested.connect(self._delete_frame_record)

        self._segments_panel.mark_start_clicked.connect(self._mark_segment_start)
        self._segments_panel.mark_end_clicked.connect(self._mark_segment_end)
        self._segments_panel.segment_jump_requested.connect(
            lambda segment: self._seek_to_frame(segment.start_frame)
        )
        self._segments_panel.segment_delete_requested.connect(self._delete_segment)
        self._segments_panel.segment_edit_requested.connect(self._edit_segment)

    def _register_shortcuts(self) -> None:
        bindings = {
            "Space": self._toggle_play_pause,
            "A": lambda: self._step_frames(-1),
            "D": lambda: self._step_frames(1),
            "Q": lambda: self._step_frames(-STEP_SMALL),
            "E": lambda: self._step_frames(STEP_SMALL),
            "Z": lambda: self._step_frames(-STEP_LARGE),
            "C": lambda: self._step_frames(STEP_LARGE),
            "S": self._save_current_frame,
        }
        self._shortcuts = []  # se retienen referencias para evitar recolección de basura
        for key, handler in bindings.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(handler)
            self._shortcuts.append(shortcut)

    def _restore_window_state(self) -> None:
        geometry, state = self._config.load_window_geometry()
        if geometry:
            self.restoreGeometry(geometry)
        if state:
            self.restoreState(state)

    # ------------------------------------------------------------------
    # Apertura de videos
    # ------------------------------------------------------------------
    def _prompt_open_video(self) -> None:
        start_dir = str(self._config.last_video_folder or Path.home())
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir video", start_dir, VIDEO_FILE_FILTER)
        if not file_path:
            return
        path = Path(file_path)
        self._config.last_video_folder = path.parent
        self._sidebar.add_video_if_missing(path)
        self._load_video(path)

    def _prompt_open_folder(self) -> None:
        start_dir = str(self._config.last_video_folder or Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Abrir carpeta de videos", start_dir)
        if not folder:
            return
        folder_path = Path(folder)
        self._config.last_video_folder = folder_path
        videos = sorted(p for p in folder_path.iterdir() if VideoPlayer.is_supported_video(p))
        if not videos:
            QMessageBox.information(self, "Sin videos", "No se encontraron videos en esa carpeta.")
            return
        self._sidebar.set_videos(videos)
        self._load_video(videos[0])

    def _handle_videos_dropped(self, paths: list[Path]) -> None:
        for path in paths:
            self._sidebar.add_video_if_missing(path)
        if paths:
            self._load_video(paths[0])

    def _load_video(self, path: Path) -> None:
        self._stop_playback()
        try:
            info = self._video_player.open(path)
        except VideoLoadError as error:
            QMessageBox.critical(self, "Error al abrir video", str(error))
            return

        self._current_video_path = path
        self._sidebar.add_video_if_missing(path)
        self._sidebar.select_video(path)

        if path not in self._video_metadata:
            self._prompt_metadata_for_video(path)

        self._pending_segment_start = None
        self._segments_panel.set_pending_start(None)

        self._video_view.clear_frame()
        self._controls.set_video_info(info)
        self._controls.set_playing(False)
        self._controls.set_saved_count(self._session_state(path).saved_count)
        self._set_video_controls_enabled(True)
        self._refresh_markers_view()

        self._show_frame(0)

        self.statusBar().showMessage(
            f"{path.name} · {info.resolution_text} · {info.fps:.2f} FPS · "
            f"{info.frame_count} frames · {info.duration_seconds:.1f}s"
        )

    def _prompt_metadata_for_video(self, path: Path) -> None:
        persona, ejercicio, angulo = self._config.last_metadata
        dialog = MetadataDialog(self, initial_persona=persona, initial_ejercicio=ejercicio, initial_angulo=angulo)
        if dialog.exec() == MetadataDialog.DialogCode.Accepted:
            metadata = dialog.metadata()
            if metadata is not None:
                self._video_metadata[path] = metadata
                self._config.set_last_metadata(metadata.persona, metadata.ejercicio, metadata.angulo)

    def _resolve_metadata_for_frame(self, frame_index: int) -> SessionMetadata | None:
        """Determina qué metadata usar al guardar un frame.

        Si el frame cae dentro de un segmento marcado (video largo con varios
        ejercicios), se usa la metadata de ese segmento. De lo contrario se
        usa la metadata general del video, pidiéndola si aún no existe.
        """
        if self._current_video_path is None:
            return None

        state = self._session_state(self._current_video_path)
        for segment in state.segments:
            if segment.contains(frame_index):
                return segment.metadata

        metadata = self._video_metadata.get(self._current_video_path)
        if metadata is None:
            self._prompt_metadata_for_video(self._current_video_path)
            metadata = self._video_metadata.get(self._current_video_path)
        return metadata

    # ------------------------------------------------------------------
    # Reproducción y navegación
    # ------------------------------------------------------------------
    def _toggle_play_pause(self) -> None:
        if not self._video_player.is_open:
            return
        self._is_playing = not self._is_playing
        self._controls.set_playing(self._is_playing)
        if self._is_playing:
            fps = self._video_player.info.fps if self._video_player.info else 30.0
            interval_ms = max(1, int(1000 / fps)) if fps > 0 else 33
            self._playback_timer.start(interval_ms)
        else:
            self._playback_timer.stop()

    def _stop_playback(self) -> None:
        self._is_playing = False
        self._playback_timer.stop()
        self._controls.set_playing(False)

    def _advance_playback(self) -> None:
        info = self._video_player.info
        if info is None:
            self._stop_playback()
            return
        next_index = self._video_player.current_index + 1
        if next_index >= info.frame_count:
            self._stop_playback()
            self._handle_video_finished()
            return
        self._show_frame(next_index)

    def _handle_video_finished(self) -> None:
        if not self._auto_next_enabled or self._current_video_path is None:
            return
        next_path = self._sidebar.next_video_after(self._current_video_path)
        if next_path is not None:
            self._load_video(next_path)

    def _step_frames(self, delta: int) -> None:
        if not self._video_player.is_open:
            return
        self._stop_playback()
        new_index = self._video_player.current_index + delta
        self._show_frame(new_index)

    def _seek_to_frame(self, frame_index: int) -> None:
        if not self._video_player.is_open:
            return
        self._stop_playback()
        self._show_frame(frame_index)

    def _show_frame(self, index: int) -> None:
        frame = self._video_player.read_frame(index)
        if frame is None:
            return
        self._current_raw_frame = frame
        self._render_current_frame()
        time_seconds = self._video_player.time_for_index(self._video_player.current_index)
        self._controls.set_current_frame(self._video_player.current_index, time_seconds)

    def _render_current_frame(self) -> None:
        if self._current_raw_frame is None:
            return
        adjustments: ImageAdjustments = self._controls.current_adjustments()
        preview_frame = apply_preview_adjustments(self._current_raw_frame, adjustments)
        self._video_view.set_frame(bgr_to_qpixmap(preview_frame))

    def _handle_adjustments_changed(self, _adjustments: ImageAdjustments) -> None:
        self._render_current_frame()

    # ------------------------------------------------------------------
    # Guardado de frames
    # ------------------------------------------------------------------
    def _save_current_frame(self) -> None:
        if not self._video_player.is_open or self._current_raw_frame is None or self._current_video_path is None:
            return

        if self._destination_dir is None:
            self._prompt_destination_folder()
            if self._destination_dir is None:
                return

        index = self._video_player.current_index
        metadata = self._resolve_metadata_for_frame(index)
        if metadata is None:
            return

        time_seconds = self._video_player.time_for_index(index)

        try:
            record = self._frame_extractor.save_frame(
                self._current_raw_frame,
                self._destination_dir,
                metadata,
                source_video=self._current_video_path,
                frame_index=index,
                time_seconds=time_seconds,
            )
        except OSError as error:
            QMessageBox.critical(self, "Error al guardar", str(error))
            return

        self._thumbnails_panel.add_record(record)
        state = self._session_state(self._current_video_path)
        state.saved_count += 1
        self._controls.set_saved_count(state.saved_count)
        self._sidebar.update_saved_count(self._current_video_path, state.saved_count)
        self.statusBar().showMessage(f"Frame guardado: {record.file_path.name}", 4000)

    def _delete_frame_record(self, record: FrameRecord) -> None:
        confirmation = QMessageBox.question(
            self,
            "Eliminar frame",
            f"¿Eliminar el archivo '{record.file_path.name}' del disco?",
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        self._frame_extractor.remove_record(record, delete_file=True)
        self._thumbnails_panel.remove_record(record)

        state = self._session_state(record.source_video)
        state.saved_count = max(0, state.saved_count - 1)
        self._sidebar.update_saved_count(record.source_video, state.saved_count)
        if record.source_video == self._current_video_path:
            self._controls.set_saved_count(state.saved_count)

    def _prompt_destination_folder(self) -> None:
        start_dir = str(self._destination_dir or self._config.last_video_folder or Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Elegir carpeta destino para los frames", start_dir)
        if not folder:
            return
        self._destination_dir = Path(folder)
        self._config.last_destination_folder = self._destination_dir
        self._top_bar.set_destination_text(str(self._destination_dir))

    def _export_metadata_json(self) -> None:
        if self._destination_dir is None:
            QMessageBox.information(self, "Sin carpeta destino", "Primero elige una carpeta destino.")
            return
        json_path = self._frame_extractor.export_json(self._destination_dir)
        QMessageBox.information(self, "Exportado", f"Metadata exportada en:\n{json_path}")

    # ------------------------------------------------------------------
    # Marcadores (bookmarks)
    # ------------------------------------------------------------------
    def _add_bookmark(self) -> None:
        if not self._video_player.is_open or self._current_video_path is None:
            return
        state = self._session_state(self._current_video_path)
        index = self._video_player.current_index
        if any(bookmark.frame_index == index for bookmark in state.bookmarks):
            return
        state.bookmarks.append(Bookmark(frame_index=index))
        state.bookmarks.sort(key=lambda b: b.frame_index)
        self._refresh_markers_view()
        self.statusBar().showMessage(f"Marcador agregado en frame {index}", 3000)

    def _refresh_markers_view(self) -> None:
        """Sincroniza combo de bookmarks, línea de tiempo y lista de segmentos."""
        if self._current_video_path is None:
            self._top_bar.set_bookmarks([])
            self._controls.set_bookmarks([])
            self._controls.set_segments([])
            self._segments_panel.set_segments([])
            return

        state = self._session_state(self._current_video_path)
        bookmark_indices = [bookmark.frame_index for bookmark in state.bookmarks]
        self._top_bar.set_bookmarks(bookmark_indices)
        self._controls.set_bookmarks(bookmark_indices)
        self._controls.set_segments(
            [
                (segment.start_frame, segment.end_frame, self._segment_color(segment.metadata.ejercicio))
                for segment in state.segments
            ]
        )
        self._segments_panel.set_segments(state.segments)

    @staticmethod
    def _segment_color(ejercicio: str) -> QColor:
        """Asigna un color estable a cada nombre de ejercicio para distinguir segmentos."""
        index = abs(hash(ejercicio.strip().lower())) % len(_SEGMENT_COLORS)
        return _SEGMENT_COLORS[index]

    def _session_state(self, path: Path) -> VideoSessionState:
        if path not in self._session_states:
            self._session_states[path] = VideoSessionState(video_path=path)
        return self._session_states[path]

    # ------------------------------------------------------------------
    # Segmentos (videos largos con varios ejercicios)
    # ------------------------------------------------------------------
    def _mark_segment_start(self) -> None:
        if not self._video_player.is_open:
            return
        self._pending_segment_start = self._video_player.current_index
        self._segments_panel.set_pending_start(self._pending_segment_start)

    def _defaults_for_new_segment(self) -> tuple[str, str]:
        """Calcula (persona, ángulo) por defecto para un nuevo segmento.

        Se toman del último segmento ya creado en este video (el tramo
        anterior), ya que normalmente persona y ángulo se mantienen entre
        ejercicios consecutivos de una misma sesión de grabación. Si aún no
        hay segmentos, se recurre a la metadata general del video o a la
        última usada globalmente.
        """
        if self._current_video_path is not None:
            state = self._session_state(self._current_video_path)
            if state.segments:
                previous = state.segments[-1]
                return previous.metadata.persona, previous.metadata.angulo

            existing_metadata = self._video_metadata.get(self._current_video_path)
            if existing_metadata is not None:
                return existing_metadata.persona, existing_metadata.angulo

        last_persona, _, last_angulo = self._config.last_metadata
        return last_persona, last_angulo

    def _mark_segment_end(self) -> None:
        if (
            not self._video_player.is_open
            or self._pending_segment_start is None
            or self._current_video_path is None
        ):
            return

        start = self._pending_segment_start
        end = self._video_player.current_index
        if end < start:
            start, end = end, start

        base_persona, base_angulo = self._defaults_for_new_segment()

        dialog = MetadataDialog(
            self, initial_persona=base_persona, initial_ejercicio="", initial_angulo=base_angulo
        )
        dialog.setWindowTitle(f"Nuevo segmento: frames {start}-{end}")
        if dialog.exec() != MetadataDialog.DialogCode.Accepted:
            return
        metadata = dialog.metadata()
        if metadata is None:
            return

        state = self._session_state(self._current_video_path)
        state.segments.append(VideoSegment(start_frame=start, end_frame=end, metadata=metadata))
        state.segments.sort(key=lambda segment: segment.start_frame)

        self._pending_segment_start = None
        self._segments_panel.set_pending_start(None)
        self._refresh_markers_view()
        self.statusBar().showMessage(
            f"Segmento agregado: {metadata.ejercicio} ({metadata.angulo}), frames {start}-{end}", 4000
        )

    def _delete_segment(self, segment: VideoSegment) -> None:
        if self._current_video_path is None:
            return
        state = self._session_state(self._current_video_path)
        if segment in state.segments:
            state.segments.remove(segment)
        self._refresh_markers_view()

    def _edit_segment(self, segment: VideoSegment) -> None:
        if self._current_video_path is None:
            return

        dialog = MetadataDialog(
            self,
            initial_persona=segment.metadata.persona,
            initial_ejercicio=segment.metadata.ejercicio,
            initial_angulo=segment.metadata.angulo,
        )
        dialog.setWindowTitle(f"Editar segmento: frames {segment.start_frame}-{segment.end_frame}")
        if dialog.exec() != MetadataDialog.DialogCode.Accepted:
            return
        metadata = dialog.metadata()
        if metadata is None:
            return

        state = self._session_state(self._current_video_path)
        try:
            index = state.segments.index(segment)
        except ValueError:
            return
        state.segments[index] = VideoSegment(
            start_frame=segment.start_frame, end_frame=segment.end_frame, metadata=metadata
        )
        self._refresh_markers_view()

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def _set_auto_next_enabled(self, enabled: bool) -> None:
        self._auto_next_enabled = enabled

    def _set_video_controls_enabled(self, enabled: bool) -> None:
        self._controls.set_controls_enabled(enabled)

    def closeEvent(self, event) -> None:  # noqa: N802
        """Persiste la geometría de la ventana y libera el video antes de cerrar."""
        self._config.save_window_geometry(self.saveGeometry(), self.saveState())
        self._video_player.release()
        super().closeEvent(event)


def apply_application_style(app) -> None:
    """Aplica la hoja de estilos oscura moderna a toda la aplicación."""
    app.setStyleSheet(DARK_STYLESHEET)
