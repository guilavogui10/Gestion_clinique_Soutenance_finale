"""
Vue VueDetailProduit - Affichage détaillé d'un produit avec ses lots.
Responsabilité : Afficher les informations complètes d'un produit et ses lots.
Pattern : Component, Container.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QScrollArea
)

from ..components.ligne_lot_card import LigneLotCard
from ..styles.facture_styles import FactureStyles
from views.shared.theme_manager import theme_manager


# =============================================================================
# MODÈLE DE DONNÉES INTERNE
# =============================================================================

@dataclass
class ChampBloc:
    """
    Représente un champ affiché dans un bloc d'informations.
    Remplace les tuples à position fixe — fragile et illisible.
    """
    icone:     str
    valeur:    str
    couleur_ic:  str = None
    couleur_val: str = None
    gras:      bool = False

    def __post_init__(self):
        _c = theme_manager.colors()
        if self.couleur_ic is None:
            self.couleur_ic = _c['text_muted']
        if self.couleur_val is None:
            self.couleur_val = _c['text_muted']


@dataclass
class StatsLots:
    """Statistiques calculées à partir des lots d'un produit."""
    stock_total:  int = 0
    qte_valide:   int = 0
    qte_bientot:  int = 0
    qte_expire:   int = 0


# =============================================================================
# HELPERS UI LOCAUX
# =============================================================================

def _sep(couleur: str = None) -> QFrame:
    """Crée un séparateur horizontal fin."""
    couleur = couleur or theme_manager.colors()['border_light']
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background:{couleur}; border:none;")
    return f


def _row_ic_val(champ: ChampBloc) -> QWidget:
    """
    Crée une ligne [icône + valeur] à partir d'un ChampBloc.

    Args:
        champ: Données du champ à afficher

    Returns:
        QWidget: Ligne configurée
    """
    w = QWidget()
    w.setStyleSheet("background:transparent;")
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)

    ic = QLabel()
    ic.setPixmap(
        qta.icon(champ.icone,
                 color=champ.couleur_ic).pixmap(QSize(11, 11))
    )
    ic.setStyleSheet(FactureStyles.icone_base())

    lbl = QLabel(str(champ.valeur) if champ.valeur else "—")
    lbl.setWordWrap(True)
    lbl.setStyleSheet(
        f"color:{champ.couleur_val}; font-size:11px; "
        f"font-weight:{'700' if champ.gras else '400'};"
        f"background:transparent; border:none;"
    )

    lay.addWidget(ic)
    lay.addWidget(lbl)
    lay.addStretch()
    return w


def _lbl_vide(texte: str) -> QLabel:
    """Crée un label centré pour état vide."""
    lbl = QLabel(texte)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(FactureStyles.label_vide())
    return lbl


def _scroll_wrap(inner_widget: QWidget) -> QScrollArea:
    """Enveloppe un widget dans un QScrollArea sans bordure."""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setStyleSheet(FactureStyles.scroll_area())
    scroll.verticalScrollBar().setStyleSheet(FactureStyles.scrollbar())
    scroll.setWidget(inner_widget)
    return scroll


# =============================================================================
# VUE PRINCIPALE
# =============================================================================

