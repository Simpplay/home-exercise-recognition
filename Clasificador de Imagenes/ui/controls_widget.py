"""Barra de controles inferior: reproducción, navegación, guardado y ajustes."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from models.data_models import ImageAdjustments, VideoInfo
from ui.timeline_slider import TimelineSlider
from utils.constants import STEP_LARGE, STEP_SMALL
from utils.formatting import format_time


class ControlsWidget(QFrame):
    """Agrupa reproducción, navegación por frames, guardado y ajustes de preview."""

    play_pause_clicked = Signal()
    step_requested = Signal(int)  # delta de frames, puede ser negativo
    seek_requested = Signal(int)  # índice de frame absoluto
    save_frame_clicked = Signal()
    bookmark_clicked = Signal()
    grid_toggled = Signal(bool)
    adjustments_changed = Signal(ImageAdjustments)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("BottomControls")

        self._video_info: VideoInfo | None = None
        self._is_playing = False

        self._build_ui()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self._position_slider = TimelineSlider()
        self._position_slider.setRange(0, 0)
        self._position_slider.sliderMoved.connect(self._handle_slider_moved)

        self._frame_label = QLabel("Frame 0 / 0")
        self._time_label = QLabel("00:00 / 00:00")

        slider_row = QHBoxLayout()
        slider_row.addWidget(self._position_slider, stretch=1)
        slider_row.addWidget(self._frame_label)
        slider_row.addWidget(self._time_label)

        self._play_button = QPushButton("▶ Reproducir")
        self._play_button.setObjectName("PrimaryButton")
        self._play_button.clicked.connect(self.play_pause_clicked.emit)

        back_30 = self._make_step_button("−30", -STEP_LARGE)
        back_5 = self._make_step_button("−5", -STEP_SMALL)
        back_1 = self._make_step_button("−1", -1)
        fwd_1 = self._make_step_button("+1", 1)
        fwd_5 = self._make_step_button("+5", STEP_SMALL)
        fwd_30 = self._make_step_button("+30", STEP_LARGE)

        transport_row = QHBoxLayout()
        transport_row.addStretch(1)
        for button in (back_30, back_5, back_1, self._play_button, fwd_1, fwd_5, fwd_30):
            transport_row.addWidget(button)
        transport_row.addStretch(1)

        self._save_button = QPushButton("💾 Guardar Frame (S)")
        self._save_button.setObjectName("PrimaryButton")
        self._save_button.clicked.connect(self.save_frame_clicked.emit)

        self._bookmark_button = QPushButton("★ Marcar")
        self._bookmark_button.clicked.connect(self.bookmark_clicked.emit)

        self._saved_count_label = QLabel("Guardados en este video: 0")

        actions_row = QHBoxLayout()
        actions_row.addWidget(self._save_button)
        actions_row.addWidget(self._bookmark_button)
        actions_row.addStretch(1)
        actions_row.addWidget(self._saved_count_label)

        adjustments_row = self._build_adjustments_row()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)
        layout.addLayout(slider_row)
        layout.addLayout(transport_row)
        layout.addLayout(actions_row)
        layout.addLayout(adjustments_row)

    def _build_adjustments_row(self) -> QHBoxLayout:
        self._grayscale_check = QCheckBox("Escala de grises")
        self._equalize_check = QCheckBox("Ecualizar histograma")
        self._grid_check = QCheckBox("Cuadrícula")

        for checkbox in (self._grayscale_check, self._equalize_check):
            checkbox.toggled.connect(self._emit_adjustments)
        self._grid_check.toggled.connect(self.grid_toggled.emit)

        self._brightness_slider = self._make_bipolar_slider()
        self._contrast_slider = self._make_bipolar_slider()
        self._brightness_slider.valueChanged.connect(self._emit_adjustments)
        self._contrast_slider.valueChanged.connect(self._emit_adjustments)

        row = QHBoxLayout()
        row.addWidget(self._grayscale_check)
        row.addWidget(self._equalize_check)
        row.addWidget(self._grid_check)
        row.addSpacing(12)
        row.addWidget(QLabel("Brillo:"))
        row.addWidget(self._brightness_slider)
        row.addWidget(QLabel("Contraste:"))
        row.addWidget(self._contrast_slider)
        return row

    @staticmethod
    def _make_bipolar_slider() -> QSlider:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(-100, 100)
        slider.setValue(0)
        slider.setFixedWidth(120)
        return slider

    def _make_step_button(self, text: str, delta: int) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("IconButton")
        button.clicked.connect(lambda: self.step_requested.emit(delta))
        return button

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def set_video_info(self, info: VideoInfo) -> None:
        """Configura el rango del slider y las etiquetas de tiempo total."""
        self._video_info = info
        self._position_slider.setRange(0, max(0, info.frame_count - 1))
        self._position_slider.set_segments([])
        self._position_slider.set_bookmarks([])

    def set_segments(self, segments: list[tuple[int, int, QColor]]) -> None:
        """Actualiza los rangos de segmento dibujados sobre la línea de tiempo."""
        self._position_slider.set_segments(segments)

    def set_bookmarks(self, frame_indices: list[int]) -> None:
        """Actualiza los ticks de marcadores dibujados sobre la línea de tiempo."""
        self._position_slider.set_bookmarks(frame_indices)

    def set_current_frame(self, frame_index: int, time_seconds: float) -> None:
        """Actualiza slider y etiquetas para reflejar el frame actual."""
        self._position_slider.blockSignals(True)
        self._position_slider.setValue(frame_index)
        self._position_slider.blockSignals(False)

        total_frames = self._video_info.frame_count if self._video_info else 0
        total_time = self._video_info.duration_seconds if self._video_info else 0.0
        self._frame_label.setText(f"Frame {frame_index} / {max(0, total_frames - 1)}")
        self._time_label.setText(f"{format_time(time_seconds)} / {format_time(total_time)}")

    def set_playing(self, is_playing: bool) -> None:
        """Actualiza el texto del botón de reproducción según el estado actual."""
        self._is_playing = is_playing
        self._play_button.setText("⏸ Pausar" if is_playing else "▶ Reproducir")

    def set_saved_count(self, count: int) -> None:
        """Actualiza el contador de frames guardados para el video actual."""
        self._saved_count_label.setText(f"Guardados en este video: {count}")

    def set_controls_enabled(self, enabled: bool) -> None:
        """Habilita o deshabilita todos los controles (por ejemplo, sin video cargado)."""
        self.setEnabled(enabled)

    def current_adjustments(self) -> ImageAdjustments:
        """Devuelve el estado actual de los ajustes de visualización."""
        return ImageAdjustments(
            grayscale=self._grayscale_check.isChecked(),
            equalize_histogram=self._equalize_check.isChecked(),
            brightness=self._brightness_slider.value(),
            contrast=self._contrast_slider.value(),
        )

    # ------------------------------------------------------------------
    # Manejadores internos
    # ------------------------------------------------------------------
    def _handle_slider_moved(self, value: int) -> None:
        self.seek_requested.emit(value)

    def _emit_adjustments(self) -> None:
        self.adjustments_changed.emit(self.current_adjustments())
