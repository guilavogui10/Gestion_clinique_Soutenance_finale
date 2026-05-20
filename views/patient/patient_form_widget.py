"""
Widget formulaire patient (version non-modale pour onglet)
Design identique à PatientFormDialog mais intégré directement dans l'onglet.
"""
import os
import qtawesome as qta
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFrame, QDateEdit
)
from models.model_patient import Patient
from views.shared.message_box import CustomMessageBox
from views.shared.theme_manager import theme_manager


class PatientFormWidget(QWidget):
    """
    Widget formulaire patient intégré dans l'onglet 'Nouveau'.
    Même design que PatientFormDialog mais sans fenêtre modale.
    """

    patient_saved = Signal()

    def __init__(self, controleur, patient_obj=None, parent=None):
        super().__init__(parent)
        self.controleur = controleur
        self.patient_obj = patient_obj
        self.info_cabinet = self.controleur.get_cabinet_info()

        self._init_ui()
        self._connecter_validations()

        if self.patient_obj:
            self._remplir_champs()

        theme_manager.theme_changed.connect(self.apply_theme)

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 6, 24, 16)
        outer.setSpacing(10)  # Réduit de 14 à 10

        self._setup_header(outer)
        self._section_infos(outer)
        outer.addStretch()

        self.apply_theme()

    # =========================================================================
    # HEADER (titre + boutons Annuler / Enregistrer)
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

        # Icône utilisateur
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
        ico_lbl.setPixmap(qta.icon("fa5s.user-injured", color=c['primary']).pixmap(22, 22))
        ico_lbl.setAlignment(Qt.AlignCenter)
        ib_layout.addWidget(ico_lbl, alignment=Qt.AlignCenter)

        # Titre + sous-titre
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        lbl_main = QLabel("Enregistrement d'un patient")
        lbl_main.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {c['text_primary']}; background: transparent; border: none;")
        lbl_sub = QLabel("Saisissez les informations du patient")
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
        label_save = " Enregistrer" if not self.patient_obj else " Mettre à jour"
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
                    height: int = 42):
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
        wrapper.setFixedHeight(height)
        self._apply_wrapper_style(wrapper)

        hbox = QHBoxLayout(wrapper)
        hbox.setContentsMargins(8, 5, 8, 5)
        hbox.setSpacing(8)

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
        hbox.addWidget(badge, 0, Qt.AlignVCenter)
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
        elif isinstance(widget, QDateEdit):
            widget.setStyleSheet(f"QDateEdit {{ {base} padding: 0; }}")
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
        vbox.setSpacing(12)  # Réduit de 18 à 12

        # Titre section
        hdr = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(qta.icon("fa5s.clipboard-list", color=c['primary']).pixmap(16, 16))
        ico.setStyleSheet("border: none; background: transparent;")
        lbl_t = QLabel("Informations du patient")
        lbl_t.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {c['primary']};"
            " background: transparent; border: none;"
        )
        hdr.addWidget(ico)
        hdr.addSpacing(8)
        hdr.addWidget(lbl_t)
        hdr.addStretch()
        vbox.addLayout(hdr)

        # ── Rangée 1 : Nom | Prénom ──
        row1 = QHBoxLayout()
        row1.setSpacing(16)
        row1.setAlignment(Qt.AlignTop)

        self.edit_nom = QLineEdit()
        self.edit_nom.setPlaceholderText("Ex: DIALLO")
        vb_nom, self._wrap_nom = self._make_field(
            "Nom", self.edit_nom, "fa5s.user", "#9b59b6"
        )
        self._err_nom = self._err_label()
        vb_nom.addWidget(self._err_nom)
        row1.addWidget(self._field_widget(vb_nom), 1, Qt.AlignTop)

        self.edit_prenom = QLineEdit()
        self.edit_prenom.setPlaceholderText("Ex: Mamadou")
        vb_prenom, self._wrap_prenom = self._make_field(
            "Prénom", self.edit_prenom, "fa5s.user", "#1abc9c"
        )
        self._err_prenom = self._err_label()
        vb_prenom.addWidget(self._err_prenom)
        row1.addWidget(self._field_widget(vb_prenom), 1, Qt.AlignTop)

        vbox.addLayout(row1)
        vbox.addSpacing(6)  # Réduit de 10 à 6

        # ── Rangée 2 : Téléphone | Genre ──
        row2 = QHBoxLayout()
        row2.setSpacing(16)

        self.edit_tel = QLineEdit()
        self.edit_tel.setPlaceholderText("Ex: 628123456")
        vb_tel, self._wrap_tel = self._make_field(
            "Téléphone", self.edit_tel, "fa5s.phone", "#27ae60"
        )
        self._err_tel = self._err_label()
        vb_tel.addWidget(self._err_tel)
        row2.addWidget(self._field_widget(vb_tel), 1, Qt.AlignTop)

        self.combo_sexe = QComboBox()
        self.combo_sexe.addItem("Homme")
        self.combo_sexe.addItem("Femme")
        vb_sexe, _ = self._make_field(
            "Genre", self.combo_sexe, "fa5s.venus-mars", "#e67e22"
        )
        row2.addWidget(self._field_widget(vb_sexe), 1, Qt.AlignTop)

        vbox.addLayout(row2)
        vbox.addSpacing(6)  # Réduit de 10 à 6

        # ── Rangée 3 : Date de naissance ──
        self.edit_date = QDateEdit()
        self.edit_date.setCalendarPopup(True)
        self.edit_date.setDisplayFormat("dd/MM/yyyy")
        self.edit_date.setDate(QDate.currentDate())
        vb_date, _ = self._make_field(
            "Date de naissance", self.edit_date, "fa5s.calendar-alt", "#3498db"
        )
        vbox.addLayout(vb_date)
        vbox.addSpacing(6)  # Réduit de 10 à 6

        # ── Rangée 4 : Profession | Adresse ──
        row4 = QHBoxLayout()
        row4.setSpacing(16)

        self.edit_profession = QLineEdit()
        self.edit_profession.setPlaceholderText("Ex: Enseignant")
        vb_prof, self._wrap_profession = self._make_field(
            "Profession", self.edit_profession, "fa5s.briefcase", "#f39c12"
        )
        self._err_profession = self._err_label()
        vb_prof.addWidget(self._err_profession)
        row4.addWidget(self._field_widget(vb_prof), 1, Qt.AlignTop)

        self.edit_adresse = QLineEdit()
        self.edit_adresse.setPlaceholderText("Ex: Conakry, Kaloum")
        vb_adr, self._wrap_adresse = self._make_field(
            "Adresse", self.edit_adresse, "fa5s.map-marker-alt", "#e74c3c"
        )
        self._err_adresse = self._err_label()
        vb_adr.addWidget(self._err_adresse)
        row4.addWidget(self._field_widget(vb_adr), 1, Qt.AlignTop)

        vbox.addLayout(row4)
        parent_layout.addWidget(card)

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

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
        self.edit_nom.textChanged.connect(self._valider_formulaire)
        self.edit_prenom.textChanged.connect(self._valider_formulaire)
        self.edit_tel.textChanged.connect(self._valider_formulaire)
        self.edit_profession.textChanged.connect(self._valider_formulaire)
        self.edit_adresse.textChanged.connect(self._valider_formulaire)

    def _valider_formulaire(self):
        tout_valide = True

        nom = self.edit_nom.text().strip()
        ok, msg = self.controleur._valider_nom(nom)
        self._set_field_state(self._wrap_nom, self._err_nom, ok, msg, bool(nom))
        if not ok:
            tout_valide = False

        prenom = self.edit_prenom.text().strip()
        ok, msg = self.controleur._valider_prenom(prenom)
        self._set_field_state(self._wrap_prenom, self._err_prenom, ok, msg, bool(prenom))
        if not ok:
            tout_valide = False

        tel = self.edit_tel.text().strip()
        ok, msg = self.controleur._valider_telephone(tel)
        if ok and not self.patient_obj:
            ok, msg = self.controleur._control_exist(tel)
        self._set_field_state(self._wrap_tel, self._err_tel, ok, msg, bool(tel))
        if not ok:
            tout_valide = False

        prof = self.edit_profession.text().strip()
        ok, msg = self.controleur._valider_profession(prof)
        self._set_field_state(self._wrap_profession, self._err_profession, ok, msg, bool(prof))
        if not ok:
            tout_valide = False

        adr = self.edit_adresse.text().strip()
        ok, msg = self.controleur._valider_adresse(adr)
        self._set_field_state(self._wrap_adresse, self._err_adresse, ok, msg, bool(adr))
        if not ok:
            tout_valide = False

        self.btn_save.setEnabled(tout_valide)
        self._apply_save_btn_style()

    def _set_field_state(self, wrapper: QFrame, err_lbl: QLabel,
                         valide: bool, msg: str, has_text: bool):
        c = theme_manager.colors()
        if not valide and has_text:
            self._apply_wrapper_style(wrapper, c['danger'])
            err_lbl.setText(msg)
            err_lbl.setVisible(True)
        elif not valide and not has_text:
            self._apply_wrapper_style(wrapper, c['border'])
            err_lbl.setVisible(False)
        else:
            bc = c['border_focus'] if (valide and has_text) else c['border']
            self._apply_wrapper_style(wrapper, bc)
            err_lbl.setVisible(False)

    # =========================================================================
    # MÉTHODES PUBLIQUES
    # =========================================================================

    def recharger_pour_patient(self, patient_obj):
        """Recharge le formulaire avec les données d'un patient pour modification"""
        self.patient_obj = patient_obj
        self._remplir_champs()
        # Changer le texte du bouton
        self.btn_save.setText(" Mettre à jour")
        self.btn_save.setIcon(qta.icon("fa5s.save", color="#ffffff"))

    # =========================================================================
    # REMPLISSAGE MODE MODIFICATION
    # =========================================================================

    def _remplir_champs(self):
        obj = self.patient_obj
        self.edit_nom.setText(obj.get_nom())
        self.edit_prenom.setText(obj.get_prenom())
        self.edit_tel.setText(obj.get_telephone())
        self.edit_profession.setText(obj.get_profession())
        self.edit_adresse.setText(obj.get_adresse())

        index = self.combo_sexe.findText(obj.get_genre())
        if index >= 0:
            self.combo_sexe.setCurrentIndex(index)

        if obj.get_naissance():
            from datetime import datetime
            if isinstance(obj.get_naissance(), str):
                date_obj = datetime.strptime(obj.get_naissance(), "%Y-%m-%d").date()
            else:
                date_obj = obj.get_naissance()
            qdate = QDate(date_obj.year, date_obj.month, date_obj.day)
            self.edit_date.setDate(qdate)

    # =========================================================================
    # ACTIONS BOUTONS
    # =========================================================================

    def _on_cancel(self):
        self.edit_nom.clear()
        self.edit_prenom.clear()
        self.edit_tel.clear()
        self.edit_profession.clear()
        self.edit_adresse.clear()
        self.combo_sexe.setCurrentIndex(0)
        self.edit_date.setDate(QDate.currentDate())

    def _soumettre(self):
        try:
            nouveau_patient = Patient(
                code_patient=self.patient_obj.get_code_patient() if self.patient_obj else "",
                nom=self.edit_nom.text().strip(),
                prenom=self.edit_prenom.text().strip(),
                telephone=self.edit_tel.text().strip(),
                naissance=self.edit_date.date().toPython(),
                genre=self.combo_sexe.currentText(),
                profession=self.edit_profession.text().strip(),
                adresse=self.edit_adresse.text().strip()
            )

            if self.patient_obj:
                ok, msg = self.controleur.update_patient(nouveau_patient)
            else:
                ok, msg = self.controleur.save_patient(nouveau_patient)

            if ok:
                CustomMessageBox("Succès", msg, True, self).exec()
                self._on_cancel()
                self.patient_saved.emit()
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
        if hasattr(self, '_wrap_nom'):
            for w in (self._wrap_nom, self._wrap_prenom, self._wrap_tel, 
                      self._wrap_profession, self._wrap_adresse):
                self._apply_wrapper_style(w)
        if hasattr(self, 'edit_nom'):
            for w in (self.edit_nom, self.edit_prenom, self.edit_tel,
                      self.edit_profession, self.edit_adresse, self.combo_sexe, self.edit_date):
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
