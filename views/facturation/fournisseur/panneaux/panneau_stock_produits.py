"""
Panneau PanneauStockProduits - Panneau latéral glissant pour la gestion du stock.
Responsabilité : Afficher les produits en stock avec navigation par onglets.
Pattern : Component, Container, Composite, Sliding Panel.
"""

import logging
from typing import List, Dict, Any, Optional, Callable
import qtawesome as qta
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QSize
from PySide6.QtGui import QColor, QPainter, QPainterPath, QBrush
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGraphicsDropShadowEffect, QScrollArea,
    QSizePolicy, QStackedWidget, QButtonGroup
)

from ..components.carte_produit_stock import CarteProduitStock
from ..vues.vue_detail_produit import VueDetailProduit
from ..vues.vue_lots_expires import VueLotsExpires
from ..vues.vue_stock_faible import VueStockFaible
from ..styles.facture_styles import FactureStyles
from views.shared.theme_manager import theme_manager


# =============================================================================
# FOND ARRONDI
# =============================================================================
class FondArrondi(QWidget):
    """Widget avec fond et coins arrondis."""
    
    def __init__(self, rayon=20, couleur_fond=FactureStyles.BLANC, parent=None):
        super().__init__(parent)
        self._rayon = rayon
        self._couleur_fond = QColor(couleur_fond)
        self.setAttribute(Qt.WA_TranslucentBackground)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect().adjusted(1, 1, -1, -1),
                            self._rayon, self._rayon)
        painter.fillPath(path, QBrush(self._couleur_fond))
        painter.end()


# =============================================================================
# HELPERS UI
# =============================================================================
def _lbl_vide(texte: str) -> QLabel:
    """Crée un label pour message vide.
    
    Args:
        texte: Texte à afficher
    
    Returns:
        QLabel: Label configuré
    """
    lbl = QLabel(texte)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(FactureStyles.label_vide())
    return lbl


def _scroll_wrap(inner_widget: QWidget) -> QScrollArea:
    """Enveloppe un widget dans un QScrollArea.
    
    Args:
        inner_widget: Widget à envelopper
    
    Returns:
        QScrollArea: Scroll area configurée
    """
    scroll = QScrollArea()
    _bg = theme_manager.colors()['bg_card']
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setStyleSheet(
        f"QScrollArea{{border:none; background:{_bg};}}"
        f"QScrollArea > QWidget{{background:{_bg};}}"
    )
    scroll.verticalScrollBar().setStyleSheet(FactureStyles.scrollbar())
    scroll.setWidget(inner_widget)
    return scroll


