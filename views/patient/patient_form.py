from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QDateEdit, 
                             QFrame, QGraphicsDropShadowEffect,QLayout)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QPixmap, QIcon
import qtawesome as qta
import os
from datetime import datetime
from models.model_patient import Patient
from views.shared.message_box import CustomMessageBox
from views.shared.theme_manager import theme_manager
from PySide6.QtCore import QPropertyAnimation, QPoint, QEasingCurve

class PatientFormDialog(QDialog):
    def __init__(self, controleur, patient_obj=None, parent=None):
        super().__init__(parent)
        self.controleur = controleur
        self.patient_obj = patient_obj  # L'objet complet si modif, sinon None
        self.info_cabinet = self.controleur.get_cabinet_info()
        
        # Configuration de la fenêtre
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(550, 650)
        
        self.init_ui()
        if self.patient_obj:
            self.remplir_champs()
        theme_manager.theme_changed.connect(self.apply_theme)

    def init_ui(self):
        # Layout principal avec ombre portée
        self.main_layout = QVBoxLayout(self)
        self.container = QFrame()
        self.container.setObjectName("MainContainer")
        
        self._apply_container_style()

        # Effet d'ombre
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 22)
        layout.setSpacing(0)

        c = theme_manager.colors()
        header_card = QFrame()
        self._header_card = header_card
        header_card.setStyleSheet(f"""
            QFrame {{
                border: none;
                border-top-left-radius: 22px;
                border-top-right-radius: 22px;
                background: {c['bg_card']};
            }}
        """)
        header_container = QVBoxLayout(header_card)
        header_container.setContentsMargins(26, 16, 26, 12)
        header_container.setSpacing(8)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        
        # Infos Cabinet
        cabinet_info_layout = QVBoxLayout()
        cabinet_info_layout.setSpacing(2) # Espace serré entre nom et adresse

        name_cab = QLabel(self.info_cabinet.get("nom_cabinet", "Cabinet Médical"))
        name_cab.setObjectName("CabinetName") # Pour le CSS spécifique
        name_cab.setWordWrap(True) # Si le nom est très long, il passe à la ligne au lieu de se masquer
        
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

        title_form = QLabel("FORMULAIRE PATIENT")
        self._title_form = title_form
        title_form.setAlignment(Qt.AlignCenter)
        title_form.setStyleSheet(
            f"color: {c['primary']}; font-size: 21px; font-weight: 900; letter-spacing: 0.8px;"
        )
        header_container.addWidget(title_form)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {c['border_light']};")
        header_container.addWidget(line)

        accent = QFrame()
        self._accent = accent
        accent.setFixedHeight(6)
        accent.setStyleSheet(f"background: {c['border_focus']}; border: none;")
        header_container.addWidget(accent)

        layout.addWidget(header_card)

        body = QVBoxLayout()
        body.setContentsMargins(26, 14, 26, 0)
        body.setSpacing(0)

        form_grid = QVBoxLayout()
        form_grid.setSpacing(15)

        # Ligne 1 : Nom / Prénom
        row1 = QHBoxLayout()
        self.edit_nom = self.add_field(row1, "Nom", "fa5s.user")
        self.edit_prenom = self.add_field(row1, "Prénom", "fa5s.users")
        form_grid.addLayout(row1)

        row2 = QHBoxLayout()
        self.edit_tel = self.add_field(row2, "Téléphone", "fa5s.phone")

        vbox_sexe = QVBoxLayout()
        vbox_sexe.setSpacing(5)
        lbl_sexe = QLabel("Genre")
        lbl_sexe.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']};")
        vbox_sexe.addWidget(lbl_sexe)
        
        self.combo_sexe = QComboBox()
        self.combo_sexe.addItem(qta.icon("fa5s.mars", color=c['primary']), "Homme")
        self.combo_sexe.addItem(qta.icon("fa5s.venus", color=c['primary']), "Femme")
        self.combo_sexe.setFixedHeight(40)
        vbox_sexe.addWidget(self.combo_sexe)
        
        row2.addLayout(vbox_sexe, 1)
        form_grid.addLayout(row2)

        vbox_date = QVBoxLayout()
        vbox_date.setSpacing(5)
        lbl_date = QLabel("Date de Naissance")
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
                border-radius: 10px;
                background-color: {c['bg_input']};
                color: {c['text_primary']};
            }}
            QDateEdit:focus {{ border: 2px solid {c['border_focus']}; }}
            
            QDateEdit::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 1px solid {c['border']};
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
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
        form_grid.addLayout(vbox_date)

        self.edit_profession = self.add_field(form_grid, "Profession", "fa5s.briefcase")
        self.edit_adresse = self.add_field(form_grid, "Adresse", "fa5s.map-marker-alt")

        body.addLayout(form_grid)
        body.addSpacing(20)
        
        # --- Connexion de la validation en temps réel ---
        
        # Nom et Prénom
        self.edit_nom.textChanged.connect(
            lambda: self.appliquer_validation(self.edit_nom, self.controleur._valider_nom, self.edit_nom.text())
        )
        self.edit_prenom.textChanged.connect(
            lambda: self.appliquer_validation(self.edit_prenom, self.controleur._valider_prenom, self.edit_prenom.text())
        )
        
        # Téléphone (Validation format + Existence)
        self.edit_tel.textChanged.connect(self.valider_telephone_complet)
        
        # Profession et Adresse
        self.edit_profession.textChanged.connect(
            lambda: self.appliquer_validation(self.edit_profession, self.controleur._valider_profession, self.edit_profession.text())
        )
        self.edit_adresse.textChanged.connect(
            lambda: self.appliquer_validation(self.edit_adresse, self.controleur._valider_adresse, self.edit_adresse.text())
        )

        # --- BOUTONS ---
        actions = QHBoxLayout()
        
        # Bouton Annuler
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setObjectName("CancelBtn")
        self.btn_cancel.setFixedHeight(45)
        self.btn_cancel.clicked.connect(self.reject)

        # Bouton Enregistrer (UNE SEULE FOIS)
        self.btn_save = QPushButton("Enregistrer")
        self.btn_save.setObjectName("SaveBtn") # Indispensable pour le CSS
        self.btn_save.setFixedHeight(45)
        self.btn_save.setIcon(qta.icon("fa5s.check", color="white"))
        
        # État initial du bouton
        est_valide = True if self.patient_obj else False
        self.btn_save.setEnabled(est_valide)
        
        # Connexion de l'action
        self.btn_save.clicked.connect(self.soumettre)

        actions.addWidget(self.btn_cancel, 1)
        actions.addWidget(self.btn_save, 2)
        body.addLayout(actions)

        layout.addLayout(body)

        self.main_layout.addWidget(self.container)

    def _apply_container_style(self):
        c = theme_manager.colors()
        self.container.setStyleSheet(f"""
            QFrame#MainContainer {{
                background-color: {c['bg_card']}; border-radius: 22px; border: 1px solid {c['border']};
            }}
            QLabel {{ color: {c['text_primary']}; font-size: 13px; background-color: transparent; }}
            QLabel#CabinetName {{ font-size: 22px; font-weight: bold; color: {c['danger']}; background-color: transparent; }}
            QLineEdit, QComboBox, QDateEdit {{
                padding: 10px; border: 1px solid {c['border']}; border-radius: 10px;
                background-color: {c['bg_input']}; color: {c['text_primary']}; font-size: 14px;
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
                border: 2px solid {c['border_focus']}; background-color: {c['bg_card']};
            }}
            QPushButton#SaveBtn {{
                background-color: {c['primary']}; color: {c['text_inverse']}; border-radius: 10px;
                font-weight: bold; font-size: 15px;
            }}
            QPushButton#SaveBtn:hover {{ background-color: {c['hover']}; }}
            QPushButton#SaveBtn:disabled {{ background-color: {c['border_light']}; color: {c['text_muted']}; }}
            QPushButton#CancelBtn {{
                background-color: {c['bg_main']}; color: {c['text_secondary']}; border-radius: 10px;
                border: 1px solid {c['border']};
            }}
            QPushButton#CancelBtn:hover {{ background-color: {c['bg_input']}; }}
        """)

    def apply_theme(self):
        c = theme_manager.colors()
        self._apply_container_style()
        if hasattr(self, '_header_card'):
            self._header_card.setStyleSheet(f"QFrame {{ border: none; border-top-left-radius: 22px; border-top-right-radius: 22px; background: {c['bg_card']}; }}")
        if hasattr(self, '_title_form'):
            self._title_form.setStyleSheet(f"color: {c['primary']}; font-size: 21px; font-weight: 900; letter-spacing: 0.8px;")
        if hasattr(self, '_accent'):
            self._accent.setStyleSheet(f"background: {c['border_focus']}; border: none;")

    def add_field(self, layout, label_text, icon_name):
        vbox = QVBoxLayout()
        vbox.setSpacing(2) # Espace réduit
        c = theme_manager.colors()
        
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']};")
        vbox.addWidget(lbl)
        
        edit = QLineEdit()
        edit.setPlaceholderText(f"Entrez le {label_text.lower()}...")
        edit.setFixedHeight(40)
        icon = qta.icon(icon_name, color=c['primary'])
        edit.addAction(icon, QLineEdit.LeadingPosition)
        vbox.addWidget(edit)
        
        # Label d'erreur (caché par défaut)
        err_lbl = QLabel("")
        err_lbl.setStyleSheet(f"color: {c['danger']}; font-size: 10px; font-style: italic;")
        err_lbl.setVisible(False)
        vbox.addWidget(err_lbl)
        
        # On attache le label d'erreur à l'edit pour le retrouver facilement
        edit.error_label = err_lbl
        
        layout.addLayout(vbox)
        return edit

    def remplir_champs(self):
        self.btn_save.setText("Mettre à jour")
        # Si on modifie, on injecte les données de l'objet Patient
        self.edit_nom.setText(self.patient_obj.get_nom())
        self.edit_prenom.setText(self.patient_obj.get_prenom())
        self.edit_tel.setText(self.patient_obj.get_telephone())
        self.edit_profession.setText(self.patient_obj.get_profession())
        self.edit_adresse.setText(self.patient_obj.get_adresse())
        
        # Sexe
        index = self.combo_sexe.findText(self.patient_obj.get_genre())
        if index >= 0: self.combo_sexe.setCurrentIndex(index)
        
        # Date
        if self.patient_obj.get_naissance():
            qdate = QDate.fromString(str(self.patient_obj.get_naissance()), "yyyy-MM-dd")
            self.edit_date.setDate(qdate)

    def soumettre(self):
        # Comme le bouton est désactivé si erreur, on arrive ici 
        # seulement si tout est déjà valide !
        
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
            # On affiche la boîte personnalisée en mode Succès
            self.show_message(True, "Le patient a été enregistré avec succès !")
            self.accept()  # Ferme le formulaire après le message 
        else:
           # On affiche la boîte en mode Erreur si le DAO a échoué (ex: DB pleine)
            self.show_message(False, f"Erreur lors de l'enregistrement : {msg}")
            
    def appliquer_validation(self, widget, validation_func, texte):
        valide, message = validation_func(texte)
        cv = theme_manager.colors()
        
        if not valide and texte != "":
            widget.setStyleSheet(f"border: 1px solid {cv['danger']}; background-color: {cv['danger_bg']};")
            widget.error_label.setText(message)
            widget.error_label.setVisible(True)
        elif not valide and texte == "":
            widget.setStyleSheet(f"border: 1px solid {cv['border']}; background-color: {cv['bg_input']}; color: {cv['text_primary']};")
            widget.error_label.setVisible(False)
        else:
            widget.setStyleSheet(f"border: 2px solid {cv['border_focus']}; background-color: {cv['bg_card']};")
            widget.error_label.setVisible(False)
            
        self.verifier_formulaire_complet()
        return valide

    def valider_telephone_complet(self):
        tel = self.edit_tel.text()
        valide, msg = self.controleur._valider_telephone(tel)
        if valide and not self.patient_obj:
            valide, msg = self.controleur._control_exist(tel)
        
        self.appliquer_validation(self.edit_tel, lambda x: (valide, msg), tel)

    def verifier_formulaire_complet(self):
        """
        Active le bouton SEULEMENT si tous les champs respectent 
        les règles strictes du contrôleur.
        """
        """Vérifie absolument tous les champs et affiche qui bloque dans la console"""
        v_nom, _ = self.controleur._valider_nom(self.edit_nom.text())
        v_pre, _ = self.controleur._valider_prenom(self.edit_prenom.text())
        v_tel, _ = self.controleur._valider_telephone(self.edit_tel.text())
        v_prof, _ = self.controleur._valider_profession(self.edit_profession.text())
        v_adr, _ = self.controleur._valider_adresse(self.edit_adresse.text())
        
        tel_disponible = True
        if not self.patient_obj:
            tel_disponible, _ = self.controleur._control_exist(self.edit_tel.text())


        tous_valides = all([v_nom, v_pre, v_tel, v_prof, v_adr]) and  tel_disponible
        self.btn_save.setEnabled(tous_valides)
        
    # --- LA BOITE DE MESSAGE COMMUNE ---
    def show_message(self, reussite, message):
        titre = "Succès" if reussite else "Information / Erreur"
        dialog = CustomMessageBox(titre, message, is_success=reussite, parent=self)
        dialog.exec()
        
        
        
    
