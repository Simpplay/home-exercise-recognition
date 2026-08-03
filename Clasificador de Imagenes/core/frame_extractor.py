"""Lógica de guardado de frames a disco y export de metadata del dataset."""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from models.data_models import FrameRecord, SessionMetadata

METADATA_FILENAME = "dataset_metadata.json"


class FrameExtractor:
    """Guarda frames como PNG con nombres únicos y lleva el registro de metadata.

    El nombre de archivo sigue el patrón:
        ``{persona}_{ejercicio}_{angulo}_{secuencia:04d}.png``

    La numeración de secuencia se calcula inspeccionando los archivos ya
    existentes en la carpeta destino para nunca sobrescribir uno existente,
    incluso entre sesiones distintas de la aplicación.
    """

    def __init__(self) -> None:
        self._records: list[FrameRecord] = []

    @property
    def records(self) -> list[FrameRecord]:
        """Copia de los registros de frames guardados en esta sesión."""
        return list(self._records)

    def save_frame(
        self,
        frame_bgr: np.ndarray,
        destination_dir: Path,
        metadata: SessionMetadata,
        source_video: Path,
        frame_index: int,
        time_seconds: float,
    ) -> FrameRecord:
        """Guarda ``frame_bgr`` como PNG en ``destination_dir`` con nombre único.

        Devuelve el ``FrameRecord`` creado. Lanza ``OSError`` si la escritura falla.
        """
        destination_dir.mkdir(parents=True, exist_ok=True)
        base_name = metadata.base_name()
        file_path = self._next_available_path(destination_dir, base_name)

        success = cv2.imwrite(str(file_path), frame_bgr)
        if not success:
            raise OSError(f"No se pudo guardar el frame en: {file_path}")

        record = FrameRecord(
            file_path=file_path,
            source_video=source_video,
            frame_index=frame_index,
            time_seconds=time_seconds,
            persona=metadata.persona,
            ejercicio=metadata.ejercicio,
            angulo=metadata.angulo,
        )
        self._records.append(record)
        return record

    def remove_record(self, record: FrameRecord, delete_file: bool = True) -> None:
        """Elimina un registro de la sesión y, opcionalmente, su archivo en disco."""
        if record in self._records:
            self._records.remove(record)
        if delete_file and record.file_path.exists():
            record.file_path.unlink()

    def export_json(self, destination_dir: Path) -> Path:
        """Escribe/actualiza un archivo JSON con la metadata de todos los frames guardados.

        Si ya existe un archivo de metadata en la carpeta, se fusionan los
        registros (evitando duplicados por ruta de archivo) en lugar de
        sobrescribirlo por completo.
        """
        destination_dir.mkdir(parents=True, exist_ok=True)
        json_path = destination_dir / METADATA_FILENAME

        existing: list[dict] = []
        if json_path.exists():
            try:
                existing = json.loads(json_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                existing = []

        existing_paths = {entry.get("archivo") for entry in existing}
        merged = existing + [
            record.to_json_dict()
            for record in self._records
            if str(record.file_path) not in existing_paths
        ]

        json_path.write_text(
            json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return json_path

    @staticmethod
    def _next_available_path(destination_dir: Path, base_name: str) -> Path:
        """Encuentra el siguiente nombre de archivo disponible para ``base_name``."""
        sequence = 1
        while True:
            candidate = destination_dir / f"{base_name}_{sequence:04d}.png"
            if not candidate.exists():
                return candidate
            sequence += 1
