"""Funciones puras de procesamiento de imagen usadas solo para previsualización.

Ninguna de estas transformaciones se aplica jamás a la imagen que se guarda en
disco: el frame original (BGR, sin modificar) siempre se conserva intacto en
``FrameExtractor``. Estas funciones solo afectan lo que se dibuja en pantalla.
"""
from __future__ import annotations

import cv2
import numpy as np

from models.data_models import ImageAdjustments


def apply_preview_adjustments(frame_bgr: np.ndarray, adjustments: ImageAdjustments) -> np.ndarray:
    """Aplica los ajustes de visualización solicitados sobre una copia del frame."""
    if adjustments.is_identity():
        return frame_bgr

    result = frame_bgr

    if adjustments.grayscale:
        gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        result = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    if adjustments.equalize_histogram:
        result = _equalize_histogram(result)

    if adjustments.brightness != 0 or adjustments.contrast != 0:
        result = _adjust_brightness_contrast(result, adjustments.brightness, adjustments.contrast)

    return result


def _equalize_histogram(frame_bgr: np.ndarray) -> np.ndarray:
    """Ecualiza el histograma trabajando en el canal de luminancia (YCrCb)."""
    ycrcb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2YCrCb)
    channels = list(cv2.split(ycrcb))
    channels[0] = cv2.equalizeHist(channels[0])
    ycrcb = cv2.merge(channels)
    return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)


def _adjust_brightness_contrast(frame_bgr: np.ndarray, brightness: int, contrast: int) -> np.ndarray:
    """Ajusta brillo y contraste. Ambos parámetros esperados en el rango -100..100."""
    brightness = max(-100, min(100, brightness))
    contrast = max(-100, min(100, contrast))

    # Factor de contraste: mapea -100..100 a un multiplicador ~0.0..3.0
    contrast_factor = (259 * (contrast + 255)) / (255 * (259 - contrast))
    adjusted = contrast_factor * (frame_bgr.astype(np.float32) - 128) + 128 + brightness
    return np.clip(adjusted, 0, 255).astype(np.uint8)
