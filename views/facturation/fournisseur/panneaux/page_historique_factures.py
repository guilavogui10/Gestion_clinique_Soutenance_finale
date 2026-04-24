"""
Page historique des factures.
Responsabilité : Afficher les 10 dernières factures groupées par date.
Pattern : Component, Page.
"""

import qtawesome as qta
from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)

from ..styles.facture_styles import FactureStyles
from .ui_helpers import scroll_wrap


class PageHistoriqueFactures(QWidget):
    """
    Page 2 du panneau factures — historique des 10 dernières factures.

    Attributs publics :
        lay_cartes_histo : QVBoxLayout — conteneur des CarteHistorique
        lbl_kpi_histo    : QLabel      — affiche le nombre de factures

    Usage:
        >>> page = PageHistoriqueFactures()
        >>> page.lbl_kpi_histo.setText("5 dernières factures")
        >>> page.lay_cartes_histo.addWidget(carte)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        self._setup_ui()

    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(self._construire_kpi())
        lay.addWidget(scroll_wrap(self._construire_conteneur()))

    def _construire_kpi(self) -> QFrame:
        """Bandeau KPI de l'historique."""
        strip = QFrame()
        strip.setFixedHeight(38)
        strip.setStyleSheet(
            f"background:{FactureStyles.BLEU_CLAIR};"
            f"border-bottom:1px solid {FactureStyles.BLEU_SOFT}20;"
        )
        lay = QHBoxLayout(strip)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(8)

        ic = QLabel()
        ic.setPixmap(
            qta.icon("fa5s.history",
                     color=FactureStyles.BLEU_SOFT).pixmap(QSize(12, 12))
        )
        ic.setStyleSheet("background:transparent;")

        self.lbl_kpi_histo = QLabel("10 dernières factures")
        self.lbl_kpi_histo.setStyleSheet(
            f"color:{FactureStyles.BLEU_SOFT}; font-size:11px; "
            f"font-weight:700; background:transparent;"
        )

        lay.addWidget(ic)
        lay.addWidget(self.lbl_kpi_histo)
        lay.addStretch()
        return strip

    def _construire_conteneur(self) -> QWidget:
        """Conteneur scrollable des cartes historique."""
        conteneur = QWidget()
        conteneur.setStyleSheet("background:transparent;")
        self.lay_cartes_histo = QVBoxLayout(conteneur)
        self.lay_cartes_histo.setContentsMargins(14, 12, 14, 14)
        self.lay_cartes_histo.setSpacing(8)
        return conteneur