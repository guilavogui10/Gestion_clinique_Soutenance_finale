"""
Dialogue d'ajout/modification d'une ligne de facture patient.
"""

from typing import Optional, Dict
import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QSpinBox
)

from ..styles.facture_patient_styles import FacturePatientStyles


class FacturePatientLineDialog(QDialog):
    """Dialogue compact pour ajouter ou modifier un service."""

    def __init__(self, parent=None, titre: str = "Ajouter un service",
                 data: Optional[Dict] = None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self._data = data or {}
        self._init_ui(titre)

    def _init_ui(self, titre: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 2px solid {FacturePatientStyles.BLEU_PRINCIPAL};
                border-radius: 14px;
            }}
        """)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(20, 20, 20, 20)
        frame_layout.setSpacing(10)

        # Header
        header = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(
            qta.icon("fa5s.clipboard-list",
                     color=FacturePatientStyles.BLEU_PRINCIPAL).pixmap(22, 22)
        )
        title = QLabel(titre)
        title.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {FacturePatientStyles.BLEU_PRINCIPAL};"
        )
        header.addWidget(icon)
        header.addWidget(title)
        header.addStretch()
        frame_layout.addLayout(header)

        # Designation
        self.input_designation = QLineEdit()
        self.input_designation.setPlaceholderText("Service (ex: Consultation)")
        self._apply_input_style(self.input_designation)
        frame_layout.addWidget(self._wrap_field("Service", self.input_designation))

        # Description / Reference
        self.input_description = QLineEdit()
        self.input_description.setPlaceholderText("Description ou reference")
        self._apply_input_style(self.input_description)
        frame_layout.addWidget(self._wrap_field("Description", self.input_description))

        # Quantite + Prix
        row = QHBoxLayout()
        self.input_quantite = QSpinBox()
        self.input_quantite.setRange(1, 9999)
        self.input_quantite.setFixedHeight(34)
        self.input_quantite.setStyleSheet(
            "border: 1px solid #e2e8f0; border-radius: 8px; padding-left: 8px;"
        )

        self.input_prix = QLineEdit()
        self.input_prix.setPlaceholderText("0")
        self.input_prix.setFixedHeight(34)
        self.input_prix.setValidator(QDoubleValidator(0.0, 999999999.0, 2))
        self._apply_input_style(self.input_prix)

        row.addLayout(self._wrap_field("Quantite", self.input_quantite))
        row.addLayout(self._wrap_field("Prix unitaire", self.input_prix))
        frame_layout.addLayout(row)

        # Boutons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setFixedSize(110, 34)
        btn_cancel.setStyleSheet(
            "background:#e5e7eb; border-radius:8px; font-weight:bold; font-size:12px;"
        )
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("Valider")
        btn_ok.setFixedSize(110, 34)
        btn_ok.setStyleSheet(
            f"background:{FacturePatientStyles.BLEU_PRINCIPAL}; color:white; "
            "border-radius:8px; font-weight:bold; font-size:12px;"
        )
        btn_ok.clicked.connect(self.accept)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        frame_layout.addLayout(btn_row)

        layout.addWidget(frame)

        # Pre-remplir si data
        if self._data:
            self.input_designation.setText(self._data.get("designation", ""))
            self.input_description.setText(self._data.get("description", ""))
            self.input_quantite.setValue(int(self._data.get("quantite", 1)))
            self.input_prix.setText(str(self._data.get("prix", "")))

    def _wrap_field(self, label: str, widget) -> QVBoxLayout:
        layout = QVBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet("font-size:10px; font-weight:bold; color:#64748b;")
        layout.addWidget(lbl)
        layout.addWidget(widget)
        return layout

    def _apply_input_style(self, widget) -> None:
        widget.setFixedHeight(34)
        widget.setStyleSheet(
            "border: 1px solid #e2e8f0; border-radius: 8px; padding-left: 8px;"
        )

    def get_data(self) -> Dict:
        return {
            "designation": self.input_designation.text().strip(),
            "description": self.input_description.text().strip(),
            "quantite": int(self.input_quantite.value()),
            "prix": float(self.input_prix.text().replace(" ", "") or 0),
        }

