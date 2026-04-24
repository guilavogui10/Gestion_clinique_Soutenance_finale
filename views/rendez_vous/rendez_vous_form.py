import os
from datetime import datetime, timedelta

import qtawesome as qta
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.modele_rendez_vous import RendezVous
from views.shared.message_box import CustomMessageBox
from views.shared.theme_manager import theme_manager


class RendezVousFormDialog(QDialog):
    STATUTS = [
        ("attente", "En attente"),
        ("confirme", "Confirme"),
        ("en_cours", "En cours"),
        ("termine", "Termine"),
        ("annule", "Annule"),
        ("absent", "Absent"),
        ("reporte", "Reporte"),
    ]

    def __init__(
        self,
        controleur,
        code_session: str,
        code_visite: str = "",
        code_personnel: str = "",
        rendez_vous_obj=None,
        parent=None,
    ):
        super().__init__(parent)
        self.controleur = controleur
        self.code_session = code_session
        self.code_visite_init = code_visite
        self.code_personnel_init = code_personnel
        self.rendez_vous_obj = rendez_vous_obj
        self.info_cabinet = self.controleur.get_cabinet_info()

        self._visites_attente = []
        self._personnels = []

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(980, 540)

        self._charger_donnees_combos()
        self._init_ui()
        self._connecter_validations()

        if self.rendez_vous_obj:
            self._remplir_champs()
        else:
            if self.code_visite_init:
                self._preselectionner_visite(self.code_visite_init)
            if self.code_personnel_init:
                self._preselectionner_personnel(self.code_personnel_init)
            self._valider_formulaire()

    def _charger_donnees_combos(self):
        try:
            self._visites_attente = self.controleur.obtenir_patients_attente_rendez_vous(self.code_session) or []
        except Exception:
            self._visites_attente = []
        try:
            self._personnels = self.controleur.lister_personnel() or []
        except Exception:
            self._personnels = []

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)

        self.container = QFrame()
        self.container.setObjectName("MainContainer")
        self._apply_container_style()

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 70))
        self.container.setGraphicsEffect(shadow)

        main = QVBoxLayout(self.container)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        self._setup_header(main)
        self._setup_body(main)
        self._setup_footer(main)
        outer.addWidget(self.container)

        theme_manager.theme_changed.connect(self.apply_theme)

    def _apply_container_style(self):
        c = theme_manager.colors()
        self.container.setStyleSheet(
            f"""
            QFrame#MainContainer {{
                background-color: {c['bg_card']};
                border-radius: 20px;
                border: 1px solid {c['border']};
            }}
            QLabel {{
                color: {c['text_primary']};
                font-size: 12px;
                background-color: transparent;
            }}
            QLabel#CabinetName {{
                font-size: 17px;
                font-weight: bold;
                color: {c['danger']};
            }}
            QLabel#SectionTitle {{
                color: {c['primary']};
                font-weight: bold;
                font-size: 11px;
            }}
            QLabel#ErrLabel {{
                color: {c['danger']};
                font-size: 10px;
                font-style: italic;
            }}
            QLineEdit, QDateTimeEdit, QComboBox {{
                padding: 8px 10px;
                border: 1px solid {c['border']};
                border-radius: 8px;
                background-color: {c['bg_input']};
                font-size: 12px;
                color: {c['text_primary']};
            }}
            QLineEdit:focus, QDateTimeEdit:focus, QComboBox:focus {{
                border: 2px solid {c['border_focus']};
                background-color: {c['bg_card']};
            }}
            QLineEdit:disabled {{
                background-color: {c['bg_main']};
                color: {c['primary']};
                border: 1px solid {c['border_light']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                width: 0;
                height: 0;
            }}
            QComboBox QAbstractItemView {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                color: {c['text_primary']};
                selection-background-color: {c['primary_light']};
                selection-color: {c['primary']};
                outline: none;
            }}
            QPushButton#SaveBtn {{
                background-color: {c['primary']};
                color: {c['text_inverse']};
                border-radius: 10px;
                font-weight: bold;
                font-size: 13px;
                padding: 10px;
            }}
            QPushButton#SaveBtn:disabled {{
                background-color: {c['border']};
                color: {c['text_muted']};
            }}
            QPushButton#CancelBtn {{
                background-color: {c['bg_main']};
                color: {c['text_secondary']};
                border-radius: 10px;
                padding: 10px;
                font-size: 13px;
                border: 1px solid {c['border']};
            }}
            """
        )

    def apply_theme(self):
        c = theme_manager.colors()
        self._apply_container_style()
        self._apply_header_style()
        self._apply_footer_style()
        self._apply_save_btn_style()
        self.sep.setStyleSheet(f"background-color: {c['border_light']}; border: none;")
        self._valider_formulaire()

    def _setup_header(self, parent_layout):
        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(65)
        self._apply_header_style()
        layout = QHBoxLayout(self.header_frame)
        layout.setContentsMargins(25, 0, 25, 0)
        c = theme_manager.colors()

        cab = QVBoxLayout()
        cab.setSpacing(1)
        nom = QLabel(self.info_cabinet.get("nom_cabinet", "Cabinet Medical"))
        nom.setObjectName("CabinetName")
        adr = QLabel(self.info_cabinet.get("adresse_cabinet", "Service des rendez-vous"))
        adr.setStyleSheet(f"color: {c['text_muted']}; font-size: 11px;")
        cab.addWidget(nom)
        cab.addWidget(adr)
        layout.addLayout(cab)
        layout.addStretch()

        titre = "Nouveau Rendez-vous" if not self.rendez_vous_obj else "Modifier Rendez-vous"
        title_lbl = QLabel(titre)
        title_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {c['primary']};")
        layout.addWidget(title_lbl)
        layout.addStretch()

        logo_path = self.info_cabinet.get("logo_url")
        if logo_path and os.path.exists(logo_path):
            logo_lbl = QLabel()
            logo_lbl.setPixmap(QPixmap(logo_path).scaled(45, 45, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            layout.addWidget(logo_lbl)

        parent_layout.addWidget(self.header_frame)

    def _apply_header_style(self):
        c = theme_manager.colors()
        self.header_frame.setStyleSheet(
            f"""
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                stop:0 {c['primary_light']}, stop:0.45 {c['bg_card']}, stop:1 {c['bg_card']});
            border-top-left-radius: 20px;
            border-top-right-radius: 20px;
            border-bottom: 1px solid {c['border_light']};
            """
        )

    def _setup_body(self, parent_layout):
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(body)
        layout.setContentsMargins(25, 18, 25, 20)
        layout.setSpacing(30)

        layout.addLayout(self._left_column(), 5)

        self.sep = QFrame()
        self.sep.setFrameShape(QFrame.VLine)
        self.sep.setFixedWidth(1)
        self.sep.setStyleSheet(f"background-color: {theme_manager.colors()['border_light']}; border: none;")
        layout.addWidget(self.sep)

        layout.addLayout(self._right_column(), 5)
        parent_layout.addWidget(body)

    def _left_column(self):
        col = QVBoxLayout()
        col.setSpacing(6)

        self._section_title(col, "Patient & visite", "fa5s.user-clock")

        col.addWidget(self._field_label("Visite liee (patient en attente de rendez-vous)"))
        self.combo_visite = QComboBox()
        self.combo_visite.setFixedHeight(36)
        self.combo_visite.addItem("-- Selectionner une visite --", "")
        for visite in self._visites_attente:
            nom = f"{visite.get('nom', '')} {visite.get('prenom', '')}".strip()
            label = (
                f"{visite.get('code_visite', '')}  |  {nom or 'Patient'}  |  "
                f"{self._fmt_date(visite.get('date_visite'))}"
            )
            self.combo_visite.addItem(label, visite)
        col.addWidget(self.combo_visite)
        self._err_visite = self._err_label()
        col.addWidget(self._err_visite)

        col.addWidget(self._field_label("Code visite"))
        self.edit_code_visite = QLineEdit()
        self.edit_code_visite.setPlaceholderText("Selectionnez une visite...")
        self.edit_code_visite.setFixedHeight(36)
        self.edit_code_visite.setReadOnly(True)
        col.addWidget(self.edit_code_visite)

        col.addWidget(self._field_label("Patient"))
        self.edit_patient = QLineEdit()
        self.edit_patient.setPlaceholderText("Le patient apparaitra ici")
        self.edit_patient.setFixedHeight(36)
        self.edit_patient.setReadOnly(True)
        col.addWidget(self.edit_patient)

        col.addWidget(self._field_label("Type de visite"))
        self.edit_type_visite = QLineEdit()
        self.edit_type_visite.setPlaceholderText("Information de la visite")
        self.edit_type_visite.setFixedHeight(36)
        self.edit_type_visite.setReadOnly(True)
        col.addWidget(self.edit_type_visite)

        col.addStretch()
        return col

    def _right_column(self):
        col = QVBoxLayout()
        col.setSpacing(6)

        self._section_title(col, "Planification", "fa5s.calendar-alt")

        col.addWidget(self._field_label("Personnel medical"))
        self.combo_personnel = QComboBox()
        self.combo_personnel.setFixedHeight(36)
        self.combo_personnel.addItem("-- Selectionner un personnel --", "")
        for personnel in self._personnels:
            label = (
                f"{personnel.get('code', '')}  |  "
                f"{personnel.get('nom', '')} {personnel.get('prenom', '')}  |  "
                f"{personnel.get('fonction', '')}"
            )
            self.combo_personnel.addItem(label, personnel.get("code", ""))
        col.addWidget(self.combo_personnel)
        self._err_personnel = self._err_label()
        col.addWidget(self._err_personnel)

        col.addWidget(self._field_label("Date et heure du rendez-vous"))
        self.edit_date = QDateTimeEdit()
        self.edit_date.setCalendarPopup(True)
        self.edit_date.setDateTime(self._default_qdatetime())
        self.edit_date.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.edit_date.setFixedHeight(36)
        col.addWidget(self.edit_date)
        self._err_date = self._err_label()
        col.addWidget(self._err_date)

        col.addWidget(self._field_label("Statut du rendez-vous"))
        self.combo_statut = QComboBox()
        self.combo_statut.setFixedHeight(36)
        for code, label in self.STATUTS:
            self.combo_statut.addItem(label, code)
        col.addWidget(self.combo_statut)
        self._err_statut = self._err_label()
        col.addWidget(self._err_statut)

        col.addWidget(self._field_label("Session active"))
        self.edit_session = QLineEdit()
        self.edit_session.setText(self.code_session or "")
        self.edit_session.setReadOnly(True)
        self.edit_session.setFixedHeight(36)
        col.addWidget(self.edit_session)

        col.addStretch()
        return col

    def _setup_footer(self, parent_layout):
        self.footer_frame = QFrame()
        self.footer_frame.setFixedHeight(62)
        self._apply_footer_style()
        layout = QHBoxLayout(self.footer_frame)
        layout.setContentsMargins(25, 0, 25, 0)
        layout.setSpacing(15)

        c = theme_manager.colors()
        self.btn_cancel = QPushButton(qta.icon("fa5s.times", color=c["text_muted"]), " Annuler")
        self.btn_cancel.setObjectName("CancelBtn")
        self.btn_cancel.setFixedHeight(42)
        self.btn_cancel.clicked.connect(self.reject)

        label_save = " Enregistrer" if not self.rendez_vous_obj else " Mettre a jour"
        self.btn_save = QPushButton(qta.icon("fa5s.save", color=c["text_inverse"]), label_save)
        self.btn_save.setObjectName("SaveBtn")
        self.btn_save.setFixedHeight(42)
        self.btn_save.setEnabled(False)
        self._apply_save_btn_style()
        self.btn_save.clicked.connect(self._soumettre)

        layout.addWidget(self.btn_cancel, 1)
        layout.addWidget(self.btn_save, 2)
        parent_layout.addWidget(self.footer_frame)

    def _apply_footer_style(self):
        c = theme_manager.colors()
        self.footer_frame.setStyleSheet(
            f"""
            background-color: {c['bg_main']};
            border-bottom-left-radius: 20px;
            border-bottom-right-radius: 20px;
            border-top: 1px solid {c['border_light']};
            """
        )

    def _apply_save_btn_style(self):
        c = theme_manager.colors()
        self.btn_save.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {c['border']};
                color: {c['text_muted']};
                border-radius: 10px;
                font-weight: bold;
                font-size: 13px;
                padding: 10px;
                border: none;
            }}
            QPushButton:enabled {{
                background-color: {c['primary']};
                color: {c['text_inverse']};
            }}
            QPushButton:enabled:hover {{
                background-color: {c['primary_hover']};
                color: {c['text_inverse']};
            }}
            """
        )

    def _field_label(self, texte: str):
        c = theme_manager.colors()
        lbl = QLabel(texte)
        lbl.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']}; font-size: 11px;")
        return lbl

    def _err_label(self):
        c = theme_manager.colors()
        lbl = QLabel("")
        lbl.setObjectName("ErrLabel")
        lbl.setStyleSheet(f"color: {c['danger']}; font-size: 10px; font-style: italic;")
        lbl.setVisible(False)
        return lbl

    def _section_title(self, layout, titre: str, icone: str):
        c = theme_manager.colors()
        hbox = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(qta.icon(icone, color=c["primary"]).pixmap(13, 13))
        lbl = QLabel(titre)
        lbl.setObjectName("SectionTitle")
        hbox.addWidget(ico)
        hbox.addSpacing(5)
        hbox.addWidget(lbl)
        hbox.addStretch()
        layout.addLayout(hbox)

    def _connecter_validations(self):
        self.combo_visite.currentIndexChanged.connect(self._on_visite_changed)
        self.combo_personnel.currentIndexChanged.connect(self._valider_formulaire)
        self.combo_statut.currentIndexChanged.connect(self._valider_formulaire)
        self.edit_date.dateTimeChanged.connect(self._valider_formulaire)

    def _on_visite_changed(self):
        data = self.combo_visite.currentData()
        if data and isinstance(data, dict):
            self.edit_code_visite.setText(str(data.get("code_visite", "")))
            patient = f"{data.get('nom', '')} {data.get('prenom', '')}".strip()
            self.edit_patient.setText(patient)
            type_visite = str(data.get("type_visite", "") or "").replace("_", " ").title()
            self.edit_type_visite.setText(type_visite)
        else:
            self.edit_code_visite.clear()
            self.edit_patient.clear()
            self.edit_type_visite.clear()
        self._valider_formulaire()

    def _valider_formulaire(self):
        tout_valide = True

        if not self.combo_visite.currentData():
            self._err_visite.setText("Veuillez selectionner une visite")
            self._err_visite.setVisible(True)
            tout_valide = False
        else:
            self._err_visite.setVisible(False)

        if not self.combo_personnel.currentData():
            self._err_personnel.setText("Veuillez selectionner un personnel")
            self._err_personnel.setVisible(True)
            tout_valide = False
        else:
            self._err_personnel.setVisible(False)

        ok, msg = self.controleur.valider_date(self.edit_date.dateTime().toPython())
        self._err_date.setText(msg if not ok else "")
        self._err_date.setVisible(not ok)
        if not ok:
            tout_valide = False

        statut = self.combo_statut.currentData() or self.combo_statut.currentText()
        ok, msg = self.controleur.valider_statut(statut)
        self._err_statut.setText(msg if not ok else "")
        self._err_statut.setVisible(not ok)
        if not ok:
            tout_valide = False

        self.btn_save.setEnabled(tout_valide)

    def _preselectionner_visite(self, code_visite: str):
        for i in range(self.combo_visite.count()):
            data = self.combo_visite.itemData(i)
            if isinstance(data, dict) and data.get("code_visite") == code_visite:
                self.combo_visite.setCurrentIndex(i)
                return

        if not code_visite:
            return

        extra_data = {
            "code_visite": code_visite,
            "nom": getattr(self.rendez_vous_obj, "patient_nom", ""),
            "prenom": getattr(self.rendez_vous_obj, "patient_prenom", ""),
            "type_visite": getattr(self.rendez_vous_obj, "type_visite", ""),
        }
        nom_complet = f"{extra_data['nom']} {extra_data['prenom']}".strip()
        label = f"{code_visite}  |  {nom_complet or 'Patient'}"
        self.combo_visite.addItem(label, extra_data)
        self.combo_visite.setCurrentIndex(self.combo_visite.count() - 1)

    def _preselectionner_personnel(self, code_personnel: str):
        for i in range(self.combo_personnel.count()):
            if self.combo_personnel.itemData(i) == code_personnel:
                self.combo_personnel.setCurrentIndex(i)
                break

    def _remplir_champs(self):
        rdv = self.rendez_vous_obj
        self._preselectionner_visite(rdv.code_visite)
        self._preselectionner_personnel(rdv.code_personnel)
        self.combo_statut.setCurrentIndex(max(self.combo_statut.findData(rdv.statut_rendez_vous), 0))
        self.edit_session.setText(rdv.code_session or self.code_session or "")

        date_value = self._to_qdatetime(rdv.date_rendez_vous)
        if date_value.isValid():
            self.edit_date.setDateTime(date_value)

    def _to_qdatetime(self, value):
        if isinstance(value, datetime):
            return QDateTime.fromSecsSinceEpoch(int(value.timestamp()))
        if isinstance(value, str):
            for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
                try:
                    dt = datetime.strptime(value, pattern)
                    return QDateTime.fromSecsSinceEpoch(int(dt.timestamp()))
                except ValueError:
                    continue
        return self._default_qdatetime()

    def _default_qdatetime(self):
        dt = datetime.now() + timedelta(minutes=30)
        dt = dt.replace(second=0, microsecond=0)
        return QDateTime.fromSecsSinceEpoch(int(dt.timestamp()))

    @staticmethod
    def _fmt_date(value):
        if hasattr(value, "strftime"):
            return value.strftime("%d/%m/%Y")
        return str(value or "")

    def _soumettre(self):
        try:
            visite_data = self.combo_visite.currentData()
            code_visite = visite_data.get("code_visite", "") if isinstance(visite_data, dict) else ""
            code_personnel = self.combo_personnel.currentData()
            statut = self.combo_statut.currentData() or "attente"

            rdv = RendezVous(
                code_rendez_vous=self.rendez_vous_obj.code_rendez_vous if self.rendez_vous_obj else None,
                code_visite=code_visite,
                code_personnel=code_personnel,
                code_session=self.code_session,
                date_rendez_vous=self.edit_date.dateTime().toPython(),
                statut_rendez_vous=statut,
            )

            if self.rendez_vous_obj:
                ok, msg = self.controleur.modifier_rendez_vous(rdv)
            else:
                ok, msg = self.controleur.creer_rendez_vous(rdv)

            if ok:
                CustomMessageBox("Succes", msg, True, self).exec()
                self.accept()
            else:
                CustomMessageBox("Erreur", msg, False, self).exec()

        except Exception as e:
            CustomMessageBox("Erreur Systeme", str(e), False, self).exec()
