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
from views.shared.theme_manager import theme_manager


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
        theme_manager.theme_changed.connect(self.apply_theme)

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
        self._container_recherche = QFrame()
        self._container_recherche.setFixedHeight(60)
        self._container_recherche.setStyleSheet(f"background:{FactureStyles.BLANC}; border:none;")
        lay = QHBoxLayout(self._container_recherche)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(8)

        # Wrapper champ + loupe
        self._wrapper_recherche = QFrame()
        self._wrapper_recherche.setStyleSheet(
            f"background:{theme_manager.colors()['bg_input']};"
            f"border:1px solid {FactureStyles.GRIS_CLAIR};"
            f"border-radius:10px;"
        )
        w_lay = QHBoxLayout(self._wrapper_recherche)
        w_lay.setContentsMargins(10, 0, 10, 0)
        w_lay.setSpacing(8)

        self._ic_recherche = QLabel()
        self._ic_recherche.setPixmap(
            qta.icon("fa5s.search",
                     color=FactureStyles.GRIS_TEXTE).pixmap(QSize(13, 13))
        )
        self._ic_recherche.setStyleSheet("background:transparent;")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher une facture...")
        self.search_input.setFixedHeight(36)
        self.search_input.setStyleSheet(
            f"border:none; background:transparent; "
            f"font-size:11px; color:{FactureStyles.GRIS_TEXTE};"
        )
        self.search_input.textChanged.connect(on_recherche)

        w_lay.addWidget(self._ic_recherche)
        w_lay.addWidget(self.search_input)

        # Bouton refresh
        self._btn_refresh = QPushButton()
        self._btn_refresh.setIcon(qta.icon("fa5s.sync-alt", color=FactureStyles.VERT_PRINCIPAL))
        self._btn_refresh.setIconSize(QSize(14, 14))
        self._btn_refresh.setFixedSize(38, 38)
        self._btn_refresh.setCursor(Qt.PointingHandCursor)
        self._btn_refresh.setToolTip("Rafraîchir la liste")
        self._btn_refresh.setStyleSheet(
            f"QPushButton{{background:{FactureStyles.VERT_CLAIR};"
            f"border:1px solid {FactureStyles.VERT_PRINCIPAL}20;"
            f"border-radius:10px;}}"
            f"QPushButton:hover{{background:{FactureStyles.VERT_PRINCIPAL};}}"
        )
        self._btn_refresh.clicked.connect(on_refresh)

        lay.addWidget(self._wrapper_recherche, 1)
        lay.addWidget(self._btn_refresh)
        return self._container_recherche

    def _construire_kpi(self) -> QFrame:
        """Bandeau KPI nombre de factures."""
        self._kpi_strip = QFrame()
        self._kpi_strip.setFixedHeight(38)
        self._kpi_strip.setStyleSheet(
            f"background:{FactureStyles.VERT_CLAIR};"
            f"border-bottom:1px solid {FactureStyles.VERT_PRINCIPAL}20;"
        )
        lay = QHBoxLayout(self._kpi_strip)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(8)

        self._ic_kpi = QLabel()
        self._ic_kpi.setPixmap(
            qta.icon("fa5s.file-invoice",
                     color=FactureStyles.VERT_PRINCIPAL).pixmap(QSize(12, 12))
        )
        self._ic_kpi.setStyleSheet("background:transparent;")

        self.lbl_kpi = QLabel("— factures")
        self.lbl_kpi.setStyleSheet(
            f"color:{FactureStyles.VERT_PRINCIPAL}; font-size:11px; "
            f"font-weight:700; background:transparent;"
        )

        lay.addWidget(self._ic_kpi)
        lay.addWidget(self.lbl_kpi)
        lay.addStretch()
        return self._kpi_strip

    def apply_theme(self) -> None:
        """Met à jour les couleurs selon le thème actif."""
        if hasattr(self, '_container_recherche'):
            self._container_recherche.setStyleSheet(
                f"background:{FactureStyles.BLANC}; border:none;"
            )
        if hasattr(self, '_wrapper_recherche'):
            self._wrapper_recherche.setStyleSheet(
                f"background:{theme_manager.colors()['bg_input']};"
                f"border:1px solid {FactureStyles.GRIS_CLAIR};"
                f"border-radius:10px;"
            )
        if hasattr(self, '_ic_recherche'):
            self._ic_recherche.setPixmap(
                qta.icon("fa5s.search",
                         color=FactureStyles.GRIS_TEXTE).pixmap(QSize(13, 13))
            )
        if hasattr(self, 'search_input'):
            self.search_input.setStyleSheet(
                f"border:none; background:transparent; "
                f"font-size:11px; color:{FactureStyles.GRIS_TEXTE};"
            )
        if hasattr(self, '_btn_refresh'):
            self._btn_refresh.setIcon(
                qta.icon("fa5s.sync-alt", color=FactureStyles.VERT_PRINCIPAL)
            )
            self._btn_refresh.setStyleSheet(
                f"QPushButton{{background:{FactureStyles.VERT_CLAIR};"
                f"border:1px solid {FactureStyles.VERT_PRINCIPAL}20;"
                f"border-radius:10px;}}"
                f"QPushButton:hover{{background:{FactureStyles.VERT_PRINCIPAL};}}"
            )
        if hasattr(self, '_kpi_strip'):
            self._kpi_strip.setStyleSheet(
                f"background:{FactureStyles.VERT_CLAIR};"
                f"border-bottom:1px solid {FactureStyles.VERT_PRINCIPAL}20;"
            )
        if hasattr(self, '_ic_kpi'):
            self._ic_kpi.setPixmap(
                qta.icon("fa5s.file-invoice",
                         color=FactureStyles.VERT_PRINCIPAL).pixmap(QSize(12, 12))
            )
        if hasattr(self, 'lbl_kpi'):
            self.lbl_kpi.setStyleSheet(
                f"color:{FactureStyles.VERT_PRINCIPAL}; font-size:11px; "
                f"font-weight:700; background:transparent;"
            )

    def _construire_conteneur(self) -> QWidget:
        """Conteneur scrollable des cartes."""
        conteneur = QWidget()
        conteneur.setStyleSheet("background:transparent;")
        self.lay_cartes = QVBoxLayout(conteneur)
        self.lay_cartes.setContentsMargins(14, 12, 14, 14)
        self.lay_cartes.setSpacing(10)
        return conteneur