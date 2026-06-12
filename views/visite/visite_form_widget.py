"""
Widget formulaire visite intégré - Design identique à consultation
"""
import qtawesome as qta
from PySide6.QtCore import Qt, QDateTime, QDate, QTime, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFrame, QDateEdit, QTimeEdit
)
from models.model_visite import Visite 
from controllers.controleur_patient import ControleurPatient
from views.shared.message_box import CustomMessageBox
from views.shared.theme_manager import theme_manager


class VisiteFormWidget(QWidget):
    """Formulaire visite intégré (non-modal)"""

    visite_saved = Signal()
    rdv_visite_created = Signal(str, str)  # (code_visite, code_session)
    
    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.controleur = controleur
        self.visite_obj = None
        self._soumission_en_cours = False
        
        self._init_ui()
        self._connecter_validations()
        
        theme_manager.theme_changed.connect(self.apply_theme)
        
        self.combo_type.currentTextChanged.connect(self.gerer_etat_temps)
        self.gerer_etat_temps(self.combo_type.currentText())
    
    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 4, 24, 6)
        outer.setSpacing(6)

        self._setup_header(outer)
        self._section_infos(outer)
        self._section_info_bas(outer)
        outer.addStretch()

        self.apply_theme()
    
    def _setup_header(self, parent_layout):
        c = theme_manager.colors()
        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(58)

        layout = QHBoxLayout(self.header_frame)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(10)

        self._icon_box = QFrame()
        self._icon_box.setFixedSize(38, 38)
        ib_layout = QHBoxLayout(self._icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        self._ico_header = QLabel()
        self._ico_header.setAlignment(Qt.AlignCenter)
        ib_layout.addWidget(self._ico_header, alignment=Qt.AlignCenter)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self._lbl_main = QLabel("Enregistrement d'une visite")
        self._lbl_sub  = QLabel("Saisissez les informations de la visite médicale")
        title_col.addWidget(self._lbl_main)
        title_col.addWidget(self._lbl_sub)

        layout.addWidget(self._icon_box)
        layout.addLayout(title_col)
        layout.addStretch()

        self.btn_cancel = QPushButton(qta.icon("fa5s.times", color=c['text_secondary']), " Annuler")
        self.btn_cancel.setFixedSize(110, 40)
        self.btn_cancel.clicked.connect(self.reset_form)

        self.btn_save = QPushButton(qta.icon("fa5s.save", color=c['text_inverse']), " Enregistrer")
        self.btn_save.setFixedSize(140, 40)
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.soumettre)

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
    
    def _make_field(self, label_text: str, widget, icon_name: str, color_key: str, height: int = 36):
        c = theme_manager.colors()
        vbox = QVBoxLayout()
        vbox.setSpacing(4)

        lbl = QLabel(label_text)
        vbox.addWidget(lbl)

        wrapper = QFrame()
        wrapper.setObjectName("inputWrapper")
        wrapper.setFixedHeight(height)
        self._apply_wrapper_style(wrapper)

        hbox = QHBoxLayout(wrapper)
        hbox.setContentsMargins(8, 2, 8, 2)
        hbox.setSpacing(6)

        badge = QFrame()
        badge.setFixedSize(24, 24)
        bl = QHBoxLayout(badge)
        bl.setContentsMargins(0, 0, 0, 0)
        ico_lbl = QLabel()
        ico_lbl.setAlignment(Qt.AlignCenter)
        ico_lbl.setStyleSheet("border: none; background: transparent;")
        bl.addWidget(ico_lbl, alignment=Qt.AlignCenter)

        self._clear_widget_style(widget, c)
        hbox.addWidget(badge, 0, Qt.AlignVCenter)

        hbox.addWidget(widget, 1)
        vbox.addWidget(wrapper)

        if not hasattr(self, '_field_registry'):
            self._field_registry = []
        self._field_registry.append({
            'wrapper':   wrapper,
            'badge':     badge,
            'ico_lbl':   ico_lbl,
            'lbl':       lbl,
            'icon_name': icon_name,
            'color_key': color_key,
        })
        self._refresh_field(self._field_registry[-1], c)

        return vbox, wrapper

    def _refresh_field(self, entry: dict, c: dict):
        icon_color = c[entry['color_key']]
        entry['badge'].setStyleSheet(
            f"background-color: {icon_color}20; border-radius: 6px; border: none;"
        )
        entry['ico_lbl'].setPixmap(
            qta.icon(entry['icon_name'], color=icon_color).pixmap(12, 12)
        )
        entry['lbl'].setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {c['text_secondary']};"
            " background: transparent; border: none;"
        )
        self._apply_wrapper_style(entry['wrapper'])
    
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
        if isinstance(widget, QComboBox):
            widget.setStyleSheet(f"""
                QComboBox {{
                    border: none;
                    background-color: {c['bg_input']};
                    color: {c['text_primary']};
                    font-size: 12px;
                    padding: 0;
                    min-height: 28px;
                }}
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
        elif isinstance(widget, (QDateEdit, QTimeEdit)):
            widget.setStyleSheet(f"""
                QDateEdit, QTimeEdit {{
                    border: none;
                    background: transparent;
                    color: {c['text_primary']};
                    font-size: 12px;
                    padding: 0;
                    selection-background-color: {c['primary']};
                    selection-color: {c['text_inverse']};
                }}
                QDateEdit::drop-down, QTimeEdit::drop-down {{
                    border: none;
                    width: 20px;
                    background: transparent;
                }}
            """)
            if isinstance(widget, QDateEdit) and widget.calendarPopup():
                self._style_calendar(widget.calendarWidget(), c)
        else:
            widget.setStyleSheet(f"""
                QLineEdit {{
                    border: none;
                    background: transparent;
                    font-size: 12px;
                    color: {c['text_primary']};
                    padding: 0;
                }}
            """)
    
    def _style_calendar(self, cal, c):
        if not cal:
            return
        cal.setStyleSheet(f"""
            QCalendarWidget QWidget {{
                background-color: {c['bg_card']};
                color: {c['text_primary']};
            }}
            QCalendarWidget QAbstractItemView {{
                background-color: {c['bg_card']};
                color: {c['text_primary']};
                selection-background-color: {c['primary']};
                selection-color: {c['text_inverse']};
                border: none;
                outline: none;
            }}
            QCalendarWidget QAbstractItemView::item:hover {{
                background-color: {c['hover']};
                border-radius: 4px;
            }}
            QCalendarWidget QWidget#qt_calendar_navigationbar {{
                background-color: {c['primary']};
                padding: 4px 8px;
            }}
            QCalendarWidget QToolButton {{
                color: {c['text_inverse']};
                background-color: transparent;
                border: none;
                font-size: 13px;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 4px;
            }}
            QCalendarWidget QToolButton:hover {{
                background-color: {c['primary_hover']};
            }}
            QCalendarWidget QSpinBox {{
                color: {c['text_inverse']};
                background-color: transparent;
                border: none;
                font-size: 13px;
                font-weight: bold;
            }}
            QCalendarWidget QSpinBox::up-button,
            QCalendarWidget QSpinBox::down-button {{ width: 0; height: 0; }}
            QCalendarWidget QMenu {{
                background-color: {c['bg_card']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 6px;
            }}
            QCalendarWidget QMenu::item:selected {{
                background-color: {c['primary']};
                color: {c['text_inverse']};
            }}
        """)

    def _section_infos(self, parent_layout):
        self._card_infos = QFrame()
        vbox = QVBoxLayout(self._card_infos)
        vbox.setContentsMargins(18, 8, 18, 8)
        vbox.setSpacing(8)

        # Titre section
        hdr = QHBoxLayout()
        self._ico_section = QLabel()
        self._ico_section.setStyleSheet("border: none; background: transparent;")
        self._lbl_section = QLabel("Informations de la visite")
        hdr.addWidget(self._ico_section)
        hdr.addSpacing(8)
        hdr.addWidget(self._lbl_section)
        hdr.addStretch()
        vbox.addLayout(hdr)

        # Rangée 1 : Code Patient | Nom Patient
        row1 = QHBoxLayout()
        row1.setSpacing(16)

        self.combo_code_p = QComboBox()
        self.combo_code_p.addItem("-- Sélectionner un patient --", "")
        patient_ctrl = ControleurPatient()
        for p in patient_ctrl.reed_Allpatient():
            self.combo_code_p.addItem(
                f"{p.get_code_patient()} - {p.get_nom()} {p.get_prenom()}",
                p.get_code_patient()
            )
        vb_code, self._wrap_code = self._make_field("Code Patient", self.combo_code_p, "fa5s.id-card", 'accent')
        self._err_code = self._err_label()
        vb_code.addWidget(self._err_code)
        row1.addWidget(self._field_widget(vb_code), 1, Qt.AlignTop)

        self.edit_nom_p = QLineEdit()
        self.edit_nom_p.setPlaceholderText("Nom complet du patient")
        self.edit_nom_p.setReadOnly(True)
        vb_nom, _ = self._make_field("Nom Complet", self.edit_nom_p, "fa5s.user-tag", 'primary')
        row1.addWidget(self._field_widget(vb_nom), 1, Qt.AlignTop)
        vbox.addLayout(row1)

        # Rangée 2 : Type | Urgence
        row2 = QHBoxLayout()
        row2.setSpacing(16)
        self.combo_type = QComboBox()
        vb_type, _ = self._make_field("Type de Visite", self.combo_type, "fa5s.calendar-check", 'info')
        row2.addWidget(self._field_widget(vb_type), 1, Qt.AlignTop)

        self.combo_urgent = QComboBox()
        vb_urg, _ = self._make_field("Niveau d'urgence", self.combo_urgent, "fa5s.exclamation-triangle", 'danger')
        row2.addWidget(self._field_widget(vb_urg), 1, Qt.AlignTop)
        vbox.addLayout(row2)

        # Rangée 3 : Date | Heure
        row3 = QHBoxLayout()
        row3.setSpacing(16)
        self.edit_date = QDateEdit()
        self.edit_date.setCalendarPopup(True)
        self.edit_date.setDate(QDate.currentDate())
        self.edit_date.setDisplayFormat("dd/MM/yyyy")
        vb_date, _ = self._make_field("Date de la visite", self.edit_date, "fa5s.calendar-alt", 'success')
        row3.addWidget(self._field_widget(vb_date), 1, Qt.AlignTop)

        self.edit_time = QTimeEdit()
        self.edit_time.setTime(QTime.currentTime())
        self.edit_time.setDisplayFormat("HH:mm")
        vb_time, _ = self._make_field("Temps / Heure", self.edit_time, "fa5s.clock", 'warning')
        row3.addWidget(self._field_widget(vb_time), 1, Qt.AlignTop)
        vbox.addLayout(row3)

        parent_layout.addWidget(self._card_infos)
    
    def _section_info_bas(self, parent_layout):
        self._card_bas = QFrame()
        self._card_bas.setFixedHeight(48)
        hbox = QHBoxLayout(self._card_bas)
        hbox.setContentsMargins(16, 0, 16, 0)
        hbox.setSpacing(12)

        self._ico_bas_frame = QFrame()
        self._ico_bas_frame.setFixedSize(30, 30)
        ifi = QHBoxLayout(self._ico_bas_frame)
        ifi.setContentsMargins(0, 0, 0, 0)
        self._ico_bas_lbl = QLabel()
        self._ico_bas_lbl.setAlignment(Qt.AlignCenter)
        ifi.addWidget(self._ico_bas_lbl, alignment=Qt.AlignCenter)

        txt = QVBoxLayout()
        txt.setSpacing(2)
        self._lbl_bas_title = QLabel("Informations")
        self._lbl_bas_desc  = QLabel(
            "Veuillez remplir tous les champs obligatoires avant d'enregistrer la visite."
        )
        txt.addWidget(self._lbl_bas_title)
        txt.addWidget(self._lbl_bas_desc)

        hbox.addWidget(self._ico_bas_frame)
        hbox.addLayout(txt)
        hbox.addStretch()
        parent_layout.addWidget(self._card_bas)
    
    def _err_label(self):
        c = theme_manager.colors()
        lbl = QLabel("")
        lbl.setStyleSheet(f"color: {c['danger']}; font-size: 10px; font-style: italic; background: transparent;")
        lbl.setVisible(False)
        return lbl
    
    def _field_widget(self, vbox: QVBoxLayout):
        w = QWidget()
        w.setStyleSheet("background: transparent; border: none;")
        w.setLayout(vbox)
        return w
    
    def _connecter_validations(self):
        self.combo_code_p.currentIndexChanged.connect(self.rechercher_patient_auto)
    
    def gerer_etat_temps(self, texte):
        est_manuel = texte in ["VIP", "Rendez vous"]
        self.edit_date.setEnabled(True)
        self.edit_time.setEnabled(est_manuel)
        
        if not est_manuel:
            self.edit_date.setDate(QDate.currentDate())
            self.edit_time.setTime(QTime.currentTime())
    
    def rechercher_patient_auto(self):
        code = self.combo_code_p.currentData()
        if not code:
            self.edit_nom_p.clear()
            self._set_field_state(self._wrap_code, self._err_code, True, "", False)
        else:
            patient = self.controleur.read_by_code_patient(code)
            if patient:
                self.edit_nom_p.setText(f"{patient.get_nom()} {patient.get_prenom()}")
                self._set_field_state(self._wrap_code, self._err_code, True, "", True)
            else:
                self.edit_nom_p.setText("Patient introuvable")
                self._set_field_state(self._wrap_code, self._err_code, False, "Code inexistant", True)
        self.verifier_formulaire_complet()
    
    def _set_field_state(self, wrapper: QFrame, err_lbl: QLabel, valide: bool, msg: str, has_text: bool):
        c = theme_manager.colors()
        if not valide and has_text:
            self._apply_wrapper_style(wrapper, c['danger'])
            err_lbl.setText(msg)
            err_lbl.setVisible(True)
        else:
            bc = c['border_focus'] if (valide and has_text) else c['border']
            self._apply_wrapper_style(wrapper, bc)
            err_lbl.setVisible(False)
    
    def verifier_formulaire_complet(self):
        patient_existe = self.edit_nom_p.text() != "" and self.edit_nom_p.text() != "Patient introuvable"
        self.btn_save.setEnabled(patient_existe)
        self._apply_save_btn_style()
    
    def reset_form(self):
        self.combo_code_p.setCurrentIndex(0)
        self.edit_nom_p.clear()
        self.combo_type.setCurrentIndex(0)
        self.combo_urgent.setCurrentIndex(0)
        self.edit_date.setDate(QDate.currentDate())
        self.edit_time.setTime(QTime.currentTime())
        self.btn_save.setEnabled(False)
        self._set_field_state(self._wrap_code, self._err_code, True, "", False)
    
    def soumettre(self):
        if self._soumission_en_cours:
            return
        
        try:
            self._soumission_en_cours = True
            self.btn_save.setEnabled(False)
            
            c_patient = self.combo_code_p.currentData()
            v_type = self.combo_type.currentText()
            v_urgent = self.combo_urgent.currentText()
            
            py_date = self.edit_date.date().toPython()
            py_time = self.edit_time.time().toPython()
            v_date_heure = QDateTime(py_date, py_time).toPython()
            
            nouvelle_visite = Visite("", c_patient, "", v_type, v_urgent, v_date_heure, None, None)
            
            ok, msg = self.controleur.save_visite(nouvelle_visite)
            
            if ok:
                CustomMessageBox("Succès", msg, True, self).exec()

                if v_type in ["VIP", "Rendez vous"]:
                    code_session = nouvelle_visite.get_code_session()
                    code_visite  = nouvelle_visite.get_code_visite()
                    if code_session and code_visite:
                        self.rdv_visite_created.emit(code_visite, code_session)

                self.reset_form()
                self.visite_saved.emit()
                self._soumission_en_cours = False
            else:
                CustomMessageBox("Erreur", msg, False, self).exec()
                self._soumission_en_cours = False
                self.verifier_formulaire_complet()
        except Exception as e:
            CustomMessageBox("Erreur Système", str(e), False, self).exec()
            self._soumission_en_cours = False
            self.verifier_formulaire_complet()
    
    def apply_theme(self):
        c = theme_manager.colors()

        # Fond global cascade
        self.setStyleSheet(f"QWidget {{ background: {c['bg_main']}; color: {c['text_primary']}; }}")

        # ── Header frame ────────────────────────────────────────────────────
        if hasattr(self, 'header_frame'):
            self.header_frame.setStyleSheet(f"""
                background-color: {c['bg_card']};
                border-radius: 14px; border: none;
            """)
        if hasattr(self, '_icon_box'):
            self._icon_box.setStyleSheet(f"""
                background-color: {c['bg_main']};
                border-radius: 10px;
                border: 1px solid {c['border_light']};
            """)
        if hasattr(self, '_ico_header'):
            self._ico_header.setPixmap(
                qta.icon("fa5s.user-md", color=c['primary']).pixmap(22, 22)
            )
        if hasattr(self, '_lbl_main'):
            self._lbl_main.setStyleSheet(
                f"font-size: 17px; font-weight: bold; color: {c['text_primary']};"
                " background: transparent; border: none;"
            )
        if hasattr(self, '_lbl_sub'):
            self._lbl_sub.setStyleSheet(
                f"font-size: 12px; color: {c['text_muted']}; background: transparent; border: none;"
            )

        # ── Card infos ────────────────────────────────────────────────────
        if hasattr(self, '_card_infos'):
            self._card_infos.setStyleSheet(f"""
                QFrame {{
                    background-color: {c['bg_card']};
                    border: 1.5px solid {c['border_light']};
                    border-radius: 14px;
                }}
            """)
        if hasattr(self, '_ico_section'):
            self._ico_section.setPixmap(
                qta.icon("fa5s.clipboard-list", color=c['primary']).pixmap(16, 16)
            )
        if hasattr(self, '_lbl_section'):
            self._lbl_section.setStyleSheet(
                f"font-size: 14px; font-weight: bold; color: {c['primary']};"
                " background: transparent; border: none;"
            )

        # ── Card bas ──────────────────────────────────────────────────────
        if hasattr(self, '_card_bas'):
            self._card_bas.setStyleSheet(f"""
                QFrame {{
                    background-color: {c['primary_light']};
                    border: 1.5px solid {c['border_light']};
                    border-radius: 14px;
                }}
            """)
        if hasattr(self, '_ico_bas_frame'):
            self._ico_bas_frame.setStyleSheet(
                f"background-color: {c['primary']}; border-radius: 18px;"
            )
        if hasattr(self, '_ico_bas_lbl'):
            self._ico_bas_lbl.setPixmap(
                qta.icon("fa5s.info", color=c['text_inverse']).pixmap(14, 14)
            )
        if hasattr(self, '_lbl_bas_title'):
            self._lbl_bas_title.setStyleSheet(
                f"font-size: 13px; font-weight: bold; color: {c['primary']}; background: transparent;"
            )
        if hasattr(self, '_lbl_bas_desc'):
            self._lbl_bas_desc.setStyleSheet(
                f"font-size: 11px; color: {c['text_secondary']}; background: transparent;"
            )

        # ── Champs (registre) ─────────────────────────────────────────────
        if hasattr(self, '_field_registry'):
            for entry in self._field_registry:
                self._refresh_field(entry, c)
        if hasattr(self, 'combo_code_p'):
            for w in (self.combo_code_p, self.edit_nom_p, self.combo_type,
                      self.combo_urgent, self.edit_date, self.edit_time):
                self._clear_widget_style(w, c)

        # ── Boutons ──────────────────────────────────────────────────────
        if hasattr(self, 'btn_cancel'):
            self.btn_cancel.setIcon(qta.icon("fa5s.times", color=c['text_secondary']))
            self.btn_cancel.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c['bg_main']};
                    color: {c['text_secondary']};
                    border: 1.5px solid {c['border']};
                    border-radius: 10px;
                    font-size: 13px; font-weight: 500;
                }}
                QPushButton:hover {{ background-color: {c['hover']}; }}
            """)
        if hasattr(self, 'btn_save'):
            self._apply_save_btn_style()

        # ── Remplir les combos si vides ───────────────────────────────────
        if hasattr(self, 'combo_type') and self.combo_type.count() == 0:
            self.combo_type.addItem(qta.icon("fa5s.bolt",          color=c['warning']), "Immediat")
            self.combo_type.addItem(qta.icon("fa5s.calendar-check",color=c['primary']), "Rendez vous")
            self.combo_type.addItem(qta.icon("fa5s.crown",         color=c['accent']),  "VIP")
            self.combo_type.addItem(qta.icon("fa5s.redo",          color=c['info']),    "Controle")
        if hasattr(self, 'combo_urgent') and self.combo_urgent.count() == 0:
            self.combo_urgent.addItem(qta.icon("fa5s.check-circle",        color=c['info']),   "Non")
            self.combo_urgent.addItem(qta.icon("fa5s.exclamation-triangle",color=c['danger']), "Oui")
