"""Constantes compartidas: pasos de navegación, extensiones y opciones fijas."""
from __future__ import annotations

STEP_SINGLE = 1
STEP_SMALL = 5
STEP_LARGE = 30

ANGULOS_DISPONIBLES: tuple[str, ...] = ("Frontal", "45 grados", "Lateral")

EJERCICIOS_DISPONIBLES: tuple[str, ...] = (
    "Squat",
    "Push-up",
    "Plank",
    "Jumping Jack",
    "Forward Lunge",
    "Sit-up",
    "High Knees",
    "Chair Dip",
    "Estiramiento lateral",
    "Superman",
)

VIDEO_FILE_FILTER = "Videos (*.mp4 *.mov *.avi *.mkv *.m4v *.wmv)"
IMAGE_THUMBNAIL_SIZE = 120

ZOOM_MIN_FACTOR = 1.0
ZOOM_MAX_FACTOR = 8.0
ZOOM_STEP_FACTOR = 1.15
