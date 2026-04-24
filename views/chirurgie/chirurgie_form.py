import os
import qtawesome as qta
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QDateEdit, QFrame,
    QGraphicsDropShadowEffect, QTextEdit
)
from models.modeles_chirurgie import Chirurgie
from views.shared.message_box import CustomMessageBox
from views.shared.theme_manager import theme_manager


class ChirurgieFormDialog(QDialog):
    """
    Formulaire chirurgie avec disposition verticale (comme patient_form).
    Traite le statut_facture automatiquement et le code_consultation qui remplit code_visite.
    """

    def __init__(self, controleur, code_session: str,
                 code_consultation: str = "", code_personnel: str = "",
                 chururgie_obj=None, parent=None):
        super().__init__(parent)
        self.controleur             = controleur
        self.code_session           = code_session
        self.code_consultation_init = code_consultation
        self.code_personnel_init    = code_personnel
        self.chururgie_obj          = chururgie_obj
        self.info_cabinet           = self.controleur.get_cabinet_info()

        self._consultations_attente = []
        self._personnels            = []

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(550, 700)

        self._charger_donnees_combos()
        self._init_ui()
        self.apply_theme()           # ← construit le formulaire

        if self.chururgie_obj:
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
                self.controleur.obtenir_patients_attente_chururgie(self.code_session) or []
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

    def _apply_container_style(self):
        c = theme_manager.colors()
        self.container.setStyleSheet(f"""
            QFrame#MainContainer {{
                background-color: {c['bg_card']};
                border-radius: 20px;
                border: 1px solid {c['border']};
            }}
            QLabel {{
                color: {c['text_primary']};
                font-size: 13px;
                background-color: transparent;
            }}
            QLabel#CabinetName {{
                font-size: 22px; font-weight: bold;
                color: {c['danger']};
                background-color: transparent;
            }}
            QLineEdit, QComboBox, QDateEdit {{
                padding: 10px;
                border: 1px solid {c['border']};
                border-radius: 8px;
                background-color: {c['bg_input']};
                font-size: 14px;
                color: {c['text_primary']};
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
                border: 2px solid {c['border_focus']};
                background-color: {c['bg_card']};
            }}
            QLineEdit:disabled {{
                background-color: {c['bg_main']};
                color: {c['primary']};
                font-weight: bold;
                border: 1px solid {c['border_light']};
            }}
            QTextEdit {{
                padding: 8px;
                border: 1px solid {c['border']};
                border-radius: 8px;
                background-color: {c['bg_input']};
                font-size: 14px;
                color: {c['text_primary']};
            }}
            QTextEdit:focus {{
                border: 2px solid {c['border_focus']};
                background-color: {c['bg_card']};
            }}
            QComboBox:disabled {{
                background-color: {c['bg_main']};
                color: {c['primary']};
                border: 1px solid {c['border_light']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                color: {c['text_primary']};
                selection-background-color: {c['primary_light']};
                selection-color: {c['primary']};
            }}
            QPushButton#SaveBtn {{
                background-color: {c['primary']};
                color: {c['text_inverse']};
                border-radius: 10px;
                font-weight: bold;
                font-size: 15px;
            }}
            QPushButton#SaveBtn:disabled {{
                background-color: {c['border_light']};
                color: {c['text_muted']};
            }}
            QPushButton#CancelBtn {{
                background-color: {c['bg_main']};
                color: {c['text_secondary']};
                border-radius: 10px;
                border: 1px solid {c['border']};
            }}
        """)

    def apply_theme(self):
        """Applique le thème actif au formulaire."""
        c = theme_manager.colors()
        self._apply_container_style()
        if hasattr(self, '_header_card'):
            self._header_card.setStyleSheet(f"""
                QFrame {{
                    border: none;
                    border-top-left-radius: 20px;
                    border-top-right-radius: 20px;
                    background: {c['bg_card']};
                }}
            """)
        if hasattr(self, '_title_form'):
            self._title_form.setStyleSheet(
                f"color: {c['primary']}; font-size: 21px; font-weight: 900; letter-spacing: 0.8px;"
            )
        if hasattr(self, '_accent'):
            self._accent.setStyleSheet(f"background: {c['border_focus']}; border: none;")
        if hasattr(self, 'btn_save'):
            self.btn_save.setIcon(qta.icon("fa5s.check", color=c['text_inverse']))

        # Ne construire l'UI qu'une seule fois
        if hasattr(self, '_ui_built'):
            return
        self._ui_built = True

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 30)
        layout.setSpacing(0)

        c = theme_manager.colors()
        header_card = QFrame()
        self._header_card = header_card
        header_card.setStyleSheet(f"""
            QFrame {{
                border: none;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                background: {c['bg_card']};
            }}
        """)
        header_container = QVBoxLayout(header_card)
        header_container.setContentsMargins(24, 16, 24, 10)
        header_container.setSpacing(8)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        cabinet_info_layout = QVBoxLayout()
        cabinet_info_layout.setSpacing(2)

        name_cab = QLabel(self.info_cabinet.get("nom_cabinet", "Cabinet Medical"))
        name_cab.setObjectName("CabinetName")
        name_cab.setWordWrap(True)

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

        header_container.addLayout(header)

        title_form = QLabel("FORMULAIRE CHIRURGIE")
        title_form.setAlignment(Qt.AlignCenter)
        title_form.setStyleSheet(
            f"color: {c['primary']}; font-size: 21px; font-weight: 900; letter-spacing: 0.8px;"
        )
        self._title_form = title_form
        header_container.addWidget(title_form)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {c['border_light']};")
        header_container.addWidget(line)

        accent = QFrame()
        accent.setFixedHeight(6)
        accent.setStyleSheet(f"background: {c['border_focus']}; border: none;")
        self._accent = accent
        header_container.addWidget(accent)

        layout.addWidget(header_card)

        body = QVBoxLayout()
        body.setContentsMargins(30, 12, 30, 0)
        body.setSpacing(10)

        # FORMULAIRE
        form_grid = QVBoxLayout()
        form_grid.setSpacing(15)

        # Consultation
        vbox_consult = QVBoxLayout()
        vbox_consult.setSpacing(2)
        lbl_consult = QLabel("Consultation liÃ©e (patient en attente chirurgie)")
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
        # Ajout de l'icÃ´ne dans le style
        self.combo_consultation.setStyleSheet("""
            QComboBox {
                padding-left: 35px;
                background-image: url(none);
            }
        """)
        # IcÃ´ne fixe Ã  gauche
        icon_consult_lbl = QLabel(self.combo_consultation)
        icon_consult_lbl.setPixmap(qta.icon("fa5s.file-medical", color=c['primary']).pixmap(18, 18))
        icon_consult_lbl.move(10, 11)
        icon_consult_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        vbox_consult.addWidget(self.combo_consultation)
        self.err_consultation = QLabel("")
        self.err_consultation.setStyleSheet(f"color: {c['danger']}; font-size: 10px; font-style: italic;")
        self.err_consultation.setVisible(False)
        vbox_consult.addWidget(self.err_consultation)
        form_grid.addLayout(vbox_consult)

        # Ligne : Code Visite + Personnel
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        # Code Visite (auto-rempli)
        vbox_visite = QVBoxLayout()
        vbox_visite.setSpacing(2)
        lbl_visite = QLabel("Code Visite (auto)")
        lbl_visite.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']};")
        vbox_visite.addWidget(lbl_visite)

        self.edit_code_visite = QLineEdit()
        self.edit_code_visite.setPlaceholderText("Auto...")
        self.edit_code_visite.setFixedHeight(40)
        self.edit_code_visite.setReadOnly(True)
        icon_visite = qta.icon("fa5s.link", color=c['primary'])
        self.edit_code_visite.addAction(icon_visite, QLineEdit.LeadingPosition)
        vbox_visite.addWidget(self.edit_code_visite)
        row1.addLayout(vbox_visite)

        # Personnel
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
        # Ajout de l'icÃ´ne dans le style
        self.combo_personnel.setStyleSheet("""
            QComboBox {
                padding-left: 35px;
                background-image: url(none);
            }
        """)
        # IcÃ´ne fixe Ã  gauche
        icon_personnel_lbl = QLabel(self.combo_personnel)
        icon_personnel_lbl.setPixmap(qta.icon("fa5s.user-md", color=c['primary']).pixmap(18, 18))
        icon_personnel_lbl.move(10, 11)
        icon_personnel_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        vbox_personnel.addWidget(self.combo_personnel)
        self.err_personnel = QLabel("")
        self.err_personnel.setStyleSheet(f"color: {c['danger']}; font-size: 10px; font-style: italic;")
        self.err_personnel.setVisible(False)
        vbox_personnel.addWidget(self.err_personnel)
        row1.addLayout(vbox_personnel)

        form_grid.addLayout(row1)

        # Ligne : Date + Frais
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        # Date
        vbox_date = QVBoxLayout()
        vbox_date.setSpacing(2)
        lbl_date = QLabel("Date de Chirurgie")
        lbl_date.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']};")
        vbox_date.addWidget(lbl_date)

        self.edit_date = QDateEdit()
        self.edit_date.setCalendarPopup(True)
        self.edit_date.setDisplayFormat("dd/MM/yyyy")
        self.edit_date.setDate(QDate.currentDate())
        self.edit_date.setFixedHeight(40)
        self.edit_date.setStyleSheet(f"""
            QDateEdit {{
                padding-left: 35px;
                border: 1px solid {c['border']};
                border-radius: 8px;
                background-color: {c['bg_input']};
            }}
            QDateEdit:focus {{ border: 2px solid {c['border_focus']}; }}
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

        cal_icon = qta.icon("fa5s.calendar-alt", color=c['primary'])
        icon_container = QLabel(self.edit_date)
        icon_container.setPixmap(cal_icon.pixmap(16, 16))
        icon_container.move(10, 12)
        icon_container.setAttribute(Qt.WA_TransparentForMouseEvents)

        vbox_date.addWidget(self.edit_date)
        row2.addLayout(vbox_date)

        # Frais
        vbox_frais = QVBoxLayout()
        vbox_frais.setSpacing(2)
        lbl_frais = QLabel("Frais (GNF)")
        lbl_frais.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']};")
        vbox_frais.addWidget(lbl_frais)

        self.edit_frais = QLineEdit()
        self.edit_frais.setPlaceholderText("Ex: 500000")
        self.edit_frais.setFixedHeight(40)
        icon = qta.icon("fa5s.money-bill-wave", color=c['primary'])
        self.edit_frais.addAction(icon, QLineEdit.LeadingPosition)
        vbox_frais.addWidget(self.edit_frais)
        self.err_frais = QLabel("")
        self.err_frais.setStyleSheet(f"color: {c['danger']}; font-size: 10px; font-style: italic;")
        self.err_frais.setVisible(False)
        vbox_frais.addWidget(self.err_frais)
        row2.addLayout(vbox_frais)

        form_grid.addLayout(row2)

        # LibellÃ© Chirurgie
        vbox_libelle = QVBoxLayout()
        vbox_libelle.setSpacing(2)
        lbl_libelle = QLabel("LibellÃ© de la Chirurgie")
        lbl_libelle.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']};")
        vbox_libelle.addWidget(lbl_libelle)

        self.edit_libelle = QTextEdit()
        self.edit_libelle.setPlaceholderText("Ex: Appendicectomie, CÃ©sarienne...")
        self.edit_libelle.setFixedHeight(80)
        self.edit_libelle.setStyleSheet("""
            QTextEdit {
                padding-left: 35px;
                padding-top: 8px;
            }
        """)
        # IcÃ´ne fixe Ã  gauche
        icon_libelle_lbl = QLabel(self.edit_libelle)
        icon_libelle_lbl.setPixmap(qta.icon("fa5s.notes-medical", color=c['primary']).pixmap(18, 18))
        icon_libelle_lbl.move(10, 10)
        icon_libelle_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        vbox_libelle.addWidget(self.edit_libelle)
        self.err_libelle = QLabel("")
        self.err_libelle.setStyleSheet(f"color: {c['danger']}; font-size: 10px; font-style: italic;")
        self.err_libelle.setVisible(False)
        vbox_libelle.addWidget(self.err_libelle)
        form_grid.addLayout(vbox_libelle)

        # Statut Facture (auto)
        vbox_statut = QVBoxLayout()
        vbox_statut.setSpacing(2)
        lbl_statut = QLabel("Statut Facture")
        lbl_statut.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']};")
        vbox_statut.addWidget(lbl_statut)

        self.combo_statut = QComboBox()
        self.combo_statut.setFixedHeight(40)
        self.combo_statut.setEnabled(False)
        self.combo_statut.addItem("Formulaire incomplet...")
        vbox_statut.addWidget(self.combo_statut)
        form_grid.addLayout(vbox_statut)

        body.addLayout(form_grid)
        body.addSpacing(20)

        # Connexion validations
        self.edit_libelle.textChanged.connect(self._valider_formulaire)
        self.edit_frais.textChanged.connect(self._valider_formulaire)
        self.combo_consultation.currentIndexChanged.connect(self._on_consultation_changed)
        self.combo_personnel.currentIndexChanged.connect(self._valider_formulaire)

        # BOUTONS
        actions = QHBoxLayout()

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setObjectName("CancelBtn")
        self.btn_cancel.setFixedHeight(45)
        self.btn_cancel.clicked.connect(self.reject)

        label_save = "Enregistrer" if not self.chururgie_obj else "Mettre Ã  jour"
        self.btn_save = QPushButton(label_save)
        self.btn_save.setObjectName("SaveBtn")
        self.btn_save.setFixedHeight(45)
        self.btn_save.setIcon(qta.icon("fa5s.check", color=c['text_inverse']))
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self._soumettre)

        actions.addWidget(self.btn_cancel, 1)
        actions.addWidget(self.btn_save, 2)
        body.addLayout(actions)

        layout.addLayout(body)
        self.main_layout.addWidget(self.container)

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def _on_consultation_changed(self):
        data = self.combo_consultation.currentData()
        if data and isinstance(data, dict):
            code_visite = data.get("code_visite", "")
            self.edit_code_visite.setText(code_visite)
        else:
            self.edit_code_visite.clear()
        self._valider_formulaire()

    def _valider_formulaire(self):
        tout_valide = True

        # LibellÃ©
        libelle = self.edit_libelle.toPlainText().strip()
        ok, msg = self.controleur.valider_texte(libelle, "libellÃ© chirurgie")
        self._style_textarea(self.edit_libelle, self.err_libelle, ok, msg, libelle)
        if not ok: tout_valide = False

        # Frais
        frais = self.edit_frais.text().strip()
        ok, msg = self.controleur.valider_frais(frais if frais else "-1")
        self._style_lineedit(self.edit_frais, self.err_frais, ok, msg, frais)
        if not ok: tout_valide = False

        # Consultation
        if not self.combo_consultation.currentData():
            self.err_consultation.setText("Veuillez sÃ©lectionner une consultation")
            self.err_consultation.setVisible(True)
            tout_valide = False
        else:
            self.err_consultation.setVisible(False)

        # Personnel
        if not self.combo_personnel.currentData():
            self.err_personnel.setText("Veuillez sÃ©lectionner un mÃ©decin")
            self.err_personnel.setVisible(True)
            tout_valide = False
        else:
            self.err_personnel.setVisible(False)

        # Statut facture dynamique
        self.combo_statut.clear()
        if tout_valide:
            self.combo_statut.addItem("attente payement")
            cn = theme_manager.colors()
            self.combo_statut.setStyleSheet(
                f"QComboBox:disabled {{ background-color: {cn['bg_main']}; "
                f"color: {cn['primary']}; border: 1px solid {cn['border_focus']}; }}"
            )
        else:
            self.combo_statut.addItem("Formulaire incomplet...")
            cn = theme_manager.colors()
            self.combo_statut.setStyleSheet(
                f"QComboBox:disabled {{ background-color: {cn['bg_main']}; "
                f"color: {cn['primary']}; border: 1px solid {cn['border_light']}; }}"
            )

        self.btn_save.setEnabled(tout_valide)

    def _style_textarea(self, widget, err_lbl, valide, message, texte):
        cv = theme_manager.colors()
        base = "border-radius: 8px; padding: 8px; font-size: 14px;"
        if not valide and texte:
            widget.setStyleSheet(f"border: 1px solid {cv['danger']}; background-color: {cv['danger_bg']}; {base}")
            err_lbl.setText(message)
            err_lbl.setVisible(True)
        elif not valide:
            widget.setStyleSheet(f"border: 1px solid {cv['border']}; background-color: {cv['bg_input']}; color: {cv['text_primary']}; {base}")
            err_lbl.setVisible(False)
        else:
            widget.setStyleSheet(f"border: 2px solid {cv['border_focus']}; background-color: {cv['bg_card']}; {base}")
            err_lbl.setVisible(False)

    def _style_lineedit(self, widget, err_lbl, valide, message, texte):
        cv = theme_manager.colors()
        if not valide and texte:
            widget.setStyleSheet(f"border: 1px solid {cv['danger']}; background-color: {cv['danger_bg']};")
            err_lbl.setText(message)
            err_lbl.setVisible(True)
        elif not valide:
            widget.setStyleSheet(f"border: 1px solid {cv['border']}; background-color: {cv['bg_input']}; color: {cv['text_primary']};")
            err_lbl.setVisible(False)
        else:
            widget.setStyleSheet(f"border: 2px solid {cv['border_focus']}; background-color: {cv['bg_card']};")
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
        c = self.chururgie_obj
        self._preselectionner_consultation(c.code_consultation)
        self.edit_code_visite.setText(c.code_visite or "")
        self._preselectionner_personnel(c.code_personnel)

        if hasattr(c.date_chururgie, "date"):
            d = c.date_chururgie.date()
            self.edit_date.setDate(QDate(d.year, d.month, d.day))

        self.edit_libelle.setPlainText(c.libelle_chururgie or "")
        self.edit_frais.setText(str(c.frais_chururgie or ""))

    # =========================================================================
    # SOUMISSION
    # =========================================================================

    def _soumettre(self):
        try:
            data_consultation = self.combo_consultation.currentData()
            code_consultation = data_consultation.get("code_consultation", "") if data_consultation else ""
            code_visite       = self.edit_code_visite.text().strip()
            code_personnel    = self.combo_personnel.currentData()

            chururgie = Chirurgie(
                code             = self.chururgie_obj.code if self.chururgie_obj else None,
                libelle_chururgie= self.edit_libelle.toPlainText().strip(),
                frais_chururgie  = float(self.edit_frais.text().strip() or 0),
                statut_facture   = self.combo_statut.currentText(),
                date_chururgie   = self.edit_date.date().toPython(),
                code_consultation= code_consultation,
                code_visite      = code_visite,
                code_session     = self.code_session,
                code_personnel   = code_personnel
            )

            if self.chururgie_obj:
                ok, msg = self.controleur.modifier_chururgie(chururgie)
            else:
                ok, msg = self.controleur.creer_chururgie(chururgie)

            if ok:
                CustomMessageBox("SuccÃ¨s", msg, True, self).exec()
                self.accept()
            else:
                CustomMessageBox("Erreur", msg, False, self).exec()

        except Exception as e:
            CustomMessageBox("Erreur SystÃ¨me", str(e), False, self).exec()

