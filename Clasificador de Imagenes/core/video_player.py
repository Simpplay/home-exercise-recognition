"""Lector de video basado en OpenCV con acceso aleatorio a frames por índice."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from models.data_models import VideoInfo

VIDEO_EXTENSIONS: tuple[str, ...] = (".mp4", ".mov", ".avi", ".mkv", ".m4v", ".wmv")


class VideoLoadError(RuntimeError):
    """Se lanza cuando un archivo de video no puede abrirse o es inválido."""


class VideoPlayer:
    """Encapsula un ``cv2.VideoCapture`` y expone navegación por índice de frame.

    La clase no maneja temporización de reproducción (eso vive en la UI a través
    de un QTimer); solo se encarga de abrir el archivo, exponer su información
    y leer frames concretos de forma eficiente.
    """

    def __init__(self) -> None:
        self._capture: cv2.VideoCapture | None = None
        self._info: VideoInfo | None = None
        self._current_index: int = 0

    @property
    def info(self) -> VideoInfo | None:
        """Información del video actualmente cargado, o ``None`` si no hay video."""
        return self._info

    @property
    def is_open(self) -> bool:
        """Indica si hay un video cargado y listo para leer."""
        return self._capture is not None and self._info is not None

    @property
    def current_index(self) -> int:
        """Índice del último frame leído."""
        return self._current_index

    def open(self, path: Path) -> VideoInfo:
        """Abre un archivo de video y devuelve su información.

        Lanza ``VideoLoadError`` si el archivo no existe o no puede decodificarse.
        """
        self.release()
        capture = cv2.VideoCapture(str(path))
        if not capture.isOpened():
            raise VideoLoadError(f"No se pudo abrir el video: {path}")

        fps = capture.get(cv2.CAP_PROP_FPS) or 0.0
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

        if frame_count <= 0 or width <= 0 or height <= 0:
            capture.release()
            raise VideoLoadError(f"El video parece inválido o corrupto: {path}")

        self._capture = capture
        self._info = VideoInfo(
            path=path, fps=fps, frame_count=frame_count, width=width, height=height
        )
        self._current_index = 0
        return self._info

    def read_frame(self, index: int) -> np.ndarray | None:
        """Lee y devuelve el frame en ``index`` (formato BGR), o ``None`` si falla.

        Si el índice solicitado es el siguiente al último leído, se evita el
        costoso ``set`` de posición y simplemente se lee secuencialmente.
        """
        if self._capture is None or self._info is None:
            return None

        clamped_index = max(0, min(index, self._info.frame_count - 1))

        if clamped_index != self._current_index + 1:
            self._capture.set(cv2.CAP_PROP_POS_FRAMES, clamped_index)

        success, frame = self._capture.read()
        if not success:
            return None

        self._current_index = clamped_index
        return frame

    def time_for_index(self, index: int) -> float:
        """Convierte un índice de frame a tiempo en segundos."""
        if self._info is None or self._info.fps <= 0:
            return 0.0
        return index / self._info.fps

    def release(self) -> None:
        """Libera los recursos del video actual, si existe."""
        if self._capture is not None:
            self._capture.release()
        self._capture = None
        self._info = None
        self._current_index = 0

    @staticmethod
    def is_supported_video(path: Path) -> bool:
        """Indica si la extensión del archivo corresponde a un video soportado."""
        return path.suffix.lower() in VIDEO_EXTENSIONS
