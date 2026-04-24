"""
Composant ProductStockCard - Card produit en stock.
Responsabilité : Afficher un produit en stock dans une card rectangulaire verticale.
Pattern : Component, Card Design.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from views.shared.animated_frame import AnimatedFrame
from views.shared.theme_manager import theme_manager


class ProductStockCard(AnimatedFrame):
    """
    Card rectangulaire verticale pour afficher un produit en stock.
    
    Structure :
    ┌─────────────────┐
    │      🔵         │  ← Icône (type produit)
    │   Amoxiline     │  ← Nom produit
    │   Comprimé      │  ← Type
    │   Stock: 100    │  ← Quantité
    │  [+ Ajouter]    │  ← Bouton
    └─────────────────┘
    """
    
    def __init__(self, libelle: str, type_produit: str, quantite: int, parent=None):
        """
        Initialise la card produit.
        
        Args:
            libelle: Nom du produit
            type_produit: Type (Liquide, Pommade, Comprimé)
            quantite: Quantité en stock
            parent: Widget parent Qt
        """
        super().__init__(parent)
        
        self.libelle = libelle
        self.type_produit = type_produit
        self.quantite = quantite
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface de la card."""
        c = theme_manager.colors()
        
        # Taille fixe pour un rectangle vertical
        self.setFixedSize(160, 180)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {c['bg_card']};
                border-radius: 14px;
                border: 1px solid {c['border']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignTop)
        
        # Icône en haut (selon le type)
        icon_container = self._create_icon()
        layout.addWidget(icon_container, alignment=Qt.AlignCenter)
        
        # Nom du produit
        lbl_nom = QLabel(self.libelle)
        lbl_nom.setStyleSheet(f"""
            color: {c['text_primary']};
            font-size: 13px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)
        lbl_nom.setAlignment(Qt.AlignCenter)
        lbl_nom.setWordWrap(True)
        lbl_nom.setMaximumHeight(40)
        layout.addWidget(lbl_nom)
        
        # Type du produit
        lbl_type = QLabel(self.type_produit)
        lbl_type.setStyleSheet(f"""
            color: {c['text_secondary']};
            font-size: 11px;
            background: transparent;
            border: none;
        """)
        lbl_type.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_type)
        
        # Quantité en stock
        lbl_qte = QLabel(f"Stock: {self.quantite}")
        couleur_qte = self._get_couleur_type()
        lbl_qte.setStyleSheet(f"""
            color: {couleur_qte};
            font-size: 14px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)
        lbl_qte.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_qte)
        
        layout.addStretch()
        
        # Bouton Ajouter en bas
        btn_ajouter = QPushButton(qta.icon("fa5s.plus", color=c['text_inverse']), " Ajouter")
        btn_ajouter.setFixedHeight(32)
        btn_ajouter.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['primary']};
                color: {c['text_inverse']};
                border-radius: 8px;
                font-weight: bold;
                font-size: 11px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {c['hover']};
            }}
        """)
        btn_ajouter.setCursor(Qt.PointingHandCursor)
        layout.addWidget(btn_ajouter)
    
    def _create_icon(self) -> QLabel:
        """Crée l'icône circulaire du type de produit."""
        c = theme_manager.colors()
        couleur = self._get_couleur_type()
        icone_name = self._get_icone_type()
        
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(50, 50)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"""
            background: {couleur}22;
            border-radius: 25px;
            border: 2px solid {couleur};
        """)
        
        # Créer un label pour l'icône à l'intérieur
        icon_inner = QLabel(icon_lbl)
        icon_inner.setPixmap(qta.icon(icone_name, color=couleur).pixmap(QSize(28, 28)))
        icon_inner.setAlignment(Qt.AlignCenter)
        icon_inner.setGeometry(11, 11, 28, 28)
        icon_inner.setStyleSheet("background: transparent; border: none;")
        
        return icon_lbl
    
    def _get_icone_type(self) -> str:
        """Retourne l'icône selon le type de produit."""
        type_lower = (self.type_produit or "").lower()
        if "liquide" in type_lower:
            return "fa5s.tint"
        if "pommade" in type_lower:
            return "fa5s.prescription-bottle"
        return "fa5s.pills"
    
    def _get_couleur_type(self) -> str:
        """Retourne la couleur selon le type de produit."""
        c = theme_manager.colors()
        type_lower = (self.type_produit or "").lower()
        if "liquide" in type_lower:
            return c['info']
        if "pommade" in type_lower:
            return c['accent']
        return c['warning']
