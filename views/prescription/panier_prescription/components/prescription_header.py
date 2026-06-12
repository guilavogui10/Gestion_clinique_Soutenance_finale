"""
Composant PrescriptionHeader.
Responsabilité : Affichage du titre et du badge compteur de lignes.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QHBoxLayout, QLabel, QFrame
from views.shared.theme_manager import theme_manager


class PrescriptionHeader:
    """Gère l'affichage du header du widget prescription."""

    def __init__(self):
        self.badge_panier = None

    def create(self, parent_layout) -> QLabel:
        c = theme_manager.colors()
        header = QHBoxLayout()
        header.setContentsMargins(14, 10, 14, 10)
        header.setSpacing(6)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(
            qta.icon("fa5s.pills", color=c['primary']).pixmap(QSize(16, 16))
        )
        icon_lbl.setStyleSheet("border: none; background: transparent;")

        title_lbl = QLabel("Prescription — Panier Médicaments")
        title_lbl.setStyleSheet(
            f"font-weight: bold; color: {c['primary']}; "
            "font-size: 12px; border: none; background: transparent;"
        )

        self.badge_panier = QLabel("0")
        self.badge_panier.setFixedSize(22, 22)
        self.badge_panier.setAlignment(Qt.AlignCenter)
        self.badge_panier.setStyleSheet(
            f"background: {c['primary']}; color: {c['text_inverse']};"
            "border-radius: 11px; font-size: 10px; font-weight: bold; border: none;"
        )

        header.addWidget(icon_lbl)
        header.addSpacing(6)
        header.addWidget(title_lbl)
        header.addStretch()
        header.addWidget(self.badge_panier)
        parent_layout.addLayout(header)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {c['border_light']}; border: none;")
        parent_layout.addWidget(sep)

        return self.badge_panier
