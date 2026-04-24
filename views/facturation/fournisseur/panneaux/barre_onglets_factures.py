"""
Barre d'onglets du panneau factures.
Responsabilité : Gérer la navigation entre les 3 onglets.
Pattern : Component, Navigation.
"""

from typing import Callable
import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QPushButton, QButtonGroup
)

from ..styles.facture_styles import FactureStyles


class BarreOngletsFactures(QFrame):
    """
    Barre de navigation à 3 onglets : Factures / Détail / Historique.

    Usage:
        >>> barre = BarreOngletsFactures(on_onglet_change)
        >>> barre.activer(0)
        >>> barre.activer_detail(True)
    """

    ONGLETS = [
        ("fa5s.file-invoice", "Factures"),
        ("fa5s.eye",          "Détail"),
        ("fa5s.history",      "Historique"),
    ]

    def __init__(self, on_change: Callable[[int], None], parent=None):
        """
        Args:
            on_change: Callback(index) appelé au changement d'onglet
        """
        super().__init__(parent)
        self.on_change = on_change
        self.setFixedHeight(50)
        self.setStyleSheet(
            f"background:{FactureStyles.BLANC};"
            f"border-bottom:1px solid {FactureStyles.GRIS_CLAIR};"
        )
        self._boutons: list[QPushButton] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 8, 16, 8)
        lay.setSpacing(4)

        groupe = QButtonGroup(self)

        for idx, (icone, label) in enumerate(self.ONGLETS):
            actif = (idx == 0)
            btn = self._creer_bouton(icone, label, actif)
            groupe.addButton(btn, idx)
            lay.addWidget(btn)
            self._boutons.append(btn)

        lay.addStretch()

        # Connexions
        self._boutons[0].clicked.connect(lambda: self.on_change(0))
        self._boutons[1].clicked.connect(lambda: self.on_change(1))
        self._boutons[2].clicked.connect(lambda: self.on_change(2))

        # Onglet détail désactivé par défaut
        self._boutons[1].setEnabled(False)

    def _creer_bouton(self, icone: str, label: str, actif: bool) -> QPushButton:
        """Crée un bouton d'onglet."""
        couleur_ic = FactureStyles.VERT_PRINCIPAL if actif else FactureStyles.GRIS_TEXTE
        btn = QPushButton(qta.icon(icone, color=couleur_ic), f"  {label}")
        btn.setFixedHeight(34)
        btn.setCheckable(True)
        btn.setChecked(actif)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            self._style_actif() if actif else self._style_inactif()
        )
        return btn

    # =========================================================================
    # API PUBLIQUE
    # =========================================================================

    def activer(self, index: int) -> None:
        """Active visuellement l'onglet à l'index donné."""
        for i, btn in enumerate(self._boutons):
            btn.setStyleSheet(
                self._style_actif() if i == index else self._style_inactif()
            )

    def activer_detail(self, actif: bool) -> None:
        """Active ou désactive le bouton onglet Détail."""
        self._boutons[1].setEnabled(actif)

    # =========================================================================
    # STYLES
    # =========================================================================

    def _style_actif(self) -> str:
        return (
            f"QPushButton{{background:{FactureStyles.VERT_PRINCIPAL};"
            f"color:{FactureStyles.BLANC}; border-radius:8px;"
            f"font-size:11px; font-weight:600; padding:0 12px; border:none;}}"
        )

    def _style_inactif(self) -> str:
        return (
            f"QPushButton{{background:transparent; color:{FactureStyles.GRIS_TEXTE};"
            f"border-radius:8px; font-size:11px; font-weight:400;"
            f"padding:0 12px; border:none;}}"
            f"QPushButton:hover{{background:{FactureStyles.GRIS_FOND};}}"
        )