"""
Widget formulaire consultation (version non-modale pour onglet)
Design identique à ConsultationFormDialog mais intégré directement dans l'onglet.
"""
import os
import qtawesome as qta
from PySide6.QtCore import Qt, QDateTime, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFrame, QTextEdit, QDateTimeEdit, QScrollArea,
    QSizePolicy
)
from models.modele_consultation import Consultation
from views.shared.message_box import CustomMessageBox
from views.shared.theme_manager import theme_manager


class ConsultationFormWidget(QWidget):
    """
    Widget formulaire consultation intégré dans l'onglet 'Nouveau'.
    Même design que ConsultationFormDialog mais sans fenêtre modale.
    """

    consultation_saved = Signal()

    def __init__(self, controleur, code_session: str, code_visite: str = "",
                 code_personnel: str = "", consultation_obj=None, parent=None):
        super().__init__(parent)
        self.controleur          = controleur
        self.code_session        = code_session
        self.code_visite_init    = code_visite
        self.code_personnel_init = code_personnel
        self.consultation_obj    = consultation_obj

        self._visites_attente = []
        self._personnels      = []

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

        theme_manager.theme_changed.connect(self.apply_theme)

    # =========================================================================
    # DONNÉES COMBOS
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
        outer.setContentsMargins(24, 6, 24, 16)
        outer.setSpacing(14)

        self._setup_header(outer)
        self._section_infos(outer)
        self._section_info_bas(outer)
        outer.addStretch()

        self.apply_theme()

    # =========================================================================
    # HEADER  (titre + boutons Annuler / Enregistrer)
    # =========================================================================

    def _setup_header(self, parent_layout):
        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(72)
        c = theme_manager.colors()
        self.header_frame.setStyleSheet(f"""
            background-color: {c['bg_card']};
            border-radius: 14px;
            border: none;
        """)

        layout = QHBoxLayout(self.header_frame)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(14)

        # Icône stéthoscope
        icon_box = QFrame()
        icon_box.setFixedSize(46, 46)
        icon_box.setStyleSheet(f"""
            background-color: {c['bg_main']};
            border-radius: 10px;
            border: 1px solid {c['border_light']};
        """)
        ib_layout = QHBoxLayout(icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        ico_lbl = QLabel()
        ico_lbl.setPixmap(qta.icon("fa5s.stethoscope", color=c['primary']).pixmap(22, 22))
        ico_lbl.setAlignment(Qt.AlignCenter)
        ib_layout.addWidget(ico_lbl, alignment=Qt.AlignCenter)

        # Titre + sous-titre
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        lbl_main = QLabel("Enregistrement d'une consultation")
        lbl_main.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {c['text_primary']}; background: transparent; border: none;")
        lbl_sub = QLabel("Saisissez les informations de la consultation")
        lbl_sub.setStyleSheet(f"font-size: 12px; color: {c['text_muted']}; background: transparent; border: none;")
        title_col.addWidget(lbl_main)
        title_col.addWidget(lbl_sub)

        layout.addWidget(icon_box)
        layout.addLayout(title_col)
        layout.addStretch()

        # Bouton Annuler
        self.btn_cancel = QPushButton(qta.icon("fa5s.times", color=c['text_secondary']), " Annuler")
        self.btn_cancel.setFixedSize(110, 40)
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['bg_main']};
                color: {c['text_secondary']};
                border: 1.5px solid {c['border']};
                border-radius: 10px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background-color: {c['hover']}; }}
        """)
        self.btn_cancel.clicked.connect(self._on_cancel)

        # Bouton Enregistrer
        label_save = " Enregistrer" if not self.consultation_obj else " Mettre à jour"
        self.btn_save = QPushButton(qta.icon("fa5s.save", color="#ffffff"), label_save)
        self.btn_save.setFixedSize(140, 40)
        self.btn_save.setEnabled(False)
        self._apply_save_btn_style()
        self.btn_save.clicked.connect(self._soumettre)

        layout.addWidget(self.btn_cancel)
        layout.addWidget(self.btn_save)
        parent_layout.addWidget(self.header_frame)

    def _apply_save_btn_style(self):
        c = theme_manager.colors()
        self.btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['border']};
                color: {c['text_muted']};
                border-radius: 10px;
                font-weight: bold;
                font-size: 13px;
                border: none;
            }}
            QPushButton:enabled {{
                background-color: {c['primary']};
                color: #ffffff;
            }}
            QPushButton:enabled:hover {{ background-color: {c['primary_hover']}; }}
        """)

    # =========================================================================
    # HELPERS : CHAMP AVEC ICÔNE
    # =========================================================================

    def _make_field(self, label_text: str, widget, icon_name: str, icon_color: str,
                    height: int = 42, align_top: bool = False):
        """Retourne (QVBoxLayout, wrapper_QFrame) : label + cadre [badge-icône + widget]."""
        c = theme_manager.colors()
        vbox = QVBoxLayout()
        vbox.setSpacing(4)

        lbl = QLabel(label_text)
        lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {c['text_secondary']};"
            " background: transparent; border: none;"
        )
        vbox.addWidget(lbl)

        wrapper = QFrame()
        wrapper.setObjectName("inputWrapper")
        if align_top:
            wrapper.setMinimumHeight(height)
        else:
            wrapper.setFixedHeight(height)
        self._apply_wrapper_style(wrapper)

        hbox = QHBoxLayout(wrapper)
        hbox.setContentsMargins(8, 5, 8, 5)
        hbox.setSpacing(8)
        v_align = Qt.AlignTop if align_top else Qt.AlignVCenter

        badge = QFrame()
        badge.setFixedSize(28, 28)
        badge.setStyleSheet(f"background-color: {icon_color}20; border-radius: 7px; border: none;")
        bl = QHBoxLayout(badge)
        bl.setContentsMargins(0, 0, 0, 0)
        ico_lbl = QLabel()
        ico_lbl.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(14, 14))
        ico_lbl.setAlignment(Qt.AlignCenter)
        ico_lbl.setStyleSheet("border: none; background: transparent;")
        bl.addWidget(ico_lbl, alignment=Qt.AlignCenter)

        self._clear_widget_style(widget, c)
        hbox.addWidget(badge, 0, v_align)
        hbox.addWidget(widget, 1)
        vbox.addWidget(wrapper)
        return vbox, wrapper

    def _apply_wrapper_style(self, wrapper: QFrame, border_color: str = None):
        c = theme_manager.colors()
        bc = border_color or c['border']
        wrapper.setStyleSheet(f"""
            QFrame#inputWrapper {{
                background-color: {c['bg_input']};
                border: 1.5px solid {bc};
                border-radius: 10px;
            }}
        """)

    def _clear_widget_style(self, widget, c):
        """Enlève bordure et fond du widget interne — le wrapper reste visible."""
        base = (
            f"border: none; background: transparent;"
            f" font-size: 12px; color: {c['text_primary']};"
        )
        if isinstance(widget, QComboBox):
            widget.setStyleSheet(f"""
                QComboBox {{ {base} padding: 0; min-height: 28px; }}
                QComboBox::drop-down {{ border: none; width: 20px; }}
                QComboBox QAbstractItemView {{
                    background-color: {c['bg_card']};
                    border: 1px solid {c['border']};
                    border-radius: 8px;
                    color: {c['text_primary']};
                    selection-background-color: {c['primary_light']};
                    outline: none;
                }}
                QComboBox QAbstractItemView::item {{ padding: 6px 10px; min-height: 26px; }}
                QComboBox QAbstractItemView::item:hover {{ background-color: {c['hover']}; }}
                QComboBox QAbstractItemView::item:selected {{
                    background-color: {c['primary_light']}; color: {c['primary']};
                }}
            """)
        elif isinstance(widget, QDateTimeEdit):
            widget.setStyleSheet(f"QDateTimeEdit {{ {base} padding: 0; }}")
        elif isinstance(widget, QTextEdit):
            widget.setStyleSheet(f"QTextEdit {{ {base} padding: 4px 0; }}")
        else:
            widget.setStyleSheet(f"QLineEdit {{ {base} padding: 0; }}")

    # =========================================================================
    # SECTION INFORMATIONS
    # =========================================================================

    def _section_infos(self, parent_layout):
        c = theme_manager.colors()
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {c['bg_card']};
                border: 1.5px solid {c['border_light']};
                border-radius: 14px;
            }}
        """)
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(22, 18, 22, 18)
        vbox.setSpacing(18)

        # Titre section
        hdr = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(qta.icon("fa5s.clipboard-list", color=c['primary']).pixmap(16, 16))
        ico.setStyleSheet("border: none; background: transparent;")
        lbl_t = QLabel("Informations de la consultation")
        lbl_t.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {c['primary']};"
            " background: transparent; border: none;"
        )
        hdr.addWidget(ico)
        hdr.addSpacing(8)
        hdr.addWidget(lbl_t)
        hdr.addStretch()
        vbox.addLayout(hdr)

        # ── Rangée 1 : Code | Diagnostique | Frais | Statut facture ──
        row1 = QHBoxLayout()
        row1.setSpacing(16)
        row1.setAlignment(Qt.AlignTop)

        self.edit_code = QLineEdit()
        self.edit_code.setPlaceholderText("Ex: CON001")
        self.edit_code.setEnabled(False)
        vb_code, _ = self._make_field("Code", self.edit_code, "fa5s.hashtag", "#9b59b6")
        row1.addWidget(self._field_widget(vb_code), 1, Qt.AlignTop)

        self.edit_diagnostique = QTextEdit()
        self.edit_diagnostique.setPlaceholderText("Saisir le diagnostique...")
        self.edit_diagnostique.setFixedHeight(80)
        vb_diag, self._wrap_diag = self._make_field(
            "Diagnostique", self.edit_diagnostique,
            "fa5s.clipboard", "#1abc9c", height=84, align_top=True
        )
        self._err_diagnostique = self._err_label()
        vb_diag.addWidget(self._err_diagnostique)
        row1.addWidget(self._field_widget(vb_diag), 1, Qt.AlignTop)

        self.edit_frais = QLineEdit()
        self.edit_frais.setPlaceholderText("Ex: 5000.00")
        vb_frais, self._wrap_frais = self._make_field(
            "Frais consultation", self.edit_frais, "fa5s.dollar-sign", "#27ae60"
        )
        self._err_frais = self._err_label()
        vb_frais.addWidget(self._err_frais)
        row1.addWidget(self._field_widget(vb_frais), 1, Qt.AlignTop)

        self.combo_statut = QComboBox()
        self.combo_statut.setEnabled(False)
        self.combo_statut.addItem("Sélectionner le statut")
        vb_statut, _ = self._make_field(
            "Statut facture", self.combo_statut, "fa5s.file-invoice", "#e67e22"
        )
        row1.addWidget(self._field_widget(vb_statut), 1, Qt.AlignTop)

        vbox.addLayout(row1)
        vbox.addSpacing(10)

        # ── Rangée 2 : Date | Code visite | Code session | Code personne ──
        row2 = QHBoxLayout()
        row2.setSpacing(16)

        self.edit_date = QDateTimeEdit()
        self.edit_date.setCalendarPopup(True)
        self.edit_date.setDateTime(QDateTime.currentDateTime())
        self.edit_date.setDisplayFormat("dd/MM/yyyy")
        vb_date, _ = self._make_field(
            "Date consultation", self.edit_date, "fa5s.calendar-alt", "#3498db"
        )
        row2.addWidget(self._field_widget(vb_date), 1, Qt.AlignTop)

        self.combo_visite = QComboBox()
        self.combo_visite.addItem("-- Sélectionner une visite --", "")
        for v in self._visites_attente:
            lv = (f"{v.get('code_visite', '')} — "
                  f"{v.get('nom', '')} {v.get('prenom', '')}")
            self.combo_visite.addItem(lv, v.get('code_visite', ''))
        vb_visite, self._wrap_visite = self._make_field(
            "Code visite", self.combo_visite, "fa5s.shopping-bag", "#e74c3c"
        )
        self._err_visite = self._err_label()
        vb_visite.addWidget(self._err_visite)
        row2.addWidget(self._field_widget(vb_visite), 1, Qt.AlignTop)

        self.edit_session = QLineEdit(self.code_session or "")
        self.edit_session.setPlaceholderText("Ex: SES001")
        self.edit_session.setEnabled(False)
        vb_sess, _ = self._make_field(
            "Code session", self.edit_session, "fa5s.graduation-cap", "#9b59b6"
        )
        row2.addWidget(self._field_widget(vb_sess), 1, Qt.AlignTop)

        self.combo_personnel = QComboBox()
        self.combo_personnel.addItem("Ex: PER001", "")
        for p in self._personnels:
            lp = (f"{p.get('code', '')} — "
                  f"{p.get('nom', '')} {p.get('prenom', '')}")
            self.combo_personnel.addItem(lp, p.get('code', ''))
        vb_perso, self._wrap_personnel = self._make_field(
            "Code personne", self.combo_personnel, "fa5s.user", "#1abc9c"
        )
        self._err_personnel = self._err_label()
        vb_perso.addWidget(self._err_personnel)
        row2.addWidget(self._field_widget(vb_perso), 1, Qt.AlignTop)

        vbox.addLayout(row2)
        parent_layout.addWidget(card)

    # =========================================================================
    # SECTION INFO BAS
    # =========================================================================

    def _section_info_bas(self, parent_layout):
        c = theme_manager.colors()
        card = QFrame()
        card.setFixedHeight(80)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {c['primary_light']};
                border: 1.5px solid {c['border_light']};
                border-radius: 14px;
            }}
        """)
        hbox = QHBoxLayout(card)
        hbox.setContentsMargins(20, 0, 20, 0)
        hbox.setSpacing(14)

        ico_frame = QFrame()
        ico_frame.setFixedSize(36, 36)
        ico_frame.setStyleSheet(f"background-color: {c['primary']}; border-radius: 18px;")
        ifi = QHBoxLayout(ico_frame)
        ifi.setContentsMargins(0, 0, 0, 0)
        il = QLabel()
        il.setPixmap(qta.icon("fa5s.info", color="#ffffff").pixmap(14, 14))
        il.setAlignment(Qt.AlignCenter)
        ifi.addWidget(il, alignment=Qt.AlignCenter)

        txt = QVBoxLayout()
        txt.setSpacing(2)
        t1 = QLabel("Informations")
        t1.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {c['primary']}; background: transparent;")
        t2 = QLabel("Veuillez remplir tous les champs obligatoires avant d'enregistrer la consultation.")
        t2.setStyleSheet(f"font-size: 11px; color: {c['text_secondary']}; background: transparent;")
        txt.addWidget(t1)
        txt.addWidget(t2)

        hbox.addWidget(ico_frame)
        hbox.addLayout(txt)
        hbox.addStretch()
        parent_layout.addWidget(card)

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def _label(self, texte: str) -> QLabel:
        c = theme_manager.colors()
        lbl = QLabel(texte)
        lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {c['text_secondary']}; background: transparent;")
        return lbl

    def _err_label(self) -> QLabel:
        c = theme_manager.colors()
        lbl = QLabel("")
        lbl.setStyleSheet(f"color: {c['danger']}; font-size: 10px; font-style: italic; background: transparent;")
        lbl.setVisible(False)
        return lbl

    def _field_widget(self, vbox: QVBoxLayout) -> QWidget:
        """Enveloppe un QVBoxLayout dans un QWidget transparent pour l'alignement AlignTop."""
        w = QWidget()
        w.setStyleSheet("background: transparent; border: none;")
        w.setLayout(vbox)
        return w

    # =========================================================================
    # VALIDATION TEMPS RÉEL
    # =========================================================================

    def _connecter_validations(self):
        self.edit_diagnostique.textChanged.connect(self._valider_formulaire)
        self.edit_frais.textChanged.connect(self._valider_formulaire)
        self.combo_visite.currentIndexChanged.connect(self._valider_formulaire)
        self.combo_personnel.currentIndexChanged.connect(self._valider_formulaire)

    def _valider_formulaire(self):
        tout_valide = True

        diag = self.edit_diagnostique.toPlainText().strip()
        ok, msg = self.controleur.valider_texte(diag, "diagnostique")
        self._set_field_state(self._wrap_diag, self._err_diagnostique, ok, msg, bool(diag))
        if not ok:
            tout_valide = False

        frais = self.edit_frais.text().strip()
        ok, msg = self.controleur.valider_frais(frais if frais else "-1")
        self._set_field_state(self._wrap_frais, self._err_frais, ok, msg, bool(frais))
        if not ok:
            tout_valide = False

        if not self.combo_visite.currentData():
            # N'afficher l'erreur que si le combo est accessible (pas pré-rempli/désactivé)
            show_err = self.combo_visite.isEnabled()
            self._set_field_state(
                self._wrap_visite, self._err_visite,
                False, "Veuillez sélectionner une visite", show_err
            )
            tout_valide = False
        else:
            # has_text=True → border focus (vert) pour confirmer la sélection valide
            self._set_field_state(self._wrap_visite, self._err_visite, True, "", True)

        if not self.combo_personnel.currentData():
            self._set_field_state(
                self._wrap_personnel, self._err_personnel,
                False, "Veuillez sélectionner un médecin", True
            )
            tout_valide = False
        else:
            self._set_field_state(self._wrap_personnel, self._err_personnel, True, "", True)

        self.combo_statut.clear()
        self.combo_statut.addItem("attente payement" if tout_valide else "Sélectionner le statut")

        self.btn_save.setEnabled(tout_valide)
        self._apply_save_btn_style()

    def _set_field_state(self, wrapper: QFrame, err_lbl: QLabel,
                         valide: bool, msg: str, has_text: bool):
        c = theme_manager.colors()
        if not valide and has_text:
            self._apply_wrapper_style(wrapper, c['danger'])
            err_lbl.setText(msg)
            err_lbl.setVisible(True)
        else:
            bc = c['border_focus'] if (valide and has_text) else c['border']
            self._apply_wrapper_style(wrapper, bc)
            err_lbl.setVisible(False)

    # =========================================================================
    # PRÉSÉLECTION
    # =========================================================================

    def _preselectionner_visite(self, code_visite: str):
        code_visite = (code_visite or "").strip()
        found = False
        for i in range(self.combo_visite.count()):
            item_data = (self.combo_visite.itemData(i) or "").strip()
            if item_data == code_visite:
                self.combo_visite.setCurrentIndex(i)
                found = True
                break
        if not found and code_visite:
            # Ajouter l'item manuellement si absent de la liste (patient déjà traité)
            self.combo_visite.addItem(code_visite, code_visite)
            self.combo_visite.setCurrentIndex(self.combo_visite.count() - 1)
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
        obj = self.consultation_obj
        if obj.code:
            self.edit_code.setText(obj.code)
        self._preselectionner_visite(obj.code_visite)
        self._preselectionner_personnel(obj.code_personnel)
        if hasattr(obj.date_consultation, 'year'):
            d = obj.date_consultation
            self.edit_date.setDateTime(QDateTime(d.year, d.month, d.day, 0, 0))
        self.edit_diagnostique.setPlainText(obj.diagnostique or "")
        self.edit_frais.setText(str(obj.frais_consultation or ""))
        self.combo_statut.setCurrentText(obj.statut_facture or "attente payement")

    # =========================================================================
    # ACTIONS BOUTONS
    # =========================================================================

    def _on_cancel(self):
        self.edit_diagnostique.clear()
        self.edit_frais.clear()
        self.combo_visite.setEnabled(True)
        self.combo_visite.setCurrentIndex(0)
        self.combo_personnel.setCurrentIndex(0)
        self.edit_date.setDateTime(QDateTime.currentDateTime())

    def recharger_liste_visites(self, code_session: str = None):
        """Recharge uniquement la liste du combo visite (sans réinitialiser le formulaire)."""
        if code_session:
            self.code_session = code_session
        self._charger_donnees_combos()
        current_data = self.combo_visite.currentData() or ""
        self.combo_visite.blockSignals(True)
        self.combo_visite.clear()
        self.combo_visite.addItem("-- Sélectionner une visite --", "")
        for v in self._visites_attente:
            lv = (f"{v.get('code_visite', '')} — "
                  f"{v.get('nom', '')} {v.get('prenom', '')}")
            self.combo_visite.addItem(lv, v.get('code_visite', ''))
        # Restaurer la sélection précédente si possible
        if current_data:
            for i in range(self.combo_visite.count()):
                if self.combo_visite.itemData(i) == current_data:
                    self.combo_visite.setCurrentIndex(i)
                    break
        self.combo_visite.blockSignals(False)

    def recharger_pour_patient(self, code_visite: str, code_session: str = None):
        """Recharge les combos et présélectionne la visite du patient sélectionné."""
        # Mettre à jour la session si fournie
        if code_session:
            self.code_session = code_session
            self.edit_session.setText(code_session)

        # Recharger les données fraîches avec la bonne session
        self._charger_donnees_combos()

        # Bloquer les signaux AVANT _on_cancel pour éviter que la validation
        # s'exécute sur un combo vide/placeholder (border rouge transitoire)
        self.combo_visite.blockSignals(True)
        self.combo_personnel.blockSignals(True)

        # Remettre à zéro le formulaire
        self._on_cancel()

        # Reconstruire le combo visite avec les nouvelles données
        self.combo_visite.clear()
        self.combo_visite.addItem("-- Sélectionner une visite --", "")
        for v in self._visites_attente:
            lv = (f"{v.get('code_visite', '')} — "
                  f"{v.get('nom', '')} {v.get('prenom', '')}")
            self.combo_visite.addItem(lv, v.get('code_visite', ''))

        self.combo_visite.blockSignals(False)
        self.combo_personnel.blockSignals(False)

        # Présélectionner la visite du patient
        if code_visite:
            self._preselectionner_visite(code_visite.strip())

    def _soumettre(self):
        try:
            code_visite    = self.combo_visite.currentData()
            code_personnel = self.combo_personnel.currentData()

            consultation = Consultation(
                code                  = self.consultation_obj.code if self.consultation_obj else None,
                diagnostique          = self.edit_diagnostique.toPlainText().strip(),
                frais_consultation    = float(self.edit_frais.text().strip() or 0),
                statut_facture        = self.combo_statut.currentText(),
                date_consultation     = self.edit_date.date().toPython(),
                code_visite           = code_visite,
                code_session          = self.code_session,
                code_personne         = code_personnel,
            )

            if self.consultation_obj:
                ok, msg = self.controleur.modifier_consultation(consultation)
            else:
                ok, msg = self.controleur.creer_consultation(consultation)

            if ok:
                CustomMessageBox("Succès", msg, True, self).exec()
                self._on_cancel()
                self.consultation_saved.emit()
            else:
                CustomMessageBox("Erreur", msg, False, self).exec()

        except Exception as e:
            CustomMessageBox("Erreur Système", str(e), False, self).exec()

    # =========================================================================
    # THÈME
    # =========================================================================

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"""
            QWidget {{
                background: {c['bg_main']};
                color: {c['text_primary']};
            }}
        """)
        # Re-appliquer les styles des wrappers et widgets internes après un changement de thème
        if hasattr(self, '_wrap_diag'):
            for w in (self._wrap_diag, self._wrap_frais, self._wrap_visite, self._wrap_personnel):
                self._apply_wrapper_style(w)
        if hasattr(self, 'edit_diagnostique'):
            for w in (self.edit_diagnostique, self.edit_frais, self.combo_visite,
                      self.combo_personnel, self.edit_code, self.edit_session,
                      self.edit_date, self.combo_statut):
                self._clear_widget_style(w, c)
        if hasattr(self, 'btn_cancel'):
            self.btn_cancel.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c['bg_main']};
                    color: {c['text_secondary']};
                    border: 1.5px solid {c['border']};
                    border-radius: 10px;
                    font-size: 13px;
                }}
                QPushButton:hover {{ background-color: {c['hover']}; }}
            """)
        if hasattr(self, 'btn_save'):
            self._apply_save_btn_style()
