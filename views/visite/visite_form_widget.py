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
from views.shared.message_box import CustomMessageBox
from views.shared.theme_manager import theme_manager


class VisiteFormWidget(QWidget):
    """Formulaire visite intégré (non-modal)"""
    
    visite_saved = Signal()
    
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
        outer.setContentsMargins(24, 6, 24, 16)
        outer.setSpacing(14)
        
        self._setup_header(outer)
        self._section_infos(outer)
        self._section_info_bas(outer)
        outer.addStretch()
        
        self.apply_theme()
    
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
        
        # Icône
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
        ico_lbl.setPixmap(qta.icon("fa5s.user-md", color=c['primary']).pixmap(22, 22))
        ico_lbl.setAlignment(Qt.AlignCenter)
        ib_layout.addWidget(ico_lbl, alignment=Qt.AlignCenter)
        
        # Titre + sous-titre
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        lbl_main = QLabel("Enregistrement d'une visite")
        lbl_main.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {c['text_primary']}; background: transparent; border: none;")
        lbl_sub = QLabel("Saisissez les informations de la visite médicale")
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
        self.btn_cancel.clicked.connect(self.reset_form)
        
        # Bouton Enregistrer
        self.btn_save = QPushButton(qta.icon("fa5s.save", color="#ffffff"), " Enregistrer")
        self.btn_save.setFixedSize(140, 40)
        self.btn_save.setEnabled(False)
        self._apply_save_btn_style()
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
    
    def _make_field(self, label_text: str, widget, icon_name: str, icon_color: str, height: int = 42):
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
        elif isinstance(widget, (QDateEdit, QTimeEdit)):
            widget.setStyleSheet(f"QDateEdit, QTimeEdit {{ {base} padding: 0; }}")
        else:
            widget.setStyleSheet(f"QLineEdit {{ {base} padding: 0; }}")
    
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
        lbl_t = QLabel("Informations de la visite")
        lbl_t.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {c['primary']};"
            " background: transparent; border: none;"
        )
        hdr.addWidget(ico)
        hdr.addSpacing(8)
        hdr.addWidget(lbl_t)
        hdr.addStretch()
        vbox.addLayout(hdr)
        
        # Rangée 1: Code Patient | Nom Patient
        row1 = QHBoxLayout()
        row1.setSpacing(16)
        
        self.edit_code_p = QLineEdit()
        self.edit_code_p.setPlaceholderText("Ex: PAT001")
        vb_code, self._wrap_code = self._make_field("Code Patient", self.edit_code_p, "fa5s.id-card", "#9b59b6")
        self._err_code = self._err_label()
        vb_code.addWidget(self._err_code)
        row1.addWidget(self._field_widget(vb_code), 1, Qt.AlignTop)
        
        self.edit_nom_p = QLineEdit()
        self.edit_nom_p.setPlaceholderText("Nom complet du patient")
        self.edit_nom_p.setReadOnly(True)
        vb_nom, _ = self._make_field("Nom Complet", self.edit_nom_p, "fa5s.user-tag", "#1abc9c")
        row1.addWidget(self._field_widget(vb_nom), 1, Qt.AlignTop)
        
        vbox.addLayout(row1)
        
        # Rangée 2: Type | Urgence
        row2 = QHBoxLayout()
        row2.setSpacing(16)
        
        self.combo_type = QComboBox()
        vb_type, _ = self._make_field("Type de Visite", self.combo_type, "fa5s.calendar-check", "#3498db")
        row2.addWidget(self._field_widget(vb_type), 1, Qt.AlignTop)
        
        self.combo_urgent = QComboBox()
        vb_urg, _ = self._make_field("Niveau d'urgence", self.combo_urgent, "fa5s.exclamation-triangle", "#e74c3c")
        row2.addWidget(self._field_widget(vb_urg), 1, Qt.AlignTop)
        
        vbox.addLayout(row2)
        
        # Rangée 3: Date | Heure
        row3 = QHBoxLayout()
        row3.setSpacing(16)
        
        self.edit_date = QDateEdit()
        self.edit_date.setCalendarPopup(True)
        self.edit_date.setDate(QDate.currentDate())
        self.edit_date.setDisplayFormat("dd/MM/yyyy")
        vb_date, _ = self._make_field("Date de la visite", self.edit_date, "fa5s.calendar-alt", "#27ae60")
        row3.addWidget(self._field_widget(vb_date), 1, Qt.AlignTop)
        
        self.edit_time = QTimeEdit()
        self.edit_time.setTime(QTime.currentTime())
        self.edit_time.setDisplayFormat("HH:mm")
        vb_time, _ = self._make_field("Temps / Heure", self.edit_time, "fa5s.clock", "#e67e22")
        row3.addWidget(self._field_widget(vb_time), 1, Qt.AlignTop)
        
        vbox.addLayout(row3)
        parent_layout.addWidget(card)
    
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
        t2 = QLabel("Veuillez remplir tous les champs obligatoires avant d'enregistrer la visite.")
        t2.setStyleSheet(f"font-size: 11px; color: {c['text_secondary']}; background: transparent;")
        txt.addWidget(t1)
        txt.addWidget(t2)
        
        hbox.addWidget(ico_frame)
        hbox.addLayout(txt)
        hbox.addStretch()
        parent_layout.addWidget(card)
    
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
        self.edit_code_p.textChanged.connect(self.rechercher_patient_auto)
    
    def gerer_etat_temps(self, texte):
        est_manuel = texte in ["VIP", "Rendez vous"]
        self.edit_date.setEnabled(True)
        self.edit_time.setEnabled(est_manuel)
        
        if not est_manuel:
            self.edit_date.setDate(QDate.currentDate())
            self.edit_time.setTime(QTime.currentTime())
    
    def rechercher_patient_auto(self):
        code = self.edit_code_p.text().strip()
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
        self.edit_code_p.clear()
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
            
            c_patient = self.edit_code_p.text().strip()
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
                    from controllers.controleur_rendez_vous import RendezVousControleur
                    from views.rendez_vous.rendez_vous_form import RendezVousFormDialog
                    
                    code_session = nouvelle_visite.get_code_session()
                    code_visite = nouvelle_visite.get_code_visite()
                    
                    if code_session and code_visite:
                        rdv_controleur = RendezVousControleur()
                        rdv_dialog = RendezVousFormDialog(
                            controleur=rdv_controleur,
                            code_session=code_session,
                            code_visite=code_visite,
                            parent=self,
                        )
                        rdv_dialog.exec()
                
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
        self.setStyleSheet(f"""
            QWidget {{
                background: {c['bg_main']};
                color: {c['text_primary']};
            }}
        """)
        
        if hasattr(self, 'combo_type') and self.combo_type.count() == 0:
            self.combo_type.addItem(qta.icon("fa5s.bolt", color=c['warning']), "Immediat")
            self.combo_type.addItem(qta.icon("fa5s.calendar-check", color=c['primary']), "Rendez vous")
            self.combo_type.addItem(qta.icon("fa5s.crown", color=c['accent']), "VIP")
            self.combo_type.addItem(qta.icon("fa5s.redo", color=c['info']), "Controle")
        
        if hasattr(self, 'combo_urgent') and self.combo_urgent.count() == 0:
            self.combo_urgent.addItem(qta.icon("fa5s.check-circle", color=c['info']), "Non")
            self.combo_urgent.addItem(qta.icon("fa5s.exclamation-triangle", color=c['danger']), "Oui")
