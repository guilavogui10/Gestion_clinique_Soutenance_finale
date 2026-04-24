import os
import qtawesome as qta
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QDateEdit, QFrame,
    QGraphicsDropShadowEffect, QTextEdit, QWidget,QDateTimeEdit
)
from PySide6.QtCore import QDateTime
from models.modele_consultation import Consultation
from views.shared.message_box import CustomMessageBox
from views.consultation.styles import ConsultationStyles
from views.shared.theme_manager import theme_manager


class ConsultationFormDialog(QDialog):
    """
    Formulaire consultation en mode paysage.
    Colonne gauche  : Diagnostic + RÃ©sultat
    Colonne droite  : Visite + Personnel + Date + Services + Facturation
    Validation temps rÃ©el identique Ã  PatientFormDialog.
    """

    def __init__(self, controleur, code_session: str, code_visite: str = "",
                 code_personnel: str = "", consultation_obj=None, parent=None):
        super().__init__(parent)
        self.controleur          = controleur
        self.code_session        = code_session
        self.code_visite_init    = code_visite
        self.code_personnel_init = code_personnel
        self.consultation_obj    = consultation_obj
        self.info_cabinet        = self.controleur.get_cabinet_info()

        self._visites_attente = []
        self._personnels      = []

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(1020, 600)

        self._charger_donnees_combos()
        self._init_ui()
        self._connecter_validations()

        if self.consultation_obj:
            self._remplir_champs()
        else:
            if self.code_visite_init:
                self._preselectionner_visite(self.code_visite_init)
            if self.code_personnel_init:
                self._preselectionner_personnel(self.code_personnel_init)

    # =========================================================================
    # DONNÃ‰ES COMBOS
    # =========================================================================

    def _charger_donnees_combos(self):
        try:
            self._visites_attente = self.controleur.obtenir_patients_attente(self.code_session) or []
        except Exception:
            self._visites_attente = []
        try:
            if hasattr(self.controleur, 'lister_personnel'):
                self._personnels = self.controleur.lister_personnel() or []
        except Exception:
            self._personnels = []

    # =========================================================================
    # UI PRINCIPALE
    # =========================================================================

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
        self._setup_corps(main)
        self._setup_footer(main)

        outer.addWidget(self.container)

        theme_manager.theme_changed.connect(self.apply_theme)

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
                font-size: 12px;
                background-color: transparent;
            }}
            QLabel#CabinetName  {{ font-size: 17px; font-weight: bold; color: {c['danger']}; }}
            QLabel#SectionTitle {{ color: {c['primary']}; font-weight: bold; font-size: 11px; }}
            QLabel#ErrLabel     {{ color: {c['danger']}; font-size: 10px; font-style: italic; }}

            QLineEdit, QDateEdit {{
                padding: 8px 10px;
                border: 1px solid {c['border']};
                border-radius: 8px;
                background-color: {c['bg_input']};
                font-size: 12px;
                color: {c['text_primary']};
            }}
            QLineEdit:focus, QDateEdit:focus {{
                border: 2px solid {c['border_focus']};
                background-color: {c['bg_card']};
            }}
            QLineEdit:disabled {{ background-color: {c['bg_main']}; color: {c['primary']}; border: 1px solid {c['border_light']}; }}

            QComboBox {{
                padding: 8px 10px;
                border: 1px solid {c['border']};
                border-radius: 8px;
                background-color: {c['bg_input']};
                font-size: 12px;
                color: {c['text_primary']};
            }}
            QComboBox:focus   {{ border: 2px solid {c['border_focus']}; background-color: {c['bg_card']}; }}
            QComboBox:disabled {{ background-color: {c['bg_main']}; color: {c['primary']}; border: 1px solid {c['border_light']}; }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox::down-arrow {{ width: 0; height: 0; }}

            QComboBox QAbstractItemView {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                color: {c['text_primary']};
                selection-background-color: {c['primary_light']};
                selection-color: {c['primary']};
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                background-color: {c['bg_card']};
                color: {c['text_primary']};
                padding: 6px 10px;
                min-height: 26px;
            }}
            QComboBox QAbstractItemView::item:hover    {{ background-color: {c['hover']}; color: {c['primary']}; }}
            QComboBox QAbstractItemView::item:selected {{ background-color: {c['primary_light']}; color: {c['primary']}; }}

            QTextEdit {{
                padding: 8px 10px;
                border: 1px solid {c['border']};
                border-radius: 8px;
                background-color: {c['bg_input']};
                font-size: 12px;
                color: {c['text_primary']};
            }}
            QTextEdit:focus {{ border: 2px solid {c['border_focus']}; background-color: {c['bg_card']}; }}

            QPushButton#SaveBtn {{
                background-color: {c['primary']}; color: {c['text_inverse']};
                border-radius: 10px; font-weight: bold;
                font-size: 13px; padding: 10px;
            }}
            QPushButton#SaveBtn:disabled {{ background-color: {c['border']}; color: {c['text_muted']}; }}
            QPushButton#CancelBtn {{
                background-color: {c['bg_main']}; color: {c['text_secondary']};
                border-radius: 10px; padding: 10px; font-size: 13px;
                border: 1px solid {c['border']};
            }}
        """)

    def apply_theme(self):
        c = theme_manager.colors()
        self._apply_container_style()
        self._apply_header_style()
        self._apply_footer_style()
        self._apply_save_btn_style()
        self.sep.setStyleSheet(f"background-color: {c['border_light']}; border: none;")
        self.addr_label.setStyleSheet(f"color: {c['text_muted']}; font-size: 11px;")
        self.title_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {c['primary']};")
        self._valider_formulaire()

    # =========================================================================
    # HEADER
    # =========================================================================

    def _setup_header(self, parent_layout):
        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(65)
        self._apply_header_style()
        layout = QHBoxLayout(self.header_frame)
        layout.setContentsMargins(25, 0, 25, 0)

        cab = QVBoxLayout()
        cab.setSpacing(1)
        n = QLabel(self.info_cabinet.get("nom_cabinet", "Cabinet MÃ©dical"))
        n.setObjectName("CabinetName")
        self.addr_label = QLabel(self.info_cabinet.get("adresse_cabinet", "Service des Consultations"))
        self.addr_label.setStyleSheet(f"color: {theme_manager.colors()['text_muted']}; font-size: 11px;")
        cab.addWidget(n)
        cab.addWidget(self.addr_label)
        layout.addLayout(cab)
        layout.addStretch()

        self.title_label = QLabel("Nouvelle Consultation" if not self.consultation_obj else "Modifier Consultation")
        self.title_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {theme_manager.colors()['primary']};")
        layout.addWidget(self.title_label)
        layout.addStretch()

        logo_path = self.info_cabinet.get('logo_url')
        if logo_path and os.path.exists(logo_path):
            ll = QLabel()
            ll.setPixmap(QPixmap(logo_path).scaled(45, 45, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            layout.addWidget(ll)

        parent_layout.addWidget(self.header_frame)

    def _apply_header_style(self):
        c = theme_manager.colors()
        self.header_frame.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                stop:0 {c['primary_light']}, stop:0.45 {c['bg_card']}, stop:1 {c['bg_card']});
            border-top-left-radius: 20px;
            border-top-right-radius: 20px;
            border-bottom: 1px solid {c['border_light']};
        """)

    # =========================================================================
    # CORPS
    # =========================================================================

    def _setup_corps(self, parent_layout):
        corps = QWidget()
        corps.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(corps)
        layout.setContentsMargins(25, 18, 25, 20)
        layout.setSpacing(30)

        layout.addLayout(self._colonne_gauche(), 5)

        self.sep = QFrame()
        self.sep.setFrameShape(QFrame.VLine)
        self.sep.setFixedWidth(1)
        self.sep.setStyleSheet(f"background-color: {theme_manager.colors()['border_light']}; border: none;")
        layout.addWidget(self.sep)

        layout.addLayout(self._colonne_droite(), 5)

        parent_layout.addWidget(corps)

    # â”€â”€â”€ COLONNE GAUCHE â”€â”€â”€

    def _colonne_gauche(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(6)

        self._titre_section(col, "Diagnostic & RÃ©sultat", "fa5s.stethoscope")

        col.addWidget(self._label_champ("Diagnostic"))
        self.edit_diagnostique = QTextEdit()
        self.edit_diagnostique.setPlaceholderText("Saisir le diagnostic mÃ©dical...")
        self.edit_diagnostique.setFixedHeight(150)
        col.addWidget(self.edit_diagnostique)
        self._err_diagnostique = self._err_label()
        col.addWidget(self._err_diagnostique)

        col.addWidget(self._label_champ("RÃ©sultat de Consultation"))
        self.edit_resultat = QTextEdit()
        self.edit_resultat.setPlaceholderText("Saisir le rÃ©sultat de la consultation...")
        self.edit_resultat.setFixedHeight(150)
        col.addWidget(self.edit_resultat)
        self._err_resultat = self._err_label()
        col.addWidget(self._err_resultat)

        col.addStretch()
        return col

    # â”€â”€â”€ COLONNE DROITE â”€â”€â”€

    def _colonne_droite(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(6)

        self._titre_section(col, "Identification", "fa5s.id-badge")

        # Visite + Personnel cÃ´te Ã  cÃ´te
        row_id = QHBoxLayout()
        row_id.setSpacing(10)

        vbox_visite = QVBoxLayout()
        vbox_visite.setSpacing(3)
        vbox_visite.addWidget(self._label_champ("Visite / Patient en attente"))
        self.combo_visite = QComboBox()
        self.combo_visite.setFixedHeight(36)
        self.combo_visite.addItem("â€” SÃ©lectionner une visite â€”", "")
        for v in self._visites_attente:
            label = (f"{v.get('code_visite', '')}  |  "
                     f"{v.get('nom', '')} {v.get('prenom', '')}  |  "
                     f"{v.get('motif', '')}")
            self.combo_visite.addItem(label, v.get('code_visite', ''))
        vbox_visite.addWidget(self.combo_visite)
        self._err_visite = self._err_label()
        vbox_visite.addWidget(self._err_visite)
        row_id.addLayout(vbox_visite)

        vbox_perso = QVBoxLayout()
        vbox_perso.setSpacing(3)
        vbox_perso.addWidget(self._label_champ("MÃ©decin / Personnel"))
        self.combo_personnel = QComboBox()
        self.combo_personnel.setFixedHeight(36)
        self.combo_personnel.addItem("â€” SÃ©lectionner un mÃ©decin â€”", "")
        for p in self._personnels:
            label = (f"{p.get('code', '')}  |  "
                     f"{p.get('nom', '')} {p.get('prenom', '')}  |  "
                     f"{p.get('fonction', '')}")
            self.combo_personnel.addItem(label, p.get('code', ''))
        vbox_perso.addWidget(self.combo_personnel)
        self._err_personnel = self._err_label()
        vbox_perso.addWidget(self._err_personnel)
        row_id.addLayout(vbox_perso)

        col.addLayout(row_id)

        # Date et Heure (Instant prÃ©sent par dÃ©faut)
        vbox_date = QVBoxLayout()
        vbox_date.setSpacing(3)
        vbox_date.addWidget(self._label_champ("Date et Heure de Consultation"))
        self.edit_date = QDateTimeEdit()
        self.edit_date.setCalendarPopup(True)
        self.edit_date.setDateTime(QDateTime.currentDateTime()) # Prend l'instant T
        self.edit_date.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.edit_date.setFixedHeight(36)
        vbox_date.addWidget(self.edit_date)
        col.addLayout(vbox_date)

        # Services
        self._titre_section(col, "Services Prescrits", "fa5s.list-alt")

        row_s1 = QHBoxLayout()
        row_s1.setSpacing(10)
        self.combo_examen    = self._combo_ouinon(row_s1, "Examen",    "fa5s.microscope")
        self.combo_chirurgie = self._combo_ouinon(row_s1, "Chirurgie", "fa5s.procedures")
        col.addLayout(row_s1)

        row_s2 = QHBoxLayout()
        row_s2.setSpacing(10)
        self.combo_lunette      = self._combo_ouinon(row_s2, "Lunettes",     "fa5s.glasses")
        self.combo_prescription = self._combo_ouinon(row_s2, "Prescription", "fa5s.pills")
        col.addLayout(row_s2)

        # Facturation
        self._titre_section(col, "Facturation", "fa5s.file-invoice-dollar")

        row_fact = QHBoxLayout()
        row_fact.setSpacing(10)

        vbox_frais = QVBoxLayout()
        vbox_frais.setSpacing(3)
        vbox_frais.addWidget(self._label_champ("Frais (GNF)"))
        self.edit_frais = QLineEdit()
        self.edit_frais.setPlaceholderText("Ex: 50000")
        self.edit_frais.setFixedHeight(36)
        self.edit_frais.addAction(
            qta.icon("fa5s.money-bill-wave", color=theme_manager.colors()['primary']),
            QLineEdit.LeadingPosition
        )
        vbox_frais.addWidget(self.edit_frais)
        self._err_frais = self._err_label()
        vbox_frais.addWidget(self._err_frais)
        row_fact.addLayout(vbox_frais)

        # Dans _colonne_droite
        vbox_statut = QVBoxLayout()
        vbox_statut.setSpacing(3)
        vbox_statut.addWidget(self._label_champ("Statut Facture"))
        self.combo_statut = QComboBox()
        self.combo_statut.setFixedHeight(36)
        self.combo_statut.setEnabled(False)  # Toujours dÃ©sactivÃ© pour l'utilisateur
        c = theme_manager.colors()
        self.combo_statut.setStyleSheet(f"QComboBox:disabled {{ background-color: {c['bg_main']}; color: {c['text_secondary']}; }}")
        vbox_statut.addWidget(self.combo_statut)
        row_fact.addLayout(vbox_statut)

        col.addLayout(row_fact)
        col.addStretch()
        return col

    # =========================================================================
    # FOOTER
    # =========================================================================

    def _setup_footer(self, parent_layout):
        self.footer_frame = QFrame()
        self.footer_frame.setFixedHeight(62)
        self._apply_footer_style()
        layout = QHBoxLayout(self.footer_frame)
        layout.setContentsMargins(25, 0, 25, 0)
        layout.setSpacing(15)

        c = theme_manager.colors()
        self.btn_cancel = QPushButton(qta.icon("fa5s.times", color=c['text_muted']), " Annuler")
        self.btn_cancel.setObjectName("CancelBtn")
        self.btn_cancel.setFixedHeight(42)
        self.btn_cancel.clicked.connect(self.reject)

        label_save = " Enregistrer" if not self.consultation_obj else " Mettre Ã  jour"
        self.btn_save = QPushButton(qta.icon("fa5s.save", color=c['text_inverse']), label_save)
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
        self.footer_frame.setStyleSheet(f"""
            background-color: {c['bg_main']};
            border-bottom-left-radius: 20px;
            border-bottom-right-radius: 20px;
            border-top: 1px solid {c['border_light']};
        """)

    def _apply_save_btn_style(self):
        c = theme_manager.colors()
        self.btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['border']}; color: {c['text_muted']};
                border-radius: 10px; font-weight: bold;
                font-size: 13px; padding: 10px; border: none;
            }}
            QPushButton:enabled {{
                background-color: {c['primary']}; color: {c['text_inverse']};
            }}
            QPushButton:enabled:hover {{
                background-color: {c['primary_hover']}; color: {c['text_inverse']};
            }}
        """)

    # =========================================================================
    # WIDGETS UTILITAIRES
    # =========================================================================

    def _label_champ(self, texte: str) -> QLabel:
        c = theme_manager.colors()
        lbl = QLabel(texte)
        lbl.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']}; font-size: 11px;")
        return lbl

    def _err_label(self) -> QLabel:
        c = theme_manager.colors()
        lbl = QLabel("")
        lbl.setObjectName("ErrLabel")
        lbl.setStyleSheet(f"color: {c['danger']}; font-size: 10px; font-style: italic;")
        lbl.setVisible(False)
        return lbl

    def _titre_section(self, layout, titre: str, icone: str):
        c = theme_manager.colors()
        hbox = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(qta.icon(icone, color=c['primary']).pixmap(13, 13))
        lbl = QLabel(titre)
        lbl.setObjectName("SectionTitle")
        hbox.addWidget(ico)
        hbox.addSpacing(5)
        hbox.addWidget(lbl)
        hbox.addStretch()
        layout.addLayout(hbox)

    def _combo_ouinon(self, layout: QHBoxLayout, label_text: str, icone: str) -> QComboBox:
        c = theme_manager.colors()
        vbox = QVBoxLayout()
        vbox.setSpacing(4)

        hbox_lbl = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(qta.icon(icone, color=c['primary']).pixmap(12, 12))
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']}; font-size: 11px;")
        hbox_lbl.addWidget(ico)
        hbox_lbl.addSpacing(4)
        hbox_lbl.addWidget(lbl)
        hbox_lbl.addStretch()
        vbox.addLayout(hbox_lbl)

        combo = QComboBox()
        combo.addItem(qta.icon("fa5s.times-circle", color=c['danger']), "Non")
        combo.addItem(qta.icon("fa5s.check-circle", color=c['primary']), "Oui")
        combo.setFixedHeight(34)
        vbox.addWidget(combo)

        layout.addLayout(vbox)
        return combo

    # =========================================================================
    # VALIDATION TEMPS RÃ‰EL
    # =========================================================================

    def _connecter_validations(self):
        """Connecte tous les champs Ã  la validation en temps rÃ©el."""
        self.edit_diagnostique.textChanged.connect(self._valider_formulaire)
        self.edit_resultat.textChanged.connect(self._valider_formulaire)
        self.edit_frais.textChanged.connect(self._valider_formulaire)
        self.combo_visite.currentIndexChanged.connect(self._valider_formulaire)
        self.combo_personnel.currentIndexChanged.connect(self._valider_formulaire)

    def _valider_formulaire(self):
        """Valide tous les champs et active/dÃ©sactive le bouton Enregistrer."""
        tout_valide = True

        # â”€â”€ Diagnostic â”€â”€
        diag = self.edit_diagnostique.toPlainText().strip()
        ok, msg = self.controleur.valider_texte(diag, "diagnostique")
        self._style_textarea(self.edit_diagnostique, self._err_diagnostique, ok, msg, diag)
        if not ok: tout_valide = False

        # â”€â”€ RÃ©sultat â”€â”€
        res = self.edit_resultat.toPlainText().strip()
        ok, msg = self.controleur.valider_texte(res, "rÃ©sultat")
        self._style_textarea(self.edit_resultat, self._err_resultat, ok, msg, res)
        if not ok: tout_valide = False

        # â”€â”€ Frais â”€â”€
        frais = self.edit_frais.text().strip()
        ok, msg = self.controleur.valider_frais(frais if frais else "-1")
        self._style_lineedit(self.edit_frais, self._err_frais, ok, msg, frais)
        if not ok: tout_valide = False

        # â”€â”€ Visite â”€â”€
        if not self.combo_visite.currentData():
            self._err_visite.setText("Veuillez sÃ©lectionner une visite")
            self._err_visite.setVisible(True)
            tout_valide = False
        else:
            self._err_visite.setVisible(False)

        # â”€â”€ Personnel â”€â”€
        if not self.combo_personnel.currentData():
            self._err_personnel.setText("Veuillez sÃ©lectionner un mÃ©decin")
            self._err_personnel.setVisible(True)
            tout_valide = False
        else:
            self._err_personnel.setVisible(False)

        # === LOGIQUE DU STATUT ===
        c = theme_manager.colors()
        self.combo_statut.clear()
        if tout_valide:
            self.combo_statut.addItem("attente payement")
            self.combo_statut.setStyleSheet(f"QComboBox:disabled {{ background-color: {c['bg_main']}; color: {c['primary']}; border: 1px solid {c['border_focus']}; }}")
        else:
            self.combo_statut.addItem("Formulaire incomplet...")
            self.combo_statut.setStyleSheet(f"QComboBox:disabled {{ background-color: {c['bg_main']}; color: {c['text_secondary']}; border: 1px solid {c['border_light']}; }}")

        self.btn_save.setEnabled(tout_valide)

    def _style_textarea(self, widget, err_lbl, valide, message, texte):
        c = theme_manager.colors()
        base = "border-radius: 8px; padding: 8px; font-size: 12px;"
        if not valide and texte:
            widget.setStyleSheet(f"border: 1px solid {c['danger']}; background-color: {c['danger_bg']}; {base}")
            err_lbl.setText(message)
            err_lbl.setVisible(True)
        elif not valide:
            widget.setStyleSheet(f"border: 1px solid {c['border']}; background-color: {c['bg_input']}; color: {c['text_primary']}; {base}")
            err_lbl.setVisible(False)
        else:
            widget.setStyleSheet(f"border: 2px solid {c['border_focus']}; background-color: {c['bg_card']}; {base}")
            err_lbl.setVisible(False)

    def _style_lineedit(self, widget, err_lbl, valide, message, texte):
        c = theme_manager.colors()
        base = "border-radius: 8px; padding: 8px; font-size: 12px;"
        if not valide and texte:
            widget.setStyleSheet(f"border: 1px solid {c['danger']}; background-color: {c['danger_bg']}; {base}")
            err_lbl.setText(message)
            err_lbl.setVisible(True)
        elif not valide:
            widget.setStyleSheet(f"border: 1px solid {c['border']}; background-color: {c['bg_input']}; color: {c['text_primary']}; {base}")
            err_lbl.setVisible(False)
        else:
            widget.setStyleSheet(f"border: 2px solid {c['border_focus']}; background-color: {c['bg_card']}; {base}")
            err_lbl.setVisible(False)

    # =========================================================================
    # PRÃ‰SÃ‰LECTION
    # =========================================================================

    def _preselectionner_visite(self, code_visite: str):
        for i in range(self.combo_visite.count()):
            if self.combo_visite.itemData(i) == code_visite:
                self.combo_visite.setCurrentIndex(i)
                break
        self.combo_visite.setEnabled(False)

    def _preselectionner_personnel(self, code_personnel: str):
        for i in range(self.combo_personnel.count()):
            if self.combo_personnel.itemData(i) == code_personnel:
                self.combo_personnel.setCurrentIndex(i)
                break

    # =========================================================================
    # REMPLISSAGE MODE MODIFICATION
    # =========================================================================

    def _remplir_champs(self):
        c = self.consultation_obj
        self._preselectionner_visite(c.code_visite)
        self._preselectionner_personnel(c.code_personnel)

        if hasattr(c.date_consultation, 'date'):
            d = c.date_consultation.date()
            self.edit_date.setDate(QDate(d.year, d.month, d.day))

        self.edit_diagnostique.setPlainText(c.diagnostique or "")
        self.edit_resultat.setPlainText(c.resultat_consultation or "")
        self.combo_examen.setCurrentText(c.examen or "Non")
        self.combo_chirurgie.setCurrentText(c.chirurgie or "Non")
        self.combo_lunette.setCurrentText(c.commandelunette or "Non")
        self.combo_prescription.setCurrentText(c.prescription_produit or "Non")
        self.edit_frais.setText(str(c.frais_consultation or ""))
        self.combo_statut.setCurrentText(c.statut_facture or "ConsultÃ©")

    # =========================================================================
    # SOUMISSION
    # =========================================================================

    def _soumettre(self):
        try:
            code_visite    = self.combo_visite.currentData()
            code_personnel = self.combo_personnel.currentData()

            consultation = Consultation(
                code                  = self.consultation_obj.code if self.consultation_obj else None,
                diagnostique          = self.edit_diagnostique.toPlainText().strip(),
                resultat_consultation = self.edit_resultat.toPlainText().strip(),
                examen                = self.combo_examen.currentText(),
                chirurgie             = self.combo_chirurgie.currentText(),
                commandelunette       = self.combo_lunette.currentText(),
                prescription_produit  = self.combo_prescription.currentText(),
                frais_consultation    = float(self.edit_frais.text().strip() or 0),
                statut_facture        = self.combo_statut.currentText(),
                date_consultation     = self.edit_date.date().toPython(),
                code_visite           = code_visite,
                code_session          = self.code_session,
                code_personnel        = code_personnel
            )

            if self.consultation_obj:
                ok, msg = self.controleur.modifier_consultation(consultation)
            else:
                ok, msg = self.controleur.creer_consultation(consultation)

            if ok:
                CustomMessageBox("SuccÃ¨s", msg, True, self).exec()
                self.accept()
            else:
                CustomMessageBox("Erreur", msg, False, self).exec()

        except Exception as e:
            CustomMessageBox("Erreur SystÃ¨me", str(e), False, self).exec()
