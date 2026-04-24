from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QDateEdit, 
                             QFrame, QGraphicsDropShadowEffect, QTimeEdit)
from PySide6.QtCore import Qt, QDateTime, QDate, QTime
from PySide6.QtGui import QColor, QPixmap
import qtawesome as qta
import os
from models.model_visite import Visite 
from views.shared.message_box import CustomMessageBox
from views.shared.theme_manager import theme_manager

class VisiteFormDialog(QDialog):
    def __init__(self, controleur, code_patient = None, visite_obj=None, parent=None):
        super().__init__(parent)
        self.controleur = controleur
        self.visite_obj = visite_obj
        self._soumission_en_cours = False
        self.info_cabinet = self.controleur.get_cabinet_info()
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(550, 700) 
        
        self.init_ui()
        self.apply_theme()           # ← construit le formulaire
        
        # Connexion de la logique de grisement
        self.combo_type.currentTextChanged.connect(self.gerer_etat_temps)
        
        if self.visite_obj:
            self.remplir_champs()
        elif code_patient:
            self.edit_code_p.setText(str(code_patient))
            self.edit_code_p.setReadOnly(True)
        else:
            self.gerer_etat_temps(self.combo_type.currentText())

        theme_manager.theme_changed.connect(self.apply_theme)

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.container = QFrame()
        self.container.setObjectName("MainContainer")
        
        self._apply_container_style()

    def _apply_container_style(self):
        c = theme_manager.colors()
        self.container.setStyleSheet(f"""
            QFrame#MainContainer {{
                background-color: {c['bg_card']}; border-radius: 20px; border: 1px solid {c['border']};
            }}
            QLabel {{ color: {c['text_primary']}; font-size: 13px; background-color: transparent; }}
            QLabel#CabinetName {{ font-size: 22px; font-weight: bold; color: {c['danger']}; }}
            QLabel#SectionTitle {{ color: {c['primary']}; font-weight: bold; font-size: 12px; text-transform: uppercase; }}
            
            QLineEdit, QComboBox, QDateEdit, QTimeEdit {{
                padding: 10px; border: 1px solid {c['border']}; border-radius: 8px;
                background-color: {c['bg_input']}; font-size: 14px; color: {c['text_primary']};
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus {{
                border: 2px solid {c['border_focus']}; background-color: {c['bg_card']};
            }}
            QLineEdit:disabled, QDateEdit:disabled, QTimeEdit:disabled {{
                background-color: {c['bg_main']}; color: {c['primary']}; border: 1px solid {c['border_light']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {c['bg_card']}; border: 1px solid {c['border']};
                color: {c['text_primary']}; selection-background-color: {c['primary_light']};
                selection-color: {c['primary']};
            }}
            QPushButton#SaveBtn {{
                background-color: {c['primary']}; color: {c['text_inverse']}; border-radius: 10px;
                font-weight: bold; font-size: 15px; padding: 10px;
            }}
            QPushButton#SaveBtn:disabled {{ background-color: {c['border_light']}; color: {c['text_muted']}; }}
            QPushButton#CancelBtn {{ background-color: {c['bg_main']}; color: {c['text_secondary']}; border-radius: 10px; padding: 10px; border: 1px solid {c['border']}; }}
        """)

    def apply_theme(self):
        c = theme_manager.colors()
        self._apply_container_style()
        if hasattr(self, '_header_card'):
            self._header_card.setStyleSheet(f"QFrame {{ border: none; border-top-left-radius: 20px; border-top-right-radius: 20px; background: {c['bg_card']}; }}")
        if hasattr(self, '_title_form'):
            self._title_form.setStyleSheet(f"color: {c['primary']}; font-size: 21px; font-weight: 900; letter-spacing: 0.8px;")
        if hasattr(self, '_accent'):
            self._accent.setStyleSheet(f"background: {c['border_focus']}; border: none;")
        if hasattr(self, 'icon_clock'):
            self.icon_clock.setPixmap(qta.icon("fa5s.clock", color=c['primary']).pixmap(20, 20))
        if hasattr(self, 'btn_save'):
            self.btn_save.setIcon(qta.icon("fa5s.save", color=c['text_inverse']))
        if hasattr(self, 'btn_cancel'):
            self.btn_cancel.setIcon(qta.icon("fa5s.times", color=c['text_secondary']))

        # Ne construire l'UI qu'une seule fois
        if hasattr(self, '_ui_built'):
            return
        self._ui_built = True

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 70))
        self.container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 35)
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
        header.setAlignment(Qt.AlignTop)
        header.setContentsMargins(0, 0, 0, 0)
        
        cab_info = QVBoxLayout()
        cab_info.setSpacing(0)
        name_cab = QLabel(self.info_cabinet.get("nom_cabinet", "Clinique MÃ©dicale"))
        name_cab.setObjectName("CabinetName")
        addr_cab = QLabel(self.info_cabinet.get("adresse_cabinet", "Service des Admissions"))
        addr_cab.setStyleSheet(f"color: {c['text_muted']}; font-size: 12px;")
        cab_info.addWidget(name_cab)
        cab_info.addWidget(addr_cab)
        header.addLayout(cab_info, 4)

        logo_path = self.info_cabinet.get('logo_url')
        if logo_path and os.path.exists(logo_path):
            logo_lbl = QLabel()
            pix = QPixmap(logo_path).scaled(75, 75, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            header.addWidget(logo_lbl, 0, Qt.AlignRight | Qt.AlignTop)

        header_container.addLayout(header)

        title_form = QLabel("FORMULAIRE VISITE")
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
        body.setContentsMargins(30, 14, 30, 0)
        body.setSpacing(15)

        # --- SECTION 1: IDENTIFICATION ---
        sec1_header = QHBoxLayout()
        sec1_icon = QLabel()
        sec1_icon.setPixmap(qta.icon("fa5s.user-circle", color=c['primary']).pixmap(16, 16))
        sec1_title = QLabel("Identification Patient")
        sec1_title.setObjectName("SectionTitle")
        sec1_header.addWidget(sec1_icon); sec1_header.addWidget(sec1_title); sec1_header.addStretch()
        body.addLayout(sec1_header)

        row1 = QHBoxLayout()
        self.edit_code_p = self.add_field(row1, "Code Patient", "fa5s.id-card")
        self.edit_nom_p = self.add_field(row1, "Nom Complet", "fa5s.user-tag")
        self.edit_nom_p.setReadOnly(True)
        body.addLayout(row1)

        # --- SECTION 2: DÃ‰TAILS ---
        sec2_header = QHBoxLayout()
        sec2_icon = QLabel()
        sec2_icon.setPixmap(qta.icon("fa5s.stethoscope", color=c['primary']).pixmap(16, 16))
        sec2_title = QLabel("DÃ©tails de la Visite")
        sec2_title.setObjectName("SectionTitle")
        sec2_header.addWidget(sec2_icon); sec2_header.addWidget(sec2_title); sec2_header.addStretch()
        body.addLayout(sec2_header)

        row2 = QHBoxLayout()
        vbox_type = QVBoxLayout(); vbox_type.setSpacing(5)
        vbox_type.addWidget(QLabel("Type de Visite"))
        self.combo_type = QComboBox()
        # Ajout d'icÃ´nes dans la combo type
        c = theme_manager.colors()
        self.combo_type.addItem(qta.icon("fa5s.bolt", color=c['warning']), "Immediat")
        self.combo_type.addItem(qta.icon("fa5s.calendar-check", color=c['primary']), "Rendez vous")
        self.combo_type.addItem(qta.icon("fa5s.crown", color=c['accent']), "VIP")
        self.combo_type.addItem(qta.icon("fa5s.redo", color=c['info']), "Controle")
        self.combo_type.setFixedHeight(40)
        vbox_type.addWidget(self.combo_type)

        vbox_urg = QVBoxLayout(); vbox_urg.setSpacing(5)
        vbox_urg.addWidget(QLabel("Niveau d'urgence"))
        self.combo_urgent = QComboBox()
        # Ajout d'icÃ´nes dans la combo urgence
        self.combo_urgent.addItem(qta.icon("fa5s.check-circle", color=c['info']), "Non")
        self.combo_urgent.addItem(qta.icon("fa5s.exclamation-triangle", color=c['danger']), "Oui")
        self.combo_urgent.setFixedHeight(40)
        vbox_urg.addWidget(self.combo_urgent)
        
        row2.addLayout(vbox_type); row2.addLayout(vbox_urg)
        body.addLayout(row2)

        # --- SECTION DATE & HEURE ---
        row_temps = QHBoxLayout()
        
        vbox_date = QVBoxLayout()
        vbox_date.addWidget(QLabel("Date de la visite"))
        self.edit_date = QDateEdit()
        self.edit_date.setCalendarPopup(True)
        self.edit_date.setDate(QDate.currentDate())
        self.edit_date.setFixedHeight(40)
        vbox_date.addWidget(self.edit_date)
        
        vbox_heure = QVBoxLayout()
        vbox_heure.addWidget(QLabel("Temps / Heure"))
        h_heure = QHBoxLayout()
        self.edit_time = QTimeEdit()
        self.edit_time.setTime(QTime.currentTime())
        self.edit_time.setFixedHeight(40)
        
        self.icon_clock = QLabel()
        self.icon_clock.setPixmap(qta.icon("fa5s.clock", color=c['primary']).pixmap(20, 20))
        
        h_heure.addWidget(self.edit_time)
        h_heure.addWidget(self.icon_clock)
        vbox_heure.addLayout(h_heure)
        
        row_temps.addLayout(vbox_date)
        row_temps.addLayout(vbox_heure)
        body.addLayout(row_temps)

        body.addSpacing(20)

        # --- BOUTONS ---
        actions = QHBoxLayout()
        actions.setSpacing(15)
        self.btn_cancel = QPushButton(" Annuler")
        self.btn_cancel.setObjectName("CancelBtn")
        self.btn_cancel.setIcon(qta.icon("fa5s.times", color=c['text_secondary']))
        self.btn_cancel.setFixedHeight(45)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton(" Enregistrer la Visite")
        self.btn_save.setObjectName("SaveBtn")
        self.btn_save.setIcon(qta.icon("fa5s.save", color=c['text_inverse']))
        self.btn_save.setFixedHeight(45)
        self.btn_save.setEnabled(False) 
        self.btn_save.clicked.connect(self.soumettre)

        actions.addWidget(self.btn_cancel, 1)
        actions.addWidget(self.btn_save, 2)
        body.addLayout(actions)

        layout.addLayout(body)
        self.main_layout.addWidget(self.container)
        self.edit_code_p.textChanged.connect(self.rechercher_patient_auto)

    def gerer_etat_temps(self, texte):
        """DÃ©sactive uniquement l'HEURE pour ImmÃ©diat/ContrÃ´le, laisse la DATE libre"""
        # On ne bloque plus la date, seulement l'heure pour les types auto
        est_manuel = texte in ["VIP", "Rendez vous"]
        
        # La date reste toujours activÃ©e (modifiÃ©e selon ta demande)
        self.edit_date.setEnabled(True) 
        
        # L'heure reste pilotÃ©e par le type
        self.edit_time.setEnabled(est_manuel)
        
        if not est_manuel:
            self.edit_date.setDate(QDate.currentDate())
            self.edit_time.setTime(QTime.currentTime())

    def add_field(self, layout, label_text, icon_name):
        vbox = QVBoxLayout(); vbox.setSpacing(5)
        lbl = QLabel(label_text); lbl.setStyleSheet(f"font-weight: bold; color: {theme_manager.colors()['text_secondary']};")
        vbox.addWidget(lbl)
        edit = QLineEdit(); edit.setFixedHeight(40)
        edit.addAction(qta.icon(icon_name, color=theme_manager.colors()['primary']), QLineEdit.LeadingPosition)
        vbox.addWidget(edit)
        err_lbl = QLabel(""); err_lbl.setStyleSheet(f"color: {theme_manager.colors()['danger']}; font-size: 10px;")
        err_lbl.setVisible(False); vbox.addWidget(err_lbl)
        edit.error_label = err_lbl
        layout.addLayout(vbox)
        return edit

    def rechercher_patient_auto(self):
        code = self.edit_code_p.text().strip()
        if not code:
            self.edit_nom_p.clear()
            self.appliquer_style_validation(self.edit_code_p, "neutre")
            self.edit_code_p.error_label.setVisible(False)
        else:
            patient = self.controleur.read_by_code_patient(code)
            if patient:
                self.edit_nom_p.setText(f"{patient.get_nom()} {patient.get_prenom()}")
                self.appliquer_style_validation(self.edit_code_p, "valide")
                self.edit_code_p.error_label.setVisible(False)
            else:
                self.edit_nom_p.setText("Patient introuvable")
                self.appliquer_style_validation(self.edit_code_p, "erreur")
                self.edit_code_p.error_label.setText("Code inexistant")
                self.edit_code_p.error_label.setVisible(True)
        self.verifier_formulaire_complet()

    def appliquer_style_validation(self, widget, etat):
        cv = theme_manager.colors()
        if etat == "valide":
            widget.setStyleSheet(f"border: 2px solid {cv['border_focus']}; background-color: {cv['success_bg']};")
        elif etat == "erreur":
            widget.setStyleSheet(f"border: 1px solid {cv['danger']}; background-color: {cv['danger_bg']};")
        else:
            widget.setStyleSheet("")

    def verifier_formulaire_complet(self):
        patient_existe = self.edit_nom_p.text() != "" and self.edit_nom_p.text() != "Patient introuvable"
        self.btn_save.setEnabled(patient_existe)

    def remplir_champs(self):
        self.btn_save.setText(" Mettre Ã  jour")
        self.edit_code_p.setText(self.visite_obj.get_code_patient())
        self.combo_type.setCurrentText(self.visite_obj.get_type_visite())
        self.combo_urgent.setCurrentText("Oui" if self.visite_obj.get_urgent() else "Non")
        
        dt_base = self.visite_obj.get_date_visite()
        if isinstance(dt_base, str):
            q_dt = QDateTime.fromString(dt_base, "yyyy-MM-dd HH:mm:ss")
        else:
            q_dt = QDateTime(dt_base)
        self.edit_date.setDate(q_dt.date())
        self.edit_time.setTime(q_dt.time())

    def soumettre(self):
        if self._soumission_en_cours:
            return

        try:
            self._soumission_en_cours = True
            if hasattr(self, "btn_save"):
                self.btn_save.setEnabled(False)

            c_visite = self.visite_obj.get_code_visite() if self.visite_obj else ""
            c_patient = self.edit_code_p.text().strip()
            v_type = self.combo_type.currentText()
            v_urgent = self.combo_urgent.currentText()
            
            py_date = self.edit_date.date().toPython()
            py_time = self.edit_time.time().toPython()
            v_date_heure = QDateTime(py_date, py_time).toPython()

            s_visite = self.visite_obj.get_statut_visite() if self.visite_obj else None
            s_patient = self.visite_obj.get_statut_patient() if self.visite_obj else None

            nouvelle_visite = Visite(c_visite, c_patient, "", v_type, v_urgent, v_date_heure, s_visite, s_patient)

            if self.visite_obj:
                ok, msg = self.controleur.update_visite(nouvelle_visite)
            else:
                ok, msg = self.controleur.save_visite(nouvelle_visite)

            if ok:
                CustomMessageBox("SuccÃ¨s", msg, True, self).exec()
                if not self.visite_obj and v_type in ["VIP", "Rendez vous"]:
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
                self.accept()
            else:
                CustomMessageBox("Erreur", msg, False, self).exec()
                self._soumission_en_cours = False
                self.verifier_formulaire_complet()
        except Exception as e:
            CustomMessageBox("Erreur SystÃ¨me", str(e), False, self).exec()
            self._soumission_en_cours = False
            self.verifier_formulaire_complet()
