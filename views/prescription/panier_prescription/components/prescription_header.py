"""
Composant PrescriptionHeader.
Responsabilité : Affichage du titre et du badge compteur de lignes.
Fidèle au pattern PanierHeader — palette médicale bleue.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QHBoxLayout, QLabel, QFrame


class PrescriptionHeader:
    """Gère l'affichage du header du widget prescription."""

    def __init__(self, bleu_principal: str):
        self.bleu_principal = bleu_principal
        self.badge_panier = None

    def create(self, parent_layout) -> QLabel:
        """
        Crée le header avec icône, titre et badge compteur.

        Args:
            parent_layout: Layout parent (QVBoxLayout du widget principal)

        Returns:
            QLabel: badge_panier — mis à jour depuis le widget principal
        """
        header = QHBoxLayout()
        header.setContentsMargins(14, 10, 14, 10)
        header.setSpacing(6)

        # Icône prescription
        icon_lbl = QLabel()
        icon_lbl.setPixmap(
            qta.icon("fa5s.pills", color=self.bleu_principal).pixmap(QSize(16, 16))
        )
        icon_lbl.setStyleSheet("border: none; background: transparent;")

        # Titre
        title_lbl = QLabel("Prescription — Panier Médicaments")
        title_lbl.setStyleSheet(
            f"font-weight: bold; color: {self.bleu_principal}; "
            "font-size: 12px; border: none; background: transparent;"
        )

        # Badge compteur lignes
        self.badge_panier = QLabel("0")
        self.badge_panier.setFixedSize(22, 22)
        self.badge_panier.setAlignment(Qt.AlignCenter)
        self.badge_panier.setStyleSheet(
            f"background: {self.bleu_principal}; color: white;"
            "border-radius: 11px; font-size: 10px; font-weight: bold; border: none;"
        )

        header.addWidget(icon_lbl)
        header.addSpacing(6)
        header.addWidget(title_lbl)
        header.addStretch()
        header.addWidget(self.badge_panier)

        parent_layout.addLayout(header)

        # Séparateur
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #f0f0f0; border: none;")
        parent_layout.addWidget(sep)

        return self.badge_panier