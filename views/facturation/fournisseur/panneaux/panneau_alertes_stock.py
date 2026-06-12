"""
Panneau PanneauAlertesStock - Panneau latéral glissant pour les alertes de stock.
Responsabilité : Afficher les alertes de rupture, stock faible et expiration.
Pattern : Component, Container, Composite, Sliding Panel.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QSize
from PySide6.QtGui import QColor, QPainter, QPainterPath, QBrush
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGraphicsDropShadowEffect, QScrollArea,
    QSizePolicy, QStackedWidget, QButtonGroup
)

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
def _lbl_vide(texte):
    """Crée un label pour message vide."""
    lbl = QLabel(texte)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(
        f"color:{FactureStyles.GRIS_TEXTE}; font-style:italic; "
        f"font-size:11px; background:transparent; padding:20px;"
    )
    return lbl


def _scroll_wrap(inner_widget):
    """Enveloppe un widget dans un QScrollArea."""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    _bg = theme_manager.colors()['bg_card']
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setStyleSheet(
        f"QScrollArea{{border:none; background:{_bg};}}"
        f"QScrollArea > QWidget{{background:{_bg};}}"
    )
    scroll.verticalScrollBar().setStyleSheet(FactureStyles.scrollbar())
    scroll.setWidget(inner_widget)
    return scroll


# =============================================================================
# CARTE D'ALERTE
# =============================================================================
class CarteAlerte(QFrame):
    """Carte d'alerte pour un produit."""
    
    def __init__(self, alerte_data: dict, parent=None):
        super().__init__(parent)
        self.data = alerte_data
        self.type_alerte = alerte_data.get('type', 'info')  # rupture, faible, expire
        
        self.setStyleSheet(
            f"QFrame{{background:{FactureStyles.BLANC}; border-radius:10px; "
            f"border-left:4px solid {self._get_couleur_type()};}}"
        )
        self.setFixedHeight(80)
        
        self._setup_ui()
    
    def _get_couleur_type(self):
        """Retourne la couleur selon le type d'alerte."""
        couleurs = {
            'rupture': FactureStyles.ROUGE_SOFT,
            'faible': FactureStyles.ORANGE_SOFT,
            'expire': FactureStyles.ROUGE_SOFT,
            'bientot': FactureStyles.ORANGE_SOFT
        }
        return couleurs.get(self.type_alerte, FactureStyles.GRIS_TEXTE)
    
    def _get_icone_type(self):
        """Retourne l'icône selon le type d'alerte."""
        icones = {
            'rupture': 'fa5s.exclamation-triangle',
            'faible': 'fa5s.exclamation-circle',
            'expire': 'fa5s.skull-crossbones',
            'bientot': 'fa5s.clock'
        }
        return icones.get(self.type_alerte, 'fa5s.info-circle')
    
    def _setup_ui(self):
        """Configure l'interface de la carte."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)
        
        # Icône d'alerte
        icone_container = QFrame()
        icone_container.setFixedSize(50, 50)
        icone_container.setStyleSheet(
            f"background:{self._get_couleur_type()}20; border-radius:25px;"
        )
        ic_lay = QVBoxLayout(icone_container)
        ic_lay.setContentsMargins(0, 0, 0, 0)
        
        ic = QLabel()
        ic.setPixmap(
            qta.icon(self._get_icone_type(), color=self._get_couleur_type()).pixmap(QSize(24, 24))
        )
        ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet("background:transparent;")
        ic_lay.addWidget(ic)
        
        layout.addWidget(icone_container)
        
        # Informations
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # Titre
        titre = QLabel(self.data.get('libelle', 'Produit'))
        titre.setStyleSheet(
            f"color:{theme_manager.colors()['text_primary']}; font-size:12px; font-weight:700; background:transparent;"
        )
        titre.setWordWrap(True)
        info_layout.addWidget(titre)
        
        # Message
        message = self._get_message()
        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet(
            f"color:{FactureStyles.GRIS_TEXTE}; font-size:10px; background:transparent;"
        )
        msg_lbl.setWordWrap(True)
        info_layout.addWidget(msg_lbl)
        
        # Badge quantité
        qte = self.data.get('quantite_actuelle', 0)
        badge = QLabel(f"{qte} unités")
        badge.setStyleSheet(
            f"background:{self._get_couleur_type()}20; color:{self._get_couleur_type()}; "
            f"border-radius:8px; padding:2px 8px; font-size:9px; font-weight:700;"
        )
        badge.setFixedHeight(18)
        info_layout.addWidget(badge)
        
        layout.addLayout(info_layout, 1)
    
    def _get_message(self):
        """Génère le message d'alerte."""
        type_alerte = self.type_alerte
        qte = self.data.get('quantite_actuelle', 0)
        
        if type_alerte == 'rupture':
            return "⚠️ Rupture de stock - Réapprovisionnement urgent"
        elif type_alerte == 'faible':
            return f"⚠️ Stock faible - Seuil critique atteint"
        elif type_alerte == 'expire':
            jours = self.data.get('jours_restants', 0)
            return f"❌ Produit expiré depuis {abs(jours)} jours"
        elif type_alerte == 'bientot':
            jours = self.data.get('jours_restants', 0)
            return f"⏰ Expire dans {jours} jours"
        return "Information"


