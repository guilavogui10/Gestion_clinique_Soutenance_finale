import os
import qtawesome as qta
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QDateEdit, QFrame,
    QGraphicsDropShadowEffect
)
from models.modeles_lunette import CommandeLunette
from views.shared.message_box import CustomMessageBox
from views.shared.theme_manager import theme_manager


class CommandeLunetteFormDialog(QDialog):
    """
    Formulaire commande de lunettes avec disposition verticale.
    Traite le statut et statut_facture automatiquement.
    La date_commande est fixÃ©e automatiquement par le contrÃ´leur.
    """

    def __init__(self, controleur, code_session: str,
                 code_consultation: str = "", code_personnel: str = "",
                 commande_obj=None, parent=None):
        super().__init__(parent)
        self.controleur             = controleur
        self.code_session           = code_session
        self.code_consultation_init = code_consultation
        self.code_personnel_init    = code_personnel
        self.commande_obj           = commande_obj
        self.info_cabinet           = self.controleur.get_cabinet_info()

        self._consultations_attente = []
        self._personnels            = []

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(550, 600)

        self._charger_donnees_combos()
        self._init_ui()

        if self.commande_obj:
            self._remplir_champs()
        else:
            if self.code_consultation_init:
                self._preselectionner_consultation(self.code_consultation_init)
            if self.code_personnel_init:
                self._preselectionner_personnel(self.code_personnel_init)
        theme_manager.theme_changed.connect(self.apply_theme)

    # =========================================================================
    # DONNEES COMBOS
    # =========================================================================

    def _charger_donnees_combos(self):
        try:
            self._consultations_attente = (
                self.controleur.obtenir_patients_attente_lunette(self.code_session) or []
            )
        except Exception:
            self._consultations_attente = []
        try:
            if hasattr(self.controleur, "lister_personnel"):
                self._personnels = self.controleur.lister_personnel() or []
        except Exception:
            self._personnels = []

    # =========================================================================
    # UI PRINCIPALE
    # =========================================================================

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.container = QFrame()
        self.container.setObjectName("MainContainer")
        self._apply_container_style()

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(30, 20, 30, 30)

        # â”€â”€ HEADER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 10)
        header.setSpacing(0)

        cabinet_info_layout = QVBoxLayout()
        cabinet_info_layout.setContentsMargins(0, 0, 0, 0)
        cabinet_info_layout.setSpacing(0)

        name_cab = QLabel(self.info_cabinet.get("nom_cabinet", "Cabinet Medical"))
        name_cab.setObjectName("CabinetName")
        name_cab.setWordWrap(True)

        c = theme_manager.colors()
        addr_cab = QLabel(self.info_cabinet.get("adresse_cabinet", ""))
        addr_cab.setStyleSheet(f"color: {c['text_muted']}; font-size: 12px; background: transparent;")

        cabinet_info_layout.addWidget(name_cab)
        cabinet_info_layout.addWidget(addr_cab)
        header.addLayout(cabinet_info_layout, 4)
        header.addStretch(1)

        logo_path = self.info_cabinet.get('logo_url')
        if logo_path and os.path.exists(logo_path):
            logo_lbl = QLabel()
            logo_lbl.setStyleSheet("background: transparent;")
            pix = QPixmap(logo_path).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            logo_lbl.setAlignment(Qt.AlignCenter)
            header.addWidget(logo_lbl)

        layout.addLayout(header)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {c['border_light']};")
        layout.addWidget(line)
        layout.addSpacing(10)

        # â”€â”€ FORMULAIRE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        form_grid = QVBoxLayout()
        form_grid.setSpacing(15)

        # â”€â”€ Consultation â”€â”€
        vbox_consult = QVBoxLayout()
        vbox_consult.setSpacing(2)
        lbl_consult = QLabel("Consultation liÃ©e (patient en attente lunettes)")
        lbl_consult.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']};")
        vbox_consult.addWidget(lbl_consult)
        self.combo_consultation = QComboBox()
        self.combo_consultation.setFixedHeight(40)
        self.combo_consultation.addItem("â€” SÃ©lectionner une consultation â€”", "")
        for consult in self._consultations_attente:
            label = (
                f"{consult.get('code_consultation', '')}  |  "
                f"{consult.get('nom', '')} {consult.get('prenom', '')}  |  "
                f"{consult.get('date_visite', '')}"
            )
            self.combo_consultation.addItem(label, {
                "code_consultation": consult.get("code_consultation", ""),
                "code_visite":       consult.get("code_visite",       "")
            })
        self.combo_consultation.setStyleSheet(
            "QComboBox { padding-left: 35px; background-image: url(none); }")
        icon_consult_lbl = QLabel(self.combo_consultation)
        icon_consult_lbl.setPixmap(
            qta.icon("fa5s.file-medical", color=c['primary']).pixmap(18, 18))
        icon_consult_lbl.move(10, 11)
        icon_consult_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        vbox_consult.addWidget(self.combo_consultation)
        self.err_consultation = QLabel("")
        self.err_consultation.setStyleSheet(
            f"color: {c['danger']}; font-size: 10px; font-style: italic;")
        self.err_consultation.setVisible(False)
        vbox_consult.addWidget(self.err_consultation)
        form_grid.addLayout(vbox_consult)

        # â”€â”€ Ligne 1 : Code Visite (auto) + Personnel â”€â”€
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        vbox_visite = QVBoxLayout()
        vbox_visite.setSpacing(2)
        lbl_visite = QLabel("Code Visite (auto)")
        lbl_visite.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']};")
        vbox_visite.addWidget(lbl_visite)
        self.edit_code_visite = QLineEdit()
        self.edit_code_visite.setPlaceholderText("Auto...")
        self.edit_code_visite.setFixedHeight(40)
        self.edit_code_visite.setReadOnly(True)
        self.edit_code_visite.addAction(
            qta.icon("fa5s.link", color=c['primary']), QLineEdit.LeadingPosition)
        vbox_visite.addWidget(self.edit_code_visite)
        row1.addLayout(vbox_visite)

        vbox_personnel = QVBoxLayout()
        vbox_personnel.setSpacing(2)
        lbl_personnel = QLabel("MÃ©decin / Personnel")
        lbl_personnel.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']};")
        vbox_personnel.addWidget(lbl_personnel)
        self.combo_personnel = QComboBox()
        self.combo_personnel.setFixedHeight(40)
        self.combo_personnel.addItem("â€” SÃ©lectionner un mÃ©decin â€”", "")
        for p in self._personnels:
            label = (
                f"{p.get('code', '')}  |  "
                f"{p.get('nom', '')} {p.get('prenom', '')}  |  "
                f"{p.get('fonction', '')}"
            )
            self.combo_personnel.addItem(label, p.get("code", ""))
        self.combo_personnel.setStyleSheet(
            "QComboBox { padding-left: 35px; background-image: url(none); }")
        icon_personnel_lbl = QLabel(self.combo_personnel)
        icon_personnel_lbl.setPixmap(
            qta.icon("fa5s.user-md", color=c['primary']).pixmap(18, 18))
        icon_personnel_lbl.move(10, 11)
        icon_personnel_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        vbox_personnel.addWidget(self.combo_personnel)
        self.err_personnel = QLabel("")
        self.err_personnel.setStyleSheet(
            f"color: {c['danger']}; font-size: 10px; font-style: italic;")
        self.err_personnel.setVisible(False)
        vbox_personnel.addWidget(self.err_personnel)
        row1.addLayout(vbox_personnel)

        form_grid.addLayout(row1)

        # â”€â”€ Ligne 2 : NumÃ©ro Cadre + NumÃ©ro Verre â”€â”€
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        vbox_cadre = QVBoxLayout()
        vbox_cadre.setSpacing(2)
        lbl_cadre = QLabel("NumÃ©ro Cadre")
        lbl_cadre.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']};")
        vbox_cadre.addWidget(lbl_cadre)
        self.edit_numero_cadre = QLineEdit()
        self.edit_numero_cadre.setPlaceholderText("Ex: CAD-2024-001")
        self.edit_numero_cadre.setFixedHeight(40)
        self.edit_numero_cadre.addAction(
            qta.icon("fa5s.glasses", color=c['primary']), QLineEdit.LeadingPosition)
        vbox_cadre.addWidget(self.edit_numero_cadre)
        self.err_cadre = QLabel("")
        self.err_cadre.setStyleSheet(
            f"color: {c['danger']}; font-size: 10px; font-style: italic;")
        self.err_cadre.setVisible(False)
        vbox_cadre.addWidget(self.err_cadre)
        row2.addLayout(vbox_cadre)

        vbox_verre = QVBoxLayout()
        vbox_verre.setSpacing(2)
        lbl_verre = QLabel("NumÃ©ro Verre Prescrit")
        lbl_verre.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']};")
        vbox_verre.addWidget(lbl_verre)
        self.edit_numero_verre = QLineEdit()
        self.edit_numero_verre.setPlaceholderText("Ex: +2.00 / -1.50")
        self.edit_numero_verre.setFixedHeight(40)
        self.edit_numero_verre.addAction(
            qta.icon("fa5s.eye", color=c['primary']), QLineEdit.LeadingPosition)
        vbox_verre.addWidget(self.edit_numero_verre)
        self.err_verre = QLabel("")
        self.err_verre.setStyleSheet(
            f"color: {c['danger']}; font-size: 10px; font-style: italic;")
        self.err_verre.setVisible(False)
        vbox_verre.addWidget(self.err_verre)
        row2.addLayout(vbox_verre)

        form_grid.addLayout(row2)

        # â”€â”€ Ligne 3 : Date Livraison + Prix â”€â”€
        row3 = QHBoxLayout()
        row3.setSpacing(10)

        vbox_date = QVBoxLayout()
        vbox_date.setSpacing(2)
        lbl_date = QLabel("Date de Livraison PrÃ©vue")
        lbl_date.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']};")
        vbox_date.addWidget(lbl_date)
        self.edit_date_livraison = QDateEdit()
        self.edit_date_livraison.setCalendarPopup(True)
        self.edit_date_livraison.setDisplayFormat("dd/MM/yyyy")
        self.edit_date_livraison.setDate(QDate.currentDate().addDays(7))
        self.edit_date_livraison.setFixedHeight(40)
        self.edit_date_livraison.setStyleSheet(f"""
            QDateEdit {{
                padding-left: 35px;
                border: 1px solid {c['border']};
                border-radius: 8px;
                background-color: {c['bg_input']};
            }}
            QDateEdit:focus {{ border: 2px solid {c['primary']}; }}
            QDateEdit::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 1px solid {c['border']};
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                background-color: {c['bg_main']};
            }}
            QDateEdit::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {c['primary']};
            }}
        """)
        icon_date_lbl = QLabel(self.edit_date_livraison)
        icon_date_lbl.setPixmap(
            qta.icon("fa5s.calendar-alt", color=c['primary']).pixmap(16, 16))
        icon_date_lbl.move(10, 12)
        icon_date_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        vbox_date.addWidget(self.edit_date_livraison)
        self.err_date = QLabel("")
        self.err_date.setStyleSheet(
            f"color: {c['danger']}; font-size: 10px; font-style: italic;")
        self.err_date.setVisible(False)
        vbox_date.addWidget(self.err_date)
        row3.addLayout(vbox_date)

        vbox_prix = QVBoxLayout()
        vbox_prix.setSpacing(2)
        lbl_prix = QLabel("Prix (GNF)")
        lbl_prix.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']};")
        vbox_prix.addWidget(lbl_prix)
        self.edit_prix = QLineEdit()
        self.edit_prix.setPlaceholderText("Ex: 850000")
        self.edit_prix.setFixedHeight(40)
        self.edit_prix.addAction(
            qta.icon("fa5s.money-bill-wave", color=c['primary']), QLineEdit.LeadingPosition)
        vbox_prix.addWidget(self.edit_prix)
        self.err_prix = QLabel("")
        self.err_prix.setStyleSheet(
            f"color: {c['danger']}; font-size: 10px; font-style: italic;")
        self.err_prix.setVisible(False)
        vbox_prix.addWidget(self.err_prix)
        row3.addLayout(vbox_prix)

        form_grid.addLayout(row3)

        # â”€â”€ Statut Facture (auto) â”€â”€
        vbox_statut_fact = QVBoxLayout()
        vbox_statut_fact.setSpacing(2)
        lbl_statut_fact = QLabel("Statut Facture")
        lbl_statut_fact.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']};")
        vbox_statut_fact.addWidget(lbl_statut_fact)
        self.combo_statut_facture = QComboBox()
        self.combo_statut_facture.setFixedHeight(40)
        self.combo_statut_facture.setEnabled(False)
        self.combo_statut_facture.addItem("Formulaire incomplet...")
        vbox_statut_fact.addWidget(self.combo_statut_facture)
        form_grid.addLayout(vbox_statut_fact)

        layout.addLayout(form_grid)
        layout.addSpacing(20)

        # â”€â”€ Connexions validations â”€â”€
        self.combo_consultation.currentIndexChanged.connect(self._on_consultation_changed)
        self.combo_personnel.currentIndexChanged.connect(self._valider_formulaire)
        self.edit_numero_cadre.textChanged.connect(self._valider_formulaire)
        self.edit_numero_verre.textChanged.connect(self._valider_formulaire)
        self.edit_date_livraison.dateChanged.connect(self._valider_formulaire)
        self.edit_prix.textChanged.connect(self._valider_formulaire)

        # â”€â”€ BOUTONS â”€â”€
        actions = QHBoxLayout()

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setObjectName("CancelBtn")
        self.btn_cancel.setFixedHeight(45)
        self.btn_cancel.clicked.connect(self.reject)

        label_save = "Enregistrer" if not self.commande_obj else "Mettre Ã  jour"
        self.btn_save = QPushButton(label_save)
        self.btn_save.setObjectName("SaveBtn")
        self.btn_save.setFixedHeight(45)
        self.btn_save.setIcon(qta.icon("fa5s.check", color=c['text_inverse']))
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self._soumettre)

        actions.addWidget(self.btn_cancel, 1)
        actions.addWidget(self.btn_save, 2)
        layout.addLayout(actions)

        self.main_layout.addWidget(self.container)

    def _apply_container_style(self):
        c = theme_manager.colors()
        self.container.setStyleSheet(f"""
            QFrame#MainContainer {{
                background-color: {c['bg_card']}; border-radius: 20px; border: 1px solid {c['border']};
            }}
            QLabel {{ color: {c['text_primary']}; font-size: 13px; background-color: transparent; }}
            QLabel#CabinetName {{ font-size: 22px; font-weight: bold; color: {c['danger']}; background-color: transparent; }}
            QLineEdit, QComboBox, QDateEdit {{
                padding: 10px; border: 1px solid {c['border']}; border-radius: 8px;
                background-color: {c['bg_input']}; font-size: 14px; color: {c['text_primary']};
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
                border: 2px solid {c['border_focus']}; background-color: {c['bg_card']};
            }}
            QLineEdit:disabled {{
                background-color: {c['bg_main']}; color: {c['primary']}; font-weight: bold;
                border: 1px solid {c['border_light']};
            }}
            QComboBox:disabled {{
                background-color: {c['bg_main']}; color: {c['primary']}; border: 1px solid {c['border_focus']};
            }}
            QPushButton#SaveBtn {{
                background-color: {c['primary']}; color: {c['text_inverse']}; border-radius: 10px;
                font-weight: bold; font-size: 15px;
            }}
            QPushButton#SaveBtn:disabled {{ background-color: {c['border_light']}; color: {c['text_muted']}; }}
            QPushButton#CancelBtn {{
                background-color: {c['bg_main']}; color: {c['text_secondary']}; border-radius: 10px;
                border: 1px solid {c['border']};
            }}
        """)

    def apply_theme(self):
        self._apply_container_style()
        c = theme_manager.colors()
        if hasattr(self, 'btn_save'):
            self.btn_save.setIcon(qta.icon("fa5s.check", color=c['text_inverse']))

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def _on_consultation_changed(self):
        data = self.combo_consultation.currentData()
        if data and isinstance(data, dict):
            self.edit_code_visite.setText(data.get("code_visite", ""))
        else:
            self.edit_code_visite.clear()
        self._valider_formulaire()

    def _valider_formulaire(self):
        tout_valide = True

        cadre = self.edit_numero_cadre.text().strip()
        ok, msg = self.controleur.valider_texte(cadre, "numÃ©ro cadre")
        self._style_lineedit(self.edit_numero_cadre, self.err_cadre, ok, msg, cadre)
        if not ok: tout_valide = False

        verre = self.edit_numero_verre.text().strip()
        ok, msg = self.controleur.valider_texte(verre, "numÃ©ro verre")
        self._style_lineedit(self.edit_numero_verre, self.err_verre, ok, msg, verre)
        if not ok: tout_valide = False

        date_livraison = self.edit_date_livraison.date().toPython()
        ok, msg = self.controleur.valider_date_livraison(date_livraison)
        if not ok:
            cv = theme_manager.colors()
            self.edit_date_livraison.setStyleSheet(
                f"border: 1px solid {cv['danger']}; background-color: {cv['danger_bg']};")
            self.err_date.setText(msg)
            self.err_date.setVisible(True)
            tout_valide = False
        else:
            cv = theme_manager.colors()
            self.edit_date_livraison.setStyleSheet(
                f"border: 2px solid {cv['border_focus']}; background-color: {cv['bg_card']};")
            self.err_date.setVisible(False)

        prix = self.edit_prix.text().strip()
        ok, msg = self.controleur.valider_prix(prix if prix else "-1")
        self._style_lineedit(self.edit_prix, self.err_prix, ok, msg, prix)
        if not ok: tout_valide = False

        if not self.combo_consultation.currentData():
            self.err_consultation.setText("Veuillez sÃ©lectionner une consultation")
            self.err_consultation.setVisible(True)
            tout_valide = False
        else:
            self.err_consultation.setVisible(False)

        if not self.combo_personnel.currentData():
            self.err_personnel.setText("Veuillez sÃ©lectionner un mÃ©decin")
            self.err_personnel.setVisible(True)
            tout_valide = False
        else:
            self.err_personnel.setVisible(False)

        self.combo_statut_facture.clear()
        if tout_valide:
            cv = theme_manager.colors()
            self.combo_statut_facture.addItem("Attente payement")
            self.combo_statut_facture.setStyleSheet(
                f"QComboBox:disabled {{ background-color: {cv['bg_main']}; "
                f"color: {cv['primary']}; border: 1px solid {cv['border_focus']}; }}")
        else:
            cv = theme_manager.colors()
            self.combo_statut_facture.addItem("Formulaire incomplet...")
            self.combo_statut_facture.setStyleSheet(
                f"QComboBox:disabled {{ background-color: {cv['bg_main']}; "
                f"color: {cv['primary']}; border: 1px solid {cv['border_light']}; }}")

        self.btn_save.setEnabled(tout_valide)

    def _style_lineedit(self, widget, err_lbl, valide, message, texte):
        cv = theme_manager.colors()
        if not valide and texte:
            widget.setStyleSheet(
                f"border: 1px solid {cv['danger']}; background-color: {cv['danger_bg']};")
            err_lbl.setText(message)
            err_lbl.setVisible(True)
        elif not valide:
            widget.setStyleSheet(
                f"border: 1px solid {cv['border']}; background-color: {cv['bg_input']}; color: {cv['text_primary']};")
            err_lbl.setVisible(False)
        else:
            widget.setStyleSheet(
                f"border: 2px solid {cv['border_focus']}; background-color: {cv['bg_card']};")
            err_lbl.setVisible(False)

    # =========================================================================
    # PRESELECTION
    # =========================================================================

    def _preselectionner_consultation(self, code_consultation: str):
        for i in range(self.combo_consultation.count()):
            data = self.combo_consultation.itemData(i)
            if isinstance(data, dict) and data.get("code_consultation") == code_consultation:
                self.combo_consultation.setCurrentIndex(i)
                self.combo_consultation.setEnabled(False)
                break

    def _preselectionner_personnel(self, code_personnel: str):
        for i in range(self.combo_personnel.count()):
            if self.combo_personnel.itemData(i) == code_personnel:
                self.combo_personnel.setCurrentIndex(i)
                break

    # =========================================================================
    # REMPLISSAGE MODE MODIFICATION
    # =========================================================================

    def _remplir_champs(self):
        c = self.commande_obj
        self._preselectionner_consultation(c.code_consultation)
        self.edit_code_visite.setText(c.code_visite or "")
        self._preselectionner_personnel(c.code_personnel)

        if c.date_livraison:
            d = c.date_livraison.date() if hasattr(c.date_livraison, "date") else c.date_livraison
            self.edit_date_livraison.setDate(QDate(d.year, d.month, d.day))

        self.edit_numero_cadre.setText(str(c.numero_cadre or ""))
        self.edit_numero_verre.setText(str(c.numero_verre or ""))
        self.edit_prix.setText(str(c.prix or ""))

    # =========================================================================
    # SOUMISSION
    # =========================================================================

    def _soumettre(self):
        try:
            data_consultation = self.combo_consultation.currentData()
            code_consultation = data_consultation.get("code_consultation", "") if data_consultation else ""
            code_visite       = self.edit_code_visite.text().strip()
            code_personnel    = self.combo_personnel.currentData()

            commande = CommandeLunette(
                code              = self.commande_obj.code if self.commande_obj else None,
                numero_cadre      = self.edit_numero_cadre.text().strip(),
                numero_verre      = self.edit_numero_verre.text().strip(),
                date_livraison    = self.edit_date_livraison.date().toPython(),
                prix              = float(self.edit_prix.text().strip() or 0),
                statut            = "attente",
                statut_facture    = self.combo_statut_facture.currentText(),
                code_consultation = code_consultation,
                code_visite       = code_visite,
                code_session      = self.code_session,
                code_personnel    = code_personnel
            )

            if self.commande_obj:
                ok, msg = self.controleur.modifier_commande(commande)
            else:
                ok, msg = self.controleur.creer_commande(commande)

            if ok:
                CustomMessageBox("SuccÃ¨s", msg, True, self).exec()
                self.accept()
            else:
                CustomMessageBox("Erreur", msg, False, self).exec()

        except Exception as e:
            CustomMessageBox("Erreur SystÃ¨me", str(e), False, self).exec()
