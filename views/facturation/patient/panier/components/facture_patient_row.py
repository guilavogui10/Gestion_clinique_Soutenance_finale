"""
Composant ligne facture patient.
Responsabilite : afficher une ligne service avec actions Modifier/Retirer.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from ..styles.facture_patient_styles import FacturePatientStyles
from views.shared.modal_theme import MC


class FacturePatientRowItem:
    """Cree une ligne visuelle pour un service facture patient."""

    def __init__(self, bleu_principal: str, rouge: str):
        self.bleu_principal = bleu_principal
        self.rouge = rouge

    def create(
        self,
        index: int,
        designation: str,
        description: str,
        quantite: int,
        prix: float,
        code_paniere: str,
        on_delete_callback,
        on_edit_callback,
    ) -> QFrame:
        ligne = QFrame()
        ligne.setFixedHeight(58)
        ligne.setStyleSheet(FacturePatientStyles.row_item())

        # Stocker les donnees pour MAJ et suppression
        ligne.code_paniere = code_paniere
        ligne.designation = designation
        ligne.description = description
        ligne.quantite = quantite
        ligne.prix = prix

        layout = QHBoxLayout(ligne)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(12)

        # Colonne index
        lbl_index = QLabel(f"{index}.")
        lbl_index.setFixedWidth(26)
        lbl_index.setAlignment(Qt.AlignCenter)
        lbl_index.setStyleSheet(f"color:{MC.TEXT_SECONDARY}; font-size:11px; font-weight:bold;")

        # Colonne service
        lbl_service = QLabel(designation)
        lbl_service.setFixedWidth(140)
        lbl_service.setStyleSheet(
            f"color:{MC.TEXT_PRIMARY}; font-size:12px; font-weight:bold;"
        )

        # Colonne description (peut afficher aussi une date)
        desc_col = QVBoxLayout()
        desc_col.setSpacing(2)
        lbl_desc = QLabel(description or "—")
        lbl_desc.setStyleSheet(f"color:{MC.TEXT_SECONDARY}; font-size:11px;")
        lbl_desc.setWordWrap(True)
        desc_col.addWidget(lbl_desc)

        desc_wrap = QFrame()
        desc_wrap.setStyleSheet("background: transparent; border: none;")
        desc_wrap.setFixedWidth(220)
        desc_wrap.setLayout(desc_col)

        # Colonne quantite
        lbl_qte = QLabel(str(quantite))
        lbl_qte.setFixedWidth(70)
        lbl_qte.setAlignment(Qt.AlignCenter)
        lbl_qte.setStyleSheet(f"color:{MC.TEXT_PRIMARY}; font-size:11px;")

        # Colonne prix unitaire
        lbl_prix = QLabel(f"{prix:,.0f} GNF".replace(",", " "))
        lbl_prix.setFixedWidth(110)
        lbl_prix.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_prix.setStyleSheet(f"color:{MC.TEXT_SECONDARY}; font-size:11px;")

        # Colonne total
        total = quantite * prix
        lbl_total = QLabel(f"{total:,.0f} GNF".replace(",", " "))
        lbl_total.setFixedWidth(110)
        lbl_total.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_total.setStyleSheet(
            f"color:{self.bleu_principal}; font-size:12px; font-weight:bold;"
        )

        # Actions
        actions = QHBoxLayout()
        actions.setSpacing(6)

        btn_remove = QPushButton(qta.icon("fa5s.trash", color="white"), "Retirer")
        btn_remove.setFixedHeight(30)
        btn_remove.setCursor(Qt.PointingHandCursor)
        btn_remove.setStyleSheet(f"""
            QPushButton {{
                background: {self.rouge};
                color: white;
                border-radius: 8px;
                font-size: 10px;
                font-weight: bold;
                padding: 4px 10px;
            }}
            QPushButton:hover {{ background: #c0392b; }}
        """)
        btn_remove.clicked.connect(lambda: on_delete_callback(ligne))

        btn_edit = QPushButton(qta.icon("fa5s.edit", color=MC.TEXT_PRIMARY), "Modifier")
        btn_edit.setFixedHeight(30)
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.setStyleSheet(f"""
            QPushButton {{
                background: {MC.BORDER};
                color: {MC.TEXT_PRIMARY};
                border-radius: 8px;
                font-size: 10px;
                font-weight: bold;
                padding: 4px 10px;
            }}
            QPushButton:hover {{ background: {MC.BORDER_LIGHT}; }}
        """)
        btn_edit.clicked.connect(lambda: on_edit_callback(ligne))

        actions.addWidget(btn_remove)
        actions.addWidget(btn_edit)

        actions_wrap = QFrame()
        actions_wrap.setStyleSheet("background: transparent; border: none;")
        actions_wrap.setFixedWidth(170)
        actions_wrap.setLayout(actions)

        # Stocker references pour MAJ
        ligne.lbl_index = lbl_index
        ligne.lbl_service = lbl_service
        ligne.lbl_desc = lbl_desc
        ligne.lbl_qte = lbl_qte
        ligne.lbl_prix = lbl_prix
        ligne.lbl_total = lbl_total

        layout.addWidget(lbl_index)
        layout.addWidget(lbl_service)
        layout.addWidget(desc_wrap, 1)
        layout.addWidget(lbl_qte)
        layout.addWidget(lbl_prix)
        layout.addWidget(lbl_total)
        layout.addWidget(actions_wrap)

        return ligne
