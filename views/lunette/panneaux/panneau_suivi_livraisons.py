import qtawesome as qta
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QSize
from PySide6.QtGui import QColor, QPainter, QPainterPath, QBrush
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGraphicsDropShadowEffect, QScrollArea,
    QSizePolicy, QStackedWidget, QButtonGroup
)

# Imports des modules séparés
from ..composants.carte_commande_attente import CarteCommandeAttente
from ..vues.vue_detail_commande import VueDetailCommande
from ..vues.vue_commandes_multiples import VueCommandesMultiples
from ..vues.vue_derniere_commande import VueDerniereCommande
from views.shared.theme_manager import theme_manager


# =============================================================================
# PALETTE CLINIQUE (dynamique depuis theme_manager)
# =============================================================================
def _c():
    return theme_manager.colors()


def _palette_from_theme():
    """Return palette color dict from theme_manager."""
    c = theme_manager.colors()
    return {
        'VERT_FONCE': c['primary'], 'VERT_CLAIR': c['success_bg'],
        'VERT_MED': c['success'], 'BLANC': c['bg_card'],
        'GRIS_FOND': c['bg_main'], 'GRIS_TEXTE': c['text_secondary'],
        'GRIS_CLAIR': c['border'], 'BLEU_SOFT': c['info'],
        'BLEU_CLAIR': c['primary_light'], 'ORANGE_SOFT': c['warning'],
        'ORANGE_CLAIR': c['warning_bg'], 'ROUGE_SOFT': c['danger'],
        'ROUGE_CLAIR': c['danger_bg'], 'VIOLET_SOFT': c['accent'],
        'VIOLET_CLAIR': c['primary_light'],
    }


# =============================================================================
# FOND ARRONDI
# =============================================================================
class FondArrondi(QWidget):
    """Widget avec fond arrondi peint manuellement, couleur pilotée par le thème."""

    def __init__(self, rayon=20, couleur_cle="bg_main", parent=None):
        super().__init__(parent)
        self._rayon      = rayon
        self._couleur_cle = couleur_cle
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect().adjusted(1, 1, -1, -1),
                            self._rayon, self._rayon)
        painter.fillPath(path, QBrush(QColor(_c()[self._couleur_cle])))
        painter.end()


# =============================================================================
# HELPERS UI
# =============================================================================
def _sep(couleur=None):
    c = _c()
    if couleur is None:
        couleur = c['border']
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background:{couleur}; border:none;")
    return f


def _fmt_date(val):
    if val and hasattr(val, "strftime"):
        return val.strftime("%d/%m/%Y")
    return str(val) if val else "—"


def _row_ic_val(icone_name, valeur,
                couleur_ic=None, couleur_val=None, gras=False):
    c = _c()
    if couleur_ic is None:
        couleur_ic = c['text_secondary']
    if couleur_val is None:
        couleur_val = c['text_secondary']
    w   = QWidget()
    w.setStyleSheet(f"background:{c['bg_card']};")
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(5)
    ic  = QLabel()
    ic.setPixmap(qta.icon(icone_name, color=couleur_ic).pixmap(QSize(11, 11)))
    ic.setStyleSheet(f"background:{c['bg_card']}; border:none;")
    lbl = QLabel(str(valeur) if valeur else "—")
    poids = "700" if gras else "400"
    lbl.setStyleSheet(
        f"color:{couleur_val}; font-size:11px; font-weight:{poids};"
        f"background:{c['bg_card']}; border:none;"
    )
    lbl.setWordWrap(True)
    lay.addWidget(ic)
    lay.addWidget(lbl)
    lay.addStretch()
    return w


def _lbl_vide(texte):
    lbl = QLabel(texte)
    lbl.setAlignment(Qt.AlignCenter)
    c = _c()
    lbl.setStyleSheet(
        f"color:{c['text_secondary']}; font-size:11px; background:{c['bg_card']};"
    )
    return lbl


