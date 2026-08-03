"""Conversión entre arrays de OpenCV (BGR) y tipos de imagen de Qt."""
from __future__ import annotations

import numpy as np
from PySide6.QtGui import QImage, QPixmap


def bgr_to_qimage(frame_bgr: np.ndarray) -> QImage:
    """Convierte un array BGR de OpenCV a ``QImage`` (RGB888), copiando el buffer."""
    height, width = frame_bgr.shape[:2]
    rgb = frame_bgr[:, :, ::-1].copy()  # BGR -> RGB, copia para buffer propio y contiguo
    bytes_per_line = 3 * width
    image = QImage(rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
    return image.copy()


def bgr_to_qpixmap(frame_bgr: np.ndarray) -> QPixmap:
    """Convierte un array BGR de OpenCV directamente a ``QPixmap``."""
    return QPixmap.fromImage(bgr_to_qimage(frame_bgr))
