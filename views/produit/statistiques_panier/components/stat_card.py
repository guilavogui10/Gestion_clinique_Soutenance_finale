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
        """Configure l'interface de la card - Style consultation avec icône encerclée."""
        self.setFixedHeight(82)
        self.setStyleSheet(StatistiquesStyles.card_stat())
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        
        # Cercle icône (style consultation)
        self.icon_circle = QFrame()
        self.icon_circle.setObjectName("KpiIconCircle")
        self.icon_circle.setFixedSize(42, 42)
        icon_layout = QHBoxLayout(self.icon_circle)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignCenter)
        
        self._icon_lbl = QLabel()
        self._icon_lbl.setAlignment(Qt.AlignCenter)
        self._icon_lbl.setFixedSize(22, 22)
        self._icon_lbl.setPixmap(qta.icon(icone, color="white").pixmap(QSize(22, 22)))
        icon_layout.addWidget(self._icon_lbl)
        
        # Style du cercle
        self.icon_circle.setStyleSheet(
            f"background: {self.couleur}; border: none; border-radius: 21px;"
        )
        
        # Layout texte
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        # Titre
        self._title_lbl = QLabel(titre)
        self._title_lbl.setObjectName("KpiTitle")
        self._title_lbl.setStyleSheet(
            "color: #6c757d; font-size: 11px; font-weight: 500; "
            "background: transparent; border: none;"
        )
        
        # Valeur
        self.value_label = QLabel(valeur)
        self.value_label.setObjectName("KpiValue")
        from PySide6.QtGui import QFont
        font_value = QFont()
        font_value.setPointSize(15)
        font_value.setBold(True)
        self.value_label.setFont(font_value)
        self.value_label.setStyleSheet(
            "color: #2c3e50; background: transparent; border: none;"
        )
        
        # Sous-titre (optionnel)
        self.subtitle_label = QLabel("")
        self.subtitle_label.setObjectName("KpiSubtitle")
        self.subtitle_label.setStyleSheet(
            "color: #6c757d; font-size: 10px; background: transparent; border: none;"
        )
        
        text_layout.addWidget(self._title_lbl)
        text_layout.addWidget(self.value_label)
        text_layout.addWidget(self.subtitle_label)
        
        layout.addWidget(self.icon_circle)
        layout.addLayout(text_layout, 1)

    # =========================================================================
    # API PUBLIQUE
    # =========================================================================
    
    def update_value(self, nouvelle_valeur: str, subtitle: str = ""):
        """
        Met à jour la valeur affichée et le sous-titre.
        
        Args:
            nouvelle_valeur: Nouvelle valeur à afficher
            subtitle: Sous-titre optionnel
        
        Usage:
            >>> card.update_value("10", "produits")
        """
        self.value_label.setText(str(nouvelle_valeur))
        if subtitle:
            self.subtitle_label.setText(subtitle)

    def update_theme_color(self, nouvelle_couleur: str):
        """Met à jour la couleur d'accent et re-stylise le cercle icône."""
        self.couleur = nouvelle_couleur
        self.icon_circle.setStyleSheet(
            f"background: {self.couleur}; border: none; border-radius: 21px;"
        )
        self._icon_lbl.setPixmap(
            qta.icon(self._icone_name, color="white").pixmap(QSize(22, 22))
        )
    
    def get_value(self) -> str:
        """
        Récupère la valeur actuelle.
        
        Returns:
            str: Valeur actuelle
        """
        return self.value_label.text()
