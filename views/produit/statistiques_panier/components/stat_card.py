"""
Composant StatCard - Card statistique simple.
Responsabilité : Afficher une statistique avec icône, titre, barre colorée et valeur.
Pattern : Component, Factory.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame

from .animated_frame import AnimatedFrame
from ..styles.statistiques_styles import StatistiquesStyles


class StatCard(AnimatedFrame):
    """
    Card statistique simple avec icône, titre, barre colorée et valeur.
    
    Structure :
    ┌─────────────────────────┐
    │ 🔴 Produits Expirés     │  ← Icône + Titre
    │ ━━━━━━━━━━━━━━━━━━━━━  │  ← Barre colorée
    │         5               │  ← Valeur (grande)
    └─────────────────────────┘
    
    Usage:
        >>> card = StatCard("Produits Expirés", "0", "fa5s.skull-crossbones", "#e74c3c")
        >>> card.update_value("5")
    """
    
    def __init__(self, titre: str, valeur: str, icone: str, couleur: str, compact: bool = False, parent=None):
        """
        Initialise la card statistique.
        
        Args:
            titre: Titre de la statistique
            valeur: Valeur initiale
            icone: Nom de l'icône FontAwesome
            couleur: Couleur hexadécimale
            compact: Mode compact (hauteur réduite)
            parent: Widget parent Qt
        """
        super().__init__(parent)
        
        self.couleur = couleur
        self._icone_name = icone
        self.compact = compact
        self._setup_ui(titre, valeur, icone)
    
    def _setup_ui(self, titre: str, valeur: str, icone: str):
        """Configure l'interface de la card."""
        # Hauteur adaptée au mode
        hauteur = 65 if self.compact else 80
        self.setFixedHeight(hauteur)
        self.setStyleSheet(StatistiquesStyles.card_stat_compact() if self.compact else StatistiquesStyles.card_stat())
        
        layout = QVBoxLayout(self)
        margins = (10, 6, 10, 6) if self.compact else (12, 8, 12, 8)
        layout.setContentsMargins(*margins)
        layout.setSpacing(2 if self.compact else 3)
        
        # Header : Icône + Titre
        header = self._create_header(titre, icone)
        layout.addLayout(header)
        
        # Barre colorée
        bar = self._create_color_bar()
        layout.addWidget(bar)
        
        # Valeur
        self.value_label = self._create_value_label(valeur)
        layout.addWidget(self.value_label)
    
    def _create_header(self, titre: str, icone: str) -> QHBoxLayout:
        """
        Crée le header avec icône et titre.
        
        Args:
            titre: Titre de la card
            icone: Nom de l'icône
        
        Returns:
            QHBoxLayout: Layout du header
        """
        header = QHBoxLayout()
        
        # Icône (taille augmentée)
        icon_size = 24 if self.compact else 20
        self._icon_lbl = QLabel()
        self._icon_lbl.setPixmap(qta.icon(icone, color=self.couleur).pixmap(QSize(icon_size, icon_size)))
        self._icon_lbl.setStyleSheet(StatistiquesStyles.icone_base())
        
        # Titre
        self._title_lbl = QLabel(titre)
        font_size = 10 if self.compact else 11
        self._title_lbl.setStyleSheet(StatistiquesStyles.label_titre_compact(font_size))
        
        header.addWidget(self._icon_lbl)
        header.addSpacing(6)
        header.addWidget(self._title_lbl)
        header.addStretch()
        
        return header
    
    def _create_color_bar(self) -> QFrame:
        """
        Crée la barre colorée.
        
        Returns:
            QFrame: Barre colorée
        """
        bar = QFrame()
        bar.setFixedHeight(3)
        bar.setStyleSheet(StatistiquesStyles.barre_couleur(self.couleur))
        self._bar = bar
        return bar
    
    def _create_value_label(self, valeur: str) -> QLabel:
        """
        Crée le label de valeur.
        
        Args:
            valeur: Valeur initiale
        
        Returns:
            QLabel: Label de valeur
        """
        value_lbl = QLabel(valeur)
        font_size = 18 if self.compact else 20
        value_lbl.setStyleSheet(StatistiquesStyles.label_valeur(self.couleur, font_size))
        value_lbl.setAlignment(Qt.AlignCenter)
        return value_lbl
    
    # =========================================================================
    # API PUBLIQUE
    # =========================================================================
    
    def update_value(self, nouvelle_valeur: str):
        """
        Met à jour la valeur affichée.
        
        Args:
            nouvelle_valeur: Nouvelle valeur à afficher
        
        Usage:
            >>> card.update_value("10")
        """
        self.value_label.setText(nouvelle_valeur)

    def update_theme_color(self, nouvelle_couleur: str):
        """Met à jour la couleur d'accent et re-stylise tous les éléments."""
        self.couleur = nouvelle_couleur
        self.setStyleSheet(StatistiquesStyles.card_stat_compact() if self.compact else StatistiquesStyles.card_stat())
        icon_size = 24 if self.compact else 20
        self._icon_lbl.setPixmap(
            qta.icon(self._icone_name, color=self.couleur).pixmap(QSize(icon_size, icon_size)))
        self._icon_lbl.setStyleSheet(StatistiquesStyles.icone_base())
        font_size = 10 if self.compact else 11
        self._title_lbl.setStyleSheet(StatistiquesStyles.label_titre_compact(font_size))
        self._bar.setStyleSheet(StatistiquesStyles.barre_couleur(self.couleur))
        font_size_val = 18 if self.compact else 20
        self.value_label.setStyleSheet(StatistiquesStyles.label_valeur(self.couleur, font_size_val))
    
    def get_value(self) -> str:
        """
        Récupère la valeur actuelle.
        
        Returns:
            str: Valeur actuelle
        """
        return self.value_label.text()