def _scroll_wrap(inner_widget):
    """Enveloppe un widget dans un QScrollArea propre."""
    c = _c()
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setStyleSheet(
        f"QScrollArea{{border:none; background:{c['bg_main']};}}"
        f"QScrollBar:vertical{{border:none;background:{c['bg_main']};"
        "width:5px;border-radius:2px;}"
        f"QScrollBar::handle:vertical{{background:{c['border']};border-radius:2px;}}"
        "QScrollBar::add-line:vertical,"
        "QScrollBar::sub-line:vertical{height:0;}"
    )
    scroll.setWidget(inner_widget)
    return scroll


# =============================================================================
# BARRE D'ONGLETS PERSONNALISÉE
# =============================================================================
class BarreOnglets(QFrame):
    """
    Barre de navigation à onglets avec badges numériques.
    """

    def __init__(self, onglets: list, parent=None):
        """
        onglets = [
            {"key": "livraisons", "icone": "fa5s.truck",       "label": "Livraisons"},
            {"key": "multiples",  "icone": "fa5s.copy",        "label": "Multiples"},
            {"key": "historique", "icone": "fa5s.history",     "label": "Historique"},
        ]
        """
        super().__init__(parent)
        self.setFixedHeight(46)
        c = _c()
        self.setStyleSheet(
            f"QFrame{{background:{c['bg_card']}; border:none;"
            f"border-bottom:1px solid {c['border']};}}"
        )

        self._boutons  = {}
        self._badges   = {}
        self._group    = QButtonGroup(self)
        self._group.setExclusive(True)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        for idx, onglet in enumerate(onglets):
            key   = onglet["key"]
            icone = onglet["icone"]
            label = onglet["label"]

            btn = QPushButton(
                qta.icon(icone, color=c['text_secondary']), f"  {label}")
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
                f"background:{c['border']}; color:{c['text_secondary']};"
                f"border-radius:9px; font-size:9px; font-weight:700; border:none;"
            )
            badge.hide()

            # Conteneur bouton + badge
            conteneur = QWidget()
            conteneur.setStyleSheet(f"background:{_c()['bg_card']};")
            c_lay = QHBoxLayout(conteneur)
            c_lay.setContentsMargins(0, 0, 8, 0)
            c_lay.setSpacing(0)
            c_lay.addWidget(btn)
            c_lay.addWidget(badge)

            self._boutons[key] = btn
            self._badges[key]  = badge
            self._group.addButton(btn, idx)
            lay.addWidget(conteneur)

        # Activer le premier par défaut
        list(self._boutons.values())[0].setChecked(True)
        self._mettre_a_jour_styles()
        self._group.buttonClicked.connect(self._on_click)

    def _on_click(self, btn):
        self._mettre_a_jour_styles()

    def _mettre_a_jour_styles(self):
        for key, btn in self._boutons.items():
            actif = btn.isChecked()
            btn.setStyleSheet(self._style_btn(actif))
            if actif:
                icone_name = btn.icon()
                # Re-colorer l'icône active
                for onglet_key, b in self._boutons.items():
                    pass  # styles gérés par stylesheet

    def _style_btn(self, actif: bool) -> str:
        c = _c()
        if actif:
            return (
                f"QPushButton{{"
                f"background:{c['bg_card']}; color:{c['primary']};"
                f"border:none; border-bottom:2px solid {c['primary']};"
                f"font-size:11px; font-weight:700; padding:0 10px;"
                f"}}"
            )
        return (
            f"QPushButton{{"
            f"background:{c['bg_card']}; color:{c['text_secondary']};"
            f"border:none; border-bottom:2px solid transparent;"
            f"font-size:11px; font-weight:400; padding:0 10px;"
            f"}}"
            f"QPushButton:hover{{"
            f"color:{c['primary']}; background:{c['hover']};"
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
            c = _c()
            couleur = c['danger'] if key in ("multiples",) else c['primary']
            badge.setStyleSheet(
                f"background:{couleur}; color:{c['text_inverse']};"
                f"border-radius:9px; font-size:9px; font-weight:700; border:none;"
            )
            badge.show()
        else:
            badge.hide()





# =============================================================================
# PANNEAU PRINCIPAL GLISSANT
# =============================================================================
class PanneauSuiviLivraisons(FondArrondi):
    """
    Panneau latéral glissant — navigation par onglets.
    Onglet 1 : Livraisons en attente (→ onglet Détail au clic sur une carte)
    Onglet 2 : Détail commande (inline, sans modal)
    Onglet 3 : Commandes multiples (anomalies)
    Onglet 4 : Dernière commande par patient
    """

    LARGEUR = 490

    def __init__(self, parent: QWidget, ctrl):
        super().__init__(rayon=20, couleur_cle="bg_main", parent=parent)
        self.ctrl          = ctrl
        self._ouvert       = False
        self._code_session = None

        self._repositionner()
        self._setup_ui()
        self._setup_ombre()

        theme_manager.theme_changed.connect(self._on_theme_change)

        self.move(parent.width(), self.y())
        self.hide()

    def _on_theme_change(self):
        """Réaction au changement de thème — mise à jour in-place."""
        self._apply_theme_styles()
        self.update()
        if self._code_session:
            self._rafraichir()

    # -------------------------------------------------------------------------
    # CONSTRUCTION UI
    # -------------------------------------------------------------------------
    def _setup_ui(self):
        c = _c()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── En-tête ──
        self._header = QFrame()
        self._header.setObjectName("suivi_header")
        self._header.setFixedHeight(62)
        h_lay = QHBoxLayout(self._header)
        h_lay.setContentsMargins(20, 0, 16, 0)

        self._ic_header = QLabel()
        self._ic_header.setStyleSheet("background:transparent;")

        col_h = QVBoxLayout()
        col_h.setSpacing(1)
        self._titre = QLabel("Suivi des Livraisons")
        self._lbl_sous_titre = QLabel("Session en cours")
        col_h.addWidget(self._titre)
        col_h.addWidget(self._lbl_sous_titre)

        self._btn_fermer = QPushButton()
        self._btn_fermer.setFixedSize(32, 32)
        self._btn_fermer.setCursor(Qt.PointingHandCursor)
        self._btn_fermer.setStyleSheet(
            "background:rgba(255,255,255,0.18); border-radius:16px; border:none;"
        )
        self._btn_fermer.clicked.connect(self.fermer)

        h_lay.addWidget(self._ic_header)
        h_lay.addSpacing(10)
        h_lay.addLayout(col_h)
        h_lay.addStretch()
        h_lay.addWidget(self._btn_fermer)
        layout.addWidget(self._header)

        # ── Barre d'onglets ──
        self._barre = BarreOnglets([
            {"key": "livraisons", "icone": "fa5s.truck",               "label": "Livraisons"},
            {"key": "detail",     "icone": "fa5s.file-alt",            "label": "Détail"},
            {"key": "multiples",  "icone": "fa5s.exclamation-triangle","label": "Multiples"},
            {"key": "historique", "icone": "fa5s.history",             "label": "Historique"},
        ])
        layout.addWidget(self._barre)

        # ── Stack principal ──
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background:{_c()['bg_main']};")

        # Page 0 — Livraisons
        self._page_livraisons = QWidget()
        self._page_livraisons.setStyleSheet(f"background:{_c()['bg_main']};")
        self._lay_livraisons = QVBoxLayout(self._page_livraisons)
        self._lay_livraisons.setContentsMargins(0, 0, 0, 0)
        self._lay_livraisons.setSpacing(0)
        # KPI strip
        self._kpi_strip = QFrame()
        self._kpi_strip.setFixedHeight(40)
        kpi_lay = QHBoxLayout(self._kpi_strip)
        kpi_lay.setContentsMargins(16, 0, 12, 0)
        self._ic_kpi = QLabel()
        self._ic_kpi.setStyleSheet("background:transparent;")
        self._lbl_kpi = QLabel("— en attente")
        self._btn_refresh = QPushButton()
        self._btn_refresh.setFixedSize(26, 26)
        self._btn_refresh.setCursor(Qt.PointingHandCursor)
        self._btn_refresh.setToolTip("Rafraîchir")
        self._btn_refresh.setStyleSheet(
            f"background:{_c()['bg_card']}; border:none; border-radius:6px;")
        self._btn_refresh.clicked.connect(self._rafraichir)
        kpi_lay.addWidget(self._ic_kpi)
        kpi_lay.addSpacing(6)
        kpi_lay.addWidget(self._lbl_kpi)
        kpi_lay.addStretch()
        kpi_lay.addWidget(self._btn_refresh)
        self._lay_livraisons.addWidget(self._kpi_strip)
        # Scroll des cartes
        self._contenu_liv = QWidget()
        self._contenu_liv.setStyleSheet(f"background:{_c()['bg_card']};")
        self._lay_cartes = QVBoxLayout(self._contenu_liv)
        self._lay_cartes.setContentsMargins(16, 12, 16, 16)
        self._lay_cartes.setSpacing(10)
        self._scroll_cartes = _scroll_wrap(self._contenu_liv)
        self._lay_livraisons.addWidget(self._scroll_cartes)

        # Page 1 — Détail
        self._vue_detail = VueDetailCommande(
            self.ctrl, on_retour=lambda: self._aller_onglet("livraisons"))
        self._page_detail = _scroll_wrap(self._vue_detail)

        # Page 2 — Multiples
        self._vue_multiples = VueCommandesMultiples()
        self._page_multiples = _scroll_wrap(self._vue_multiples)

        # Page 3 — Historique
        self._vue_historique = VueDerniereCommande()
        self._page_historique = _scroll_wrap(self._vue_historique)

        self._stack.addWidget(self._page_livraisons)  # index 0
        self._stack.addWidget(self._page_detail)      # index 1
        self._stack.addWidget(self._page_multiples)   # index 2
        self._stack.addWidget(self._page_historique)  # index 3

        # Wrapper arrondi bas
        wrapper = QFrame()
        wrapper.setStyleSheet(
            f"background:{_c()['bg_card']};"
            "border-bottom-left-radius:20px;"
            "border-bottom-right-radius:20px;"
        )
        w_lay = QVBoxLayout(wrapper)
        w_lay.setContentsMargins(0, 0, 0, 0)
        w_lay.addWidget(self._stack)
        layout.addWidget(wrapper)

        # ── Connexions onglets ──
        self._barre.connecter("livraisons", lambda: self._aller_onglet("livraisons"))
        self._barre.connecter("detail",     lambda: self._aller_onglet("detail"))
        self._barre.connecter("multiples",  lambda: self._aller_onglet("multiples"))
        self._barre.connecter("historique", lambda: self._aller_onglet("historique"))

        # Appliquer le thème initial
        self._apply_theme_styles()

    def _setup_ombre(self):
        ombre = QGraphicsDropShadowEffect(self)
        ombre.setBlurRadius(45)
        ombre.setOffset(-10, 0)
        ombre.setColor(QColor(0, 0, 0, 70))
        self.setGraphicsEffect(ombre)

    # -------------------------------------------------------------------------
    # THÈME — mise à jour in-place
    # -------------------------------------------------------------------------
    def _apply_theme_styles(self):
        """Applique les couleurs du thème courant sur tous les éléments fixes."""
        c = _c()

        # En-tête — sélecteur #id pour forcer le repaint du gradient
        self._header.setStyleSheet(
            f"#suivi_header{{"
            f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {c['primary']},stop:1 {c['primary_hover']});"
            f"border-top-left-radius:20px;border-top-right-radius:20px;"
            f"}}"
        )
        self._header.style().unpolish(self._header)
        self._header.style().polish(self._header)
        self._header.update()

        self._ic_header.setPixmap(
            qta.icon("fa5s.shipping-fast", color=c['text_inverse']).pixmap(QSize(20, 20)))
        self._titre.setStyleSheet(
            f"color:{c['text_inverse']}; font-size:14px; font-weight:700; background:transparent;"
        )
        self._lbl_sous_titre.setStyleSheet(
            f"color:rgba(255,255,255,0.70); font-size:11px; background:transparent;"
        )
        self._btn_fermer.setIcon(qta.icon("fa5s.times", color=c['text_inverse']))

        # KPI strip
        self._kpi_strip.setStyleSheet(
            f"background:{c['success_bg']}; border:none;")
        self._ic_kpi.setPixmap(
            qta.icon("fa5s.boxes", color=c['primary']).pixmap(QSize(13, 13)))
        self._lbl_kpi.setStyleSheet(
            f"color:{c['primary']}; font-size:11px; font-weight:600;"
            f"background:transparent;"
        )
        self._btn_refresh.setIcon(
            qta.icon("fa5s.sync-alt", color=c['primary']))

        # Barre d'onglets
        self._barre._mettre_a_jour_styles()

    # -------------------------------------------------------------------------
    # NAVIGATION ONGLETS
    # -------------------------------------------------------------------------
    def _aller_onglet(self, key: str):
        mapping = {
            "livraisons": 0,
            "detail":     1,
            "multiples":  2,
            "historique": 3,
        }
        idx = mapping.get(key, 0)
        self._stack.setCurrentIndex(idx)
        self._barre.activer(key)

    def _voir_detail(self, code_commande: str, row_apercu: dict):
        """Appelé au clic sur Détail d'une carte — switch vers onglet détail."""
        self._vue_detail.charger(code_commande, row_apercu)
        self._aller_onglet("detail")

    # -------------------------------------------------------------------------
    # CHARGEMENT DES DONNÉES
    # -------------------------------------------------------------------------
    def actualiser(self, code_session: str):
        self._code_session = code_session
        self._rafraichir()

    def _rafraichir(self):
        if not self._code_session:
            return

        # ── Onglet Livraisons ──
        while self._lay_cartes.count():
            item = self._lay_cartes.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        commandes = []
        try:
            commandes = (
                self.ctrl.obtenir_toutes_commandes_attente_livraison(
                    self._code_session) or [])
        except Exception:
            pass

        n = len(commandes)
        self._lbl_kpi.setText(
            f"{n} commande{'s' if n > 1 else ''} en attente")
        self._lbl_sous_titre.setText(
            f"Session · {n} résultat{'s' if n > 1 else ''}")
        self._barre.set_badge("livraisons", n)

        if commandes:
            for row in commandes:
                carte = CarteCommandeAttente(
                    row, self.ctrl,
                    on_voir_detail    = self._voir_detail,
                    on_livre_callback = self._rafraichir
                )
                self._lay_cartes.addWidget(carte)
        else:
            self._lay_cartes.addWidget(
                _lbl_vide("Aucune commande en attente de livraison"))

        self._lay_cartes.addStretch()

        # ── Onglet Multiples ──
        multiples = []
        try:
            multiples = (
                self.ctrl.obtenir_patients_commandes_multiples(
                    self._code_session) or [])
        except Exception:
            pass
        self._vue_multiples.charger(multiples)
        self._barre.set_badge("multiples", len(multiples))

        # ── Onglet Historique ──
        try:
            historique = (
                self.ctrl.lister_commandes_completes(self._code_session) or [])
            self._vue_historique.charger(historique)
        except Exception:
            self._vue_historique.charger([])

    # -------------------------------------------------------------------------
    # ANIMATION OUVERTURE / FERMETURE
    # -------------------------------------------------------------------------
    def _repositionner(self):
        parent = self.parent()
        if parent:
            self.setFixedSize(self.LARGEUR, parent.height())

    def ouvrir(self):
        if self._ouvert:
            return
        self._ouvert = True
        self._repositionner()
        self.show()
        self.raise_()
        pw    = self.parent().width()
        debut = QRect(pw,                0, self.LARGEUR, self.height())
        fin   = QRect(pw - self.LARGEUR, 0, self.LARGEUR, self.height())
        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(380)
        self._anim.setStartValue(debut)
        self._anim.setEndValue(fin)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()

    def fermer(self):
        if not self._ouvert:
            return
        pw    = self.parent().width()
        debut = self.geometry()
        fin   = QRect(pw, 0, self.LARGEUR, self.height())
        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(300)
        self._anim.setStartValue(debut)
        self._anim.setEndValue(fin)
        self._anim.setEasingCurve(QEasingCurve.InCubic)
        self._anim.finished.connect(self.hide)
        self._anim.finished.connect(lambda: setattr(self, "_ouvert", False))
        self._anim.start()

    def basculer(self):
        self.fermer() if self._ouvert else self.ouvrir()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._ouvert and self.parent():
            pw = self.parent().width()
            self.setGeometry(pw - self.LARGEUR, 0,
                             self.LARGEUR, self.parent().height())