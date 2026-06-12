"""
=============================================================================
 PATIENTS LUNETTE ATTENTE — grille de cartes (pattern chirurgie/examen)
=============================================================================
 Données DAO retournées par patients_en_attente_lunette() :
   code_visite, date_visite, statut_patient,
   code_consultation, date_consultation,
   code_patient, nom, prenom, telephone
=============================================================================
"""

import qtawesome as qta
from PySide6.QtCore    import Qt, QSize, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QScrollArea, QGridLayout, QSizePolicy,
    QDialog
)

from views.shared.theme_manager import theme_manager
from views.lunette.styles       import LunetteStyles


# =============================================================================
# PATIENT CARD
# =============================================================================

class PatientLunetteCard(QFrame):
    """Carte d'un patient en attente de lunettes."""

    CARD_WIDTH  = 170
    CARD_HEIGHT = 250

    proceder_signal      = Signal(object)   # émet le dict patient (Procéder / Fin lunette)
    changer_statut_clicked = Signal(object) # émet le dict patient (Démarrer / Fin)

    def __init__(self, patient: dict, parent=None):
        super().__init__(parent)
        self.patient = patient
        self._statut_patient = str(patient.get('statut_patient', '') or '')
        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)
        self.setCursor(Qt.PointingHandCursor)

        self._icon_rows: list = []   # (icon_lbl, icon_name, value_lbl)
        self._setup_ui()
        self._apply_theme()
        theme_manager.theme_changed.connect(self._apply_theme)

    # ─── Construction ────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(2)

        # Avatar
        self._avatar_lbl = QLabel()
        self._avatar_lbl.setAlignment(Qt.AlignCenter)
        self._avatar_lbl.setStyleSheet(f"border: none; background: {theme_manager.colors()['bg_card']};")
        root.addWidget(self._avatar_lbl)

        # Nom
        nom = f"{self.patient.get('nom','') or ''} {self.patient.get('prenom','') or ''}".strip()
        self._lbl_nom = QLabel(nom or "Patient inconnu")
        self._lbl_nom.setAlignment(Qt.AlignCenter)
        self._lbl_nom.setWordWrap(True)
        root.addWidget(self._lbl_nom)

        # Badge statut
        statut = self._statut_patient.strip()
        badge_text = "En optique" if statut == "En lunette" else "Attente Lunette"
        self._badge_statut = QLabel(badge_text)
        self._badge_statut.setAlignment(Qt.AlignCenter)
        root.addWidget(self._badge_statut)

        # Badge code patient
        self._badge = QLabel(str(self.patient.get('code_patient', '')))
        self._badge.setAlignment(Qt.AlignCenter)
        root.addWidget(self._badge)

        # Séparateur
        self._sep = QFrame()
        self._sep.setFrameShape(QFrame.HLine)
        self._sep.setFixedHeight(1)
        root.addWidget(self._sep)

        # Infos
        infos_layout = QVBoxLayout()
        infos_layout.setSpacing(1)

        champs = [
            ("fa5s.calendar-check", "Date",  self._fmt_date(self.patient.get('date_visite'))),
            ("fa5s.file-medical",   "Cons.",  str(self.patient.get('code_consultation', '') or '—')),
            ("fa5s.phone",          "Tél.",   str(self.patient.get('telephone', '') or '—')),
        ]
        for icon_name, label, valeur in champs:
            row_w, ic_lbl, val_lbl = self._build_info_row(
                icon_name, label, str(valeur).strip() if valeur else "—"
            )
            infos_layout.addWidget(row_w)
            self._icon_rows.append((ic_lbl, icon_name, val_lbl))

        root.addLayout(infos_layout)
        root.addSpacing(4)

        # Bouton Procéder (ouvrir formulaire commande) — action principale
        self._btn = QPushButton(" Procéder")
        self._btn.setFixedHeight(24)
        self._btn.setCursor(Qt.PointingHandCursor)
        self._btn.clicked.connect(lambda: self.proceder_signal.emit(self.patient))
        root.addWidget(self._btn)

        root.addSpacing(3)

        # Bouton Démarrer / Fin lunette — changement de statut
        statut = self._statut_patient.strip()
        btn_statut_label = " Fin lunette" if statut == "En lunette" else " Démarrer lunette"
        self._btn_statut = QPushButton(btn_statut_label)
        self._btn_statut.setFixedHeight(24)
        self._btn_statut.setCursor(Qt.PointingHandCursor)
        self._btn_statut.clicked.connect(lambda: self.changer_statut_clicked.emit(self.patient))
        root.addWidget(self._btn_statut)

    def _build_info_row(self, icon_name: str, label: str, value: str):
        container = QWidget()
        container.setStyleSheet(f"background: {theme_manager.colors()['bg_card']}; border: none;")
        h = QHBoxLayout(container)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(5)

        ic_lbl = QLabel()
        ic_lbl.setFixedSize(14, 14)
        ic_lbl.setStyleSheet(f"border: none; background: {theme_manager.colors()['bg_card']};")

        lbl_lbl = QLabel(f"{label}:")
        lbl_lbl.setFixedWidth(38)
        lbl_lbl.setStyleSheet(f"border: none; background: {theme_manager.colors()['bg_card']};")

        val_lbl = QLabel(value)
        val_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        val_lbl.setWordWrap(True)
        val_lbl.setStyleSheet(f"border: none; background: {theme_manager.colors()['bg_card']};")

        h.addWidget(ic_lbl)
        h.addWidget(lbl_lbl)
        h.addWidget(val_lbl)
        ic_lbl._label_widget = lbl_lbl
        return container, ic_lbl, val_lbl

    @staticmethod
    def _fmt_date(val) -> str:
        if not val:
            return "—"
        if hasattr(val, "strftime"):
            return val.strftime("%d/%m/%Y")
        return str(val)

    # ─── Thème ───────────────────────────────────────────────────────────

    def _apply_theme(self):
        c = theme_manager.colors()
        primary = c['primary']

        self.setStyleSheet(f"""
            PatientLunetteCard {{
                background-color : {c['bg_card']};
                border           : 1.5px solid {c['border']};
                border-radius    : 16px;
            }}
            PatientLunetteCard:hover {{
                border           : 1.5px solid {primary};
                background-color : {c['hover']};
            }}
        """)

        self._avatar_lbl.setPixmap(
            qta.icon("fa5s.user-circle", color=primary).pixmap(QSize(40, 40))
        )
        self._lbl_nom.setStyleSheet(
            f"font-size:11px; font-weight:700; color:{c['text_primary']}; border:none;"
        )
        self._badge.setStyleSheet(f"""
            font-size    : 9px; font-weight : 600;
            color        : {primary};
            background   : {primary}22;
            border-radius: 6px;
            padding      : 1px 5px;
            border       : 1px solid {primary}55;
        """)
        self._sep.setStyleSheet(f"background:{c['border_light']}; border:none;")

        for ic_lbl, icon_name, val_lbl in self._icon_rows:
            ic_lbl.setPixmap(
                qta.icon(icon_name, color=primary).pixmap(QSize(12, 12))
            )
            ic_lbl._label_widget.setStyleSheet(
                f"font-size:9px; font-weight:600; color:{c['text_muted']}; border:none;"
            )
            val_lbl.setStyleSheet(
                f"font-size:9px; color:{c['text_secondary']}; border:none;"
            )

        # Style bouton statut : vert = Démarrer, orange = Fin
        statut = self._statut_patient.strip()
        if statut == "En lunette":
            self._btn_statut.setStyleSheet(f"""
                QPushButton {{
                    background: {c['warning']}; color: {c['text_inverse']}; border: none;
                    border-radius: 6px; font-size: 10px; font-weight: 600;
                }}
                QPushButton:hover {{ background: {c['warning']}cc; }}
            """)
            self._btn_statut.setIcon(qta.icon("fa5s.stop-circle", color=c['text_inverse']))
        else:
            self._btn_statut.setStyleSheet(f"""
                QPushButton {{
                    background: {c['success']}; color: {c['text_inverse']}; border: none;
                    border-radius: 6px; font-size: 10px; font-weight: 600;
                }}
                QPushButton:hover {{ background: {c['success']}cc; }}
            """)
            self._btn_statut.setIcon(qta.icon("fa5s.play-circle", color=c['text_inverse']))

        self._btn.setStyleSheet(LunetteStyles.button_primary())
        self._btn.setIcon(
            qta.icon("fa5s.glasses", color=c['text_inverse'])
        )

        # Style badge statut
        if statut == "En lunette":
            self._badge_statut.setStyleSheet(f"""
                font-size: 9px; font-weight: 600;
                color: {c['warning']}; background: {c['warning']}22;
                border-radius: 6px; padding: 1px 5px;
                border: 1px solid {c['warning']}55;
            """)
        else:
            self._badge_statut.setStyleSheet(f"""
                font-size: 9px; font-weight: 600;
                color: {primary}; background: {primary}22;
                border-radius: 6px; padding: 1px 5px;
                border: 1px solid {primary}55;
            """)


