"""
Composant Header du panier.
Responsabilité : Affichage du titre et du badge compteur.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QHBoxLayout, QLabel, QFrame
from views.shared.theme_manager import theme_manager


class PanierHeader:
    """Gère l'affichage du header du panier."""
    
    def __init__(self, vert_principal: str):
        self.vert_principal = vert_principal
        self.badge_panier = None
        self._icon_lbl = None
        self._title_lbl = None
        self._sep = None
    
    def create(self, parent_layout) -> QLabel:
        """
        Crée le header avec titre et badge.
        Retourne le widget badge pour mise à jour externe.
        """
        header = QHBoxLayout()
        header.setContentsMargins(14, 10, 14, 10)
        header.setSpacing(6)

        # Icône
        self._icon_lbl = QLabel()
        self._icon_lbl.setPixmap(
            qta.icon("fa5s.shopping-basket", color=self.vert_principal).pixmap(QSize(16, 16))
        )
        self._icon_lbl.setStyleSheet("border: none; background: transparent;")

        # Titre
        self._title_lbl = QLabel("Panier — Alimentation du Stock")
        self._title_lbl.setStyleSheet(
            f"font-weight: bold; color: {self.vert_principal}; "
            "font-size: 12px; border: none; background: transparent;"
        )

        # Badge compteur
        self.badge_panier = QLabel("0")
        self.badge_panier.setFixedSize(22, 22)
        self.badge_panier.setAlignment(Qt.AlignCenter)
        self.badge_panier.setStyleSheet(
            f"background: {self.vert_principal}; color: white;"
            "border-radius: 11px; font-size: 10px; font-weight: bold; border: none;"
        )

        header.addWidget(self._icon_lbl)
        header.addSpacing(6)
        header.addWidget(self._title_lbl)
        header.addStretch()
        header.addWidget(self.badge_panier)
        
        parent_layout.addLayout(header)
        
        # Séparateur
        c = theme_manager.colors()
        self._sep = QFrame()
        self._sep.setFixedHeight(1)
        self._sep.setStyleSheet(f"background: {c['border_light']}; border: none;")
        parent_layout.addWidget(self._sep)
        
        return self.badge_panier

    def apply_theme(self, c: dict):
        """Met à jour les couleurs selon le thème actif."""
        self.vert_principal = c['primary']
        if self._icon_lbl:
            self._icon_lbl.setPixmap(
                qta.icon("fa5s.shopping-basket", color=c['primary']).pixmap(QSize(16, 16))
            )
        if self._title_lbl:
            self._title_lbl.setStyleSheet(
                f"font-weight: bold; color: {c['primary']}; "
                "font-size: 12px; border: none; background: transparent;"
            )
        if self.badge_panier:
            self.badge_panier.setStyleSheet(
                f"background: {c['primary']}; color: {c['text_inverse']};"
                "border-radius: 11px; font-size: 10px; font-weight: bold; border: none;"
            )
        if self._sep:
            self._sep.setStyleSheet(f"background: {c['border_light']}; border: none;")
