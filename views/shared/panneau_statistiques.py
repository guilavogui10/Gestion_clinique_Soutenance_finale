import qtawesome as qta

from PySide6.QtCore    import (Qt, QPropertyAnimation, QEasingCurve,
                                QRect, QSize, QTimer)
from PySide6.QtGui     import QColor, QPainter, QPainterPath, QBrush, QPen
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGraphicsDropShadowEffect, QScrollArea,
    QSizePolicy
)

from views.shared.theme_manager import theme_manager


def _c():
    """Raccourci pour obtenir la palette courante."""
    return theme_manager.colors()


# Couleurs podium top diagnostics (sémantiques — indépendantes du thème)
COULEURS_RANG = [
    "#D4AF37",   # Or   — #1
    "#9CA3AF",   # Argent — #2
    "#CD7F32",   # Bronze — #3
]


# =============================================================================
# WIDGET FOND ARRONDI (base pour le panneau)
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
# BARRE DE PROGRESSION ANIMÉE (taux de services)
# =============================================================================
class BarreProgression(QWidget):

    COULEURS = {
        "examen":       "#3B82F6",
        "chiurgie":     "#EF4444",
        "lunette":      "#D4AF37",
        "prescription": "#10B981",
    }
    LABELS = {
        "examen":       ("fa5s.microscope",    "Examens complémentaires"),
        "chiurgie":     ("fa5s.procedures",    "Interventions chirurgicales"),
        "lunette":      ("fa5s.glasses",       "Commandes de lunettes"),
        "prescription": ("fa5s.pills",         "Prescriptions médicales"),
    }

    def __init__(self, cle: str, valeur: float, parent=None):
        super().__init__(parent)
        self.cle    = cle
        self.valeur = valeur
        self._pct_actuel = 0.0
        self._setup_ui()
        QTimer.singleShot(400, self._demarrer_animation)

    def _setup_ui(self):
        c = _c()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(5)

        icone_name, label_txt = self.LABELS.get(self.cle, ("fa5s.chart-bar", self.cle))
        couleur = self.COULEURS.get(self.cle, c['primary'])

        # Ligne : icône + nom + %
        header = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(qta.icon(icone_name, color=couleur).pixmap(QSize(13, 13)))

        nom = QLabel(label_txt)
        nom.setStyleSheet(
            f"color:{c['text_secondary']}; font-size:11px; font-weight:600; background:transparent;"
        )

        self.lbl_pct = QLabel("0 %")
        self.lbl_pct.setStyleSheet(
            f"color:{couleur}; font-size:12px; font-weight:700; background:transparent;"
        )
        self.lbl_pct.setAlignment(Qt.AlignRight)

        header.addWidget(ic)
        header.addSpacing(5)
        header.addWidget(nom)
        header.addStretch()
        header.addWidget(self.lbl_pct)
        layout.addLayout(header)

        # Piste
        self._piste = QFrame()
        self._piste.setFixedHeight(7)
        self._piste.setStyleSheet(
            f"background:{c['border_light']}; border-radius:4px;"
        )
        piste_inner = QHBoxLayout(self._piste)
        piste_inner.setContentsMargins(0, 0, 0, 0)
        piste_inner.setSpacing(0)

        self._fill = QFrame()
        self._fill.setFixedHeight(7)
        self._fill.setFixedWidth(0)
        self._fill.setStyleSheet(
            f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {couleur}99,stop:1 {couleur});"
            f"border-radius:4px;"
        )
        piste_inner.addWidget(self._fill)
        piste_inner.addStretch()
        layout.addWidget(self._piste)

    def _demarrer_animation(self):
        self._timer = QTimer()
        self._timer.setInterval(14)
        self._timer.timeout.connect(self._animer)
        self._timer.start()

    def _animer(self):
        if self._pct_actuel >= self.valeur:
            self._pct_actuel = self.valeur
            self._timer.stop()
        self._pct_actuel = min(self._pct_actuel + 1.2, self.valeur)
        w = max(0, int((self._piste.width() - 2) * self._pct_actuel / 100))
        self._fill.setFixedWidth(w)
        self.lbl_pct.setText(f"{self._pct_actuel:.1f} %")


