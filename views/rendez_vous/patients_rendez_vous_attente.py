import qtawesome as qta
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from views.rendez_vous.styles import RendezVousStyles
from views.shared.theme_manager import theme_manager


class PatientCard(QFrame):
    planifier_signal = Signal(object)

    CARD_WIDTH = 170
    CARD_HEIGHT = 188

    def __init__(self, patient, parent=None):
        super().__init__(parent)
        self.patient = patient
        self._icon_rows = []
        self._setup_shadow()
        self._setup_ui()
        self._apply_theme()
        theme_manager.theme_changed.connect(self._apply_theme)

    def _setup_shadow(self):
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(18)
        self._shadow.setOffset(0, 5)
        self._shadow.setColor(QColor(0, 0, 0, 45))
        self.setGraphicsEffect(self._shadow)

    def enterEvent(self, event):
        self._shadow.setBlurRadius(28)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._shadow.setBlurRadius(18)
        super().leaveEvent(event)

    def _setup_ui(self):
        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 6)
        root.setSpacing(0)

        avatar_row = QHBoxLayout()
        self._avatar_lbl = QLabel()
        self._avatar_lbl.setFixedSize(30, 30)
        self._avatar_lbl.setAlignment(Qt.AlignCenter)
        avatar_row.addStretch()
        avatar_row.addWidget(self._avatar_lbl)
        avatar_row.addStretch()
        root.addLayout(avatar_row)
        root.addSpacing(3)

        nom = self.patient.get("nom", "")
        prenom = self.patient.get("prenom", "")
        nom_complet = f"{nom} {prenom}".strip() or "Patient inconnu"

        self._lbl_nom = QLabel(nom_complet)
        self._lbl_nom.setAlignment(Qt.AlignCenter)
        self._lbl_nom.setWordWrap(True)
        root.addWidget(self._lbl_nom)
        root.addSpacing(3)

        badge_row = QHBoxLayout()
        self._badge = QLabel("Attente rendez-vous")
        self._badge.setAlignment(Qt.AlignCenter)
        self._badge.setFixedHeight(16)
        badge_row.addStretch()
        badge_row.addWidget(self._badge)
        badge_row.addStretch()
        root.addLayout(badge_row)
        root.addSpacing(3)

        self._sep = QFrame()
        self._sep.setFrameShape(QFrame.HLine)
        self._sep.setFixedHeight(1)
        root.addWidget(self._sep)
        root.addSpacing(3)

        infos_layout = QVBoxLayout()
        infos_layout.setSpacing(2)

        urgent_value = "Urgent" if self.patient.get("urgent") else "Normal"
        champs = [
            ("fa5s.id-card", "Code", self.patient.get("code_patient", "-")),
            ("fa5s.calendar-day", "Visite", self._fmt_date(self.patient.get("date_visite"))),
            ("fa5s.notes-medical", "Type", str(self.patient.get("type_visite", "-")).replace("_", " ").title()),
            ("fa5s.exclamation-circle", "Priorite", urgent_value),
        ]

        for icon_name, label, valeur in champs:
            row_widget, icon_lbl, value_lbl = self._build_info_row(icon_name, label, valeur or "-")
            infos_layout.addWidget(row_widget)
            self._icon_rows.append((icon_lbl, icon_name, value_lbl))

        root.addLayout(infos_layout)
        root.addStretch()

        self._btn = QPushButton(" Planifier")
        self._btn.setFixedHeight(26)
        self._btn.setCursor(Qt.PointingHandCursor)
        self._btn.clicked.connect(lambda: self.planifier_signal.emit(self.patient))
        root.addWidget(self._btn)

    def _build_info_row(self, icon_name: str, label: str, value: str):
        container = QWidget()
        h = QHBoxLayout(container)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(12, 12)

        lbl_label = QLabel(f"{label}:")
        lbl_label.setFixedWidth(42)

        value_lbl = QLabel(value)
        value_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        value_lbl.setWordWrap(True)

        h.addWidget(icon_lbl)
        h.addWidget(lbl_label)
        h.addWidget(value_lbl)
        icon_lbl._label_widget = lbl_label
        return container, icon_lbl, value_lbl

    @staticmethod
    def _fmt_date(date_val) -> str:
        if not date_val:
            return "-"
        if hasattr(date_val, "strftime"):
            return date_val.strftime("%d/%m/%Y")
        return str(date_val)

    def _apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(
            f"""
            PatientCard {{
                background-color: {c['bg_card']};
                border: 1.5px solid {c['border']};
                border-radius: 16px;
            }}
            PatientCard:hover {{
                border: 1.5px solid {c['primary']};
                background-color: {c['hover']};
            }}
            """
        )
        self._avatar_lbl.setPixmap(qta.icon("fa5s.user-circle", color=c["primary"]).pixmap(QSize(30, 30)))
        self._lbl_nom.setStyleSheet(
            f"font-size: 9px; font-weight: 700; color: {c['text_primary']}; border: none;"
        )
        self._badge.setStyleSheet(
            f"""
            font-size: 7px;
            font-weight: 600;
            color: {c['warning']};
            background: {c['warning']}22;
            border-radius: 6px;
            padding: 1px 5px;
            border: 1px solid {c['warning']}55;
            """
        )
        self._sep.setStyleSheet(f"background: {c['border_light']}; border: none;")
        for icon_lbl, icon_name, value_lbl in self._icon_rows:
            icon_lbl.setPixmap(qta.icon(icon_name, color=c["primary"]).pixmap(QSize(11, 11)))
            icon_lbl._label_widget.setStyleSheet(
                f"font-size: 7px; font-weight: 600; color: {c['text_muted']}; border: none;"
            )
            value_lbl.setStyleSheet(
                f"font-size: 7px; color: {c['text_secondary']}; border: none;"
            )
        self._btn.setStyleSheet(RendezVousStyles.button_primary())
        self._btn.setIcon(qta.icon("fa5s.calendar-plus", color=c['text_inverse']))