# =============================================================================
# GRILLE PRINCIPALE
# =============================================================================

class PatientsAttenteView(QWidget):
    """Grille scrollable de PatientLunetteCard."""

    ouvrir_formulaire    = Signal(str)    # émet code_acte
    commande_creee       = Signal()
    changer_statut_signal = Signal(object) # émet le dict patient

    NB_COLS = 5

    def __init__(self, ctrl, code_session: str, parent=None):
        super().__init__(parent)
        self.ctrl         = ctrl
        self.code_session = code_session
        self._setup_ui()
        self._apply_theme()
        theme_manager.theme_changed.connect(self._apply_theme)
        self.charger_patients()

    # ─── Construction ────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 12, 20, 12)
        root.setSpacing(10)

        # Header
        hdr = QHBoxLayout()
        hdr.setSpacing(8)
        self._h_icon = QLabel()
        self._h_icon.setFixedSize(20, 20)
        self._h_icon.setStyleSheet(f"border:none; background:{theme_manager.colors()['bg_card']};")
        self._h_title = QLabel("Patients en Attente de Lunettes")
        self._h_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._h_badge = QLabel("0 patient(s)")
        hdr.addWidget(self._h_icon)
        hdr.addWidget(self._h_title)
        hdr.addStretch()
        hdr.addWidget(self._h_badge)
        root.addLayout(hdr)

        self._h_sep = QFrame()
        self._h_sep.setFrameShape(QFrame.HLine)
        self._h_sep.setFixedHeight(1)
        root.addWidget(self._h_sep)

        # Scroll + grille
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._cards_container = QWidget()
        self._grid = QGridLayout(self._cards_container)
        self._grid.setSpacing(12)
        self._grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._scroll.setWidget(self._cards_container)
        root.addWidget(self._scroll, 1)

        # Empty state
        self._empty = self._build_empty_state()
        root.addWidget(self._empty)
        self._empty.hide()

    def _build_empty_state(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(12)
        self._empty_icon = QLabel()
        self._empty_icon.setAlignment(Qt.AlignCenter)
        self._empty_icon.setStyleSheet(f"border:none; background:{theme_manager.colors()['bg_card']};")
        self._empty_msg = QLabel("Aucun patient en attente de lunettes pour cette session.")
        self._empty_msg.setAlignment(Qt.AlignCenter)
        self._empty_msg.setWordWrap(True)
        lay.addStretch()
        lay.addWidget(self._empty_icon)
        lay.addWidget(self._empty_msg)
        lay.addStretch()
        return w

    # ─── Chargement ──────────────────────────────────────────────────────

    def charger_patients(self):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        patients = self.ctrl.obtenir_patients_attente_lunette(self.code_session)

        if not patients:
            self._scroll.hide()
            self._empty.show()
            self._h_badge.setText("0 patient(s)")
            return

        self._empty.hide()
        self._scroll.show()
        self._h_badge.setText(f"{len(patients)} patient(s)")

        for idx, patient in enumerate(patients):
            card = PatientLunetteCard(patient)
            card.proceder_signal.connect(self._on_proceder)
            card.changer_statut_clicked.connect(self.changer_statut_signal.emit)
            self._grid.addWidget(card, idx // self.NB_COLS, idx % self.NB_COLS)

    # ─── Action ──────────────────────────────────────────────────────────

    def _on_proceder(self, patient):
        code = patient.get('code_acte', '') if isinstance(patient, dict) \
               else getattr(patient, 'code_acte', '')
        self.ouvrir_formulaire.emit(code)

    # ─── Thème ───────────────────────────────────────────────────────────

    def _apply_theme(self):
        c = theme_manager.colors()
        primary = c['primary']

        self.setStyleSheet(f"background:{c['bg_main']};")
        self._cards_container.setStyleSheet(f"background:{theme_manager.colors()['bg_main']};")
        self._scroll.setStyleSheet(
            f"QScrollArea{{background:{theme_manager.colors()['bg_main']}; border:none;}}"
        )
        self._scroll.verticalScrollBar().setStyleSheet(LunetteStyles.scrollbar())

        self._h_icon.setPixmap(
            qta.icon("fa5s.glasses", color=primary).pixmap(QSize(18, 18))
        )
        self._h_title.setStyleSheet(
            f"font-size:14px; font-weight:700; color:{c['text_primary']}; border:none;"
        )
        self._h_badge.setStyleSheet(f"""
            font-size:11px; font-weight:600; color:{c['text_muted']};
            background:{c['bg_card']};
            border-radius:10px; padding:2px 10px;
            border:1px solid {c['border_light']};
        """)
        self._h_sep.setStyleSheet(f"background:{c['border_light']}; border:none;")

        self._empty_icon.setPixmap(
            qta.icon("fa5s.inbox", color=c['text_muted']).pixmap(QSize(72, 72))
        )
        self._empty_msg.setStyleSheet(
            f"font-size:14px; color:{c['text_muted']}; border:none;"
        )


# =============================================================================
# DIALOG WRAPPER
# =============================================================================

class PatientsAttenteDialog(QDialog):
    """QDialog encapsulant PatientsAttenteView pour l'ouverture rapide."""

    ouvrir_nouveau_tab = Signal(str)   # émet code_acte pour basculer sur l'onglet Nouveau

    def __init__(self, ctrl, code_session: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Patients en Attente de Lunettes")
        self.setModal(True)
        self.resize(1050, 650)
        self.setMinimumSize(700, 480)
        self._setup_ui(ctrl, code_session)
        self._apply_theme()
        theme_manager.theme_changed.connect(self._apply_theme)

    def _setup_ui(self, ctrl, code_session: str):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header custom
        self._header = QFrame()
        self._header.setFixedHeight(56)
        h_lay = QHBoxLayout(self._header)
        h_lay.setContentsMargins(20, 0, 16, 0)
        h_lay.setSpacing(10)

        self._title_icon = QLabel()
        self._title_icon.setFixedSize(22, 22)
        self._title_icon.setStyleSheet(f"border:none; background:{theme_manager.colors()['bg_card']};")

        self._title_lbl = QLabel("Patients en Attente de Lunettes")

        self._btn_close = QPushButton(
            qta.icon("fa5s.times", color=theme_manager.colors()['text_muted']), ""
        )
        self._btn_close.setFixedSize(32, 32)
        self._btn_close.setCursor(Qt.PointingHandCursor)
        self._btn_close.clicked.connect(self.reject)

        h_lay.addWidget(self._title_icon)
        h_lay.addWidget(self._title_lbl)
        h_lay.addStretch()
        h_lay.addWidget(self._btn_close)
        root.addWidget(self._header)

        self._sep = QFrame()
        self._sep.setFrameShape(QFrame.HLine)
        self._sep.setFixedHeight(1)
        root.addWidget(self._sep)

        self._view = PatientsAttenteView(ctrl, code_session, parent=self)
        self._view.ouvrir_formulaire.connect(self._on_ouvrir_formulaire)
        root.addWidget(self._view, 1)

    def _on_ouvrir_formulaire(self, code_acte: str):
        self.ouvrir_nouveau_tab.emit(code_acte)
        self.accept()

    def _apply_theme(self):
        c = theme_manager.colors()
        primary = c['primary']

        self.setStyleSheet(f"""
            QDialog{{
                background:{c['bg_main']};
                border:1px solid {c['border']};
                border-radius:12px;
            }}
        """)
        self._header.setStyleSheet(
            f"background:{c['bg_card']}; border:none;"
        )
        self._title_icon.setPixmap(
            qta.icon("fa5s.glasses", color=primary).pixmap(QSize(20, 20))
        )
        self._title_lbl.setStyleSheet(
            f"font-size:15px; font-weight:700; color:{c['text_primary']}; border:none;"
        )
        self._btn_close.setStyleSheet(f"""
            QPushButton{{background:{c['bg_card']}; border:none; border-radius:6px;}}
            QPushButton:hover{{background:{c['danger']}22;}}
        """)
        self._btn_close.setIcon(qta.icon("fa5s.times", color=c['text_muted']))
        self._sep.setStyleSheet(f"background:{c['border_light']}; border:none;")
