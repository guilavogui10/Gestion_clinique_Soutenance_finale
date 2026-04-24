"""
Composant StockDetailCard - Card scrollable avec liste de stock dÃ©taillÃ©.
ResponsabilitÃ© : Afficher une liste scrollable de produits en stock.
Pattern : Component, Container, Composite.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget, QScrollArea

from .animated_frame import AnimatedFrame
from .ligne_stock_card import LigneStockCard
from ..styles.statistiques_styles import StatistiquesStyles
from views.shared.theme_manager import theme_manager


class StockDetailCard(AnimatedFrame):
    """
    Card avec liste scrollable montrant le stock par type et libellÃ© produit.
    
    Structure :
    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚ ðŸ“¦ Stock Disponible par LibellÃ©    â”‚
    â”‚ â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”‚
    â”‚ â”‚ [LIQ] ParacÃ©tamol 500mg    100  â”‚ â”‚
    â”‚ â”‚ [POM] IbuprofÃ¨ne gel        50  â”‚ â”‚
    â”‚ â”‚ [COM] Aspirine 100mg        75  â”‚ â”‚
    â”‚ â”‚ ...                             â”‚ â”‚
    â”‚ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â”‚
    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
    
    Usage:
        >>> card = StockDetailCard("#003f20")
        >>> card.charger_produits(liste_produits)
    """
    
    def __init__(self, couleur_principale: str, parent=None, show_header: bool = True):
        """
        Initialise la card de stock dÃ©taillÃ©.
        
        Args:
            couleur_principale: Couleur principale pour le titre
            parent: Widget parent Qt
        """
        super().__init__(parent)
        
        self.couleur_principale = couleur_principale
        self.show_header = show_header
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface de la card."""
        self.setMinimumHeight(140)
        self.setStyleSheet(StatistiquesStyles.card_base())
        
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 8, 12, 8)
        outer.setSpacing(4)
        
        # Header
        if self.show_header:
            header = self._create_header()
            outer.addLayout(header)
        
        # Zone scrollable
        scroll = self._create_scroll_area()
        outer.addWidget(scroll)
    
    def _create_header(self) -> QHBoxLayout:
        """
        CrÃ©e le header de la card.
        
        Returns:
            QHBoxLayout: Layout du header
        """
        header = QHBoxLayout()
        
        # IcÃ´ne
        icon_lbl = QLabel()
        icon_lbl.setPixmap(
            qta.icon("fa5s.layer-group", color=self.couleur_principale).pixmap(QSize(16, 16))
        )
        icon_lbl.setStyleSheet(StatistiquesStyles.icone_base())
        
        # Titre
        title_lbl = QLabel("Stock Disponible par LibellÃ©")
        title_lbl.setStyleSheet(
            f"font-weight: bold; color: {self.couleur_principale}; "
            f"font-size: 11px; border: none; background: transparent;"
        )
        
        header.addWidget(icon_lbl)
        header.addSpacing(6)
        header.addWidget(title_lbl)
        header.addStretch()
        
        return header
    
    def _create_scroll_area(self) -> QScrollArea:
        """
        CrÃ©e la zone scrollable.
        
        Returns:
            QScrollArea: Zone scrollable
        """
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(StatistiquesStyles.scroll_area())
        self.scroll_area.verticalScrollBar().setStyleSheet(StatistiquesStyles.scrollbar())
        
        # Conteneur pour les lignes
        self.container_lignes = QWidget()
        self.container_lignes.setStyleSheet(StatistiquesStyles.transparent())
        self.layout_lignes = QVBoxLayout(self.container_lignes)
        self.layout_lignes.setContentsMargins(0, 0, 0, 0)
        self.layout_lignes.setSpacing(4)
        self.layout_lignes.addStretch()
        
        self.scroll_area.setWidget(self.container_lignes)
        
        return self.scroll_area
    
    # =========================================================================
    # API PUBLIQUE
    # =========================================================================
    
    def charger_produits(self, produits: list):
        """
        Charge la liste des produits dans la card.
        
        Args:
            produits: Liste de dictionnaires avec 'designation', 'type', 'quantite'
        
        Usage:
            >>> produits = [
            ...     {'designation': 'ParacÃ©tamol', 'type': 'Liquide', 'quantite': 100},
            ...     {'designation': 'IbuprofÃ¨ne', 'type': 'Pommade', 'quantite': 50}
            ... ]
            >>> card.charger_produits(produits)
        """
        # Vider les anciennes lignes
        self.vider()
        
        if not produits:
            self._afficher_message_vide()
            return
        
        # Ajouter les nouvelles lignes
        for produit in produits:
            couleur = StatistiquesStyles.obtenir_couleur_type(produit['type'])
            
            ligne = LigneStockCard(
                libelle=produit['designation'],
                type_produit=produit['type'],
                quantite=produit['quantite'],
                couleur=couleur
            )
            
            # InsÃ©rer avant le stretch
            count = self.layout_lignes.count()
            self.layout_lignes.insertWidget(count - 1, ligne)
    
    def vider(self):
        """
        Vide toutes les lignes de la liste.
        
        Usage:
            >>> card.vider()
        """
        # Parcourir en sens inverse pour Ã©viter les problÃ¨mes d'index
        for i in reversed(range(self.layout_lignes.count())):
            item = self.layout_lignes.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                # Ne pas supprimer le stretch
                if not isinstance(widget, QWidget) or widget.objectName() != "stretch":
                    widget.deleteLater()
    
    def _afficher_message_vide(self):
        """Affiche un message quand il n'y a pas de donnÃ©es."""
        label_vide = QLabel("Aucun produit en stock")
        label_vide.setStyleSheet(StatistiquesStyles.label_vide())
        label_vide.setAlignment(Qt.AlignCenter)
        self.layout_lignes.insertWidget(0, label_vide)
    
    def get_nombre_produits(self) -> int:
        """
        Retourne le nombre de produits affichÃ©s.
        
        Returns:
            int: Nombre de produits
        """
        # -1 pour exclure le stretch
        return self.layout_lignes.count() - 1

    def update_theme_color(self, nouvelle_couleur: str):
        """Met à jour la couleur du header lors d'un changement de thème."""
        self.couleur_principale = nouvelle_couleur
        self._icon_lbl.setPixmap(
            qta.icon("fa5s.layer-group", color=nouvelle_couleur).pixmap(QSize(16, 16))
        )
        self._title_lbl.setStyleSheet(
            f"font-weight: bold; color: {nouvelle_couleur}; "
            f"font-size: 11px; border: none; background: transparent;"
        )

