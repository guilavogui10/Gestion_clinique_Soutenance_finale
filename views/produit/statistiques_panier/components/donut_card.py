"""
Composant DonutCard - Card avec graphe donut (cercle de progression).
Responsabilité : Afficher une statistique avec graphe circulaire de pourcentage.
Pattern : Component, Composition.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel

from .animated_frame import AnimatedFrame
from .circular_progress import CircularProgress
from ..styles.statistiques_styles import StatistiquesStyles
from views.shared.theme_manager import theme_manager


class DonutCard(AnimatedFrame):
    """
    Card avec un mini-graphe donut (cercle de progression).
    
    Structure :
    ┌─────────────────────────────┐
    │ 💧 Stock Liquide            │
    │ 100 unités          ⭕ 50%  │  ← Cercle de progression
    └─────────────────────────────┘
    
    Usage:
        >>> card = DonutCard("Stock Liquide", "0 unités", 0, "#3498db", "fa5s.tint")
        >>> card.update_value("100 unités", 50)
    """
    
    def __init__(self, titre: str, valeur: str, pourcentage: int,
                 couleur: str, icone: str, parent=None):
        """
        Initialise la DonutCard.
        
        Args:
            titre: Titre de la statistique
            valeur: Valeur textuelle (ex: "100 unités")
            pourcentage: Pourcentage pour le graphe (0-100)
            couleur: Couleur hexadécimale
            icone: Nom de l'icône FontAwesome
            parent: Widget parent Qt
        """
        super().__init__(parent)
        
        self.couleur = couleur
        self.pourcentage = pourcentage
        self._icone_name = icone

        self._setup_ui(titre, valeur, icone)
        theme_manager.theme_changed.connect(self.apply_theme)
    
    def _setup_ui(self, titre: str, valeur: str, icone: str):
        """Configure l'interface de la card."""
        self.setFixedHeight(90)
        self.setStyleSheet(StatistiquesStyles.card_donut())
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        
        # Partie gauche : Texte
        text_layout = self._create_text_section(titre, valeur, icone)
        layout.addLayout(text_layout)
        
        layout.addStretch()
        
        # Partie droite : Cercle de progression
        circle_container = self._create_circle_section()
        layout.addWidget(circle_container, alignment=Qt.AlignVCenter)
    
    def _create_text_section(self, titre: str, valeur: str, icone: str) -> QVBoxLayout:
        """
        Crée la section texte (icône + titre + valeur).
        
        Args:
            titre: Titre de la card
            valeur: Valeur à afficher
            icone: Nom de l'icône
        
        Returns:
            QVBoxLayout: Layout de la section texte
        """
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        # Ligne icône + titre
        icon_row = QHBoxLayout()
        
        self._icon_lbl = QLabel()
        self._icon_lbl.setPixmap(qta.icon(icone, color=self.couleur).pixmap(QSize(18, 18)))
        self._icon_lbl.setStyleSheet(StatistiquesStyles.icone_base())
        
        self._title_lbl = QLabel(titre)
        self._title_lbl.setStyleSheet(StatistiquesStyles.label_titre())
        
        icon_row.addWidget(self._icon_lbl)
        icon_row.addSpacing(6)
        icon_row.addWidget(self._title_lbl)
        icon_row.addStretch()
        
        text_layout.addLayout(icon_row)
        
        # Valeur
        self.value_label = QLabel(valeur)
        self.value_label.setStyleSheet(StatistiquesStyles.label_valeur(self.couleur, 18))
        text_layout.addWidget(self.value_label)
        
        text_layout.addStretch()
        
        return text_layout
    
    def _create_circle_section(self) -> CircularProgress:
        """
        Crée la section cercle de progression.
        
        Returns:
            CircularProgress: Widget de progression circulaire
        """
        # Widget de progression circulaire personnalisé
        self.circular_progress = CircularProgress(
            pourcentage=self.pourcentage,
            couleur=self.couleur,
            taille=60
        )
        
        return self.circular_progress
    
    # =========================================================================
    # API PUBLIQUE
    # =========================================================================
    
    def update_value(self, nouvelle_valeur: str, nouveau_pourcentage: int):
        """
        Met à jour la valeur et le pourcentage.
        
        Args:
            nouvelle_valeur: Nouvelle valeur textuelle
            nouveau_pourcentage: Nouveau pourcentage (0-100)
        
        Usage:
            >>> card.update_value("150 unités", 75)
        """
        self.value_label.setText(nouvelle_valeur)
        self.pourcentage = nouveau_pourcentage
        self.circular_progress.set_value(nouveau_pourcentage)

    def update_theme_color(self, nouvelle_couleur: str):
        """Met à jour la couleur d’accent et re-stylise tous les éléments."""
        self.couleur = nouvelle_couleur
        self.setStyleSheet(StatistiquesStyles.card_donut())
        self._icon_lbl.setPixmap(
            qta.icon(self._icone_name, color=self.couleur).pixmap(QSize(18, 18)))
        self._icon_lbl.setStyleSheet(StatistiquesStyles.icone_base())
        self._title_lbl.setStyleSheet(StatistiquesStyles.label_titre())
        self.value_label.setStyleSheet(StatistiquesStyles.label_valeur(self.couleur, 18))
        self.circular_progress.set_color(self.couleur)

    def apply_theme(self):
        """Met à jour les couleurs selon le thème actif (conserve la couleur d’accent)."""
        self.update_theme_color(self.couleur)
    
    def get_value(self) -> str:
        """
        Récupère la valeur actuelle.
        
        Returns:
            str: Valeur actuelle
        """
        return self.value_label.text()
    
    def get_pourcentage(self) -> int:
        """
        Récupère le pourcentage actuel.
        
        Returns:
            int: Pourcentage actuel
        """
        return self.pourcentage
