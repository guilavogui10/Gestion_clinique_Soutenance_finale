"""
Dialog d'enregistrement du choix patient pour un acte médical.

Choix :
  • maintenant  → exécution immédiate, mise en file d'attente
  • plus_tard   → planification, rendez-vous
  • ailleurs    → exécution externe, refus interne

Selon le choix, des champs supplémentaires apparaissent (raison, date RDV, etc.).
"""
import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QGraphicsDropShadowEffect, QButtonGroup,
    QRadioButton, QTextEdit, QDateTimeEdit, QWidget, QStackedWidget,
)
from PySide6.QtCore import QDateTime
from views.shared.theme_manager import theme_manager
from views.shared.message_box import CustomMessageBox


class ChoixPatientDialog(QDialog):
    """
    Enregistre le choix patient pour un acte.
    Emet `choix_valide` avec (id_acte, choix, options_dict).
    """
    choix_valide = Signal(int, str, dict)

    def __init__(self, controleur, acte_row: dict, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self.acte_row = acte_row

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(520, 520)

        self._init_ui()
        theme_manager.theme_changed.connect(self._apply_theme)
        self._apply_theme()

    # =========================================================================
    def _init_ui(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 70))

        self.container = QFrame(self)
        self.container.setGraphicsEffect(shadow)
        self.container.setObjectName("ChoixContainer")

        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header ─────────────────────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(68)
        header.setObjectName("ChoixHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 16, 0)

        self._icon_lbl = QLabel()
        self._icon_lbl.setFixedSize(32, 32)
        self._title_lbl = QLabel("Choix du patient")
        self._title_lbl.setObjectName("ChoixHeaderTitle")
        acte_id = self.acte_row.get("id_acte", "")
        sub = QLabel(f"Acte #{acte_id} — {self.acte_row.get('type_acte', '')}")
        sub.setObjectName("ChoixHeaderSub")

        vbox = QVBoxLayout()
        vbox.setSpacing(2)
        vbox.addWidget(self._title_lbl)
        vbox.addWidget(sub)

        header_layout.addWidget(self._icon_lbl)
        header_layout.addSpacing(10)
        header_layout.addLayout(vbox, 1)

        btn_close = QPushButton()
        btn_close.setFixedSize(32, 32)
        btn_close.setObjectName("BtnClose")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.reject)
        self._btn_close = btn_close
        header_layout.addWidget(btn_close)
        main_layout.addWidget(header)

        # Corps ───────────────────────────────────────────────────────────────
        body = QFrame()
        body.setObjectName("ChoixBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 20, 24, 20)
        body_layout.setSpacing(16)

        # Bandeau info acte
        info_frame = QFrame()
        info_frame.setObjectName("InfoBandeau")
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(14, 10, 14, 10)
        decision = self.acte_row.get("decision_medicale", "")[:80]
        info_layout.addWidget(QLabel(f"<b>Décision :</b> {decision}"))
        body_layout.addWidget(info_frame)

        # Sélection du choix
        choice_lbl = QLabel("Que souhaite faire le patient ?")
        choice_lbl.setObjectName("SectionLabel")
        body_layout.addWidget(choice_lbl)

        self.btn_group = QButtonGroup(self)

        self.radio_maintenant = self._radio_card(
            "fa5s.bolt",        "Maintenant",
            "Exécution immédiate — entrée en file d'attente",
            "maintenant", "#10B981"
        )
        self.radio_plus_tard = self._radio_card(
            "fa5s.calendar-plus", "Plus tard",
            "Reporter — planification d'un rendez-vous",
            "plus_tard", "#3B82F6"
        )
        self.radio_ailleurs = self._radio_card(
            "fa5s.external-link-alt", "Ailleurs",
            "Réalisation externe — refus interne",
            "ailleurs", "#EF4444"
        )

        for radio, widget in (self.radio_maintenant, self.radio_plus_tard, self.radio_ailleurs):
            self.btn_group.addButton(radio)
            body_layout.addWidget(widget)

        # Zone contextuelle (stacked)
        self.stacked = QStackedWidget()
        self.stacked.setFixedHeight(80)

        # Page 0 – maintenant : code visite
        page_now = QWidget()
        pl = QVBoxLayout(page_now)
        pl.setContentsMargins(0, 0, 0, 0)
        lbl_v = QLabel("Code visite *")
        lbl_v.setObjectName("FieldLabel")
        self.edit_code_visite = QLineEdit()
        self.edit_code_visite.setPlaceholderText("ex: VST-2024-0012")
        pl.addWidget(lbl_v)
        pl.addWidget(self.edit_code_visite)
        self.stacked.addWidget(page_now)

        # Page 1 – plus_tard : date RDV
        page_later = QWidget()
        pll = QVBoxLayout(page_later)
        pll.setContentsMargins(0, 0, 0, 0)
        lbl_rdv = QLabel("Date du rendez-vous *")
        lbl_rdv.setObjectName("FieldLabel")
        self.edit_date_rdv = QDateTimeEdit()
        self.edit_date_rdv.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.edit_date_rdv.setCalendarPopup(True)
        self.edit_date_rdv.setDisplayFormat("dd/MM/yyyy HH:mm")
        pll.addWidget(lbl_rdv)
        pll.addWidget(self.edit_date_rdv)
        self.stacked.addWidget(page_later)

        # Page 2 – ailleurs : raison
        page_ailleurs = QWidget()
        pal = QVBoxLayout(page_ailleurs)
        pal.setContentsMargins(0, 0, 0, 0)
        lbl_r = QLabel("Raison (optionnel)")
        lbl_r.setObjectName("FieldLabel")
        self.edit_raison_ailleurs = QLineEdit()
        self.edit_raison_ailleurs.setPlaceholderText("Motif du refus interne…")
        pal.addWidget(lbl_r)
        pal.addWidget(self.edit_raison_ailleurs)
        self.stacked.addWidget(page_ailleurs)

        body_layout.addWidget(self.stacked)
        main_layout.addWidget(body)

        # Footer ──────────────────────────────────────────────────────────────
        footer = QFrame()
        footer.setObjectName("ChoixFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 12, 24, 12)
        footer_layout.setSpacing(10)
        footer_layout.addStretch()

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setObjectName("BtnCancel")
        self.btn_cancel.setFixedHeight(40)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_validate = QPushButton("Valider le choix")
        self.btn_validate.setObjectName("BtnValidate")
        self.btn_validate.setFixedHeight(40)
        self.btn_validate.setCursor(Qt.PointingHandCursor)
        self.btn_validate.clicked.connect(self._on_validate)

        footer_layout.addWidget(self.btn_cancel)
        footer_layout.addWidget(self.btn_validate)
        main_layout.addWidget(footer)

        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(20, 20, 20, 20)
        wrapper.addWidget(self.container)

        # Connexions radio → stacked
        self.radio_maintenant[0].toggled.connect(lambda on: self.stacked.setCurrentIndex(0) if on else None)
        self.radio_plus_tard[0].toggled.connect(lambda on: self.stacked.setCurrentIndex(1) if on else None)
        self.radio_ailleurs[0].toggled.connect(lambda on: self.stacked.setCurrentIndex(2) if on else None)
        self.radio_maintenant[0].setChecked(True)

    def _radio_card(self, icon_name, title, subtitle, value, color):
        """Crée une carte radio stylisée. Retourne (QRadioButton, QFrame)."""
        frame = QFrame()
        frame.setObjectName("RadioCard")
        frame.setProperty("choix_value", value)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        radio = QRadioButton()
        radio.setObjectName("RadioBtn")
        radio.setProperty("choix_value", value)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(icon_name, color=color).pixmap(22, 22))
        icon_lbl.setFixedSize(24, 24)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)
        title_lbl = QLabel(f"<b>{title}</b>")
        title_lbl.setObjectName("RadioTitle")
        sub_lbl = QLabel(subtitle)
        sub_lbl.setObjectName("RadioSub")
        text_layout.addWidget(title_lbl)
        text_layout.addWidget(sub_lbl)

        layout.addWidget(radio)
        layout.addWidget(icon_lbl)
        layout.addLayout(text_layout, 1)

        frame.mousePressEvent = lambda _: radio.setChecked(True)
        return radio, frame

    # =========================================================================
    def _on_validate(self):
        checked = self.btn_group.checkedButton()
        if not checked:
            CustomMessageBox.warning(self, "Choix requis", "Veuillez sélectionner un choix.")
            return

        choix = checked.property("choix_value")
        options = {}

        if choix == "maintenant":
            code_visite = self.edit_code_visite.text().strip()
            if not code_visite:
                CustomMessageBox.warning(self, "Champ manquant", "Le code visite est obligatoire.")
                return
            options["code_visite"] = code_visite

        elif choix == "plus_tard":
            options["date_rdv"] = self.edit_date_rdv.dateTime().toString("yyyy-MM-dd HH:mm:ss")

        elif choix == "ailleurs":
            options["raison"] = self.edit_raison_ailleurs.text().strip()

        id_acte = self.acte_row.get("id_acte")
        self.choix_valide.emit(id_acte, choix, options)
        self.accept()

    # =========================================================================
    def _apply_theme(self):
        c = theme_manager.colors()
        self.container.setStyleSheet(f"""
            QFrame#ChoixContainer {{
                background: {c['bg_card']};
                border-radius: 20px;
                border: 1px solid {c['border']};
            }}
            QFrame#ChoixHeader {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {c['bg_card']}, stop:1 {c['bg_main']});
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
            }}
            QLabel#ChoixHeaderTitle {{
                font-size: 16px; font-weight: bold; color: {c['text_primary']};
                background: transparent;
            }}
            QLabel#ChoixHeaderSub {{
                font-size: 12px; color: {c['text_secondary']};
                background: transparent;
            }}
            QFrame#ChoixBody {{ background: {c['bg_card']}; }}
            QFrame#ChoixFooter {{
                background: {c['bg_main']};
                border-bottom-left-radius: 20px;
                border-bottom-right-radius: 20px;
                border-top: 1px solid {c['border']};
            }}
            QFrame#InfoBandeau {{
                background: {c['primary_light']};
                border-radius: 10px;
                border: 1px solid {c['border']};
            }}
            QLabel#SectionLabel {{
                font-size: 13px; font-weight: 600; color: {c['text_primary']};
                background: transparent;
            }}
            QFrame#RadioCard {{
                background: {c['bg_main']};
                border: 1px solid {c['border']};
                border-radius: 10px;
            }}
            QFrame#RadioCard:hover {{
                background: {c['primary_light']};
                border: 1px solid {c['primary']};
            }}
            QLabel#RadioTitle {{ font-size: 13px; color: {c['text_primary']}; background: transparent; }}
            QLabel#RadioSub   {{ font-size: 11px; color: {c['text_muted']};    background: transparent; }}
            QLabel#FieldLabel {{ color: {c['text_secondary']}; font-size: 12px; font-weight:600; background:transparent; }}
            QLineEdit, QDateTimeEdit {{
                padding: 8px 12px;
                border: 1px solid {c['border']};
                border-radius: 8px;
                background: {c['bg_input']};
                color: {c['text_primary']};
                font-size: 13px;
            }}
            QLineEdit:focus, QDateTimeEdit:focus {{
                border: 2px solid {c['border_focus']};
            }}
            QPushButton#BtnValidate {{
                background: {c['primary']};
                color: white;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                padding: 0 24px;
                border: none;
            }}
            QPushButton#BtnValidate:hover {{ background: {c['primary_hover']}; }}
            QPushButton#BtnCancel {{
                background: {c['bg_main']};
                color: {c['text_secondary']};
                border-radius: 8px;
                font-size: 14px;
                padding: 0 18px;
                border: 1px solid {c['border']};
            }}
            QPushButton#BtnClose {{
                background: transparent;
                border: none;
                border-radius: 6px;
            }}
            QPushButton#BtnClose:hover {{ background: {c['danger_bg']}; }}
        """)
        self._btn_close.setIcon(qta.icon("fa5s.times", color=c["danger"]))
        self._icon_lbl.setPixmap(qta.icon("fa5s.user-check", color=c["primary"]).pixmap(28, 28))
