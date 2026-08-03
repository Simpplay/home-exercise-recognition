"""Configuración persistente de la aplicación usando QSettings."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings

_ORG_NAME = "VisionUNAL"
_APP_NAME = "ClasificadorDeImagenes"

_KEY_LAST_VIDEO_FOLDER = "last_video_folder"
_KEY_LAST_DEST_FOLDER = "last_destination_folder"
_KEY_LAST_PERSONA = "last_persona"
_KEY_LAST_EJERCICIO = "last_ejercicio"
_KEY_LAST_ANGULO = "last_angulo"
_KEY_WINDOW_GEOMETRY = "window_geometry"
_KEY_WINDOW_STATE = "window_state"


class AppConfig:
    """Envoltorio tipado sobre ``QSettings`` para las preferencias de la app."""

    def __init__(self) -> None:
        self._settings = QSettings(_ORG_NAME, _APP_NAME)

    @property
    def last_video_folder(self) -> Path | None:
        """Última carpeta desde la que se abrió un video."""
        value = self._settings.value(_KEY_LAST_VIDEO_FOLDER, type=str)
        return Path(value) if value else None

    @last_video_folder.setter
    def last_video_folder(self, folder: Path) -> None:
        self._settings.setValue(_KEY_LAST_VIDEO_FOLDER, str(folder))

    @property
    def last_destination_folder(self) -> Path | None:
        """Última carpeta usada como destino de guardado de frames."""
        value = self._settings.value(_KEY_LAST_DEST_FOLDER, type=str)
        return Path(value) if value else None

    @last_destination_folder.setter
    def last_destination_folder(self, folder: Path) -> None:
        self._settings.setValue(_KEY_LAST_DEST_FOLDER, str(folder))

    @property
    def last_metadata(self) -> tuple[str, str, str]:
        """Últimos valores de (persona, ejercicio, angulo) usados."""
        return (
            self._settings.value(_KEY_LAST_PERSONA, "", type=str),
            self._settings.value(_KEY_LAST_EJERCICIO, "", type=str),
            self._settings.value(_KEY_LAST_ANGULO, "", type=str),
        )

    def set_last_metadata(self, persona: str, ejercicio: str, angulo: str) -> None:
        """Guarda los últimos valores de metadata usados en el diálogo."""
        self._settings.setValue(_KEY_LAST_PERSONA, persona)
        self._settings.setValue(_KEY_LAST_EJERCICIO, ejercicio)
        self._settings.setValue(_KEY_LAST_ANGULO, angulo)

    def save_window_geometry(self, geometry: bytes, state: bytes) -> None:
        """Persiste la geometría y el estado de la ventana principal."""
        self._settings.setValue(_KEY_WINDOW_GEOMETRY, geometry)
        self._settings.setValue(_KEY_WINDOW_STATE, state)

    def load_window_geometry(self) -> tuple[bytes | None, bytes | None]:
        """Recupera la geometría y el estado guardados de la ventana, si existen."""
        geometry = self._settings.value(_KEY_WINDOW_GEOMETRY)
        state = self._settings.value(_KEY_WINDOW_STATE)
        return geometry, state
