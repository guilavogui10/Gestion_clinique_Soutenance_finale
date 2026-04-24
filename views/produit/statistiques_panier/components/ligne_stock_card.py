"""
Composant LigneStockCard - Ligne dans la liste de stock détaillé.
Responsabilité : Afficher une ligne de produit avec icône, libellé et quantité.
Pattern : Component, List Item.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget, QVBoxLayout

from ..styles.statistiques_styles import StatistiquesStyles
from views.shared.theme_manager import theme_manager


class LigneStockCard(QFrame):
    """
    Ligne dans la card 'Stock par libellé'.

    Structure :
    ┌───────────────────────────────────────────────┐
    │ (icône)  Libellé                 x12          │
    │         Type                                   │
    └───────────────────────────────────────────────┘

    Usage:
        >>> ligne = LigneStockCard("Paracétamol 500mg", "Liquide", 100, "#3498db")
    """

    def __init__(self, libelle: str, type_produit: str,
                 quantite: int, couleur: str, parent=None):
        """
        Initialise la ligne de stock.

        Args:
            libelle: Libellé du produit
            type_produit: Type de produit (Liquide, Pommade, Comprimé)
            quantite: Quantité en stock
            couleur: Couleur hexadécimale associée au type
            parent: Widget parent Qt
        """
        super().__init__(parent)

        self.libelle = libelle
        self.type_produit = type_produit
        self.quantite = quantite
        self.couleur = couleur

        self._setup_ui()

    def _setup_ui(self):
        """Configure l'interface de la ligne."""
        self.setFixedHeight(64)
        self.setStyleSheet(StatistiquesStyles.ligne_stock())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(12)

        # Icône produit
        icon = self._create_icon()
        layout.addWidget(icon)

        # Colonne texte (libellé + type)
        text_col = self._create_text_col()
        layout.addWidget(text_col)

        layout.addStretch()

        # Quantité
        qte_lbl = self._create_quantity_label()
        layout.addWidget(qte_lbl)

    def _create_icon(self) -> QLabel:
        """Crée l'icône circulaire du type de produit."""
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(36, 36)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            f"background: {self.couleur}22; border-radius: 16px; border: none;"
        )
        icon_lbl.setPixmap(
            qta.icon(self._icone_par_type(), color=self.couleur).pixmap(QSize(20, 20))
        )
        return icon_lbl

    def _create_text_col(self) -> QWidget:
        """Crée la colonne texte (libellé + type)."""
        c = theme_manager.colors()
        container = QWidget()
        col = QVBoxLayout(container)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(2)

        lbl = QLabel(self.libelle)
        lbl.setStyleSheet(
            f"color: {c['text_primary']}; font-size: 12px; font-weight: 600; "
            "border: none; background: transparent;"
        )

        lbl_type = QLabel(self.type_produit)
        lbl_type.setStyleSheet(
            f"color: {c['text_secondary']}; font-size: 10px; border: none; background: transparent;"
        )

        col.addWidget(lbl)
        col.addWidget(lbl_type)
        return container

    def _create_quantity_label(self) -> QLabel:
        """Crée le label de quantité."""
        qte_lbl = QLabel(f"x{self.quantite}")
        qte_lbl.setStyleSheet(
            f"color: {self.couleur}; font-weight: bold; font-size: 13px; "
            f"border: none; background: transparent;"
        )
        qte_lbl.setFixedWidth(60)
        qte_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return qte_lbl

    def _icone_par_type(self) -> str:
        """Retourne l'icône qawesome selon le type de produit."""
        type_lower = (self.type_produit or "").lower()
        if "liquide" in type_lower:
            return "fa5s.tint"
        if "pommade" in type_lower:
            return "fa5s.prescription-bottle"
        return "fa5s.pills"

    # =========================================================================
    # API PUBLIQUE
    # =========================================================================

    def update_quantite(self, nouvelle_quantite: int):
        """Met à jour la quantité affichée."""
        self.quantite = nouvelle_quantite
        # Pour mise à jour dynamique, recréer la ligne ou garder une ref
