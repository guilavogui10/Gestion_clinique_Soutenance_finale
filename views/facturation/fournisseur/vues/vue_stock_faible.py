"""
Vue VueStockFaible - Affichage des produits en stock faible.
Responsabilité : Afficher la liste des produits dont le stock est sous le seuil.
Pattern : Component, List View.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame

from ..styles.facture_styles import FactureStyles


def _lbl_vide(texte):
    """Crée un label pour message vide."""
    lbl = QLabel(texte)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(FactureStyles.label_vide())
    return lbl


def _row_ic_val(icone_name, valeur, couleur_ic=FactureStyles.GRIS_TEXTE,
                couleur_val=FactureStyles.GRIS_TEXTE, gras=False):
    """Crée une ligne icône + valeur."""
    w = QWidget()
    w.setStyleSheet("background:transparent;")
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(5)
    
    ic = QLabel()
    ic.setPixmap(qta.icon(icone_name, color=couleur_ic).pixmap(QSize(11, 11)))
    ic.setStyleSheet(FactureStyles.icone_base())
    
    lbl = QLabel(str(valeur) if valeur else "—")
    poids = "700" if gras else "400"
    lbl.setStyleSheet(
        f"color:{couleur_val}; font-size:11px; font-weight:{poids};"
        f"background:transparent; border:none;"
    )
    lbl.setWordWrap(True)
    
    lay.addWidget(ic)
    lay.addWidget(lbl)
    lay.addStretch()
    return w


class VueStockFaible(QWidget):
    """
    Vue affichant tous les produits en stock faible.
    
    Usage:
        >>> vue = VueStockFaible()
        >>> vue.charger(produits_stock_faible)
    """
    
    def __init__(self, parent=None):
        """Initialise la vue stock faible."""
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 12, 16, 16)
        self._layout.setSpacing(10)
    
    def charger(self, produits: list):
        """
        Charge la liste des produits en stock faible.
        
        Args:
            produits: Liste des produits en stock faible
        """
        # Vider
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not produits:
            self._layout.addWidget(
                _lbl_vide("Aucun produit en stock faible")
            )
            self._layout.addStretch()
            return
        
        # En-tête informatif
        info = QLabel(f"{len(produits)} produit(s) en stock faible détecté(s)")
        info.setStyleSheet(
            f"color:{FactureStyles.ORANGE_SOFT}; font-size:11px; font-weight:700;"
            f"background:{FactureStyles.ORANGE_CLAIR}; border-radius:8px; padding:6px 10px;"
            f"border:1px solid {FactureStyles.ORANGE_SOFT};"
        )
        info.setWordWrap(True)
        self._layout.addWidget(info)
        
        # Liste des produits
        for produit in produits:
            self._layout.addWidget(self._carte_produit(produit))
        
        self._layout.addStretch()
    
    def _carte_produit(self, produit) -> QFrame:
        """Crée une carte pour un produit en stock faible."""
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame{{background:{FactureStyles.BLANC}; border-radius:12px;"
            f"border:1px solid {FactureStyles.GRIS_CLAIR};}}"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)
        
        # Ligne 1 : Code + Badge
        l1 = QHBoxLayout()
        # ✅ CORRECTION : produit est un dictionnaire
        code = produit.get('code_produit', '')
        code_lbl = QLabel(f"#{code}")
        code_lbl.setStyleSheet(
            f"color:{FactureStyles.VERT_PRINCIPAL}; font-size:12px; font-weight:700;"
            f"background:transparent; border:none;"
        )
        
        badge = QLabel("STOCK FAIBLE")
        badge.setStyleSheet(FactureStyles.label_badge(
            FactureStyles.ORANGE_CLAIR, FactureStyles.ORANGE_SOFT
        ))
        
        l1.addWidget(code_lbl)
        l1.addStretch()
        l1.addWidget(badge)
        lay.addLayout(l1)
        
        # Ligne 2 : Libellé
        libelle = produit.get('libelle', 'Produit inconnu')
        lay.addWidget(_row_ic_val(
            "fa5s.box", libelle,
            FactureStyles.GRIS_TEXTE, "#1F2937", gras=True
        ))
        
        # Ligne 3 : Stock actuel
        stock = produit.get('quantite_actuelle', 0)
        lay.addWidget(_row_ic_val(
            "fa5s.exclamation-triangle",
            f"Stock actuel : {stock} unités",
            FactureStyles.ORANGE_SOFT, FactureStyles.ORANGE_SOFT, gras=True
        ))
        
        return frame
