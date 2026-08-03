"""Slider de línea de tiempo que superpone segmentos y marcadores sobre la barra."""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QSlider, QStyle, QStyleOptionSlider, QWidget


class TimelineSlider(QSlider):
    """``QSlider`` horizontal que dibuja los segmentos y bookmarks del video.

    Pensado para videos largos con varios ejercicios: permite ver de un
    vistazo dónde empieza y termina cada tramo marcado, y dónde están los
    frames marcados con bookmark, sin perder el comportamiento normal de
    arrastre del slider.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)
        self._segments: list[tuple[int, int, QColor]] = []
        self._bookmarks: list[int] = []

    def set_segments(self, segments: list[tuple[int, int, QColor]]) -> None:
        """Reemplaza los rangos de segmento a dibujar como (inicio, fin, color)."""
        self._segments = segments
        self.update()

    def set_bookmarks(self, frame_indices: list[int]) -> None:
        """Reemplaza los índices de frame marcados con bookmark a dibujar."""
        self._bookmarks = frame_indices
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 (nombre requerido por Qt)
        super().paintEvent(event)
        span = self.maximum() - self.minimum()
        if span <= 0 or (not self._segments and not self._bookmarks):
            return

        groove_rect = self._groove_rect()
        if groove_rect.width() <= 0:
            return

        painter = QPainter(self)

        for start, end, color in self._segments:
            x1 = groove_rect.left() + (start - self.minimum()) / span * groove_rect.width()
            x2 = groove_rect.left() + (end - self.minimum()) / span * groove_rect.width()
            fill_color = QColor(color)
            fill_color.setAlpha(170)
            painter.fillRect(
                QRectF(x1, groove_rect.top(), max(2.0, x2 - x1), groove_rect.height()), fill_color
            )

        pen = QPen(QColor("#f5c542"))
        pen.setWidth(2)
        painter.setPen(pen)
        for index in self._bookmarks:
            x = groove_rect.left() + (index - self.minimum()) / span * groove_rect.width()
            painter.drawLine(int(x), groove_rect.top() - 3, int(x), groove_rect.bottom() + 3)

    def _groove_rect(self):
        """Obtiene el rectángulo de la ranura del slider según el estilo activo."""
        option = QStyleOptionSlider()
        self.initStyleOption(option)
        return self.style().subControlRect(
            QStyle.ComplexControl.CC_Slider, option, QStyle.SubControl.SC_SliderGroove, self
        )