# =============================================================================
# CARTE DIAGNOSTIC (remplace le graphe matplotlib)
# =============================================================================
class CarteDiagnostic(QFrame):
    """
    Carte visuelle pour un diagnostic :
    [Rang]  [Nom du diagnostic]        [Barre]  [Nb cas]
    Beaucoup plus lisible qu'un graphe matplotlib pour le jury.
    """

    def __init__(self, rang: int, diagnostic: str, nombre: int,
                 max_nombre: int, parent=None):
        super().__init__(parent)
        c = _c()
        couleur = COULEURS_RANG[min(rang - 1, len(COULEURS_RANG) - 1)]
        self.setStyleSheet(
            f"QFrame{{background:{c['bg_card']}; border-radius:10px;"
            f"border:1px solid {c['border_light']};}}"
        )
        self.setFixedHeight(52)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # Badge rang
        badge = QLabel(str(rang))
        badge.setFixedSize(28, 28)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            f"background:{couleur}; color:{c['text_inverse']};"
            f"border-radius:14px; font-size:11px; font-weight:700; border:none;"
        )
        layout.addWidget(badge)

        # Nom du diagnostic
        nom = QLabel(diagnostic or "—")
        nom.setStyleSheet(
            f"color:{c['text_primary']}; font-size:11px; font-weight:600; background:transparent;"
        )
        nom.setMinimumWidth(100)
        nom.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(nom, 1)

        # Mini barre de proportion
        piste = QFrame()
        piste.setFixedSize(90, 7)
        piste.setStyleSheet(f"background:{c['border_light']}; border-radius:4px; border:none;")
        piste_in = QHBoxLayout(piste)
        piste_in.setContentsMargins(0, 0, 0, 0)
        fill = QFrame()
        fill.setFixedHeight(7)
        proportion = int(90 * nombre / max_nombre) if max_nombre > 0 else 0
        fill.setFixedWidth(max(4, proportion))
        fill.setStyleSheet(
            f"background:{couleur}; border-radius:4px; border:none;"
        )
        piste_in.addWidget(fill)
        piste_in.addStretch()
        layout.addWidget(piste)

        # Nombre de cas
        nb_lbl = QLabel(f"{nombre} cas")
        nb_lbl.setFixedWidth(48)
        nb_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        nb_lbl.setStyleSheet(
            f"color:{couleur}; font-size:12px; font-weight:700; background:transparent;"
        )
        layout.addWidget(nb_lbl)