# =============================================================================
# BARRE D'ONGLETS
# =============================================================================
class BarreOnglets(QFrame):
    """Barre de navigation à onglets avec badges numériques."""
    
    def __init__(self, onglets: list, parent=None):
        super().__init__(parent)
        self.setFixedHeight(46)
        self.setStyleSheet(
            f"QFrame{{background:{FactureStyles.BLANC}; border:none;"
            f"border-bottom:1px solid {FactureStyles.GRIS_CLAIR};}}"
        )
        
        self._boutons = {}
        self._badges = {}
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
            self._group.addButton(btn, idx)
            lay.addWidget(conteneur)
        
        # Activer le premier
        list(self._boutons.values())[0].setChecked(True)
        self._mettre_a_jour_styles()
        self._group.buttonClicked.connect(self._on_click)
    
    def _on_click(self, btn):
        self._mettre_a_jour_styles()

    def _mettre_a_jour_styles(self) -> None:
        """Met à jour les styles du fond et de tous les boutons."""
        c = theme_manager.colors()
        self.setStyleSheet(
            f"QFrame{{background:{c['bg_card']}; border:none;"
            f"border-bottom:1px solid {c['border_light']};}}"
        )
        for key, btn in self._boutons.items():
            btn.setStyleSheet(self._style_btn(btn.isChecked()))
    
    def _style_btn(self, actif: bool) -> str:
        if actif:
            return (
                f"QPushButton{{"
                f"background:transparent; color:{FactureStyles.VERT_PRINCIPAL};"
                f"border:none; border-bottom:2px solid {FactureStyles.VERT_PRINCIPAL};"
                f"font-size:11px; font-weight:700; padding:0 10px;"
                f"}}"
            )
        return (
            f"QPushButton{{"
            f"background:transparent; color:{FactureStyles.GRIS_TEXTE};"
            f"border:none; border-bottom:2px solid transparent;"
            f"font-size:11px; font-weight:400; padding:0 10px;"
            f"}}"
            f"QPushButton:hover{{"
            f"color:{FactureStyles.VERT_PRINCIPAL}; background:{theme_manager.colors()['hover']};"
            f"}}"
        )
    
    def connecter(self, key: str, callback):
        """Connecte un callback à un onglet."""
        if key in self._boutons:
            self._boutons[key].clicked.connect(callback)
    
    def activer(self, key: str):
        """Active un onglet par programmation."""
        if key in self._boutons:
            self._boutons[key].setChecked(True)
            self._mettre_a_jour_styles()
    
    def set_badge(self, key: str, nombre: int):
        """Met à jour le badge numérique d'un onglet."""
        if key not in self._badges:
            return
        badge = self._badges[key]
        if nombre > 0:
            badge.setText(str(nombre))
            couleur = FactureStyles.ROUGE_SOFT if key in ("rupture", "expire") else FactureStyles.ORANGE_SOFT
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
class PanneauAlertesStock(FondArrondi):
    """
    Panneau latéral glissant pour les alertes de stock.
    
    Onglets :
    1. Rupture : Produits à 0
    2. Stock Faible : Produits sous le seuil
    3. Expirés : Lots expirés
    4. Bientôt : Lots bientôt expirés
    """
    
    LARGEUR = 420
    
    def __init__(self, parent: QWidget, ctrl):
        super().__init__(rayon=20, couleur_fond=FactureStyles.BLANC, parent=parent)
        self.ctrl = ctrl
        self._ouvert = False
        self._code_session = None
        
        self._repositionner()
        self._setup_ui()
        self._setup_ombre()

        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

        self.move(parent.width(), self.y())
        self.hide()
    
    def _setup_ui(self):
        """Configure l'interface du panneau."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # En-tête
        header = QFrame()
        header.setFixedHeight(62)
        header.setStyleSheet(
            f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {FactureStyles.ROUGE_SOFT},stop:1 {theme_manager.colors()['danger']});"
            f"border-top-left-radius:20px; border-top-right-radius:20px;"
        )
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(20, 0, 16, 0)
        
        ic_h = QLabel()
        ic_h.setPixmap(
            qta.icon("fa5s.bell", color=FactureStyles.BLANC).pixmap(QSize(20, 20))
        )
        ic_h.setStyleSheet("background:transparent;")
        
        col_h = QVBoxLayout()
        col_h.setSpacing(1)
        t1 = QLabel("Alertes de Stock")
        t1.setStyleSheet(
            f"color:{FactureStyles.BLANC}; font-size:14px; font-weight:700; background:transparent;"
        )
        self._lbl_sous_titre = QLabel("Notifications en temps réel")
        self._lbl_sous_titre.setStyleSheet(
            f"color:rgba(255,255,255,0.70); font-size:11px; background:transparent;"
        )
        col_h.addWidget(t1)
        col_h.addWidget(self._lbl_sous_titre)
        
        btn_fermer = QPushButton(qta.icon("fa5s.times", color=FactureStyles.BLANC), "")
        btn_fermer.setFixedSize(32, 32)
        btn_fermer.setCursor(Qt.PointingHandCursor)
        btn_fermer.setStyleSheet(
            "background:rgba(255,255,255,0.18); border-radius:16px; border:none;"
        )
        btn_fermer.clicked.connect(self.fermer)
        
        h_lay.addWidget(ic_h)
        h_lay.addSpacing(10)
        h_lay.addLayout(col_h)
        h_lay.addStretch()
        h_lay.addWidget(btn_fermer)
        layout.addWidget(header)
        
        # Barre d'onglets
        self._barre = BarreOnglets([
            {"key": "rupture", "icone": "fa5s.exclamation-triangle", "label": "Rupture"},
            {"key": "faible",  "icone": "fa5s.exclamation-circle",   "label": "Stock Faible"},
            {"key": "expire",  "icone": "fa5s.skull-crossbones",     "label": "Expirés"},
            {"key": "bientot", "icone": "fa5s.clock",                "label": "Bientôt"},
        ])
        layout.addWidget(self._barre)
        
        # Stack principal
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background:transparent;")
        
        # Pages
        self._pages = {}
        self._layouts = {}
        
        for key in ["rupture", "faible", "expire", "bientot"]:
            page = QWidget()
            page.setStyleSheet("background:transparent;")
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(12, 12, 12, 12)
            page_layout.setSpacing(8)
            
            self._pages[key] = page
            self._layouts[key] = page_layout
            self._stack.addWidget(_scroll_wrap(page))
        
        layout.addWidget(self._stack)
        
        # Connexions onglets
        self._barre.connecter("rupture", lambda: self._aller_onglet("rupture"))
        self._barre.connecter("faible",  lambda: self._aller_onglet("faible"))
        self._barre.connecter("expire",  lambda: self._aller_onglet("expire"))
        self._barre.connecter("bientot", lambda: self._aller_onglet("bientot"))
    
    def _setup_ombre(self):
        """Configure l'ombre du panneau."""
        ombre = QGraphicsDropShadowEffect(self)
        ombre.setBlurRadius(45)
        ombre.setOffset(-10, 0)
        ombre.setColor(QColor(0, 0, 0, 70))
        self.setGraphicsEffect(ombre)
    
    def _aller_onglet(self, key: str):
        """Change d'onglet."""
        mapping = {"rupture": 0, "faible": 1, "expire": 2, "bientot": 3}
        idx = mapping.get(key, 0)
        self._stack.setCurrentIndex(idx)
        self._barre.activer(key)
    
    def actualiser(self, code_session: str):
        """Charge les alertes pour une session."""
        self._code_session = code_session
        self._rafraichir()
    
    def _rafraichir(self):
        """Rafraîchit les données."""
        if not self._code_session:
            return
        
        # Vider tous les layouts
        for key, lay in self._layouts.items():
            while lay.count():
                item = lay.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        
        try:
            # 1. Ruptures de stock
            ruptures = self.ctrl.obtenir_ruptures_stock(self._code_session) or []
            self._afficher_alertes("rupture", ruptures, "rupture")
            self._barre.set_badge("rupture", len(ruptures))
            
            # 2. Stock faible
            faibles = self.ctrl.obtenir_stock_faible(self._code_session, seuil=10) or []
            self._afficher_alertes("faible", faibles, "faible")
            self._barre.set_badge("faible", len(faibles))
            
            # 3. Lots expirés
            expires = self.ctrl.obtenir_lots_expires(self._code_session) or []
            self._afficher_alertes("expire", expires, "expire")
            self._barre.set_badge("expire", len(expires))
            
            # 4. Lots bientôt expirés
            bientot = self.ctrl.obtenir_lots_a_expirer(self._code_session, jours=30) or []
            self._afficher_alertes("bientot", bientot, "bientot")
            self._barre.set_badge("bientot", len(bientot))
            
            # Mettre à jour le sous-titre
            total = len(ruptures) + len(faibles) + len(expires) + len(bientot)
            self._lbl_sous_titre.setText(f"{total} alerte{'s' if total > 1 else ''} active{'s' if total > 1 else ''}")
            
        except Exception as e:
            print(f"[PanneauAlertesStock] Erreur rafraîchissement: {e}")
            import traceback
            traceback.print_exc()
    
    def _afficher_alertes(self, key: str, alertes: list, type_alerte: str):
        """Affiche les alertes dans un onglet."""
        lay = self._layouts[key]
        
        if not alertes:
            lay.addWidget(_lbl_vide("Aucune alerte pour le moment"))
            lay.addStretch()
            return
        
        for alerte in alertes:
            data = {
                'type': type_alerte,
                'libelle': alerte.get('libelle', 'Produit'),
                'quantite_actuelle': alerte.get('quantite_actuelle') or alerte.get('stock_lot', 0),
                'jours_restants': alerte.get('jours_restants', 0)
            }
            carte = CarteAlerte(data)
            lay.addWidget(carte)
        
        lay.addStretch()
    
    def obtenir_nombre_total_alertes(self) -> int:
        """Retourne le nombre total d'alertes."""
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
    
    def _repositionner(self):
        """Repositionne le panneau."""
        parent = self.parent()
        if parent:
            self.setFixedSize(self.LARGEUR, parent.height())
    
    def ouvrir(self):
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
    
    def fermer(self):
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
    
    def basculer(self):
        """Bascule l'état du panneau."""
        self.fermer() if self._ouvert else self.ouvrir()
    
    def apply_theme(self) -> None:
        """Met à jour les couleurs selon le thème actif."""
        c = theme_manager.colors()
        # Fond arrondi peint via QPainter
        self._couleur_fond = QColor(c['bg_card'])
        self.update()
        # Barre d'onglets
        if hasattr(self, '_barre'):
            self._barre.setStyleSheet(
                f"QFrame{{background:{c['bg_card']}; border:none;"
                f"border-bottom:1px solid {c['border_light']};}}"
            )
            self._barre._mettre_a_jour_styles()

    def resizeEvent(self, event):
        """Gère le redimensionnement."""
        super().resizeEvent(event)
        if self._ouvert and self.parent():
            pw = self.parent().width()
            self.setGeometry(pw - self.LARGEUR, 0,
                             self.LARGEUR, self.parent().height())