class PatientsAttenteRendezVousView(QWidget):
    rdv_cree = Signal()
    NB_COLS = 5

    def __init__(self, ctrl, code_session: str, parent=None):
        super().__init__(parent)
        self.ctrl = ctrl
        self.code_session = code_session
        self._setup_ui()
        self._apply_theme()
        theme_manager.theme_changed.connect(self._apply_theme)
        self.charger_patients()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 12, 20, 12)
        root.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(8)

        self._h_icon = QLabel()
        self._h_icon.setFixedSize(20, 20)

        self._h_title = QLabel("Patients en attente de rendez-vous")
        self._h_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._h_badge_count = QLabel("0 patient(s)")

        header.addWidget(self._h_icon)
        header.addWidget(self._h_title)
        header.addStretch()
        header.addWidget(self._h_badge_count)
        root.addLayout(header)

        self._h_sep = QFrame()
        self._h_sep.setFrameShape(QFrame.HLine)
        self._h_sep.setFixedHeight(1)
        root.addWidget(self._h_sep)

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

        self._empty = self._build_empty_state()
        root.addWidget(self._empty)
        self._empty.hide()

    def _build_empty_state(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        self._empty_icon = QLabel()
        self._empty_icon.setAlignment(Qt.AlignCenter)
        self._empty_msg = QLabel("Aucun patient en attente de rendez-vous pour cette session.")
        self._empty_msg.setAlignment(Qt.AlignCenter)
        self._empty_msg.setWordWrap(True)

        layout.addStretch()
        layout.addWidget(self._empty_icon)
        layout.addWidget(self._empty_msg)
        layout.addStretch()
        return widget

    def charger_patients(self):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        patients = self.ctrl.obtenir_patients_attente_rendez_vous(self.code_session) or []

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
            card.planifier_signal.connect(self._on_planifier)
            row = idx // self.NB_COLS
            col = idx % self.NB_COLS
            self._grid.addWidget(card, row, col)

    def _on_planifier(self, patient):
        from views.rendez_vous.rendez_vous_form import RendezVousFormDialog

        dialog = RendezVousFormDialog(
            controleur=self.ctrl,
            code_session=self.code_session,
            code_visite=patient.get("code_visite", ""),
            rendez_vous_obj=None,
            parent=self,
        )
        if dialog.exec():
            self.charger_patients()
            self.rdv_cree.emit()

    def _apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"background: {c['bg_main']};")
        self._cards_container.setStyleSheet("background: transparent;")
        self._scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self._scroll.verticalScrollBar().setStyleSheet(RendezVousStyles.scrollbar())
        self._h_icon.setPixmap(qta.icon("fa5s.user-clock", color=c["warning"]).pixmap(QSize(18, 18)))
        self._h_title.setStyleSheet(
            f"font-size: 14px; font-weight: 700; color: {c['text_primary']}; border: none;"
        )
        self._h_badge_count.setStyleSheet(
            f"""
            font-size: 11px;
            font-weight: 600;
            color: {c['text_muted']};
            background: {c.get('bg_alt', c['bg_card'])};
            border-radius: 10px;
            padding: 2px 10px;
            border: 1px solid {c['border_light']};
            """
        )
        self._h_sep.setStyleSheet(f"background: {c['border_light']}; border: none;")
        self._empty_icon.setPixmap(qta.icon("fa5s.inbox", color=c["text_muted"]).pixmap(QSize(72, 72)))
        self._empty_msg.setStyleSheet(f"font-size: 14px; color: {c['text_muted']}; border: none;")


class PatientsAttenteDialog(QDialog):
    def __init__(self, ctrl, code_session: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Patients en attente de rendez-vous")
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

        self._header = QFrame()
        self._header.setFixedHeight(56)
        h_layout = QHBoxLayout(self._header)
        h_layout.setContentsMargins(20, 0, 16, 0)
        h_layout.setSpacing(10)

        self._title_icon = QLabel()
        self._title_icon.setFixedSize(22, 22)
        self._title_lbl = QLabel("Patients en attente de rendez-vous")

        self._btn_close = QPushButton()
        self._btn_close.setFixedSize(32, 32)
        self._btn_close.setCursor(Qt.PointingHandCursor)
        self._btn_close.setToolTip("Fermer")
        self._btn_close.clicked.connect(self.reject)

        h_layout.addWidget(self._title_icon)
        h_layout.addWidget(self._title_lbl)
        h_layout.addStretch()
        h_layout.addWidget(self._btn_close)
        root.addWidget(self._header)

        self._sep = QFrame()
        self._sep.setFrameShape(QFrame.HLine)
        self._sep.setFixedHeight(1)
        root.addWidget(self._sep)

        self._view = PatientsAttenteRendezVousView(ctrl, code_session, parent=self)
        root.addWidget(self._view, 1)

    def _apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {c['bg_main']};
                border: 1px solid {c['border']};
                border-radius: 12px;
            }}
            """
        )
        self._header.setStyleSheet(f"background: {c['bg_card']}; border: none; border-radius: 0px;")
        self._title_icon.setPixmap(qta.icon("fa5s.user-clock", color=c["warning"]).pixmap(QSize(20, 20)))
        self._title_lbl.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {c['text_primary']}; border: none;"
        )
        self._btn_close.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {c['danger']}22;
            }}
            """
        )
        self._btn_close.setIcon(qta.icon("fa5s.times", color=c["text_muted"]))
        self._sep.setStyleSheet(f"background: {c['border_light']}; border: none;")
