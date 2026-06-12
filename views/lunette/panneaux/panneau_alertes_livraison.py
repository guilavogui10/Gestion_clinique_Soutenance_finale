import qtawesome as qta

from PySide6.QtCore    import (Qt, QPropertyAnimation, QEasingCurve,
                                QRect, QSize, QTimer)
from PySide6.QtGui     import QColor, QPainter, QPainterPath, QBrush
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGraphicsDropShadowEffect, QScrollArea,
    QSizePolicy
)

from views.shared.theme_manager import theme_manager

# =============================================================================
# PALETTE CLINIQUE (dynamique depuis theme_manager)
# =============================================================================
def _colors():
    return theme_manager.colors()


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
        painter.fillPath(path, QBrush(QColor(_colors()[self._couleur_cle])))
        painter.end()


# =============================================================================
# CARTE ALERTE — une commande par carte
# =============================================================================
class CarteAlerteCommande(QFrame):
    """
    Carte affichant les informations complètes d'une commande en alerte.
    Couleur rouge pour retard, orange pour livraison dans 2 jours.
    """

    def __init__(self, row: dict, mode: str, parent=None):
        """
        mode = 'retard'   → rouge  — affiche jours_retard
        mode = 'bientot'  → orange — affiche jours_restants
        """
        super().__init__(parent)

        c = _colors()
        couleur_fond   = c['danger_bg']  if mode == "retard" else c['warning_bg']
        couleur_bord   = c['danger']     if mode == "retard" else c['warning']
        couleur_badge  = c['danger']     if mode == "retard" else c['warning']

        self.setStyleSheet(
            f"QFrame{{"
            f"background:{couleur_fond};"
            f"border-radius:10px;"
            f"border:1px solid {couleur_bord};"
            f"}}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # ── Ligne 1 : code commande + badge jours ──
        ligne1 = QHBoxLayout()

        code_lbl = QLabel(f"#{row.get('commande_code', '—')}")
        code_lbl.setStyleSheet(
            f"color:{c['primary']}; font-size:12px; font-weight:700;"
            f"background:{c['bg_card']}; border:none;"
        )
        ligne1.addWidget(code_lbl)
        ligne1.addStretch()

        if mode == "retard":
            jours = row.get("jours_retard", 0)
            texte_badge = f"+{jours} j de retard"
        else:
            jours = row.get("jours_restants", 0)
            texte_badge = f"Dans {jours} j"

        badge = QLabel(texte_badge)
        badge.setStyleSheet(
            f"background:{couleur_badge}; color:{c['text_inverse']};"
            f"border-radius:8px; font-size:10px; font-weight:700;"
            f"padding: 2px 8px; border:none;"
        )
        ligne1.addWidget(badge)
        layout.addLayout(ligne1)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{couleur_bord}; border:none; opacity:0.3;")
        layout.addWidget(sep)

        # ── Ligne 2 : patient ──
        nom    = row.get("patient_nom",    "")
        prenom = row.get("patient_prenom", "")
        nom_complet = f"{nom} {prenom}".strip() or "Patient inconnu"

        ligne2 = QHBoxLayout()
        ic_patient = QLabel()
        ic_patient.setPixmap(
            qta.icon("fa5s.user", color=c['text_secondary']).pixmap(QSize(11, 11)))
        ic_patient.setStyleSheet("background:{c['bg_card']}; border:none;")
        patient_lbl = QLabel(nom_complet)
        patient_lbl.setStyleSheet(
            f"color:{c['text_primary']}; font-size:11px; font-weight:600;"
            f"background:{c['bg_card']}; border:none;"
        )
        ligne2.addWidget(ic_patient)
        ligne2.addSpacing(5)
        ligne2.addWidget(patient_lbl)
        ligne2.addStretch()
        layout.addLayout(ligne2)

        # ── Ligne 3 : numéro verre + numéro cadre ──
        ligne3 = QHBoxLayout()

        ic_verre = QLabel()
        ic_verre.setPixmap(
            qta.icon("fa5s.eye", color=c['text_secondary']).pixmap(QSize(11, 11)))
        ic_verre.setStyleSheet("background:{c['bg_card']}; border:none;")
        verre_lbl = QLabel(f"Verre : {row.get('numero_verre', '—')}")
        verre_lbl.setStyleSheet(
            f"color:{c['text_secondary']}; font-size:10px;"
            f"background:{c['bg_card']}; border:none;"
        )

        ic_cadre = QLabel()
        ic_cadre.setPixmap(
            qta.icon("fa5s.glasses", color=c['text_secondary']).pixmap(QSize(11, 11)))
        ic_cadre.setStyleSheet("background:{c['bg_card']}; border:none;")
        cadre_lbl = QLabel(f"Cadre : {row.get('numero_cadre', '—')}")
        cadre_lbl.setStyleSheet(
            f"color:{c['text_secondary']}; font-size:10px;"
            f"background:{c['bg_card']}; border:none;"
        )

        ligne3.addWidget(ic_verre)
        ligne3.addSpacing(4)
        ligne3.addWidget(verre_lbl)
        ligne3.addSpacing(14)
        ligne3.addWidget(ic_cadre)
        ligne3.addSpacing(4)
        ligne3.addWidget(cadre_lbl)
        ligne3.addStretch()
        layout.addLayout(ligne3)

        # ── Ligne 4 : date livraison prévue + personnel ──
        ligne4 = QHBoxLayout()

        date_val = row.get("date_livraison")
        if date_val and hasattr(date_val, "strftime"):
            date_str = date_val.strftime("%d/%m/%Y")
        elif date_val:
            date_str = str(date_val)
        else:
            date_str = "—"

        ic_date = QLabel()
        ic_date.setPixmap(
            qta.icon("fa5s.calendar-alt", color=couleur_badge).pixmap(QSize(11, 11)))
        ic_date.setStyleSheet("background:{c['bg_card']}; border:none;")
        date_lbl = QLabel(f"Livraison prévue : {date_str}")
        date_lbl.setStyleSheet(
            f"color:{couleur_badge}; font-size:10px; font-weight:600;"
            f"background:{c['bg_card']}; border:none;"
        )

        nom_per    = row.get("personnel_nom",    "")
        prenom_per = row.get("personnel_prenom", "")
        per_complet = f"{nom_per} {prenom_per}".strip() or "—"

        ic_per = QLabel()
        ic_per.setPixmap(
            qta.icon("fa5s.user-md", color=c['text_secondary']).pixmap(QSize(11, 11)))
        ic_per.setStyleSheet("background:{c['bg_card']}; border:none;")
        per_lbl = QLabel(per_complet)
        per_lbl.setStyleSheet(
            f"color:{c['text_secondary']}; font-size:10px;"
            f"background:{c['bg_card']}; border:none;"
        )

        ligne4.addWidget(ic_date)
        ligne4.addSpacing(4)
        ligne4.addWidget(date_lbl)
        ligne4.addStretch()
        ligne4.addWidget(ic_per)
        ligne4.addSpacing(4)
        ligne4.addWidget(per_lbl)
        layout.addLayout(ligne4)


# =============================================================================
# PANNEAU PRINCIPAL GLISSANT
# =============================================================================
class PanneauAlertesLivraison(FondArrondi):
    """
    Panneau latéral glissant (droite → gauche).
    Affiche deux sections :
      - Commandes à livrer dans les 2 prochains jours  (orange)
      - Commandes dont le délai de livraison est dépassé (rouge)
    """

    LARGEUR = 460

    def __init__(self, parent: QWidget, ctrl):
        super().__init__(rayon=20, couleur_cle="bg_main", parent=parent)
        self.ctrl    = ctrl
        self._ouvert = False
        self._last_code_session = None

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
        if self._last_code_session:
            self.actualiser(self._last_code_session)

    # -------------------------------------------------------------------------
    # CONSTRUCTION UI
    # -------------------------------------------------------------------------
    def _setup_ui(self):
        c = _colors()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── En-tête ──
        self._header = QFrame()
        self._header.setObjectName("alertes_header")
        self._header.setFixedHeight(62)
        h_lay = QHBoxLayout(self._header)
        h_lay.setContentsMargins(20, 0, 16, 0)

        self._ic_header = QLabel()
        self._ic_header.setStyleSheet("background:transparent;")

        self._titre = QLabel("Alertes Livraisons — Session en cours")

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

        # ── Zone scrollable ──
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        contenu = QWidget()
        contenu.setStyleSheet(f"background:{_c()['bg_main']};")
        self._contenu_layout = QVBoxLayout(contenu)
        self._contenu_layout.setContentsMargins(16, 16, 16, 16)
        self._contenu_layout.setSpacing(16)

        # Sections créées une fois
        self._section_bientot = self._creer_section(
            "fa5s.clock",       "warning", "Livraisons dans les 2 prochains jours")
        self._section_retard  = self._creer_section(
            "fa5s.exclamation-triangle", "danger", "Livraisons en retard")

        self._contenu_layout.addWidget(self._section_bientot)
        self._contenu_layout.addWidget(self._section_retard)
        self._contenu_layout.addStretch()

        self._scroll.setWidget(contenu)

        wrapper = QFrame()
        wrapper.setStyleSheet(
            f"background:{_c()['bg_card']};"
            "border-bottom-left-radius:20px;"
            "border-bottom-right-radius:20px;"
        )
        w_lay = QVBoxLayout(wrapper)
        w_lay.setContentsMargins(0, 0, 0, 0)
        w_lay.addWidget(self._scroll)
        layout.addWidget(wrapper)

        # Appliquer le thème initial
        self._apply_theme_styles()

    def _creer_section(self, icone_name: str,
                       couleur_cle: str, titre: str) -> QFrame:
        """Crée un cadre section blanc arrondi avec compteur."""
        c = _colors()
        frame = QFrame()
        frame._icone_name  = icone_name
        frame._couleur_cle = couleur_cle
        frame._titre_text  = titre

        ombre = QGraphicsDropShadowEffect()
        ombre.setBlurRadius(16)
        ombre.setOffset(0, 3)
        shadow_color = QColor(c['primary'])
        shadow_color.setAlpha(20)
        ombre.setColor(shadow_color)
        frame.setGraphicsEffect(ombre)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)

        # Titre + compteur
        hdr = QHBoxLayout()
        frame._ic = QLabel()
        frame._ic.setStyleSheet("background:{c['bg_card']}; border:none;")
        frame._tl = QLabel(titre)

        frame._compteur = QLabel("0")
        frame._compteur.setFixedSize(24, 24)
        frame._compteur.setAlignment(Qt.AlignCenter)

        hdr.addWidget(frame._ic)
        hdr.addSpacing(7)
        hdr.addWidget(frame._tl)
        hdr.addStretch()
        hdr.addWidget(frame._compteur)
        layout.addLayout(hdr)

        frame._sep = QFrame()
        frame._sep.setFixedHeight(1)
        layout.addWidget(frame._sep)

        # Conteneur enfant rechargeable
        enfant = QWidget()
        enfant.setStyleSheet("background:{c['bg_card']}; border:none;")
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
    # THÈME — mise à jour in-place
    # -------------------------------------------------------------------------
    def _apply_theme_styles(self):
        """Applique les couleurs du thème courant sur tous les éléments fixes."""
        c = _colors()

        # En-tête — sélecteur #id pour forcer le repaint du gradient
        self._header.setStyleSheet(
            f"#alertes_header{{"
            f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {c['primary']},stop:1 {c['primary_hover']});"
            f"border-top-left-radius:20px;border-top-right-radius:20px;"
            f"}}"
        )
        self._header.style().unpolish(self._header)
        self._header.style().polish(self._header)
        self._header.update()

        self._ic_header.setPixmap(
            qta.icon("fa5s.bell", color=c['text_inverse']).pixmap(QSize(20, 20)))
        self._titre.setStyleSheet(
            f"color:{c['text_inverse']}; font-size:14px; font-weight:700;"
            f"letter-spacing:0.3px; background:{c['bg_card']};"
        )
        self.btn_fermer.setIcon(qta.icon("fa5s.times", color=c['text_inverse']))

        # Scrollbar
        self._scroll.setStyleSheet(
            f"QScrollArea{{border:none; background:{c['bg_main']};}}"
            f"QScrollBar:vertical{{border:none;background:{c['bg_main']};"
            f"width:5px;border-radius:2px;}}"
            f"QScrollBar::handle:vertical{{background:{c['border']};border-radius:2px;}}"
            f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}"
        )

        # Sections
        for section in (self._section_bientot, self._section_retard):
            couleur_icone = c[section._couleur_cle]
            section.setStyleSheet(
                f"QFrame{{background:{c['bg_card']}; border-radius:14px;"
                f"border:1px solid {c['border']};}}"
            )
            section._ic.setPixmap(
                qta.icon(section._icone_name, color=couleur_icone).pixmap(QSize(14, 14)))
            section._tl.setStyleSheet(
                f"color:{c['primary']}; font-size:12px; font-weight:700; border:none;"
            )
            section._compteur.setStyleSheet(
                f"background:{couleur_icone}; color:{c['text_inverse']};"
                f"border-radius:12px; font-size:10px; font-weight:700; border:none;"
            )
            section._sep.setStyleSheet(
                f"background:{c['success_bg']}; border:none;"
            )

    # -------------------------------------------------------------------------
    # CHARGEMENT DES DONNÉES
    # -------------------------------------------------------------------------
    def actualiser(self, code_session: str):
        """Recharge les données des deux sections depuis le contrôleur."""
        self._last_code_session = code_session

        # ── Section 1 : dans 2 jours ──
        self._vider(self._section_bientot)
        bientot = self.ctrl.obtenir_commandes_a_livrer_dans_deux_jours(code_session)
        self._section_bientot._compteur.setText(str(len(bientot)))
        if bientot:
            for row in bientot:
                self._section_bientot._enfant_layout.addWidget(
                    CarteAlerteCommande(row, mode="bientot"))
        else:
            self._section_bientot._enfant_layout.addWidget(
                self._lbl_vide("Aucune livraison prévue dans les 2 prochains jours"))

        # ── Section 2 : en retard ──
        self._vider(self._section_retard)
        retards = self.ctrl.obtenir_commandes_en_retard(code_session)
        self._section_retard._compteur.setText(str(len(retards)))
        if retards:
            for row in retards:
                self._section_retard._enfant_layout.addWidget(
                    CarteAlerteCommande(row, mode="retard"))
        else:
            self._section_retard._enfant_layout.addWidget(
                self._lbl_vide("Aucune commande en retard"))

    def _vider(self, section: QFrame):
        layout = section._enfant_layout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _lbl_vide(self, texte: str) -> QLabel:
        c = _colors()
        lbl = QLabel(texte)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            f"color:{c['text_secondary']}; font-size:11px; background:{c['bg_card']};"
        )
        return lbl

    # -------------------------------------------------------------------------
    # ANIMATION OUVERTURE / FERMETURE (identique à la référence)
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