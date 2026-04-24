import os
import qtawesome as qta
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QDateTimeEdit, QFrame,
    QGraphicsDropShadowEffect, QTextEdit, QWidget
)
from models.modeles_examen import Examen
from views.shared.message_box import CustomMessageBox
from views.examen.styles import ExamenStyles
from views.shared.theme_manager import theme_manager


class ExamenFormDialog(QDialog):
    """
    Formulaire examen en mode paysage.
    Colonne gauche  : Libelle + Resultat
    Colonne droite  : Consultation â†’ Visite (auto) + Personnel + Date + Facturation
    Quand une consultation est selectionnee, le champ code_visite se remplit automatiquement.
    """

    def __init__(self, controleur, code_session: str,
                 code_consultation: str = "", code_personnel: str = "",
                 examen_obj=None, parent=None):
        super().__init__(parent)
        self.controleur             = controleur
        self.code_session           = code_session
        self.code_consultation_init = code_consultation
        self.code_personnel_init    = code_personnel
        self.examen_obj             = examen_obj
        self.info_cabinet           = self.controleur.get_cabinet_info()

        self._consultations_attente = []
        self._personnels            = []

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(1020, 560)

        self._charger_donnees_combos()
        self._init_ui()
        self._connecter_validations()

        if self.examen_obj:
            self._remplir_champs()
        else:
            if self.code_consultation_init:
                self._preselectionner_consultation(self.code_consultation_init)
            if self.code_personnel_init:
                self._preselectionner_personnel(self.code_personnel_init)

    # =========================================================================
    # DONNEES COMBOS
    # =========================================================================

    def _charger_donnees_combos(self):
        """Charge les consultations en attente d examen et le personnel."""
        try:
            self._consultations_attente = (
                self.controleur.obtenir_patients_attente_examen(self.code_session) or []
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
                background-color: {c['bg_card']}; border-radius: 20px; border: 1px solid {c['border']};
            }}
            QLabel {{ color: {c['text_primary']}; font-size: 12px; background-color: transparent; }}
            QLabel#CabinetName  {{ font-size: 17px; font-weight: bold; color: {c['danger']}; }}
            QLabel#SectionTitle {{ color: {c['primary']}; font-weight: bold; font-size: 11px; }}
            QLabel#ErrLabel     {{ color: {c['danger']}; font-size: 10px; font-style: italic; }}
            QLineEdit, QDateTimeEdit {{
                padding: 8px 10px; border: 1px solid {c['border']};
                border-radius: 8px; background-color: {c['bg_input']};
                font-size: 12px; color: {c['text_primary']};
            }}
            QLineEdit:focus, QDateTimeEdit:focus {{ border: 2px solid {c['border_focus']}; background-color: {c['bg_card']}; }}
            QLineEdit:disabled {{ background-color: {c['bg_main']}; color: {c['primary']}; border: 1px solid {c['border_light']}; }}
            QComboBox {{
                padding: 8px 10px; border: 1px solid {c['border']};
                border-radius: 8px; background-color: {c['bg_input']};
                font-size: 12px; color: {c['text_primary']};
            }}
            QComboBox:focus   {{ border: 2px solid {c['border_focus']}; background-color: {c['bg_card']}; }}
            QComboBox:disabled {{ background-color: {c['bg_main']}; color: {c['primary']}; border: 1px solid {c['border_light']}; }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox::down-arrow {{ width: 0; height: 0; }}
            QComboBox QAbstractItemView {{
                background-color: {c['bg_card']}; border: 1px solid {c['border']};
                border-radius: 8px; color: {c['text_primary']};
                selection-background-color: {c['primary_light']}; selection-color: {c['primary']}; outline: none;
            }}
            QTextEdit {{
                padding: 8px 10px; border: 1px solid {c['border']};
                border-radius: 8px; background-color: {c['bg_input']};
                font-size: 12px; color: {c['text_primary']};
            }}
            QTextEdit:focus {{ border: 2px solid {c['border_focus']}; background-color: {c['bg_card']}; }}
            QPushButton#SaveBtn {{
                background-color: {c['primary']}; color: {c['text_inverse']};
                border-radius: 10px; font-weight: bold; font-size: 13px; padding: 10px;
            }}
            QPushButton#SaveBtn:disabled {{ background-color: {c['border']}; color: {c['text_muted']}; }}
            QPushButton#CancelBtn {{
                background-color: {c['bg_main']}; color: {c['text_secondary']};
                border-radius: 10px; padding: 10px; font-size: 13px; border: 1px solid {c['border']};
            }}
        """)

    def apply_theme(self):
        c = theme_manager.colors()
        self._apply_container_style()
        self._apply_header_style()
        self._apply_footer_style()
        self._apply_save_btn_style()
        self.sep.setStyleSheet(f"background-color: {c['border_light']}; border: none;")
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
        c = theme_manager.colors()

        cab = QVBoxLayout()
        cab.setSpacing(1)
        n = QLabel(self.info_cabinet.get("nom_cabinet", "Cabinet Medical"))
        n.setObjectName("CabinetName")
        a = QLabel(self.info_cabinet.get("adresse_cabinet", "Service des Examens"))
        a.setStyleSheet(f"color: {c['text_muted']}; font-size: 11px;")
        cab.addWidget(n)
        cab.addWidget(a)
        layout.addLayout(cab)
        layout.addStretch()

        t = QLabel("Nouvel Examen" if not self.examen_obj else "Modifier Examen")
        t.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {c['primary']};")
        layout.addWidget(t)
        layout.addStretch()

        logo_path = self.info_cabinet.get("logo_url")
        if logo_path and os.path.exists(logo_path):
            ll = QLabel()
            ll.setPixmap(QPixmap(logo_path).scaled(
                45, 45, Qt.KeepAspectRatio, Qt.SmoothTransformation))
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

        self._titre_section(col, "Libelle & Resultat", "fa5s.microscope")

        col.addWidget(self._label_champ("Libelle de l Examen"))
        self.edit_libelle = QTextEdit()
        self.edit_libelle.setPlaceholderText("Ex: Fond d oeil, Tonometrie, Champ visuel...")
        self.edit_libelle.setFixedHeight(150)
        col.addWidget(self.edit_libelle)
        self._err_libelle = self._err_label()
        col.addWidget(self._err_libelle)

        col.addWidget(self._label_champ("Resultat de l Examen"))
        self.edit_resultat = QTextEdit()
        self.edit_resultat.setPlaceholderText("Saisir le resultat de l examen...")
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

        # Consultation
        col.addWidget(self._label_champ("Consultation liee (patient en attente examen)"))
        self.combo_consultation = QComboBox()
        self.combo_consultation.setFixedHeight(36)
        self.combo_consultation.addItem("â€” Selectionner une consultation â€”", "")
        for c in self._consultations_attente:
            label = (
                f"{c.get('code_consultation', '')}  |  "
                f"{c.get('nom', '')} {c.get('prenom', '')}  |  "
                f"{c.get('date_consultation', '')}"
            )
            self.combo_consultation.addItem(label, {
                "code_consultation": c.get("code_consultation", ""),
                "code_visite":       c.get("code_visite",       "")
            })
        col.addWidget(self.combo_consultation)
        self._err_consultation = self._err_label()
        col.addWidget(self._err_consultation)

        # Code Visite â€” lecture seule, auto-rempli
        col.addWidget(self._label_champ("Code Visite (rempli automatiquement)"))
        self.edit_code_visite = QLineEdit()
        self.edit_code_visite.setPlaceholderText("Selectionnez une consultation...")
        self.edit_code_visite.setFixedHeight(36)
        self.edit_code_visite.setReadOnly(True)
        c_vis = theme_manager.colors()
        self.edit_code_visite.setStyleSheet(
            f"background-color: {c_vis['bg_main']}; color: {c_vis['primary']}; "
            f"font-weight: bold; border: 1px solid {c_vis['border']}; border-radius: 8px;"
        )
        col.addWidget(self.edit_code_visite)

        # Personnel
        col.addWidget(self._label_champ("Medecin / Personnel"))
        self.combo_personnel = QComboBox()
        self.combo_personnel.setFixedHeight(36)
        self.combo_personnel.addItem("â€” Selectionner un medecin â€”", "")
        for p in self._personnels:
            label = (
                f"{p.get('code', '')}  |  "
                f"{p.get('nom', '')} {p.get('prenom', '')}  |  "
                f"{p.get('fonction', '')}"
            )
            self.combo_personnel.addItem(label, p.get("code", ""))
        col.addWidget(self.combo_personnel)
        self._err_personnel = self._err_label()
        col.addWidget(self._err_personnel)

        # Date
        col.addWidget(self._label_champ("Date et Heure de l Examen"))
        self.edit_date = QDateTimeEdit()
        self.edit_date.setCalendarPopup(True)
        self.edit_date.setDateTime(QDateTime.currentDateTime())
        self.edit_date.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.edit_date.setFixedHeight(36)
        col.addWidget(self.edit_date)

        # Facturation
        self._titre_section(col, "Facturation", "fa5s.file-invoice-dollar")

        row_fact = QHBoxLayout()
        row_fact.setSpacing(10)

        vbox_frais = QVBoxLayout()
        vbox_frais.setSpacing(3)
        vbox_frais.addWidget(self._label_champ("Frais (GNF)"))
        self.edit_frais = QLineEdit()
        self.edit_frais.setPlaceholderText("Ex: 80000")
        self.edit_frais.setFixedHeight(36)
        self.edit_frais.addAction(
            qta.icon("fa5s.money-bill-wave", color=theme_manager.colors()['primary']),
            QLineEdit.LeadingPosition
        )
        vbox_frais.addWidget(self.edit_frais)
        self._err_frais = self._err_label()
        vbox_frais.addWidget(self._err_frais)
        row_fact.addLayout(vbox_frais)

        vbox_statut = QVBoxLayout()
        vbox_statut.setSpacing(3)
        vbox_statut.addWidget(self._label_champ("Statut Facture"))
        self.combo_statut = QComboBox()
        self.combo_statut.setFixedHeight(36)
        self.combo_statut.setEnabled(False)
        c_st = theme_manager.colors()
        self.combo_statut.setStyleSheet(
            f"QComboBox:disabled {{ background-color: {c_st['bg_main']}; color: {c_st['text_secondary']}; }}"
        )
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

        label_save = " Enregistrer" if not self.examen_obj else " Mettre a jour"
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

    # =========================================================================
    # VALIDATION TEMPS REEL
    # =========================================================================

    def _connecter_validations(self):
        self.edit_libelle.textChanged.connect(self._valider_formulaire)
        self.edit_resultat.textChanged.connect(self._valider_formulaire)
        self.edit_frais.textChanged.connect(self._valider_formulaire)
        self.combo_consultation.currentIndexChanged.connect(self._on_consultation_changed)
        self.combo_personnel.currentIndexChanged.connect(self._valider_formulaire)

    def _on_consultation_changed(self):
        """
        Quand une consultation est selectionnee :
        1. Remplit automatiquement le champ code_visite
        2. Relance la validation du formulaire
        """
        data = self.combo_consultation.currentData()
        if data and isinstance(data, dict):
            code_visite = data.get("code_visite", "")
            self.edit_code_visite.setText(code_visite)
        else:
            self.edit_code_visite.clear()
        self._valider_formulaire()

    def _valider_formulaire(self):
        tout_valide = True

        # Libelle
        libelle = self.edit_libelle.toPlainText().strip()
        ok, msg = self.controleur.valider_texte(libelle, "libelle examen")
        self._style_textarea(self.edit_libelle, self._err_libelle, ok, msg, libelle)
        if not ok: tout_valide = False

        # Resultat
        res = self.edit_resultat.toPlainText().strip()
        ok, msg = self.controleur.valider_texte(res, "resultat")
        self._style_textarea(self.edit_resultat, self._err_resultat, ok, msg, res)
        if not ok: tout_valide = False

        # Frais
        frais = self.edit_frais.text().strip()
        ok, msg = self.controleur.valider_frais(frais if frais else "-1")
        self._style_lineedit(self.edit_frais, self._err_frais, ok, msg, frais)
        if not ok: tout_valide = False

        # Consultation
        if not self.combo_consultation.currentData():
            self._err_consultation.setText("Veuillez selectionner une consultation")
            self._err_consultation.setVisible(True)
            tout_valide = False
        else:
            self._err_consultation.setVisible(False)

        # Personnel
        if not self.combo_personnel.currentData():
            self._err_personnel.setText("Veuillez selectionner un medecin")
            self._err_personnel.setVisible(True)
            tout_valide = False
        else:
            self._err_personnel.setVisible(False)

        # Statut facture dynamique
        c = theme_manager.colors()
        self.combo_statut.clear()
        if tout_valide:
            self.combo_statut.addItem("attente payement")
            self.combo_statut.setStyleSheet(
                f"QComboBox:disabled {{ background-color: {c['bg_main']}; "
                f"color: {c['primary']}; border: 1px solid {c['border_focus']}; }}"
            )
        else:
            self.combo_statut.addItem("Formulaire incomplet...")
            self.combo_statut.setStyleSheet(
                f"QComboBox:disabled {{ background-color: {c['bg_main']}; "
                f"color: {c['text_secondary']}; border: 1px solid {c['border_light']}; }}"
            )

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
        e = self.examen_obj
        self._preselectionner_consultation(e.code_consultation)
        self.edit_code_visite.setText(e.code_visite or "")
        self._preselectionner_personnel(e.code_personnel)

        if hasattr(e.date_examen, "date"):
            from PySide6.QtCore import QDate
            d = e.date_examen.date()
            self.edit_date.setDate(QDate(d.year, d.month, d.day))

        self.edit_libelle.setPlainText(e.libelle_examen or "")
        self.edit_resultat.setPlainText(e.resultat_examen or "")
        self.edit_frais.setText(str(e.frais_examen or ""))

    # =========================================================================
    # SOUMISSION
    # =========================================================================

    def _soumettre(self):
        try:
            data_consultation = self.combo_consultation.currentData()
            code_consultation = data_consultation.get("code_consultation", "") if data_consultation else ""
            code_visite       = self.edit_code_visite.text().strip()
            code_personnel    = self.combo_personnel.currentData()

            examen = Examen(
                code             = self.examen_obj.code if self.examen_obj else None,
                libelle_examen   = self.edit_libelle.toPlainText().strip(),
                resultat_examen  = self.edit_resultat.toPlainText().strip(),
                frais_examen     = float(self.edit_frais.text().strip() or 0),
                statut_facture   = self.combo_statut.currentText(),
                date_examen      = self.edit_date.dateTime().toPython(),
                code_consultation= code_consultation,
                code_visite      = code_visite,
                code_session     = self.code_session,
                code_personnel   = code_personnel
            )

            if self.examen_obj:
                ok, msg = self.controleur.modifier_examen(examen)
            else:
                ok, msg = self.controleur.creer_examen(examen)

            if ok:
                CustomMessageBox("Succes", msg, True, self).exec()
                self.accept()
            else:
                CustomMessageBox("Erreur", msg, False, self).exec()

        except Exception as e:
            CustomMessageBox("Erreur Systeme", str(e), False, self).exec()