# =============================================================================
# PANNEAU PRINCIPAL GLISSANT
# =============================================================================
class PanneauStatistiques(FondArrondi):
    """
    Panneau lateral glissant (droite → gauche).
    Coins arrondis, ombre portée, design cohérent avec les autres modales.
    """

    LARGEUR = 460

    def __init__(self, parent: QWidget, ctrl):
        super().__init__(rayon=20, couleur_cle="bg_main", parent=parent)
        self.ctrl     = ctrl
        self._ouvert  = False
        self._code_session = None

        self._repositionner()
        self._setup_ui()
        self._setup_ombre()

        self.move(parent.width(), self.y())
        self.hide()

        theme_manager.theme_changed.connect(self._on_theme_change)

    # -------------------------------------------------------------------------
    # CONSTRUCTION UI
    # -------------------------------------------------------------------------
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- En-tête arrondi en haut ---
        self._header = QFrame()
        self._header.setFixedHeight(62)
        h_lay = QHBoxLayout(self._header)
        h_lay.setContentsMargins(20, 0, 16, 0)

        self._ic_header = QLabel()
        self._ic_header.setStyleSheet("background:transparent;")

        self._titre = QLabel("Analyse — Session en cours")

        self.btn_fermer = QPushButton()
        self.btn_fermer.setFixedSize(32, 32)
        self.btn_fermer.setCursor(Qt.PointingHandCursor)
        self.btn_fermer.setStyleSheet(
            "background:rgba(255,255,255,0.18); border-radius:16px; border:none;"
        )
        self.btn_fermer.clicked.connect(self.fermer)

        h_lay.addWidget(self._ic_header)
        h_lay.addSpacing(10)
        h_lay.addWidget(self._titre)
        h_lay.addStretch()
        h_lay.addWidget(self.btn_fermer)
        layout.addWidget(self._header)

        # --- Zone scrollable ---
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        contenu = QWidget()
        contenu.setStyleSheet("background:transparent;")
        self._contenu_layout = QVBoxLayout(contenu)
        self._contenu_layout.setContentsMargins(16, 16, 16, 16)
        self._contenu_layout.setSpacing(16)

        # Sections créées une fois
        self._section_taux   = self._creer_section(
            "fa5s.exchange-alt", "Taux de conversion des services")
        self._section_diagno = self._creer_section(
            "fa5s.stethoscope",  "Top des diagnostics posés")

        self._contenu_layout.addWidget(self._section_taux)
        self._contenu_layout.addWidget(self._section_diagno)
        self._contenu_layout.addStretch()

        self._scroll.setWidget(contenu)

        # Wrapper pour arrondir le bas
        wrapper = QFrame()
        wrapper.setStyleSheet(
            "background:transparent;"
            "border-bottom-left-radius:20px;"
            "border-bottom-right-radius:20px;"
        )
        w_lay = QVBoxLayout(wrapper)
        w_lay.setContentsMargins(0, 0, 0, 0)
        w_lay.addWidget(self._scroll)
        layout.addWidget(wrapper)

        # Appliquer le thème initial
        self._apply_theme_styles()

    def _creer_section(self, icone_name: str, titre: str) -> QFrame:
        """Crée un cadre section arrondi."""
        frame = QFrame()
        frame._icone_name = icone_name
        frame._titre_text = titre

        ombre = QGraphicsDropShadowEffect()
        ombre.setBlurRadius(16)
        ombre.setOffset(0, 3)
        ombre.setColor(QColor(0, 0, 0, 20))
        frame.setGraphicsEffect(ombre)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)

        # Titre section
        hdr = QHBoxLayout()
        frame._ic = QLabel()
        frame._ic.setStyleSheet("background:transparent; border:none;")
        frame._tl = QLabel(titre)
        hdr.addWidget(frame._ic)
        hdr.addSpacing(7)
        hdr.addWidget(frame._tl)
        hdr.addStretch()
        layout.addLayout(hdr)

        frame._sep = QFrame()
        frame._sep.setFixedHeight(1)
        layout.addWidget(frame._sep)

        # Conteneur enfant rechargeable
        enfant = QWidget()
        enfant.setStyleSheet("background:transparent; border:none;")
        enfant_layout = QVBoxLayout(enfant)
        enfant_layout.setContentsMargins(0, 0, 0, 0)
        enfant_layout.setSpacing(8)
        layout.addWidget(enfant)
        frame._enfant_layout = enfant_layout

        return frame

    def _setup_ombre(self):
        ombre = QGraphicsDropShadowEffect(self)
        ombre.setBlurRadius(45)
        ombre.setOffset(-10, 0)
        ombre.setColor(QColor(0, 0, 0, 70))
        self.setGraphicsEffect(ombre)

    # -------------------------------------------------------------------------
    # CHARGEMENT DES DONNÉES
    # -------------------------------------------------------------------------
    def actualiser(self, code_session: str):
        """Recharge les données des deux sections."""
        self._code_session = code_session

        # Section 1 — Taux de conversion
        self._vider(self._section_taux)
        taux = self.ctrl.obtenir_taux_conversion(code_session)
        if taux:
            for cle, valeur in taux.items():
                self._section_taux._enfant_layout.addWidget(
                    BarreProgression(cle, float(valeur))
                )
        else:
            self._section_taux._enfant_layout.addWidget(
                self._lbl_vide("Aucune donnée disponible"))

        # Section 2 — Top diagnostics
        self._vider(self._section_diagno)
        top = self.ctrl.obtenir_top_diagnostics(code_session, limite=7)
        if top:
            max_nb = top[0]["nombre"] if top else 1
            for i, row in enumerate(top):
                carte = CarteDiagnostic(
                    rang       = i + 1,
                    diagnostic = row["diagnostique"],
                    nombre     = row["nombre"],
                    max_nombre = max_nb
                )
                self._section_diagno._enfant_layout.addWidget(carte)
        else:
            self._section_diagno._enfant_layout.addWidget(
                self._lbl_vide("Aucun diagnostic enregistré"))

    def _vider(self, section: QFrame):
        layout = section._enfant_layout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _lbl_vide(self, texte: str) -> QLabel:
        c = _c()
        lbl = QLabel(texte)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            f"color:{c['text_secondary']}; font-size:11px; background:transparent;"
        )
        return lbl

    # -------------------------------------------------------------------------
    # THÈME
    # -------------------------------------------------------------------------
    def _apply_theme_styles(self):
        """Applique les couleurs du thème courant sur tous les éléments fixes."""
        c = _c()

        # En-tête
        self._header.setStyleSheet(
            f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {c['primary']},stop:1 {c['primary_hover']});"
            f"border-top-left-radius:20px; border-top-right-radius:20px;"
        )
        self._ic_header.setPixmap(
            qta.icon("fa5s.chart-pie", color=c['text_inverse']).pixmap(QSize(20, 20))
        )
        self._titre.setStyleSheet(
            f"color:{c['text_inverse']}; font-size:14px; font-weight:700;"
            f"letter-spacing:0.3px; background:transparent;"
        )
        self.btn_fermer.setIcon(qta.icon("fa5s.times", color=c['text_inverse']))

        # Scrollbar
        self._scroll.setStyleSheet(
            f"QScrollArea{{border:none; background:transparent;}}"
            f"QScrollBar:vertical{{border:none;background:{c['bg_main']};"
            f"width:5px;border-radius:2px;}}"
            f"QScrollBar::handle:vertical{{background:{c['border']};border-radius:2px;}}"
            f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}"
        )

        # Sections
        for section in (self._section_taux, self._section_diagno):
            section.setStyleSheet(
                f"QFrame{{background:{c['bg_card']}; border-radius:14px;"
                f"border:1px solid {c['border_light']};}}"
            )
            section._ic.setPixmap(
                qta.icon(section._icone_name, color=c['primary']).pixmap(QSize(14, 14))
            )
            section._tl.setStyleSheet(
                f"color:{c['primary']}; font-size:12px; font-weight:700; border:none;"
            )
            section._sep.setStyleSheet(
                f"background:{c['primary_light']}; border:none;"
            )

    def _on_theme_change(self):
        """Réaction au changement de thème."""
        self._apply_theme_styles()
        self.update()
        if self._code_session:
            self.actualiser(self._code_session)

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
        debut = QRect(pw,                    0, self.LARGEUR, self.height())
        fin   = QRect(pw - self.LARGEUR,     0, self.LARGEUR, self.height())

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