class VueDetailProduit(QWidget):
    """
    Vue détail d'un produit affichée dans le panneau (onglet Détail).

    Affiche 3 blocs :
    - Informations Produit (code, libellé, type, stock total)
    - Statistiques (valides / bientôt expirés / expirés)
    - Liste des Lots (LigneLotCard par lot)
    """

    def __init__(self, ctrl, on_retour, parent=None):
        """
        Args:
            ctrl:      Contrôleur panier (fournit lister_lots_par_produit)
            on_retour: Callback pour retourner à la liste
            parent:    Widget parent Qt
        """
        super().__init__(parent)
        self.ctrl        = ctrl
        self.on_retour   = on_retour
        self.code_session: Optional[str] = None
        self.logger      = logging.getLogger(__name__)

        self.setStyleSheet("background:transparent;")
        self._setup_ui()
        theme_manager.theme_changed.connect(self.apply_theme)

    # =========================================================================
    # CONSTRUCTION UI
    # =========================================================================

    def _setup_ui(self) -> None:
        """Construit le squelette de l'interface."""
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 12, 16, 16)
        self._layout.setSpacing(12)

        self._layout.addWidget(self._construire_btn_retour())

        # Corps scrollable — sera peuplé dans charger()
        self._corps = QWidget()
        self._corps.setStyleSheet("background:transparent;")
        self._corps_lay = QVBoxLayout(self._corps)
        self._corps_lay.setContentsMargins(0, 0, 0, 0)
        self._corps_lay.setSpacing(12)

        self._layout.addWidget(_scroll_wrap(self._corps))

    def _construire_btn_retour(self) -> QPushButton:
        """Construit le bouton de retour à la liste."""
        _c = theme_manager.colors()
        self._btn_retour = QPushButton(
            qta.icon("fa5s.arrow-left", color=_c['primary']),
            "  Retour à la liste"
        )
        self._btn_retour.setFixedHeight(34)
        self._btn_retour.setCursor(Qt.PointingHandCursor)
        self._btn_retour.setStyleSheet(
            f"QPushButton{{background:{_c['success_bg']};"
            f"color:{_c['primary']}; border-radius:8px;"
            f"border:none; font-size:11px; font-weight:600; padding:0 12px;}}"
            f"QPushButton:hover{{background:{_c['primary']};"
            f"color:{_c['text_inverse']};}}"
        )
        self._btn_retour.clicked.connect(self.on_retour)
        return self._btn_retour

    def apply_theme(self) -> None:
        """Met à jour les couleurs selon le thème actif."""
        c = theme_manager.colors()
        if hasattr(self, '_btn_retour'):
            self._btn_retour.setIcon(
                qta.icon("fa5s.arrow-left", color=c['primary'])
            )
            self._btn_retour.setStyleSheet(
                f"QPushButton{{background:{c['success_bg']};"
                f"color:{c['primary']}; border-radius:8px;"
                f"border:none; font-size:11px; font-weight:600; padding:0 12px;}}"
                f"QPushButton:hover{{background:{c['primary']};"
                f"color:{c['text_inverse']};}}"
            )

    # =========================================================================
    # CHARGEMENT
    # =========================================================================

    def charger(self, code_produit: str, code_session: str,
                row_apercu: dict = None) -> None:
        """
        Charge et affiche les données complètes d'un produit.

        Args:
            code_produit: Code du produit à afficher
            code_session: Code de la session en cours
            row_apercu:   Données d'aperçu déjà disponibles (optionnel)
        """
        self._vider_corps()
        self.code_session = code_session
        data = row_apercu or {}

        lots  = self._recuperer_lots(code_produit, code_session)
        stats = self._calculer_stats(lots)

        self._corps_lay.addWidget(
            self._construire_bloc_infos(code_produit, data, stats)
        )
        self._corps_lay.addWidget(
            self._construire_bloc_statistiques(stats)
        )
        self._corps_lay.addWidget(
            self._construire_bloc_lots(lots)
        )
        self._corps_lay.addStretch()

    # =========================================================================
    # LOGIQUE MÉTIER
    # =========================================================================

    def _recuperer_lots(self, code_produit: str,
                        code_session: str) -> List[dict]:
        """
        Récupère les lots du produit via le contrôleur.

        Returns:
            Liste de dictionnaires lots, vide en cas d'erreur
        """
        try:
            return self.ctrl.lister_lots_par_produit(
                code_produit, code_session
            ) or []
        except Exception as e:
            self.logger.error(
                f"Erreur récupération lots produit={code_produit}: {e}",
                exc_info=True
            )
            return []

    def _calculer_stats(self, lots: List[dict]) -> StatsLots:
        """
        Calcule les statistiques de stock à partir des lots.

        Note : idéalement ces calculs devraient être faits côté contrôleur.
        Ils sont ici car les lots sont chargés directement dans la vue
        sans passer par une méthode dédiée du contrôleur.

        Args:
            lots: Liste des lots du produit

        Returns:
            StatsLots: Statistiques calculées
        """
        stats = StatsLots()

        for lot in lots:
            qte    = lot.get('stock_lot', 0) or 0
            statut = lot.get('statut_lot', 'Valide')
            stats.stock_total += qte

            if statut == 'Expiré':
                stats.qte_expire  += qte
            elif statut == 'À Expirer':
                stats.qte_bientot += qte
            else:
                stats.qte_valide  += qte

        return stats

    # =========================================================================
    # BLOCS D'AFFICHAGE
    # =========================================================================

    def _construire_bloc_infos(self, code_produit: str,
                                data: dict,
                                stats: StatsLots) -> QFrame:
        """Bloc 1 : informations générales du produit."""
        libelle = data.get('designation') or data.get('libelle') or '—'
        type_produit = data.get('type', '—')

        champs = [
            ChampBloc(
                icone="fa5s.barcode",
                valeur=f"Code : {code_produit}",
                gras=True
            ),
            ChampBloc(
                icone="fa5s.tag",
                valeur=f"Libellé : {libelle}",
                gras=True
            ),
            ChampBloc(
                icone="fa5s.flask",
                valeur=f"Type : {type_produit}",
                couleur_ic=FactureStyles.obtenir_couleur_type(type_produit),
                couleur_val=FactureStyles.obtenir_couleur_type(type_produit)
            ),
            ChampBloc(
                icone="fa5s.layer-group",
                valeur=f"Stock Total : {stats.stock_total} unités",
                gras=True
            ),
        ]

        _c = theme_manager.colors()
        return self._construire_bloc(
            "fa5s.box", _c['primary'],
            "Informations Produit", champs
        )

    def _construire_bloc_statistiques(self, stats: StatsLots) -> QFrame:
        """Bloc 2 : statistiques valide / bientôt / expiré."""
        _c = theme_manager.colors()
        champs = [
            ChampBloc(
                icone="fa5s.check-circle",
                valeur=f"Valides : {stats.qte_valide} unité{'s' if stats.qte_valide > 1 else ''}",
                couleur_ic=_c['success'],
                couleur_val=_c['success'],
                gras=True
            ),
            ChampBloc(
                icone="fa5s.hourglass-half",
                valeur=f"Bientôt expirés : {stats.qte_bientot} unité{'s' if stats.qte_bientot > 1 else ''}",
                couleur_ic=_c['warning'],
                couleur_val=_c['warning'],
                gras=(stats.qte_bientot > 0)
            ),
            ChampBloc(
                icone="fa5s.times-circle",
                valeur=f"Expirés : {stats.qte_expire} unité{'s' if stats.qte_expire > 1 else ''}",
                couleur_ic=_c['danger'],
                couleur_val=_c['danger'],
                gras=(stats.qte_expire > 0)
            ),
        ]

        return self._construire_bloc(
            "fa5s.chart-pie", _c['info'],
            "Statistiques", champs
        )

    def _construire_bloc_lots(self, lots: List[dict]) -> QFrame:
        """Bloc 3 : liste détaillée des lots avec LigneLotCard."""
        frame = self._creer_cadre(
            "fa5s.list", theme_manager.colors()['accent'],
            f"Liste des Lots ({len(lots)})"
        )
        lay = frame.layout()

        if not lots:
            lay.addWidget(_lbl_vide("Aucun lot disponible pour ce produit"))
            return frame

        for lot in lots:
            date_exp       = lot.get('date_expiration')
            qte            = lot.get('stock_lot', 0) or 0
            statut_lot     = lot.get('statut_lot', 'Valide')
            jours_restants = lot.get('jours_restants', 0)

            # Normalisation du statut pour LigneLotCard
            statut = self._normaliser_statut(statut_lot)

            lay.addWidget(LigneLotCard(date_exp, qte, statut, jours_restants))

        return frame

    # =========================================================================
    # COMPOSANTS GÉNÉRIQUES
    # =========================================================================

    def _construire_bloc(self, icone: str, couleur: str,
                          titre: str,
                          champs: List[ChampBloc]) -> QFrame:
        """
        Crée un bloc générique avec titre + liste de champs.

        Args:
            icone:   Icône qtawesome du titre
            couleur: Couleur du titre et de l'icône
            titre:   Texte du titre
            champs:  Liste de ChampBloc à afficher

        Returns:
            QFrame: Bloc configuré
        """
        frame = self._creer_cadre(icone, couleur, titre)
        lay   = frame.layout()

        for champ in champs:
            lay.addWidget(_row_ic_val(champ))

        return frame

    def _creer_cadre(self, icone: str, couleur: str,
                     titre: str) -> QFrame:
        """
        Crée un cadre avec en-tête (icône + titre + séparateur).

        Args:
            icone:   Icône qtawesome
            couleur: Couleur de l'icône et du titre
            titre:   Texte du titre

        Returns:
            QFrame: Cadre avec layout vertical prêt à recevoir des widgets
        """
        _c = theme_manager.colors()
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame{{background:{_c['bg_card']}; border-radius:12px;"
            f"border:1px solid {_c['border']};}}"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)

        # En-tête
        hdr = QHBoxLayout()
        ic  = QLabel()
        ic.setPixmap(qta.icon(icone, color=couleur).pixmap(QSize(13, 13)))
        ic.setStyleSheet(FactureStyles.icone_base())

        lbl_titre = QLabel(titre)
        lbl_titre.setStyleSheet(
            f"color:{couleur}; font-size:11px; font-weight:700; border:none;"
        )

        hdr.addWidget(ic)
        hdr.addSpacing(6)
        hdr.addWidget(lbl_titre)
        hdr.addStretch()

        lay.addLayout(hdr)
        lay.addWidget(_sep(FactureStyles.VERT_CLAIR))

        return frame

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def _normaliser_statut(self, statut_lot: str) -> str:
        """
        Convertit le statut BDD en statut attendu par LigneLotCard.

        Args:
            statut_lot: Statut brut de la BDD ('Expiré', 'À Expirer', 'Valide')

        Returns:
            str: 'expire' | 'bientot' | 'valide'
        """
        mapping = {
            'Expiré':    'expire',
            'À Expirer': 'bientot',
        }
        return mapping.get(statut_lot, 'valide')

    def _vider_corps(self) -> None:
        """Vide le corps scrollable avant rechargement."""
        while self._corps_lay.count():
            item = self._corps_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()