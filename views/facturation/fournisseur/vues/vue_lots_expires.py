"""
Vue VueLotsExpires - Affichage des lots expirés.
Responsabilité : Afficher la liste des lots dont la date d'expiration est dépassée.
Pattern : Component, List View.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame

from ..components.ligne_lot_card import LigneLotCard
from ..styles.facture_styles import FactureStyles


def _lbl_vide(texte):
    """Crée un label pour message vide."""
    lbl = QLabel(texte)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(FactureStyles.label_vide())
    return lbl


class VueLotsExpires(QWidget):
    """
    Vue affichant tous les lots expirés de la session.
    
    Usage:
        >>> vue = VueLotsExpires()
        >>> vue.charger(lots_expires)
    """
    
    def __init__(self, parent=None):
        """Initialise la vue lots expirés."""
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 12, 16, 16)
        self._layout.setSpacing(10)
    
    def charger(self, lots: list):
        """
        Charge la liste des lots expirés.
        
        Args:
            lots: Liste des lots expirés
        """
        # Vider
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not lots:
            self._layout.addWidget(
                _lbl_vide("Aucun lot expiré sur cette session")
            )
            self._layout.addStretch()
            return
        
        # En-tête informatif
        info = QLabel(f"{len(lots)} lot(s) expiré(s) détecté(s)")
        info.setStyleSheet(
            f"color:{FactureStyles.ROUGE_SOFT}; font-size:11px; font-weight:700;"
            f"background:{FactureStyles.ROUGE_CLAIR}; border-radius:8px; padding:6px 10px;"
            f"border:1px solid {FactureStyles.ROUGE_SOFT};"
        )
        info.setWordWrap(True)
        self._layout.addWidget(info)
        
        # Liste des lots
        for lot in lots:
            self._layout.addWidget(self._carte_lot(lot))
        
        self._layout.addStretch()
    
    def _carte_lot(self, lot) -> QFrame:
        """Crée une carte pour un lot expiré."""
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame{{background:{FactureStyles.BLANC}; border-radius:12px;"
            f"border:1px solid {FactureStyles.GRIS_CLAIR};}}"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)
        
        # Ligne 1 : Produit
        # ✅ CORRECTION : lot est un dictionnaire
        libelle = lot.get('libelle', 'Produit inconnu')
        nom_lbl = QLabel(libelle)
        nom_lbl.setStyleSheet(
            f"color:#1F2937; font-size:12px; font-weight:700;"
            f"background:transparent; border:none;"
        )
        lay.addWidget(nom_lbl)
        
        # Ligne 2 : Date + Quantité
        date_exp = lot.get('date_expiration')
        qte = lot.get('stock_lot', 0)
        
        ligne = LigneLotCard(date_exp, qte, "expire")
        lay.addWidget(ligne)
        
        return frame
