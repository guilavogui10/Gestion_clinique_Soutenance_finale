"""
=============================================================================
 PATIENTS EN ATTENTE DE CHIRURGIE
=============================================================================
 Composants :
   - PatientCard          : carte individuelle d'un patient
   - PatientsAttenteChirurgieView : grille scrollable de cartes
   - PatientsAttenteDialog     : dialog wrapper appelé depuis ChirurgieView

 Utilisation depuis ChirurgieView._ouvrir_formulaire :
   dialog = PatientsAttenteDialog(self.ctrl, self.code_session, parent=self)
   dialog.exec()
   self.charger_chururgies(self.code_session)
=============================================================================
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QScrollArea, QFrame,
    QGraphicsDropShadowEffect, QSizePolicy, QDialog
)

from views.shared.theme_manager import theme_manager
from views.chirurgie.styles import ChirurgieStyles


# =============================================================================
# PATIENT CARD
# =============================================================================

class PatientCard(QFrame):
    """
    Carte carrée arrondie représentant un patient en attente de chirurgie.

    Signals
    -------
    proceder_signal(object) : émis avec l'objet patient quand l'utilisateur
                              clique sur "Procéder la Chirurgie".
    """

    proceder_signal = Signal(object)

    # Dimensions fixes — cohérentes avec la grille
    CARD_WIDTH  = 160
    CARD_HEIGHT = 180

    def __init__(self, patient, parent=None):
        super().__init__(parent)
        self.patient      = patient
        self._icon_rows   = []   # [(icon_lbl, icon_name, value_lbl), ...]
        self._setup_shadow()
        self._setup_ui()
        self._apply_theme()
        theme_manager.theme_changed.connect(self._apply_theme)

    # ─── Shadow ───────────────────────────────────────────────────────────

    def _setup_shadow(self):
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(18)
        self._shadow.setOffset(0, 5)
        self._shadow.setColor(QColor(0, 0, 0, 45))
        self.setGraphicsEffect(self._shadow)

    # ─── Hover lift ───────────────────────────────────────────────────────

    def enterEvent(self, event):
        self._shadow.setBlurRadius(28)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._shadow.setBlurRadius(18)
        super().leaveEvent(event)

    # ─── UI ───────────────────────────────────────────────────────────────

    def _setup_ui(self):
        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 6)
        root.setSpacing(0)

        # ── Avatar centré ────────────────────────────────────────────────
        avatar_row = QHBoxLayout()
        self._avatar_lbl = QLabel()
        self._avatar_lbl.setFixedSize(40, 40)
        self._avatar_lbl.setAlignment(Qt.AlignCenter)
        self._avatar_lbl.setStyleSheet("border: none; background: transparent;")
        avatar_row.addStretch()
        avatar_row.addWidget(self._avatar_lbl)
        avatar_row.addStretch()
        root.addLayout(avatar_row)
        root.addSpacing(3)

        # ── Nom / prénom ─────────────────────────────────────────────────
        if isinstance(self.patient, dict):
            nom = self.patient.get('nom', '') or ''
            prenom = self.patient.get('prenom', '') or ''
        else:
            nom = getattr(self.patient, 'nom', '') or ''
            prenom = getattr(self.patient, 'prenom', '') or ''
        nom_complet = f"{nom} {prenom}".strip() or "Patient inconnu"

        self._lbl_nom = QLabel(nom_complet)
        self._lbl_nom.setAlignment(Qt.AlignCenter)
        self._lbl_nom.setWordWrap(True)
        self._lbl_nom.setStyleSheet("border: none;")
        root.addWidget(self._lbl_nom)
        root.addSpacing(3)

        # ── Badge statut ─────────────────────────────────────────────────
        badge_row = QHBoxLayout()
        self._badge = QLabel("Attente Chirurgie")
        self._badge.setAlignment(Qt.AlignCenter)
        self._badge.setFixedHeight(16)
        self._badge.setStyleSheet("border: none;")
        badge_row.addStretch()
        badge_row.addWidget(self._badge)
        badge_row.addStretch()
        root.addLayout(badge_row)
        root.addSpacing(3)

        # ── Séparateur ───────────────────────────────────────────────────
        self._sep = QFrame()
        self._sep.setFrameShape(QFrame.HLine)
        self._sep.setFixedHeight(1)
        root.addWidget(self._sep)
        root.addSpacing(3)

        # ── Infos patient ─────────────────────────────────────────────────
        infos_layout = QVBoxLayout()
        infos_layout.setSpacing(2)

        if isinstance(self.patient, dict):
            champs = [
                ("fa5s.id-card",        "Code",   self.patient.get('code_patient', None)),
                ("fa5s.calendar-day",   "Visite", self._fmt_date(self.patient.get('date_visite', None))),
                ("fa5s.notes-medical",  "Diag.",  self.patient.get('diagnostique', None)),
            ]
        else:
            champs = [
                ("fa5s.id-card",        "Code",   getattr(self.patient, 'code_patient', None)),
                ("fa5s.calendar-day",   "Visite", self._fmt_date(getattr(self.patient, 'date_visite', None))),
                ("fa5s.notes-medical",  "Diag.",  getattr(self.patient, 'diagnostique', None)),
            ]

        for icon_name, label, valeur in champs:
            row_widget, icon_lbl, value_lbl = self._build_info_row(
                icon_name, label,
                str(valeur).strip() if valeur else "—"
            )
            infos_layout.addWidget(row_widget)
            self._icon_rows.append((icon_lbl, icon_name, value_lbl))

        root.addLayout(infos_layout)
        root.addStretch()

        # ── Bouton ────────────────────────────────────────────────────────
        self._btn = QPushButton(" Procéder")
        self._btn.setFixedHeight(26)
        self._btn.setCursor(Qt.PointingHandCursor)
        self._btn.clicked.connect(lambda: self.proceder_signal.emit(self.patient))
        root.addWidget(self._btn)

    def _build_info_row(self, icon_name: str, label: str, value: str):
        """Construit une ligne icône + label + valeur dans un QWidget."""
        container = QWidget()
        container.setStyleSheet("background: transparent; border: none;")
        h = QHBoxLayout(container)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(16, 16)
        icon_lbl.setStyleSheet("border: none; background: transparent;")

        lbl_label = QLabel(f"{label}:")
        lbl_label.setFixedWidth(40)
        lbl_label.setStyleSheet("border: none; background: transparent;")

        value_lbl = QLabel(value)
        value_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        value_lbl.setWordWrap(True)
        value_lbl.setStyleSheet("border: none; background: transparent;")

        h.addWidget(icon_lbl)
        h.addWidget(lbl_label)
        h.addWidget(value_lbl)

        # On stocke le label pour le thème
        icon_lbl._label_widget = lbl_label

        return container, icon_lbl, value_lbl

    @staticmethod
    def _fmt_date(date_val) -> str:
        if not date_val:
            return "—"
        if hasattr(date_val, "strftime"):
            return date_val.strftime("%d/%m/%Y")
        return str(date_val)

    # ─── Thème ────────────────────────────────────────────────────────────

    def _apply_theme(self):
        c = theme_manager.colors()

        # Carte
        self.setStyleSheet(f"""
            PatientCard {{
                background-color : {c['bg_card']};
                border           : 1.5px solid {c['border']};
                border-radius    : 16px;
            }}
            PatientCard:hover {{
                border           : 1.5px solid {c['danger']};
                background-color : {c.get('bg_alt', c['bg_card'])};
            }}
        """)

        # Avatar
        self._avatar_lbl.setPixmap(
            qta.icon("fa5s.user-circle", color=c['danger']).pixmap(QSize(40, 40))
        )

        # Nom
        self._lbl_nom.setStyleSheet(
            f"font-size: 11px; font-weight: 700; color: {c['text_primary']}; border: none;"
        )

        # Badge
        self._badge.setStyleSheet(f"""
            font-size    : 9px;
            font-weight  : 600;
            color        : {c['danger']};
            background   : {c['danger']}22;
            border-radius: 6px;
            padding      : 1px 5px;
            border       : 1px solid {c['danger']}55;
        """)

        # Séparateur
        self._sep.setStyleSheet(f"background: {c['border_light']}; border: none;")

        # Lignes d'info
        for icon_lbl, icon_name, value_lbl in self._icon_rows:
            icon_lbl.setPixmap(
                qta.icon(icon_name, color=c['danger']).pixmap(QSize(15, 15))
            )
            # label (ex: "Code:")
            icon_lbl._label_widget.setStyleSheet(
                f"font-size: 9px; font-weight: 600; color: {c['text_muted']}; border: none;"
            )
            # valeur
            value_lbl.setStyleSheet(
                f"font-size: 9px; color: {c['text_secondary']}; border: none;"
            )

        # Bouton
        self._btn.setStyleSheet(ChirurgieStyles.button_primary())
        self._btn.setIcon(
            qta.icon("fa5s.procedures", color=c.get('text_inverse', '#ffffff'))
        )


# =============================================================================
# GRILLE PRINCIPALE
# =============================================================================

class PatientsAttenteChirurgieView(QWidget):
    """
    Widget principal : header + grille scrollable de PatientCard.
    Peut être embarqué dans n'importe quel layout ou dialog.
    """

    # Signal émis quand une chirurgie est créée pour rafraîchir la vue parent
    chirurgie_creee = Signal()
    # Signal émis pour ouvrir le formulaire dans l'onglet Nouveau
    ouvrir_formulaire = Signal(str)

    # Nombre de colonnes dans la grille
    NB_COLS = 5

    def __init__(self, ctrl, code_session: str, parent=None):
        super().__init__(parent)
        self.ctrl         = ctrl
        self.code_session = code_session
        self._setup_ui()
        self._apply_theme()
        theme_manager.theme_changed.connect(self._apply_theme)
        self.charger_patients()

    # ─── Construction UI ──────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 12, 20, 12)
        root.setSpacing(10)

        # ── Header ────────────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(8)

        self._h_icon = QLabel()
        self._h_icon.setFixedSize(20, 20)
        self._h_icon.setStyleSheet("border: none; background: transparent;")

        self._h_title = QLabel("Patients en Attente de Chirurgie")
        self._h_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._h_badge_count = QLabel("0 patient(s)")

        header.addWidget(self._h_icon)
        header.addWidget(self._h_title)
        header.addStretch()
        header.addWidget(self._h_badge_count)
        root.addLayout(header)

        # ── Séparateur header ─────────────────────────────────────────────
        self._h_sep = QFrame()
        self._h_sep.setFrameShape(QFrame.HLine)
        self._h_sep.setFixedHeight(1)
        root.addWidget(self._h_sep)

        # ── Scroll area ───────────────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setFrameShape(QFrame.NoFrame)

        self._cards_container = QWidget()
        self._grid = QGridLayout(self._cards_container)
        self._grid.setSpacing(12)
        self._grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self._scroll.setWidget(self._cards_container)
        root.addWidget(self._scroll, 1)

        # ── Empty state ───────────────────────────────────────────────────
        self._empty = self._build_empty_state()
        root.addWidget(self._empty)
        self._empty.hide()

    def _build_empty_state(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        self._empty_icon = QLabel()
        self._empty_icon.setAlignment(Qt.AlignCenter)
        self._empty_icon.setStyleSheet("border: none; background: transparent;")

        self._empty_msg = QLabel("Aucun patient en attente de chirurgie pour cette session.")
        self._empty_msg.setAlignment(Qt.AlignCenter)
        self._empty_msg.setWordWrap(True)
        self._empty_msg.setStyleSheet("border: none;")

        layout.addStretch()
        layout.addWidget(self._empty_icon)
        layout.addWidget(self._empty_msg)
        layout.addStretch()
        return widget

    # ─── Chargement données ───────────────────────────────────────────────

    def charger_patients(self):
        """Recharge la grille depuis le contrôleur."""
        # Vider proprement la grille
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        patients = self.ctrl.obtenir_patients_attente_chururgie(self.code_session)

        if not patients:
            self._scroll.hide()
            self._empty.show()
            self._h_badge_count.setText("0 patient(s)")
            return

        self._empty.hide()
        self._scroll.show()
        self._h_badge_count.setText(f"{len(patients)} patient(s)")

        for idx, patient in enumerate(patients):
            card = PatientCard(patient)
            card.proceder_signal.connect(self._on_proceder)
            row = idx // self.NB_COLS
            col = idx  % self.NB_COLS
            self._grid.addWidget(card, row, col)

    # ─── Action "Procéder" ────────────────────────────────────────────────

    def _on_proceder(self, patient):
        """Émet le signal ouvrir_formulaire avec le code_consultation du patient."""
        if isinstance(patient, dict):
            code_consultation = patient.get('code_consultation', '')
        else:
            code_consultation = getattr(patient, 'code_consultation', '')
        self.ouvrir_formulaire.emit(code_consultation)

    # ─── Thème ────────────────────────────────────────────────────────────

    def _apply_theme(self):
        c = theme_manager.colors()

        self.setStyleSheet(f"background: {c['bg_main']};")
        self._cards_container.setStyleSheet("background: transparent;")

        self._scroll.setStyleSheet(f"""
            QScrollArea {{
                background : transparent;
                border     : none;
            }}
        """)
        self._scroll.verticalScrollBar().setStyleSheet(ChirurgieStyles.scrollbar())

        # Header icon
        self._h_icon.setPixmap(
            qta.icon("fa5s.procedures", color=c['danger']).pixmap(QSize(18, 18))
        )

        # Header title
        self._h_title.setStyleSheet(
            f"font-size: 14px; font-weight: 700; color: {c['text_primary']}; border: none;"
        )

        # Badge compteur
        self._h_badge_count.setStyleSheet(f"""
            font-size    : 11px;
            font-weight  : 600;
            color        : {c['text_muted']};
            background   : {c.get('bg_alt', c['bg_card'])};
            border-radius: 10px;
            padding      : 2px 10px;
            border       : 1px solid {c['border_light']};
        """)

        # Séparateur
        self._h_sep.setStyleSheet(f"background: {c['border_light']}; border: none;")

        # Empty state
        self._empty_icon.setPixmap(
            qta.icon("fa5s.inbox", color=c['text_muted']).pixmap(QSize(72, 72))
        )
        self._empty_msg.setStyleSheet(
            f"font-size: 14px; color: {c['text_muted']}; border: none;"
        )


# =============================================================================
# DIALOG WRAPPER
# =============================================================================

class PatientsAttenteDialog(QDialog):
    """
    QDialog encapsulant PatientsAttenteChirurgieView.
    Appelé depuis ChirurgieView.on_patients_waiting.
    Émet ouvrir_nouveau_tab(code_consultation) pour basculer sur l'onglet Nouveau.
    """

    ouvrir_nouveau_tab = Signal(str)

    def __init__(self, ctrl, code_session: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Patients en Attente de Chirurgie")
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

        # ── Barre de titre custom ─────────────────────────────────────────
        self._header = QFrame()
        self._header.setFixedHeight(56)
        h_layout = QHBoxLayout(self._header)
        h_layout.setContentsMargins(20, 0, 16, 0)
        h_layout.setSpacing(10)

        self._title_icon = QLabel()
        self._title_icon.setFixedSize(22, 22)
        self._title_icon.setStyleSheet("border: none; background: transparent;")

        self._title_lbl = QLabel("Patients en Attente de Chirurgie")

        btn_close = QPushButton(qta.icon("fa5s.times", color=theme_manager.colors()['text_muted']), "")
        btn_close.setFixedSize(32, 32)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setToolTip("Fermer")
        btn_close.clicked.connect(self.reject)
        self._btn_close = btn_close

        h_layout.addWidget(self._title_icon)
        h_layout.addWidget(self._title_lbl)
        h_layout.addStretch()
        h_layout.addWidget(btn_close)
        root.addWidget(self._header)

        # ── Séparateur ────────────────────────────────────────────────────
        self._sep = QFrame()
        self._sep.setFrameShape(QFrame.HLine)
        self._sep.setFixedHeight(1)
        root.addWidget(self._sep)

        # ── Vue principale ────────────────────────────────────────────────
        self._view = PatientsAttenteChirurgieView(ctrl, code_session, parent=self)
        self._view.ouvrir_formulaire.connect(self._on_ouvrir_formulaire)
        root.addWidget(self._view, 1)

    def _on_ouvrir_formulaire(self, code_consultation: str):
        """Relaie le signal vers la vue parente puis ferme le dialog."""
        self.ouvrir_nouveau_tab.emit(code_consultation)
        self.accept()

    def _apply_theme(self):
        c = theme_manager.colors()

        self.setStyleSheet(f"""
            QDialog {{
                background : {c['bg_main']};
                border     : 1px solid {c['border']};
                border-radius: 12px;
            }}
        """)

        self._header.setStyleSheet(
            f"background: {c['bg_card']}; border: none; border-radius: 0px;"
        )

        self._title_icon.setPixmap(
            qta.icon("fa5s.procedures", color=c['danger']).pixmap(QSize(20, 20))
        )

        self._title_lbl.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {c['text_primary']}; border: none;"
        )

        self._btn_close.setStyleSheet(f"""
            QPushButton {{
                background   : transparent;
                border       : none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {c['danger']}22;
            }}
        """)
        self._btn_close.setIcon(qta.icon("fa5s.times", color=c['text_muted']))

        self._sep.setStyleSheet(f"background: {c['border_light']}; border: none;")
