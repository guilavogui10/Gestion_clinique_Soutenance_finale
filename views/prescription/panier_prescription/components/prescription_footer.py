"""
Composant PrescriptionFooter.
Responsabilité : Affichage du total de la prescription et boutons d'action.
Fidèle au pattern PanierFooter — palette médicale bleue.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton,
    QFrame, QLabel
)
from ..styles.prescription_style import PrescriptionStyles
from views.shared.theme_manager import theme_manager


class PrescriptionFooter:
    """
    Gère le footer du widget prescription.
    Pattern : Facade pour simplifier la création du footer.
    """

    def __init__(self, bleu_principal: str):
        self.bleu_principal = bleu_principal

        # Widgets exposés
        self.lbl_total       = None
        self.btn_valider     = None
        self.btn_annuler     = None

    def create(self, parent_layout):
        """
        Crée le footer complet avec total et boutons.

        Args:
            parent_layout: Layout parent du widget principal

        Returns:
            tuple: (lbl_total, btn_valider, btn_annuler)
        """
        # Séparateur
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #f0f0f0; border: none;")
        parent_layout.addWidget(sep)

        # Frame footer
        footer_frame = QFrame()
        footer_frame.setStyleSheet("background: white; border: none;")
        footer_layout = QVBoxLayout(footer_frame)
        footer_layout.setContentsMargins(14, 10, 14, 12)
        footer_layout.setSpacing(10)

        self._create_total_section(footer_layout)
        self._create_buttons_section(footer_layout)

        parent_layout.addWidget(footer_frame)

        return self.lbl_total, self.btn_valider, self.btn_annuler

    # =========================================================================
    # SECTIONS PRIVÉES
    # =========================================================================

    def _create_total_section(self, layout):
        """Crée la ligne d'affichage du total prescription."""
        total_row = QHBoxLayout()

        # Icône
        icon_total = QLabel()
        icon_total.setPixmap(
            qta.icon("fa5s.file-medical-alt", color=self.bleu_principal).pixmap(QSize(14, 14))
        )
        icon_total.setStyleSheet("border: none; background: transparent;")

        # Label titre
        lbl_titre = QLabel("Total Prescription")
        lbl_titre.setStyleSheet(
            "font-weight: bold; color: #333; font-size: 12px;"
            "border: none; background: transparent;"
        )

        # Montant
        self.lbl_total = QLabel("0 GNF")
        self.lbl_total.setStyleSheet(
            f"font-weight: bold; color: {self.bleu_principal};"
            "font-size: 16px; border: none; background: transparent;"
        )

        total_row.addWidget(icon_total)
        total_row.addSpacing(6)
        total_row.addWidget(lbl_titre)
        total_row.addStretch()
        total_row.addWidget(self.lbl_total)
        layout.addLayout(total_row)

    def _create_buttons_section(self, layout):
        """Crée les boutons Valider et Annuler."""
        btns_row = QHBoxLayout()
        btns_row.setSpacing(8)

        # Bouton Valider
        self.btn_valider = QPushButton(
            qta.icon("fa5s.check-circle", color=theme_manager.colors()['success']),
            " Valider la Prescription"
        )
        self.btn_valider.setFixedHeight(40)
        self.btn_valider.setCursor(Qt.PointingHandCursor)
        self.btn_valider.setStyleSheet(PrescriptionStyles.btn_valider())
        self.btn_valider.setToolTip(
            "Valider la prescription — le statut patient passera à 'Attente payement'"
        )

        # Bouton Annuler
        self.btn_annuler = QPushButton(
            qta.icon("fa5s.trash-alt", color=theme_manager.colors()['danger']),
            " Annuler"
        )
        self.btn_annuler.setFixedHeight(40)
        self.btn_annuler.setFixedWidth(110)
        self.btn_annuler.setCursor(Qt.PointingHandCursor)
        self.btn_annuler.setStyleSheet(PrescriptionStyles.btn_annuler())
        self.btn_annuler.setToolTip("Supprimer toutes les lignes de la prescription en cours")

        btns_row.addWidget(self.btn_valider)
        btns_row.addWidget(self.btn_annuler)
        layout.addLayout(btns_row)

    # =========================================================================
    # API PUBLIQUE
    # =========================================================================

    def update_total(self, montant: float) -> None:
        """
        Met à jour l'affichage du total.

        Args:
            montant: Montant total en GNF
        """
        self.lbl_total.setText(f"{montant:,.0f} GNF".replace(",", " "))