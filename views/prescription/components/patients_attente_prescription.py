"""
Patients en attente de prescription - même logique que consultation
"""

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

from views.prescription.styles import PrescriptionStyles
from views.shared.theme_manager import theme_manager


class PatientCard(QFrame):
    proceder_signal = Signal(object)
    changer_statut_clicked = Signal(object)

    CARD_WIDTH = 170
    CARD_HEIGHT = 250

    def __init__(self, patient, parent=None):
        super().__init__(parent)
        self.patient = patient
        self._statut_patient = (
            patient.get("statut_patient", "") if isinstance(patient, dict)
            else getattr(patient, "statut_patient", "")
        ) or ""
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
        root.setContentsMargins(8, 6, 8, 6)
        root.setSpacing(0)

        avatar_row = QHBoxLayout()
        self._avatar_lbl = QLabel()
        self._avatar_lbl.setFixedSize(26, 26)
        self._avatar_lbl.setAlignment(Qt.AlignCenter)
        self._avatar_lbl.setStyleSheet("border: none; background: transparent;")
        avatar_row.addStretch()
        avatar_row.addWidget(self._avatar_lbl)
        avatar_row.addStretch()
        root.addLayout(avatar_row)
        root.addSpacing(2)

        nom = self.patient.get("nom", "") if isinstance(self.patient, dict) else getattr(self.patient, "nom", "")
        prenom = self.patient.get("prenom", "") if isinstance(self.patient, dict) else getattr(self.patient, "prenom", "")
        nom_complet = f"{nom} {prenom}".strip() or "Patient inconnu"

        self._lbl_nom = QLabel(nom_complet)
        self._lbl_nom.setAlignment(Qt.AlignCenter)
        self._lbl_nom.setWordWrap(True)
        self._lbl_nom.setStyleSheet("border: none;")
        root.addWidget(self._lbl_nom)
        root.addSpacing(2)

        badge_row = QHBoxLayout()
        badge_text = "En pharmacie" if "En pharmacie" in self._statut_patient else "Attente Pharmacie"
        self._badge = QLabel(badge_text)
        self._badge.setAlignment(Qt.AlignCenter)
        self._badge.setFixedHeight(16)
        self._badge.setStyleSheet("border: none;")
        badge_row.addStretch()
        badge_row.addWidget(self._badge)
        badge_row.addStretch()
        root.addLayout(badge_row)
        root.addSpacing(2)

        self._sep = QFrame()
        self._sep.setFrameShape(QFrame.HLine)
        self._sep.setFixedHeight(1)
        root.addWidget(self._sep)
        root.addSpacing(2)

        infos_layout = QVBoxLayout()
        infos_layout.setSpacing(1)

        champs = [
            ("fa5s.id-card", "Code", self._get_value("code_patient")),
            ("fa5s.calendar-day", "Visite", self._fmt_date(self._get_value("date_visite"))),
            ("fa5s.phone-alt", "Tel.", self._get_value("telephone") or "—"),
            ("fa5s.stethoscope", "Cons.", self._get_value("code_consultation") or "—"),
        ]

        for icon_name, label, valeur in champs:
            row_widget, icon_lbl, value_lbl = self._build_info_row(icon_name, label, str(valeur).strip() if valeur else "—")
            infos_layout.addWidget(row_widget)
            self._icon_rows.append((icon_lbl, icon_name, value_lbl))

        root.addLayout(infos_layout)
        root.addSpacing(4)

        self._btn = QPushButton(" Prescrire")
        self._btn.setFixedHeight(24)
        self._btn.setCursor(Qt.PointingHandCursor)
        self._btn.clicked.connect(lambda: self.proceder_signal.emit(self.patient))
        root.addWidget(self._btn)

        root.addSpacing(3)

        statut = self._statut_patient.strip()
        if statut == "En pharmacie":
            btn_label = " Fin pharmacie"
        else:
            btn_label = " Démarrer pharmacie"
        self._btn_statut = QPushButton(btn_label)
        self._btn_statut.setFixedHeight(24)
        self._btn_statut.setCursor(Qt.PointingHandCursor)
        self._btn_statut.clicked.connect(lambda: self.changer_statut_clicked.emit(self.patient))
        root.addWidget(self._btn_statut)

    def _get_value(self, key):
        if isinstance(self.patient, dict):
            return self.patient.get(key)
        return getattr(self.patient, key, None)

    def _build_info_row(self, icon_name: str, label: str, value: str):
        container = QWidget()
        container.setStyleSheet("background: transparent; border: none;")
        h = QHBoxLayout(container)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(12, 12)
        icon_lbl.setStyleSheet("border: none; background: transparent;")

        lbl_label = QLabel(f"{label}:")
        lbl_label.setFixedWidth(30)
        lbl_label.setStyleSheet("border: none; background: transparent;")

        value_lbl = QLabel(value)
        value_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        value_lbl.setWordWrap(True)
        value_lbl.setStyleSheet("border: none; background: transparent;")

        h.addWidget(icon_lbl)
        h.addWidget(lbl_label)
        h.addWidget(value_lbl)

        icon_lbl._label_widget = lbl_label
        return container, icon_lbl, value_lbl

    @staticmethod
    def _fmt_date(date_val) -> str:
        if not date_val:
            return "—"
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

        self._avatar_lbl.setPixmap(qta.icon("fa5s.user-circle", color=c["primary"]).pixmap(QSize(26, 26)))
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

        self._btn.setStyleSheet(PrescriptionStyles.button_primary())
        self._btn.setIcon(qta.icon("fa5s.prescription", color=c['text_inverse']))

        statut = self._statut_patient.strip()
        if statut == "En pharmacie":
            statut_bg = c['warning']
            statut_icon = "fa5s.check-circle"
        else:
            statut_bg = c['success']
            statut_icon = "fa5s.play-circle"
        self._btn_statut.setStyleSheet(f"""
            QPushButton {{
                background: {statut_bg};
                color: {c['text_inverse']};
                border: none;
                border-radius: 6px;
                font-size: 8px;
                font-weight: 700;
                padding: 0 4px;
            }}
            QPushButton:hover {{
                background: {statut_bg}cc;
            }}
        """)
        self._btn_statut.setIcon(qta.icon(statut_icon, color=c['text_inverse']))


