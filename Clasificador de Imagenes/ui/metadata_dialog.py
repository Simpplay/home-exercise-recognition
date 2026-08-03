"""Diálogo para capturar la metadata de organización (persona/ejercicio/ángulo)."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from models.data_models import SessionMetadata
from utils.constants import ANGULOS_DISPONIBLES, EJERCICIOS_DISPONIBLES


class MetadataDialog(QDialog):
    """Solicita al usuario Persona, Ejercicio y Ángulo antes de trabajar un video."""

    def __init__(
        self,
        parent: QWidget | None = None,
        initial_persona: str = "",
        initial_ejercicio: str = "",
        initial_angulo: str = "",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Información del video")
        self.setMinimumWidth(360)
        self.setModal(True)

        self._persona_edit = QLineEdit(initial_persona)
        self._persona_edit.setPlaceholderText("Ej: Persona03")

        self._ejercicio_combo = QComboBox()
        self._ejercicio_combo.addItems(EJERCICIOS_DISPONIBLES)
        if initial_ejercicio:
            index = self._ejercicio_combo.findText(initial_ejercicio)
            if index >= 0:
                self._ejercicio_combo.setCurrentIndex(index)

        self._angulo_combo = QComboBox()
        self._angulo_combo.setEditable(True)
        self._angulo_combo.addItems(ANGULOS_DISPONIBLES)
        if initial_angulo:
            index = self._angulo_combo.findText(initial_angulo)
            if index >= 0:
                self._angulo_combo.setCurrentIndex(index)
            else:
                self._angulo_combo.setCurrentText(initial_angulo)

        form_layout = QFormLayout()
        form_layout.addRow("Persona:", self._persona_edit)
        form_layout.addRow("Ejercicio:", self._ejercicio_combo)
        form_layout.addRow("Ángulo:", self._angulo_combo)

        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._button_box.accepted.connect(self._handle_accept)
        self._button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)
        layout.addWidget(self._button_box)

        self._result_metadata: SessionMetadata | None = None
        self._persona_edit.setFocus()

    def _handle_accept(self) -> None:
        """Valida los campos y cierra el diálogo si son válidos."""
        persona = self._persona_edit.text().strip()
        ejercicio = self._ejercicio_combo.currentText().strip()
        angulo = self._angulo_combo.currentText().strip()

        if not persona or not ejercicio or not angulo:
            self._persona_edit.setFocus()
            return

        self._result_metadata = SessionMetadata(persona=persona, ejercicio=ejercicio, angulo=angulo)
        self.accept()

    def metadata(self) -> SessionMetadata | None:
        """Devuelve la metadata capturada, o ``None`` si el diálogo fue cancelado."""
        return self._result_metadata