# =============================================================================
# BARRE D'ONGLETS
# =============================================================================
class BarreOnglets(QFrame):
    """Barre de navigation à onglets avec badges numériques."""
    
    def __init__(self, onglets: List[Dict[str, str]], parent: Optional[QWidget] = None):
        """
        Initialise la barre d'onglets.
        
        Args:
            onglets: Liste de dictionnaires avec 'key', 'icone', 'label'
            parent: Widget parent Qt
        """
        super().__init__(parent)
        self.setFixedHeight(46)
        _c = theme_manager.colors()
        self.setStyleSheet(
            f"QFrame{{background:{_c['bg_card']}; border:none;"
            f"border-bottom:1px solid {_c['border_light']};}}"
        )
        
        self._boutons = {}
        self._badges = {}
        self._icones = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        
        for idx, onglet in enumerate(onglets):
            key = onglet["key"]
            icone = onglet["icone"]
            label = onglet["label"]
            
            btn = QPushButton(
                qta.icon(icone, color=FactureStyles.GRIS_TEXTE), f"  {label}"
            )
            btn.setCheckable(True)
            btn.setFixedHeight(46)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setStyleSheet(self._style_btn(False))
            btn.setProperty("onglet_key", key)
            
            # Badge numérique
            badge = QLabel("0")
            badge.setFixedSize(18, 18)
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet(
                f"background:{FactureStyles.GRIS_CLAIR}; color:{FactureStyles.GRIS_TEXTE};"
                f"border-radius:9px; font-size:9px; font-weight:700; border:none;"
            )
            badge.hide()
            
            # Conteneur
            conteneur = QWidget()
            conteneur.setStyleSheet("background:transparent;")
            c_lay = QHBoxLayout(conteneur)
            c_lay.setContentsMargins(0, 0, 8, 0)
            c_lay.setSpacing(0)
            c_lay.addWidget(btn)
            c_lay.addWidget(badge)
            
            self._boutons[key] = btn
            self._badges[key] = badge
            self._icones[key] = icone
            self._group.addButton(btn, idx)
            lay.addWidget(conteneur)
        
        # Activer le premier
        list(self._boutons.values())[0].setChecked(True)
        self._mettre_a_jour_styles()
        self._group.buttonClicked.connect(self._on_click)
    
    def _on_click(self, btn: QPushButton) -> None:
        """Gère le clic sur un onglet.
        
        Args:
            btn: Bouton cliqué
        """
        self._mettre_a_jour_styles()
    
    def _mettre_a_jour_styles(self) -> None:
        """Met à jour les styles de tous les boutons et du fond."""
        c = theme_manager.colors()
        self.setStyleSheet(
            f"QFrame{{background:{c['bg_card']}; border:none;"
            f"border-bottom:1px solid {c['border_light']};}}"
        )
        for key, btn in self._boutons.items():
            actif = btn.isChecked()
            btn.setStyleSheet(self._style_btn(actif))
            icon_color = c['primary'] if actif else c['text_muted']
            btn.setIcon(qta.icon(self._icones[key], color=icon_color))
    
    def _style_btn(self, actif: bool) -> str:
        c = theme_manager.colors()
        if actif:
            return (
                f"QPushButton{{"
                f"background:transparent; color:{c['primary']};"
                f"border:none; border-bottom:2px solid {c['primary']};"
                f"font-size:11px; font-weight:700; padding:0 10px;"
                f"}}"
            )
        return (
            f"QPushButton{{"
            f"background:transparent; color:{c['text_muted']};"
            f"border:none; border-bottom:2px solid transparent;"
            f"font-size:11px; font-weight:400; padding:0 10px;"
            f"}}"
            f"QPushButton:hover{{"
            f"color:{c['primary']}; background:{c['bg_input']};"
            f"}}"
        )
    
    def connecter(self, key: str, callback: Callable) -> None:
        """Connecte un callback à un onglet.
        
        Args:
            key: Clé de l'onglet
            callback: Fonction à appeler
        """
        if key in self._boutons:
            self._boutons[key].clicked.connect(callback)
    
    def activer(self, key: str) -> None:
        """Active un onglet par programmation.
        
        Args:
            key: Clé de l'onglet à activer
        """
        if key in self._boutons:
            self._boutons[key].setChecked(True)
            self._mettre_a_jour_styles()
    
    def set_badge(self, key: str, nombre: int) -> None:
        """Met à jour le badge numérique d'un onglet.
        
        Args:
            key: Clé de l'onglet
            nombre: Nombre à afficher
        """
        if key not in self._badges:
            return
        badge = self._badges[key]
        if nombre > 0:
            badge.setText(str(nombre))
            couleur = FactureStyles.ROUGE_SOFT if key in ("expires",) else FactureStyles.VERT_PRINCIPAL
            badge.setStyleSheet(
                f"background:{couleur}; color:{FactureStyles.BLANC};"
                f"border-radius:9px; font-size:9px; font-weight:700; border:none;"
            )
            badge.show()
        else:
            badge.hide()


