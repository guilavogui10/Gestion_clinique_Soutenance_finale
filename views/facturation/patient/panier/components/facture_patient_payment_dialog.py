"""
Dialogue de paiement pour facture patient.
Modes : Especes, Mobile Money, Carte bancaire.
"""

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QComboBox, QLineEdit
)

from ..styles.facture_patient_styles import FacturePatientStyles


class FacturePatientPaymentDialog(QDialog):
    """Dialogue moderne pour saisir le paiement patient."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.mode_paiement = None
        self.telephone = ""
        self._init_ui()

    def _init_ui(self) -> None:
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
        frame_layout.setContentsMargins(22, 22, 22, 22)
        frame_layout.setSpacing(12)

        icon = QLabel()
        icon.setPixmap(
            qta.icon("fa5s.credit-card",
                     color=FacturePatientStyles.BLEU_PRINCIPAL).pixmap(46, 46)
        )
        icon.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(icon)

        title = QLabel("Paiement de la facture")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"font-size:16px; font-weight:bold; color:{FacturePatientStyles.BLEU_PRINCIPAL};"
        )
        frame_layout.addWidget(title)

        # Mode paiement
        lbl_mode = QLabel("Mode de paiement")
        lbl_mode.setStyleSheet("font-size:12px; font-weight:bold; color:#475569;")
        frame_layout.addWidget(lbl_mode)

        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Especes", "Mobile Money", "Carte bancaire"])
        self.combo_mode.setFixedHeight(36)
        self.combo_mode.setStyleSheet(
            "border:1px solid #e2e8f0; border-radius:8px; padding-left:10px;"
        )
        self.combo_mode.currentIndexChanged.connect(self._toggle_phone)
        frame_layout.addWidget(self.combo_mode)

        # Telephone
        lbl_tel = QLabel("Telephone (Mobile Money uniquement)")
        lbl_tel.setStyleSheet("font-size:12px; font-weight:bold; color:#475569;")
        frame_layout.addWidget(lbl_tel)

        self.input_tel = QLineEdit()
        self.input_tel.setPlaceholderText("Ex: 628123456")
        self.input_tel.setFixedHeight(36)
        self.input_tel.setStyleSheet(
            "border:1px solid #e2e8f0; border-radius:8px; padding-left:10px;"
        )
        frame_layout.addWidget(self.input_tel)

        # Buttons
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
        btn_ok.clicked.connect(self._validate)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        frame_layout.addLayout(btn_row)

        layout.addWidget(frame)
        self._toggle_phone()

    def _toggle_phone(self) -> None:
        is_mobile = self.combo_mode.currentText() == "Mobile Money"
        self.input_tel.setEnabled(is_mobile)
        if not is_mobile:
            self.input_tel.clear()

    def _validate(self) -> None:
        self.mode_paiement = self.combo_mode.currentText()
        self.telephone = self.input_tel.text().strip()
        if self.mode_paiement == "Mobile Money" and not self.telephone:
            from .modern_message_box import ModernMessageBox
            ModernMessageBox.warning(
                self, "Attention", "Telephone requis pour Mobile Money",
                FacturePatientStyles.BLEU_PRINCIPAL
            )
            return
        self.accept()

    def get_data(self):
        return {
            "mode_paiement": self.mode_paiement,
            "telephone": self.telephone,
        }

