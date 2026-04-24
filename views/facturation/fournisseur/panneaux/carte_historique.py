"""
Composant CarteHistorique - Carte compacte pour l'historique des factures.
Responsabilité : Afficher un résumé d'une facture dans l'onglet Historique.
Pattern : Component, Reusability.
"""

from datetime import datetime
from typing import Dict, Any, Callable

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)

from ..styles.facture_styles import FactureStyles
from .ui_helpers import separateur_h


class CarteHistorique(QFrame):
    """
    Carte compacte représentant une facture dans l'onglet Historique.

    Structure :
    ┌────────────────────────────────────┐
    │ [#FCF001]              [clock] 14:30 │
    │ ─────────────────────────────────── │
    │ [truck] Pharma Guinée SARL          │
    │ [coins] 250 000 GNF  [Espèces] [>] │
    └────────────────────────────────────┘

    Usage:
        >>> carte = CarteHistorique(row, on_voir_detail)
        >>> layout.addWidget(carte)
    """

    def __init__(self, row: Dict[str, Any],
                 on_voir_detail: Callable,
                 parent=None):
        """
        Initialise la carte historique.

        Args:
            row: Dictionnaire avec les données de la facture
            on_voir_detail: Callback(code_facture, row) pour voir le détail
            parent: Widget parent Qt
        """
        super().__init__(parent)
        self.row           = row
        self.on_voir_detail = on_voir_detail

        self.setStyleSheet(
            f"QFrame{{background:{FactureStyles.BLANC}; border-radius:10px;"
            f"border:1px solid {FactureStyles.GRIS_CLAIR};}}"
            f"QFrame:hover{{border:1px solid {FactureStyles.BLEU_SOFT};"
            f"background:{FactureStyles.BLEU_CLAIR};}}"
        )

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Construit l'interface de la carte."""
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(6)

        lay.addLayout(self._ligne_code_heure())
        lay.addWidget(separateur_h())
        lay.addLayout(self._ligne_fournisseur())
        lay.addLayout(self._ligne_montant_actions())

    # =========================================================================
    # LIGNES
    # =========================================================================

    def _ligne_code_heure(self) -> QHBoxLayout:
        """Ligne 1 : badge code facture + heure."""
        lay = QHBoxLayout()
        lay.setSpacing(0)

        # Badge code
        code = self.row.get('code_facture_four', '—')
        badge = QFrame()
        badge.setStyleSheet(
            f"background:{FactureStyles.VERT_CLAIR}; border-radius:6px; border:none;"
        )
        b_lay = QHBoxLayout(badge)
        b_lay.setContentsMargins(8, 3, 8, 3)
        b_lay.setSpacing(5)

        ic_hash = QLabel()
        ic_hash.setPixmap(
            qta.icon("fa5s.hashtag",
                     color=FactureStyles.VERT_PRINCIPAL).pixmap(QSize(10, 10))
        )
        ic_hash.setStyleSheet("background:transparent;")

        lbl_code = QLabel(code)
        lbl_code.setStyleSheet(
            f"color:{FactureStyles.VERT_PRINCIPAL}; font-size:11px; "
            f"font-weight:700; background:transparent; border:none;"
        )
        b_lay.addWidget(ic_hash)
        b_lay.addWidget(lbl_code)

        # Heure
        heure_lay = QHBoxLayout()
        heure_lay.setSpacing(5)

        ic_clock = QLabel()
        ic_clock.setPixmap(
            qta.icon("fa5s.clock",
                     color=FactureStyles.GRIS_TEXTE).pixmap(QSize(10, 10))
        )
        ic_clock.setStyleSheet("background:transparent;")

        date_val = self.row.get('date_facture_four')
        heure = (date_val.strftime("%H:%M")
                 if isinstance(date_val, datetime) else "—")
        lbl_heure = QLabel(heure)
        lbl_heure.setStyleSheet(
            f"color:{FactureStyles.GRIS_TEXTE}; font-size:10px; "
            f"background:transparent; border:none;"
        )
        heure_lay.addWidget(ic_clock)
        heure_lay.addWidget(lbl_heure)

        lay.addWidget(badge)
        lay.addStretch()
        lay.addLayout(heure_lay)
        return lay

    def _ligne_fournisseur(self) -> QHBoxLayout:
        """Ligne 2 : icône camion + nom fournisseur."""
        lay = QHBoxLayout()
        lay.setSpacing(8)

        ic = QLabel()
        ic.setPixmap(
            qta.icon("fa5s.truck",
                     color=FactureStyles.VERT_PRINCIPAL).pixmap(QSize(12, 12))
        )
        ic.setStyleSheet("background:transparent;")

        lbl = QLabel(self.row.get('fournisseur_nom') or 'Fournisseur inconnu')
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            f"color:#1F2937; font-size:11px; font-weight:600; "
            f"background:transparent; border:none;"
        )

        lay.addWidget(ic)
        lay.addWidget(lbl, 1)
        return lay

    def _ligne_montant_actions(self) -> QHBoxLayout:
        """Ligne 3 : montant + badge mode paiement + bouton détail."""
        lay = QHBoxLayout()
        lay.setSpacing(8)

        # Montant
        montant_lay = QHBoxLayout()
        montant_lay.setSpacing(5)

        ic_coins = QLabel()
        ic_coins.setPixmap(
            qta.icon("fa5s.coins",
                     color=FactureStyles.VERT_PRINCIPAL).pixmap(QSize(12, 12))
        )
        ic_coins.setStyleSheet("background:transparent;")

        montant = (self.row.get('Montant_total')
                   or self.row.get('montant_total') or 0)
        lbl_montant = QLabel(
            f"{int(montant):,}".replace(",", " ") + " GNF"
        )
        lbl_montant.setStyleSheet(
            f"color:{FactureStyles.VERT_PRINCIPAL}; font-size:11px; "
            f"font-weight:700; background:transparent; border:none;"
        )
        montant_lay.addWidget(ic_coins)
        montant_lay.addWidget(lbl_montant)

        # Badge mode paiement
        mode = self.row.get('mode_payement') or '—'
        badge_mode = QFrame()
        badge_mode.setStyleSheet(
            f"background:{FactureStyles.BLEU_CLAIR}; border-radius:6px; border:none;"
        )
        bm_lay = QHBoxLayout(badge_mode)
        bm_lay.setContentsMargins(6, 3, 8, 3)
        bm_lay.setSpacing(5)

        ic_card = QLabel()
        ic_card.setPixmap(
            qta.icon("fa5s.credit-card",
                     color=FactureStyles.BLEU_SOFT).pixmap(QSize(10, 10))
        )
        ic_card.setStyleSheet("background:transparent;")

        lbl_mode = QLabel(mode.capitalize())
        lbl_mode.setStyleSheet(
            f"color:{FactureStyles.BLEU_SOFT}; font-size:9px; "
            f"font-weight:700; background:transparent; border:none;"
        )
        bm_lay.addWidget(ic_card)
        bm_lay.addWidget(lbl_mode)

        # Bouton voir détail
        btn = QPushButton()
        btn.setIcon(
            qta.icon("fa5s.chevron-right", color=FactureStyles.BLANC)
        )
        # ✅ Après
        btn.setIcon(
            qta.icon("fa5s.eye", color=FactureStyles.BLEU_SOFT)
        )
        btn.setIconSize(QSize(13, 13))
        btn.setFixedSize(28, 28)
        btn.setStyleSheet(
            f"QPushButton{{background:{FactureStyles.BLEU_CLAIR};"
            f"border:none; border-radius:8px;}}"
            f"QPushButton:hover{{background:{FactureStyles.BLEU_SOFT};}}"
        )

        lay.addLayout(montant_lay)
        lay.addStretch()
        lay.addWidget(badge_mode)
        lay.addWidget(btn)
        return lay