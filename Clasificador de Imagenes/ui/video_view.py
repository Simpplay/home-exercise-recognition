"""Widget de visualización de video con soporte de zoom y paneo."""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QWidget

from utils.constants import ZOOM_MAX_FACTOR, ZOOM_MIN_FACTOR, ZOOM_STEP_FACTOR


class VideoView(QGraphicsView):
    """``QGraphicsView`` especializado en mostrar frames de video.

    Soporta zoom con Ctrl + rueda del mouse, paneo por arrastre cuando hay
    zoom aplicado, y una cuadrícula opcional de regla de tercios superpuesta
    para ayudar a centrar al sujeto en el encuadre.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._pixmap_item = QGraphicsPixmapItem()
        self._scene.addItem(self._pixmap_item)

        self._zoom_factor = ZOOM_MIN_FACTOR
        self._grid_enabled = False

        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setBackgroundBrush(QColor("#101116"))
        self.setFrameShape(QGraphicsView.Shape.NoFrame)

    def set_frame(self, pixmap: QPixmap) -> None:
        """Actualiza el frame mostrado. Ajusta la vista al primer frame recibido."""
        is_first_frame = self._pixmap_item.pixmap().isNull()
        self._pixmap_item.setPixmap(pixmap)
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        if is_first_frame:
            self.reset_zoom()
        self.viewport().update()

    def clear_frame(self) -> None:
        """Limpia la imagen mostrada (por ejemplo, al cerrar un video)."""
        self._pixmap_item.setPixmap(QPixmap())
        self._scene.setSceneRect(QRectF())

    def reset_zoom(self) -> None:
        """Restablece el zoom para ajustar el frame completo a la vista."""
        self.resetTransform()
        self._zoom_factor = ZOOM_MIN_FACTOR
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        if not self._pixmap_item.pixmap().isNull():
            self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

    def set_grid_enabled(self, enabled: bool) -> None:
        """Activa o desactiva la cuadrícula guía de encuadre."""
        self._grid_enabled = enabled
        self.viewport().update()

    def wheelEvent(self, event) -> None:  # noqa: N802 (nombre requerido por Qt)
        """Hace zoom con Ctrl + rueda; de lo contrario ignora el evento."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            angle = event.angleDelta().y()
            if angle == 0:
                return
            factor = ZOOM_STEP_FACTOR if angle > 0 else 1 / ZOOM_STEP_FACTOR
            self._apply_zoom(self._zoom_factor * factor)
            event.accept()
        else:
            event.ignore()

    def resizeEvent(self, event) -> None:  # noqa: N802
        """Mantiene el ajuste automático si no se ha aplicado zoom manual."""
        super().resizeEvent(event)
        if self._zoom_factor <= ZOOM_MIN_FACTOR and not self._pixmap_item.pixmap().isNull():
            self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

    def drawForeground(self, painter: QPainter, rect: QRectF) -> None:  # noqa: N802
        """Dibuja la cuadrícula de regla de tercios sobre el frame, si está activa."""
        if not self._grid_enabled or self._pixmap_item.pixmap().isNull():
            return

        bounds = self._pixmap_item.boundingRect()
        pen = QPen(QColor(255, 255, 255, 130))
        pen.setWidth(0)  # pluma cosmética: siempre 1px en pantalla, sin importar el zoom
        painter.setPen(pen)

        for i in (1, 2):
            x = bounds.left() + bounds.width() * i / 3
            painter.drawLine(QPointF(x, bounds.top()), QPointF(x, bounds.bottom()))
            y = bounds.top() + bounds.height() * i / 3
            painter.drawLine(QPointF(bounds.left(), y), QPointF(bounds.right(), y))

    def _apply_zoom(self, new_zoom: float) -> None:
        """Aplica un nuevo factor de zoom absoluto, respetando los límites configurados."""
        new_zoom = max(ZOOM_MIN_FACTOR, min(ZOOM_MAX_FACTOR, new_zoom))
        if new_zoom == self._zoom_factor:
            return
        relative_factor = new_zoom / self._zoom_factor
        self._zoom_factor = new_zoom
        self.scale(relative_factor, relative_factor)
        is_zoomed = new_zoom > ZOOM_MIN_FACTOR
        self.setDragMode(
            QGraphicsView.DragMode.ScrollHandDrag if is_zoomed else QGraphicsView.DragMode.NoDrag
        )
