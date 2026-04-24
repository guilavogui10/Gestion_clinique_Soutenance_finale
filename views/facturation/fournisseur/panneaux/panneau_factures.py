"""
Panneau PanneauFactures - Orchestrateur du panneau latéral factures.
Responsabilité : Assembler les composants et gérer les données.
Pattern : Composite, Sliding Panel.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any

import qtawesome as qta
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QRect, QSize
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGraphicsDropShadowEffect, QStackedWidget
)

from ..components.carte_facture import CarteFacture
from ..vues.vue_detail_facture import VueDetailFacture
from ..styles.facture_styles import FactureStyles
from .ui_helpers import FondArrondi, lbl_vide, scroll_wrap, separateur_h
from .carte_historique import CarteHistorique
from .header_factures import HeaderFactures
from .barre_onglets_factures import BarreOngletsFactures
from .page_liste_factures import PageListeFactures
from .page_historique_factures import PageHistoriqueFactures


class PanneauFactures(FondArrondi):
    """
    Panneau latéral glissant — orchestrateur principal.
    Assemble : Header + BarreOnglets + Stack(Liste | Détail | Historique).
    """

    LARGEUR = 520

    # =========================================================================
    # INITIALISATION
    # =========================================================================

    def __init__(self, parent: QWidget, facture_ctrl: Any, panier_ctrl: Any):
        super().__init__(rayon=20, couleur_fond=FactureStyles.GRIS_FOND, parent=parent)
        self.facture_ctrl          = facture_ctrl
        self.panier_ctrl           = panier_ctrl
        self._ouvert               = False
        self._code_session         = None
        self._factures_completes: List[Dict[str, Any]] = []
        self.logger                = logging.getLogger(__name__)

        self._repositionner()
        self._setup_ui()
        self._setup_ombre()

        self.move(parent.width(), self.y())
        self.hide()

    # =========================================================================
    # ASSEMBLAGE UI
    # =========================================================================

    def _setup_ui(self) -> None:
        """Assemble les 4 composants du panneau."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Header
        self._header = HeaderFactures(on_fermer=self.fermer)
        layout.addWidget(self._header)

        # 2. Barre d'onglets
        self._barre = BarreOngletsFactures(on_change=self._aller_onglet)
        layout.addWidget(self._barre)

        # 3. Stack des pages
        layout.addWidget(self._construire_stack())

    def _construire_stack(self) -> QFrame:
        """Construit le stack avec les 3 pages."""
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background:transparent;")

        # Page 0 — Liste
        self._page_liste = PageListeFactures(
            on_recherche=self._filtrer_factures,
            on_refresh=self._rafraichir
        )
        self._stack.addWidget(self._page_liste)

        # Page 1 — Détail
        self._vue_detail = VueDetailFacture(
            self.facture_ctrl,
            self.panier_ctrl,
            on_retour=lambda: self._aller_onglet(0)
        )
        self._stack.addWidget(scroll_wrap(self._vue_detail))

        # Page 2 — Historique
        self._page_histo = PageHistoriqueFactures()
        self._stack.addWidget(self._page_histo)

        wrapper = QFrame()
        wrapper.setStyleSheet(
            "background:transparent;"
            "border-bottom-left-radius:20px;"
            "border-bottom-right-radius:20px;"
        )
        w_lay = QVBoxLayout(wrapper)
        w_lay.setContentsMargins(0, 0, 0, 0)
        w_lay.addWidget(self._stack)
        return wrapper

    # =========================================================================
    # NAVIGATION
    # =========================================================================

    def _aller_onglet(self, index: int) -> None:
        """Change d'onglet et déclenche le chargement si nécessaire."""
        self._stack.setCurrentIndex(index)
        self._barre.activer(index)
        if index == 2:
            self._charger_historique()

    # =========================================================================
    # DONNÉES — Liste
    # =========================================================================

    def actualiser(self, code_session: str) -> None:
        """Point d'entrée public : charge les données pour une session."""
        self._code_session = code_session
        self._rafraichir()

    def _rafraichir(self) -> None:
        """Rafraîchit la liste des factures."""
        if not self._code_session:
            return

        self.logger.info(f"Rafraîchissement factures session={self._code_session}")
        self._vider_layout(self._page_liste.lay_cartes)

        try:
            factures = self.facture_ctrl.lister_factures(self._code_session) or []
            self._factures_completes = [self._objet_vers_dict(f) for f in factures]
            self._afficher_factures(self._factures_completes)
        except Exception as e:
            self.logger.error(f"Erreur chargement factures: {e}", exc_info=True)
            self._page_liste.lay_cartes.addWidget(lbl_vide(f"Erreur : {e}"))
            self._page_liste.lay_cartes.addStretch()

    def _objet_vers_dict(self, f: Any) -> Dict[str, Any]:
        """Convertit un objet FactureFournisseur en dictionnaire affichable."""
        montant = getattr(f, 'montant_total', 0) or 0
        return {
            "code_facture_four": getattr(f, 'code_facture_four', ''),
            "date_facture_four": getattr(f, 'date_facture_four', None),
            "montant_total":     montant,   # ✅ m minuscule — cohérent avec CarteFacture
            "Montant_total":     montant,   # ✅ M majuscule — cohérent avec VueDetailFacture
            "mode_payement":     getattr(f, 'mode_payement', ''),
            "fournisseur_nom":   getattr(f, 'fournisseur_nom', '—'),
        }

    def _afficher_factures(self, factures: List[Dict[str, Any]]) -> None:
        """Affiche les cartes dans la page liste."""
        n = len(factures)
        self._page_liste.lbl_kpi.setText(f"{n} facture{'s' if n > 1 else ''}")
        self._header.lbl_sous_titre.setText(
            f"Session · {n} résultat{'s' if n > 1 else ''}"
        )

        if factures:
            for row in factures:
                self._page_liste.lay_cartes.addWidget(
                    CarteFacture(row, self._voir_detail)
                )
        else:
            self._page_liste.lay_cartes.addWidget(lbl_vide("Aucune facture trouvée"))

        self._page_liste.lay_cartes.addStretch()

    def _filtrer_factures(self, texte: str) -> None:
        """Filtre les cartes selon le texte saisi."""
        if not self._factures_completes:
            return

        self._vider_layout(self._page_liste.lay_cartes)
        texte = texte.lower().strip()

        if not texte:
            self._afficher_factures(self._factures_completes)
            return

        filtrees = [
            f for f in self._factures_completes
            if texte in str(f.get('code_facture_four', '')).lower()
            or texte in str(f.get('fournisseur_nom', '')).lower()
        ]
        self._afficher_factures(filtrees)

    # =========================================================================
    # DONNÉES — Historique
    # =========================================================================

    def _charger_historique(self) -> None:
        """Charge les 10 dernières factures."""
        self._vider_layout(self._page_histo.lay_cartes_histo)

        if not self._code_session:
            return

        try:
            dernieres = self.facture_ctrl.obtenir_dernieres_factures(
                self._code_session, limite=10
            )

            if not dernieres:
                self._page_histo.lay_cartes_histo.addWidget(
                    lbl_vide("Aucune facture dans l'historique")
                )
                self._page_histo.lay_cartes_histo.addStretch()
                return

            n = len(dernieres)
            self._page_histo.lbl_kpi_histo.setText(
                f"{n} dernière{'s' if n > 1 else ''} facture{'s' if n > 1 else ''}"
            )

            for date_str, items in self._grouper_par_date(dernieres).items():
                self._page_histo.lay_cartes_histo.addWidget(
                    self._creer_separateur_date(date_str)
                )
                for row in items:
                    self._page_histo.lay_cartes_histo.addWidget(
                        CarteHistorique(row, self._voir_detail)
                    )

            self._page_histo.lay_cartes_histo.addStretch()

        except Exception as e:
            self.logger.error(f"Erreur historique: {e}", exc_info=True)
            self._page_histo.lay_cartes_histo.addWidget(lbl_vide(f"Erreur : {e}"))
            self._page_histo.lay_cartes_histo.addStretch()

    def _grouper_par_date(self, factures: List[Dict]) -> Dict[str, List]:
        """Groupe les factures par date."""
        groupes: Dict[str, List] = {}
        for row in factures:
            date_val = row.get('date_facture_four')
            cle = (
                date_val.strftime("%d/%m/%Y")
                if isinstance(date_val, datetime)
                else str(date_val)[:10] if date_val else "—"
            )
            groupes.setdefault(cle, []).append(row)
        return groupes

    def _creer_separateur_date(self, date_str: str) -> QFrame:
        """Séparateur de groupe de date."""
        frame = QFrame()
        frame.setFixedHeight(28)
        frame.setStyleSheet(
            f"background:{FactureStyles.GRIS_FOND}; border-radius:6px; border:none;"
        )
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(10, 0, 10, 0)
        lay.setSpacing(6)

        ic = QLabel()
        ic.setPixmap(
            qta.icon("fa5s.calendar-day",
                     color=FactureStyles.GRIS_TEXTE).pixmap(QSize(11, 11))
        )
        ic.setStyleSheet("background:transparent;")

        lbl = QLabel(date_str)
        lbl.setStyleSheet(
            f"color:{FactureStyles.GRIS_TEXTE}; font-size:10px; "
            f"font-weight:700; background:transparent; border:none;"
        )
        lay.addWidget(ic)
        lay.addWidget(lbl)
        lay.addStretch()
        return frame

    # =========================================================================
    # DÉTAIL
    # =========================================================================

    def _voir_detail(self, code_facture: str, row_apercu: Dict[str, Any]) -> None:
        """Ouvre le détail et active l'onglet Détail."""
        self._vue_detail.charger(code_facture)
        self._barre.activer_detail(True)
        self._aller_onglet(1)

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def _vider_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _setup_ombre(self) -> None:
        ombre = QGraphicsDropShadowEffect(self)
        ombre.setBlurRadius(45)
        ombre.setOffset(-10, 0)
        ombre.setColor(QColor(0, 0, 0, 70))
        self.setGraphicsEffect(ombre)

    def _repositionner(self) -> None:
        parent = self.parent()
        if parent:
            self.setFixedSize(self.LARGEUR, parent.height())

    # =========================================================================
    # ANIMATION
    # =========================================================================

    def ouvrir(self) -> None:
        if self._ouvert:
            return
        self._ouvert = True
        self._repositionner()
        self.show()
        self.raise_()
        pw = self.parent().width()
        self._animer(
            QRect(pw, 0, self.LARGEUR, self.height()),
            QRect(pw - self.LARGEUR, 0, self.LARGEUR, self.height()),
            380, QEasingCurve.OutCubic
        )

    def fermer(self) -> None:
        if not self._ouvert:
            return
        pw = self.parent().width()
        anim = self._animer(
            self.geometry(),
            QRect(pw, 0, self.LARGEUR, self.height()),
            300, QEasingCurve.InCubic
        )
        anim.finished.connect(self.hide)
        anim.finished.connect(lambda: setattr(self, "_ouvert", False))

    def basculer(self) -> None:
        self.fermer() if self._ouvert else self.ouvrir()

    def _animer(self, debut, fin, duree, courbe) -> QPropertyAnimation:
        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(duree)
        self._anim.setStartValue(debut)
        self._anim.setEndValue(fin)
        self._anim.setEasingCurve(courbe)
        self._anim.start()
        return self._anim

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._ouvert and self.parent():
            pw = self.parent().width()
            self.setGeometry(pw - self.LARGEUR, 0,
                             self.LARGEUR, self.parent().height())