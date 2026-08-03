"""Modelos de datos inmutables usados en toda la aplicación."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class VideoInfo:
    """Información estática de un video cargado."""

    path: Path
    fps: float
    frame_count: int
    width: int
    height: int

    @property
    def duration_seconds(self) -> float:
        """Duración total del video en segundos."""
        if self.fps <= 0:
            return 0.0
        return self.frame_count / self.fps

    @property
    def resolution_text(self) -> str:
        """Resolución formateada como 'ancho x alto'."""
        return f"{self.width}x{self.height}"


@dataclass(frozen=True)
class ImageAdjustments:
    """Ajustes de visualización aplicados únicamente al preview, no al guardado."""

    grayscale: bool = False
    equalize_histogram: bool = False
    brightness: int = 0  # rango sugerido -100..100
    contrast: int = 0  # rango sugerido -100..100

    def is_identity(self) -> bool:
        """Indica si no hay ningún ajuste activo."""
        return (
            not self.grayscale
            and not self.equalize_histogram
            and self.brightness == 0
            and self.contrast == 0
        )


@dataclass(frozen=True)
class SessionMetadata:
    """Metadata de organización elegida al abrir un video."""

    persona: str
    ejercicio: str
    angulo: str

    def base_name(self) -> str:
        """Construye el prefijo de nombre de archivo a partir de la metadata."""
        def normalize(text: str) -> str:
            return text.strip().replace(" ", "_")

        return f"{normalize(self.persona)}_{normalize(self.ejercicio)}_{normalize(self.angulo)}"


@dataclass(frozen=True)
class FrameRecord:
    """Registro de un frame guardado, usado para la vista de miniaturas y el export JSON."""

    file_path: Path
    source_video: Path
    frame_index: int
    time_seconds: float
    persona: str
    ejercicio: str
    angulo: str

    def to_json_dict(self) -> dict:
        """Serializa el registro a un diccionario compatible con JSON."""
        return {
            "archivo": str(self.file_path),
            "video_origen": str(self.source_video),
            "frame": self.frame_index,
            "tiempo_segundos": round(self.time_seconds, 3),
            "persona": self.persona,
            "ejercicio": self.ejercicio,
            "angulo": self.angulo,
        }


@dataclass
class Bookmark:
    """Marcador sobre un frame interesante de un video."""

    frame_index: int
    label: str = ""


@dataclass
class VideoSegment:
    """Rango de frames dentro de un video largo que corresponde a un solo ejercicio.

    Se usa para videos de ~4 minutos que contienen varios ejercicios seguidos
    de una misma persona: cada segmento delimita dónde empieza y termina un
    ejercicio y qué metadata (ejercicio/ángulo) debe usarse al guardar frames
    dentro de ese rango.
    """

    start_frame: int
    end_frame: int
    metadata: SessionMetadata

    def contains(self, frame_index: int) -> bool:
        """Indica si ``frame_index`` cae dentro de este segmento."""
        return self.start_frame <= frame_index <= self.end_frame

    def label(self) -> str:
        """Texto descriptivo del segmento para mostrar en listas."""
        return f"{self.metadata.ejercicio} · {self.metadata.angulo}  [{self.start_frame}-{self.end_frame}]"


@dataclass
class VideoSessionState:
    """Estado mutable de sesión asociado a un video (bookmarks, contador, etc.)."""

    video_path: Path
    saved_count: int = 0
    bookmarks: list[Bookmark] = field(default_factory=list)
    segments: list[VideoSegment] = field(default_factory=list)
