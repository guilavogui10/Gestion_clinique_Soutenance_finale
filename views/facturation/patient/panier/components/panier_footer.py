"""
Composant PanierFooter - Footer avec total et boutons d'action.
Responsabilité : Affichage du total et gestion des boutons finaliser/annuler.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton,
    QFrame, QLabel
)
from ..styles.panier_styles import PanierStyles
from views.shared.theme_manager import theme_manager


class PanierFooter:
    """
    Gère le footer du panier avec total et boutons d'action.
    Pattern : Facade pour simplifier la création du footer.
    """
    
    def __init__(self, vert_principal: str):
        self.vert_principal = vert_principal
        
        # Widgets du footer
        self.lbl_total_facture = None
        self.btn_finaliser = None
        self.btn_annuler_facture = None
        self._sep = None
        self._footer_frame = None
        self._icon_total = None
        self._lbl_total_titre = None
    
    def create(self, parent_layout):
        """
        Crée le footer complet avec total et boutons.
        
        Args:
            parent_layout: Layout parent où ajouter le footer
        
        Returns:
            tuple: (lbl_total_facture, btn_finaliser, btn_annuler_facture)
        """
        c = theme_manager.colors()
        
        # Séparateur avant le footer
        self._sep = QFrame()
        self._sep.setFixedHeight(1)
        self._sep.setStyleSheet(f"background: {c['border_light']}; border: none;")
        parent_layout.addWidget(self._sep)
        
        # Frame du footer
        self._footer_frame = QFrame()
        self._footer_frame.setStyleSheet(f"background: {c['bg_card']}; border: none;")
        footer_layout = QVBoxLayout(self._footer_frame)
        footer_layout.setContentsMargins(14, 10, 14, 12)
        footer_layout.setSpacing(10)

        # Section Total
        self._create_total_section(footer_layout)
        
        # Section Boutons
        self._create_buttons_section(footer_layout)

        parent_layout.addWidget(self._footer_frame)
        
        return self.lbl_total_facture, self.btn_finaliser, self.btn_annuler_facture
    
    def _create_total_section(self, layout):
        """Crée la section affichage du total."""
        c = theme_manager.colors()
        total_row = QHBoxLayout()
        
        # Icône
        self._icon_total = QLabel()
        self._icon_total.setPixmap(
            qta.icon("fa5s.receipt", color=self.vert_principal).pixmap(QSize(14, 14))
        )
        self._icon_total.setStyleSheet("border: none; background: transparent;")
        
        # Label titre
        self._lbl_total_titre = QLabel("Total Facture")
        self._lbl_total_titre.setStyleSheet(
            f"font-weight: bold; color: {c['text_primary']}; font-size: 12px; "
            "border: none; background: transparent;"
        )
        
        # Label montant
        self.lbl_total_facture = QLabel("0 GNF")
        self.lbl_total_facture.setStyleSheet(
            f"font-weight: bold; color: {self.vert_principal};"
            "font-size: 16px; border: none; background: transparent;"
        )
        
        total_row.addWidget(self._icon_total)
        total_row.addSpacing(6)
        total_row.addWidget(self._lbl_total_titre)
        total_row.addStretch()
        total_row.addWidget(self.lbl_total_facture)
        layout.addLayout(total_row)
    
    def _create_buttons_section(self, layout):
        """Crée la section des boutons d'action."""
        btns_row = QHBoxLayout()
        btns_row.setSpacing(8)

        # Bouton Finaliser
        self.btn_finaliser = QPushButton(
            qta.icon("fa5s.check-circle", color=theme_manager.colors()['text_inverse']), " Valider la Facture"
        )
        self.btn_finaliser.setFixedHeight(40)
        self.btn_finaliser.setCursor(Qt.PointingHandCursor)
        self.btn_finaliser.setStyleSheet(PanierStyles.btn_finaliser())

        # Bouton Annuler
        self.btn_annuler_facture = QPushButton(
            qta.icon("fa5s.trash-alt", color=theme_manager.colors()['text_inverse']), " Annuler"
        )
        self.btn_annuler_facture.setFixedHeight(40)
        self.btn_annuler_facture.setFixedWidth(100)
        self.btn_annuler_facture.setCursor(Qt.PointingHandCursor)
        self.btn_annuler_facture.setStyleSheet(PanierStyles.btn_annuler())

        btns_row.addWidget(self.btn_finaliser)
        btns_row.addWidget(self.btn_annuler_facture)
        layout.addLayout(btns_row)
    
    def update_total(self, montant: float):
        """
        Met à jour l'affichage du total.
        
        Args:
            montant: Montant total à afficher
        """
        self.lbl_total_facture.setText(f"{montant:,.0f} GNF".replace(",", " "))

    def apply_theme(self, c: dict):
        """Met à jour les couleurs selon le thème actif."""
        self.vert_principal = c['primary']
        if self._sep:
            self._sep.setStyleSheet(f"background: {c['border_light']}; border: none;")
        if self._footer_frame:
            self._footer_frame.setStyleSheet(f"background: {c['bg_card']}; border: none;")
        if self._icon_total:
            self._icon_total.setPixmap(
                qta.icon("fa5s.receipt", color=c['primary']).pixmap(QSize(14, 14))
            )
        if self._lbl_total_titre:
            self._lbl_total_titre.setStyleSheet(
                f"font-weight: bold; color: {c['text_primary']}; font-size: 12px; "
                "border: none; background: transparent;"
            )
        if self.lbl_total_facture:
            self.lbl_total_facture.setStyleSheet(
                f"font-weight: bold; color: {c['primary']};"
                "font-size: 16px; border: none; background: transparent;"
            )
        if self.btn_finaliser:
            self.btn_finaliser.setStyleSheet(PanierStyles.btn_finaliser())
            self.btn_finaliser.setIcon(qta.icon("fa5s.check-circle", color=c['text_inverse']))
        if self.btn_annuler_facture:
            self.btn_annuler_facture.setStyleSheet(PanierStyles.btn_annuler())
            self.btn_annuler_facture.setIcon(qta.icon("fa5s.trash-alt", color=c['text_inverse']))
