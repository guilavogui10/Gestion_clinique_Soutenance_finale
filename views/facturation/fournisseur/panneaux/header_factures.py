"""
Header du panneau factures.
Responsabilité : Construire l'en-tête dégradé avec titre et bouton fermer.
Pattern : Component.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton

from ..styles.facture_styles import FactureStyles


class HeaderFactures(QFrame):
    """
    En-tête dégradé vert du panneau factures.

    Structure :
    ┌──────────────────────────────────────────┐
    │ [ic] Factures Fournisseurs     [x]       │
    │      Session en cours                    │
    └──────────────────────────────────────────┘
    """

    def __init__(self, on_fermer, parent=None):
        """
        Args:
            on_fermer: Callback appelé au clic sur le bouton fermer
        """
        super().__init__(parent)
        self.setFixedHeight(62)
        self.setStyleSheet(
            f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {FactureStyles.VERT_PRINCIPAL},stop:1 #005c2e);"
            f"border-top-left-radius:20px; border-top-right-radius:20px;"
        )
        self._setup_ui(on_fermer)

    def _setup_ui(self, on_fermer) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 0, 16, 0)

        # Icône principale
        ic = QLabel()
        ic.setPixmap(
            qta.icon("fa5s.file-invoice-dollar",
                     color=FactureStyles.BLANC).pixmap(QSize(20, 20))
        )
        ic.setStyleSheet("background:transparent;")

        # Titres
        col = QVBoxLayout()
        col.setSpacing(1)

        t1 = QLabel("Factures Fournisseurs")
        t1.setStyleSheet(
            f"color:{FactureStyles.BLANC}; font-size:14px; "
            f"font-weight:700; background:transparent;"
        )

        self.lbl_sous_titre = QLabel("Session en cours")
        self.lbl_sous_titre.setStyleSheet(
            f"color:rgba(255,255,255,0.70); font-size:11px; "
            f"background:transparent;"
        )
        col.addWidget(t1)
        col.addWidget(self.lbl_sous_titre)

        # Bouton fermer
        btn_fermer = QPushButton(
            qta.icon("fa5s.times", color=FactureStyles.BLANC), ""
        )
        btn_fermer.setFixedSize(32, 32)
        btn_fermer.setCursor(Qt.PointingHandCursor)
        btn_fermer.setToolTip("Fermer")
        btn_fermer.setStyleSheet(
            "QPushButton{background:rgba(255,255,255,0.18);"
            "border-radius:16px; border:none;}"
            "QPushButton:hover{background:rgba(255,255,255,0.30);}"
        )
        btn_fermer.clicked.connect(on_fermer)

        lay.addWidget(ic)
        lay.addSpacing(10)
        lay.addLayout(col)
        lay.addStretch()
        lay.addWidget(btn_fermer)