class PatientsAttentePrescriptionView(QWidget):
    prescription_creee = Signal()
    ouvrir_formulaire = Signal(str)
    changer_statut_signal = Signal(object)
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
        self._h_icon.setStyleSheet("border: none; background: transparent;")

        self._h_title = QLabel("Patients en Attente de Prescription")
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

    def _build_empty_state(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        self._empty_icon = QLabel()
        self._empty_icon.setAlignment(Qt.AlignCenter)
        self._empty_icon.setStyleSheet("border: none; background: transparent;")

        self._empty_msg = QLabel("Aucun patient en attente de prescription pour cette session.")
        self._empty_msg.setAlignment(Qt.AlignCenter)
        self._empty_msg.setWordWrap(True)
        self._empty_msg.setStyleSheet("border: none;")

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

        patients = self.ctrl.obtenir_patients_en_attente(self.code_session)

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
            card.changer_statut_clicked.connect(self.changer_statut_signal.emit)
            row = idx // self.NB_COLS
            col = idx % self.NB_COLS
            self._grid.addWidget(card, row, col)

    def _on_proceder(self, patient):
        code_acte = patient.get("code_acte", "") if isinstance(patient, dict) else getattr(patient, "code_acte", "")
        self.ouvrir_formulaire.emit(code_acte)

    def _apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"background: {c['bg_card']};")
        self._cards_container.setStyleSheet(f"background: {c['bg_card']};")
        self._scroll.setStyleSheet(
            f"""
            QScrollArea {{
                background: {c['bg_card']};
                border: none;
            }}
            QScrollArea > QWidget {{
                background: {c['bg_card']};
            }}
            """
        )
        self._scroll.verticalScrollBar().setStyleSheet(PrescriptionStyles.scrollbar())
        self._h_icon.setPixmap(qta.icon("fa5s.hourglass-half", color=c["warning"]).pixmap(QSize(18, 18)))
        self._h_title.setStyleSheet(
            f"font-size: 14px; font-weight: 700; color: {c['text_primary']}; border: none;"
        )
        self._h_badge_count.setStyleSheet(
            f"""
            font-size: 11px;
            font-weight: 600;
            color: {c['text_muted']};
            background: {c['bg_card']};
            border-radius: 10px;
            padding: 2px 10px;
            border: 1px solid {c['border_light']};
            """
        )
        self._h_sep.setStyleSheet(f"background: {c['border_light']}; border: none;")
        self._empty_icon.setPixmap(qta.icon("fa5s.inbox", color=c["text_muted"]).pixmap(QSize(72, 72)))
        self._empty_msg.setStyleSheet(
            f"font-size: 14px; color: {c['text_muted']}; border: none;"
        )


class PatientsAttentePrescriptionDialog(QDialog):
    ouvrir_nouveau_tab = Signal(str)

    def __init__(self, ctrl, code_session: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Patients en Attente de Prescription")
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
        self._title_icon.setStyleSheet("border: none; background: transparent;")

        self._title_lbl = QLabel("Patients en Attente de Prescription")

        self._btn_close = QPushButton("")
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

        self._view = PatientsAttentePrescriptionView(ctrl, code_session, parent=self)
        self._view.ouvrir_formulaire.connect(self._on_ouvrir_formulaire)
        root.addWidget(self._view, 1)

    def _on_ouvrir_formulaire(self, code_acte: str):
        self.ouvrir_nouveau_tab.emit(code_acte)
        self.accept()

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
        self._title_icon.setPixmap(qta.icon("fa5s.hourglass-half", color=c["warning"]).pixmap(QSize(20, 20)))
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