# =============================================================================
# PANNEAU PRINCIPAL
# =============================================================================
class PanneauStockProduits(FondArrondi):
    """
    Panneau latéral glissant pour la gestion du stock produits.
    
    Onglets :
    1. Stock Produits : Liste des produits avec bouton détail
    2. Détail Produit : Vue détaillée d'un produit avec ses lots
    3. Lots Expirés : Liste des lots expirés
    4. Stock Faible : Liste des produits en stock faible
    """
    
    LARGEUR = 650
    
    def __init__(self, parent: QWidget, ctrl: Any):
        """
        Initialise le panneau.
        
        Args:
            parent: Widget parent
            ctrl: Contrôleur panier
        """
        super().__init__(rayon=20, couleur_fond=FactureStyles.GRIS_FOND, parent=parent)
        self.ctrl = ctrl
        self._ouvert = False
        self._code_session = None
        self.logger = logging.getLogger(__name__)
        
        self._repositionner()
        self._setup_ui()
        self._setup_ombre()

        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

        self.move(parent.width(), self.y())
        self.hide()
    
    def _setup_ui(self) -> None:
        """Configure l'interface du panneau."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # En-tête
        self._header = QFrame()
        self._header.setFixedHeight(62)
        c = theme_manager.colors()
        self._header.setStyleSheet(
            f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {c['primary']},stop:1 {c['primary_hover']});"
            f"border-top-left-radius:20px; border-top-right-radius:20px;"
        )
        h_lay = QHBoxLayout(self._header)
        h_lay.setContentsMargins(20, 0, 16, 0)
        
        self._ic_header = QLabel()
        self._ic_header.setPixmap(
            qta.icon("fa5s.boxes", color=c['text_inverse']).pixmap(QSize(20, 20))
        )
        self._ic_header.setStyleSheet("background:transparent;")
        
        col_h = QVBoxLayout()
        col_h.setSpacing(1)
        self._lbl_titre = QLabel("Gestion du Stock")
        self._lbl_titre.setStyleSheet(
            f"color:{c['text_inverse']}; font-size:14px; font-weight:700; background:transparent;"
        )
        self._lbl_sous_titre = QLabel("Session en cours")
        self._lbl_sous_titre.setStyleSheet(
            f"color:{c['text_inverse']}; opacity:0.7; font-size:11px; background:transparent;"
        )
        col_h.addWidget(self._lbl_titre)
        col_h.addWidget(self._lbl_sous_titre)
        
        self._btn_fermer = QPushButton(qta.icon("fa5s.times", color=c['text_inverse']), "")
        self._btn_fermer.setFixedSize(32, 32)
        self._btn_fermer.setCursor(Qt.PointingHandCursor)
        self._btn_fermer.setStyleSheet(
            f"background:{c['primary_hover']}; border-radius:16px; border:none;"
        )
        self._btn_fermer.clicked.connect(self.fermer)
        
        h_lay.addWidget(self._ic_header)
        h_lay.addSpacing(10)
        h_lay.addLayout(col_h)
        h_lay.addStretch()
        h_lay.addWidget(self._btn_fermer)
        layout.addWidget(self._header)
        
        # Barre d'onglets
        self._barre = BarreOnglets([
            {"key": "stock",    "icone": "fa5s.boxes",              "label": "Stock Produits"},
            {"key": "detail",   "icone": "fa5s.file-alt",           "label": "Détail"},
            {"key": "rupture",  "icone": "fa5s.exclamation-triangle", "label": "Rupture"},
            {"key": "faible",   "icone": "fa5s.exclamation-circle",   "label": "Stock Faible"},
            {"key": "expire",   "icone": "fa5s.skull-crossbones",     "label": "Expirés"},
            {"key": "bientot",  "icone": "fa5s.clock",                "label": "Bientôt"},
        ])
        layout.addWidget(self._barre)
        
        # Stack principal
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background:transparent;")
        
        # Page 0 — Stock Produits
        self._page_stock = QWidget()
        self._page_stock.setStyleSheet("background:transparent;")
        self._lay_stock = QVBoxLayout(self._page_stock)
        self._lay_stock.setContentsMargins(0, 0, 0, 0)
        self._lay_stock.setSpacing(0)
        
        # KPI strip
        self._kpi_strip = QFrame()
        self._kpi_strip.setFixedHeight(40)
        self._kpi_strip.setStyleSheet(f"background:{FactureStyles.VERT_CLAIR}; border:none;")
        kpi_lay = QHBoxLayout(self._kpi_strip)
        kpi_lay.setContentsMargins(16, 0, 12, 0)
        self._ic_kpi = QLabel()
        self._ic_kpi.setPixmap(
            qta.icon("fa5s.boxes", color=FactureStyles.VERT_PRINCIPAL).pixmap(QSize(13, 13))
        )
        self._ic_kpi.setStyleSheet("background:transparent;")
        self._lbl_kpi = QLabel("— produits en stock")
        self._lbl_kpi.setStyleSheet(
            f"color:{FactureStyles.VERT_PRINCIPAL}; font-size:11px; font-weight:600;"
            f"background:transparent;"
        )
        self._btn_refresh = QPushButton(qta.icon("fa5s.sync-alt", color=FactureStyles.VERT_PRINCIPAL), "")
        self._btn_refresh.setFixedSize(26, 26)
        self._btn_refresh.setCursor(Qt.PointingHandCursor)
        self._btn_refresh.setToolTip("Rafraîchir")
        self._btn_refresh.setStyleSheet("background:transparent; border:none; border-radius:6px;")
        self._btn_refresh.clicked.connect(self._rafraichir)
        kpi_lay.addWidget(self._ic_kpi)
        kpi_lay.addSpacing(6)
        kpi_lay.addWidget(self._lbl_kpi)
        kpi_lay.addStretch()
        kpi_lay.addWidget(self._btn_refresh)
        self._lay_stock.addWidget(self._kpi_strip)
        
        # Scroll des cartes
        self._contenu_stock = QWidget()
        self._contenu_stock.setStyleSheet("background:transparent;")
        self._lay_cartes = QVBoxLayout(self._contenu_stock)
        self._lay_cartes.setContentsMargins(16, 12, 16, 16)
        self._lay_cartes.setSpacing(10)
        self._lay_stock.addWidget(_scroll_wrap(self._contenu_stock))
        
        # Page 1 — Détail
        self._vue_detail = VueDetailProduit(
            self.ctrl, on_retour=lambda: self._aller_onglet("stock")
        )
        self._page_detail = _scroll_wrap(self._vue_detail)
        
        # Page 2 — Rupture de stock
        self._page_rupture = QWidget()
        self._page_rupture.setStyleSheet("background:transparent;")
        self._lay_rupture = QVBoxLayout(self._page_rupture)
        self._lay_rupture.setContentsMargins(12, 12, 12, 12)
        self._lay_rupture.setSpacing(8)
        
        # Page 3 — Stock Faible
        self._vue_faible = VueStockFaible()
        self._page_faible = _scroll_wrap(self._vue_faible)
        
        # Page 4 — Expirés
        self._vue_expires = VueLotsExpires()
        self._page_expires = _scroll_wrap(self._vue_expires)
        
        # Page 5 — Bientôt expirés
        self._page_bientot = QWidget()
        self._page_bientot.setStyleSheet("background:transparent;")
        self._lay_bientot = QVBoxLayout(self._page_bientot)
        self._lay_bientot.setContentsMargins(12, 12, 12, 12)
        self._lay_bientot.setSpacing(8)
        
        self._stack.addWidget(self._page_stock)    # index 0
        self._stack.addWidget(self._page_detail)   # index 1
        self._stack.addWidget(_scroll_wrap(self._page_rupture))  # index 2
        self._stack.addWidget(self._page_faible)   # index 3
        self._stack.addWidget(self._page_expires)  # index 4
        self._stack.addWidget(_scroll_wrap(self._page_bientot))  # index 5
        
        # Wrapper arrondi bas
        wrapper = QFrame()
        wrapper.setStyleSheet(
            "background:transparent;"
            "border-bottom-left-radius:20px;"
            "border-bottom-right-radius:20px;"
        )
        w_lay = QVBoxLayout(wrapper)
        w_lay.setContentsMargins(0, 0, 0, 0)
        w_lay.addWidget(self._stack)
        layout.addWidget(wrapper)
        
        # Connexions onglets
        self._barre.connecter("stock",   lambda: self._aller_onglet("stock"))
        self._barre.connecter("detail",  lambda: self._aller_onglet("detail"))
        self._barre.connecter("rupture", lambda: self._aller_onglet("rupture"))
        self._barre.connecter("faible",  lambda: self._aller_onglet("faible"))
        self._barre.connecter("expire",  lambda: self._aller_onglet("expire"))
        self._barre.connecter("bientot", lambda: self._aller_onglet("bientot"))
    
    def apply_theme(self) -> None:
        """Met à jour les couleurs selon le thème actif."""
        c = theme_manager.colors()
        # Fond arrondi
        self._couleur_fond = QColor(c['bg_card'])
        self.update()
        # En-tête
        self._header.setStyleSheet(
            f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {c['primary']},stop:1 {c['primary_hover']});"
            f"border-top-left-radius:20px; border-top-right-radius:20px;"
        )
        self._ic_header.setPixmap(
            qta.icon("fa5s.boxes", color=c['text_inverse']).pixmap(QSize(20, 20))
        )
        self._lbl_titre.setStyleSheet(
            f"color:{c['text_inverse']}; font-size:14px; font-weight:700; background:transparent;"
        )
        self._lbl_sous_titre.setStyleSheet(
            f"color:{c['text_inverse']}; opacity:0.7; font-size:11px; background:transparent;"
        )
        self._btn_fermer.setIcon(qta.icon("fa5s.times", color=c['text_inverse']))
        self._btn_fermer.setStyleSheet(
            f"background:{c['primary_hover']}; border-radius:16px; border:none;"
        )
        # Onglets
        self._barre._mettre_a_jour_styles()
        # KPI strip
        if hasattr(self, '_kpi_strip'):
            self._kpi_strip.setStyleSheet(f"background:{c['success_bg']}; border:none;")
        if hasattr(self, '_ic_kpi'):
            self._ic_kpi.setPixmap(
                qta.icon("fa5s.boxes", color=c['primary']).pixmap(QSize(13, 13))
            )
        if hasattr(self, '_lbl_kpi'):
            self._lbl_kpi.setStyleSheet(
                f"color:{c['primary']}; font-size:11px; font-weight:600; background:transparent;"
            )
        if hasattr(self, '_btn_refresh'):
            self._btn_refresh.setIcon(qta.icon("fa5s.sync-alt", color=c['primary']))
    
    def _setup_ombre(self) -> None:
        """Configure l'ombre du panneau."""
        ombre = QGraphicsDropShadowEffect(self)
        ombre.setBlurRadius(45)
        ombre.setOffset(-10, 0)
        ombre.setColor(QColor(0, 0, 0, 70))
        self.setGraphicsEffect(ombre)
    
    def _aller_onglet(self, key: str) -> None:
        """Change d'onglet.
        
        Args:
            key: Clé de l'onglet cible
        """
        mapping = {
            "stock":   0,
            "detail":  1,
            "rupture": 2,
            "faible":  3,
            "expire":  4,
            "bientot": 5,
        }
        idx = mapping.get(key, 0)
        self._stack.setCurrentIndex(idx)
        self._barre.activer(key)
    
    def _voir_detail(self, code_produit: str, row_apercu: Dict[str, Any]) -> None:
        """Affiche le détail d'un produit.
        
        Args:
            code_produit: Code du produit
            row_apercu: Données d'aperçu du produit
        """
        self._vue_detail.charger(code_produit, self._code_session, row_apercu)
        self._aller_onglet("detail")
    
    def actualiser(self, code_session: str) -> None:
        """Charge les données pour une session.
        
        Args:
            code_session: Code de la session active
        """
        self._code_session = code_session
        self._rafraichir()
    
    def _rafraichir(self) -> None:
        """Rafraîchit les données."""
        if not self._code_session:
            return
        
        # Onglet Stock Produits
        while self._lay_cartes.count():
            item = self._lay_cartes.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        produits = []
        try:
            # ✅ Lire depuis la table stocks (tous les produits approvisionnes)
            # plutôt que panier_facture_four (mouvements = peut être incomplet)
            stock_detaille = self.ctrl.obtenir_stock_detaille(self._code_session, limite=100) or []
            
            for row in stock_detaille:
                code_prod = row.get('code_produit', '')
                if not code_prod:
                    continue
                
                # Récupérer les lots pour calculer valides/expirés
                lots = self.ctrl.lister_lots_par_produit(code_prod, self._code_session) or []
                
                stock_total = row.get('quantite', 0)
                qte_valide = 0
                qte_a_expirer = 0
                qte_expire = 0
                
                for lot in lots:
                    qte = lot.get('stock_lot', 0)
                    statut = lot.get('statut_lot', 'Valide')
                    if statut == 'Expiré':
                        qte_expire += qte
                    elif statut == 'À Expirer':
                        qte_a_expirer += qte
                    else:
                        qte_valide += qte
                
                # Lot le plus proche de l'expiration
                lot_proche = None
                jours_min = float('inf')
                for lot in lots:
                    jours = lot.get('jours_restants', float('inf'))
                    if isinstance(jours, (int, float)) and jours >= 0 and jours < jours_min:
                        jours_min = jours
                        lot_proche = lot
                
                produits.append({
                    "code_produit":  code_prod,
                    "designation":   row.get('designation', 'Produit'),
                    "type":          row.get('type', '—'),
                    "quantite_stock": stock_total,
                    "qte_valide":    qte_valide,
                    "qte_a_expirer": qte_a_expirer,
                    "qte_expire":    qte_expire,
                    "jours_restants": jours_min if jours_min != float('inf') else None,
                    "statut_proche": lot_proche.get('statut_lot', 'Valide') if lot_proche else 'Valide',
                })
            
        except Exception as e:
            self.logger.error(f"Erreur chargement produits: {e}", exc_info=True)
        
        n = len(produits)
        self._lbl_kpi.setText(f"{n} produit{'s' if n > 1 else ''} en stock")
        self._lbl_sous_titre.setText(f"Session · {n} résultat{'s' if n > 1 else ''}")
        self._barre.set_badge("stock", n)
        
        if produits:
            for row in produits:
                carte = CarteProduitStock(
                    row, self.ctrl, on_voir_detail=self._voir_detail
                )
                self._lay_cartes.addWidget(carte)
        else:
            self._lay_cartes.addWidget(_lbl_vide("Aucun produit en stock"))
        
        self._lay_cartes.addStretch()
        
        # Onglet Rupture de stock
        try:
            ruptures = self.ctrl.obtenir_ruptures_stock(self._code_session) or []
            self._afficher_alertes_rupture(ruptures)
            self._barre.set_badge("rupture", len(ruptures))
        except Exception:
            self._afficher_alertes_rupture([])
        
        # Onglet Stock Faible
        try:
            stock_faible = self.ctrl.obtenir_stock_faible(self._code_session, seuil=10) or []
            self._vue_faible.charger(stock_faible)
            self._barre.set_badge("faible", len(stock_faible))
        except Exception:
            self._vue_faible.charger([])
        
        # Onglet Expirés
        try:
            lots_expires = self.ctrl.obtenir_lots_expires(self._code_session) or []
            self._vue_expires.charger(lots_expires)
            self._barre.set_badge("expire", len(lots_expires))
        except Exception:
            self._vue_expires.charger([])
        
        # Onglet Bientôt expirés
        try:
            lots_bientot = self.ctrl.obtenir_lots_a_expirer(self._code_session, jours=30) or []
            self._afficher_alertes_bientot(lots_bientot)
            self._barre.set_badge("bientot", len(lots_bientot))
        except Exception:
            self._afficher_alertes_bientot([])
    
    def _repositionner(self) -> None:
        """Repositionne le panneau."""
        parent = self.parent()
        if parent:
            self.setFixedSize(self.LARGEUR, parent.height())
    
    def ouvrir(self) -> None:
        """Ouvre le panneau avec animation."""
        if self._ouvert:
            return
        self._ouvert = True
        self._repositionner()
        self.show()
        self.raise_()
        pw = self.parent().width()
        debut = QRect(pw, 0, self.LARGEUR, self.height())
        fin = QRect(pw - self.LARGEUR, 0, self.LARGEUR, self.height())
        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(380)
        self._anim.setStartValue(debut)
        self._anim.setEndValue(fin)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()
    
    def fermer(self) -> None:
        """Ferme le panneau avec animation."""
        if not self._ouvert:
            return
        pw = self.parent().width()
        debut = self.geometry()
        fin = QRect(pw, 0, self.LARGEUR, self.height())
        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(300)
        self._anim.setStartValue(debut)
        self._anim.setEndValue(fin)
        self._anim.setEasingCurve(QEasingCurve.InCubic)
        self._anim.finished.connect(self.hide)
        self._anim.finished.connect(lambda: setattr(self, "_ouvert", False))
        self._anim.start()
    
    def basculer(self) -> None:
        """Bascule l'état du panneau."""
        self.fermer() if self._ouvert else self.ouvrir()
    
    def resizeEvent(self, event):
        """Gère le redimensionnement."""
        super().resizeEvent(event)
        if self._ouvert and self.parent():
            pw = self.parent().width()
            self.setGeometry(pw - self.LARGEUR, 0,
                             self.LARGEUR, self.parent().height())
    
    def _afficher_alertes_rupture(self, ruptures: List[Dict[str, Any]]) -> None:
        """Affiche les alertes de rupture de stock.
        
        Args:
            ruptures: Liste des produits en rupture
        """
        # Vider le layout
        while self._lay_rupture.count():
            item = self._lay_rupture.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not ruptures:
            self._lay_rupture.addWidget(_lbl_vide("✅ Aucune rupture de stock"))
            self._lay_rupture.addStretch()
            return
        
        for rupture in ruptures:
            carte = self._creer_carte_alerte(
                libelle=rupture.get('libelle', 'Produit'),
                message="Rupture de stock - Réapprovisionnement urgent",
                quantite=0,
                couleur=FactureStyles.ROUGE_SOFT,
                icone="fa5s.exclamation-triangle"
            )
            self._lay_rupture.addWidget(carte)
        
        self._lay_rupture.addStretch()
    
    def _afficher_alertes_bientot(self, lots: List[Dict[str, Any]]) -> None:
        """Affiche les alertes de lots bientôt expirés.
        
        Args:
            lots: Liste des lots bientôt expirés
        """
        # Vider le layout
        while self._lay_bientot.count():
            item = self._lay_bientot.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not lots:
            self._lay_bientot.addWidget(_lbl_vide("✅ Aucun lot bientôt expiré"))
            self._lay_bientot.addStretch()
            return
        
        for lot in lots:
            jours = lot.get('jours_restants', 0)
            carte = self._creer_carte_alerte(
                libelle=lot.get('libelle', 'Produit'),
                message=f"Expire dans {jours} jour{'s' if jours > 1 else ''}",
                quantite=lot.get('stock_lot', 0),
                couleur=FactureStyles.ORANGE_SOFT,
                icone="fa5s.clock"
            )
            self._lay_bientot.addWidget(carte)
        
        self._lay_bientot.addStretch()
    
    def _creer_carte_alerte(self, libelle: str, message: str, quantite: int, couleur: str, icone: str) -> QFrame:
        """Crée une carte d'alerte."""
        from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
        
        carte = QFrame()
        carte.setStyleSheet(
            f"QFrame{{background:{FactureStyles.BLANC}; border-radius:10px;}}"
        )
        carte.setFixedHeight(80)
        
        layout = QHBoxLayout(carte)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)
        
        # Icône
        icone_container = QFrame()
        icone_container.setFixedSize(50, 50)
        icone_container.setStyleSheet(f"background:{couleur}20; border-radius:25px;")
        ic_lay = QVBoxLayout(icone_container)
        ic_lay.setContentsMargins(0, 0, 0, 0)
        
        ic = QLabel()
        ic.setPixmap(qta.icon(icone, color=couleur).pixmap(QSize(24, 24)))
        ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet("background:transparent;")
        ic_lay.addWidget(ic)
        
        layout.addWidget(icone_container)
        
        # Informations
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        titre = QLabel(libelle)
        titre.setStyleSheet(
            f"color:{theme_manager.colors()['text_primary']}; font-size:12px; font-weight:700; background:transparent;"
        )
        titre.setWordWrap(True)
        info_layout.addWidget(titre)
        
        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet(
            f"color:{FactureStyles.GRIS_TEXTE}; font-size:10px; background:transparent;"
        )
        msg_lbl.setWordWrap(True)
        info_layout.addWidget(msg_lbl)
        
        badge = QLabel(f"{quantite} unités")
        badge.setStyleSheet(
            f"background:{couleur}20; color:{couleur}; "
            f"border-radius:8px; padding:2px 8px; font-size:9px; font-weight:700;"
        )
        badge.setFixedHeight(18)
        info_layout.addWidget(badge)
        
        layout.addLayout(info_layout, 1)
        
        return carte
    
    def obtenir_nombre_total_alertes(self) -> int:
        """Retourne le nombre total d'alertes (pour le badge de notification)."""
        if not self._code_session:
            return 0
        
        try:
            ruptures = len(self.ctrl.obtenir_ruptures_stock(self._code_session) or [])
            faibles = len(self.ctrl.obtenir_stock_faible(self._code_session, seuil=10) or [])
            expires = len(self.ctrl.obtenir_lots_expires(self._code_session) or [])
            bientot = len(self.ctrl.obtenir_lots_a_expirer(self._code_session, jours=30) or [])
            return ruptures + faibles + expires + bientot
        except Exception:
            return 0
