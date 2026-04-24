"""
Page liste des factures.
Responsabilité : Afficher la liste des factures avec recherche et KPI.
Pattern : Component, Page.
"""

from typing import Callable
import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QLineEdit
)

from ..styles.facture_styles import FactureStyles
from .ui_helpers import scroll_wrap


class PageListeFactures(QWidget):
    """
    Page 0 du panneau factures — liste avec recherche temps réel.

    Attributs publics (modifiables par le panneau parent) :
        lay_cartes  : QVBoxLayout — conteneur des CarteFacture
        lbl_kpi     : QLabel      — affiche le nombre de factures

    Usage:
        >>> page = PageListeFactures(on_recherche, on_refresh)
        >>> page.lbl_kpi.setText("5 factures")
        >>> page.lay_cartes.addWidget(carte)
    """

    def __init__(self, on_recherche: Callable[[str], None],
                 on_refresh: Callable,
                 parent=None):
        """
        Args:
            on_recherche: Callback(texte) déclenché à chaque frappe
            on_refresh:   Callback déclenché au clic sur refresh
        """
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        self._setup_ui(on_recherche, on_refresh)

    def _setup_ui(self, on_recherche, on_refresh) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(self._construire_barre_recherche(on_recherche, on_refresh))
        lay.addWidget(self._construire_kpi())
        lay.addWidget(scroll_wrap(self._construire_conteneur()))

    # =========================================================================
    # SOUS-COMPOSANTS
    # =========================================================================

    def _construire_barre_recherche(self, on_recherche, on_refresh) -> QFrame:
        """Barre avec champ recherche + icône loupe + bouton refresh."""
        container = QFrame()
        container.setFixedHeight(60)
        container.setStyleSheet(f"background:{FactureStyles.BLANC}; border:none;")
        lay = QHBoxLayout(container)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(8)

        # Wrapper champ + loupe
        wrapper = QFrame()
        wrapper.setStyleSheet(
            f"background:{FactureStyles.GRIS_FOND};"
            f"border:1px solid {FactureStyles.GRIS_CLAIR};"
            f"border-radius:10px;"
        )
        w_lay = QHBoxLayout(wrapper)
        w_lay.setContentsMargins(10, 0, 10, 0)
        w_lay.setSpacing(8)

        ic = QLabel()
        ic.setPixmap(
            qta.icon("fa5s.search",
                     color=FactureStyles.GRIS_TEXTE).pixmap(QSize(13, 13))
        )
        ic.setStyleSheet("background:transparent;")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher une facture...")
        self.search_input.setFixedHeight(36)
        self.search_input.setStyleSheet(
            "border:none; background:transparent; "
            "font-size:11px; color:#1F2937;"
        )
        self.search_input.textChanged.connect(on_recherche)

        w_lay.addWidget(ic)
        w_lay.addWidget(self.search_input)

        # Bouton refresh
        btn = QPushButton()
        btn.setIcon(qta.icon("fa5s.sync-alt", color=FactureStyles.VERT_PRINCIPAL))
        btn.setIconSize(QSize(14, 14))
        btn.setFixedSize(38, 38)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setToolTip("Rafraîchir la liste")
        btn.setStyleSheet(
            f"QPushButton{{background:{FactureStyles.VERT_CLAIR};"
            f"border:1px solid {FactureStyles.VERT_PRINCIPAL}20;"
            f"border-radius:10px;}}"
            f"QPushButton:hover{{background:{FactureStyles.VERT_PRINCIPAL};}}"
        )
        btn.clicked.connect(on_refresh)

        lay.addWidget(wrapper, 1)
        lay.addWidget(btn)
        return container

    def _construire_kpi(self) -> QFrame:
        """Bandeau KPI nombre de factures."""
        strip = QFrame()
        strip.setFixedHeight(38)
        strip.setStyleSheet(
            f"background:{FactureStyles.VERT_CLAIR};"
            f"border-bottom:1px solid {FactureStyles.VERT_PRINCIPAL}20;"
        )
        lay = QHBoxLayout(strip)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(8)

        ic = QLabel()
        ic.setPixmap(
            qta.icon("fa5s.file-invoice",
                     color=FactureStyles.VERT_PRINCIPAL).pixmap(QSize(12, 12))
        )
        ic.setStyleSheet("background:transparent;")

        self.lbl_kpi = QLabel("— factures")
        self.lbl_kpi.setStyleSheet(
            f"color:{FactureStyles.VERT_PRINCIPAL}; font-size:11px; "
            f"font-weight:700; background:transparent;"
        )

        lay.addWidget(ic)
        lay.addWidget(self.lbl_kpi)
        lay.addStretch()
        return strip

    def _construire_conteneur(self) -> QWidget:
        """Conteneur scrollable des cartes."""
        conteneur = QWidget()
        conteneur.setStyleSheet("background:transparent;")
        self.lay_cartes = QVBoxLayout(conteneur)
        self.lay_cartes.setContentsMargins(14, 12, 14, 14)
        self.lay_cartes.setSpacing(10)
        return conteneur