"""
Widget formulaire personnel (version non-modale pour onglet)
Design identique à PersonnelFormDialog mais intégré directement dans l'onglet.
"""
import os
import qtawesome as qta
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QFileDialog, QDateEdit
)
from views.shared.message_box import CustomMessageBox
from views.shared.theme_manager import theme_manager


class PersonnelFormWidget(QWidget):
    """
    Widget formulaire personnel intégré dans l'onglet 'Nouveau'.
    Même design que PersonnelFormDialog mais sans fenêtre modale.
    """

    personnel_saved = Signal()

    def __init__(self, controleur, personnel_obj=None, parent=None):
        super().__init__(parent)
        self.controleur = controleur
        self.personnel_obj = personnel_obj or {}
        self.info_cabinet = (
            self.controleur.get_cabinet_info()
            if hasattr(self.controleur, "get_cabinet_info") else {}
        )
        self.selected_photo_path = None

        self._init_ui()

        if self.personnel_obj:
            self._remplir_champs()
        
        self._connecter_validations()

        theme_manager.theme_changed.connect(self.apply_theme)

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 4, 20, 10)
        outer.setSpacing(8)

        # Initialiser les attributs pour éviter les erreurs
        self.edit_nom = None
        self.edit_prenom = None
        self.edit_fonction = None
        self.edit_contact = None
        self.edit_mail = None
        self.edit_adresse = None
        self.date_naissance = None
        self.edit_mdp = None
        self.edit_mdp_existant = None
        self.mode_modification = False  # Flag pour savoir si on est en mode modification

        self._setup_header(outer)
        self._section_form(outer)

        self.apply_theme()

    def _setup_header(self, parent_layout):
        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(60)
        c = theme_manager.colors()
        self.header_frame.setStyleSheet(f"""
            background-color: {c['bg_card']};
            border-radius: 12px;
            border: none;
        """)

        layout = QHBoxLayout(self.header_frame)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        # Icône users
        icon_box = QFrame()
        self._icon_box = icon_box
        icon_box.setFixedSize(46, 46)
        icon_box.setStyleSheet(f"""
            background-color: {c['bg_input']};
            border-radius: 10px;
            border: 1px solid {c['border_light']};
        """)
        ib_layout = QHBoxLayout(icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        ico_lbl = QLabel()
        ico_lbl.setPixmap(qta.icon("fa5s.users", color=c['primary']).pixmap(22, 22))
        ico_lbl.setAlignment(Qt.AlignCenter)
        ib_layout.addWidget(ico_lbl, alignment=Qt.AlignCenter)

        # Titre + sous-titre
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        
        titre = "Enregistrement d'un personnel" if not self.personnel_obj else "Modification du personnel"
        lbl_main = QLabel(titre)
        lbl_main.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {c['text_primary']}; background: transparent; border: none;")
        lbl_sub = QLabel("Saisissez les informations du membre du personnel")
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
        label_save = " Enregistrer" if not self.personnel_obj else " Mettre à jour"
        self.btn_save = QPushButton(qta.icon("fa5s.save", color=theme_manager.color("text_inverse")), label_save)
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
                color: {c['text_inverse']};
            }}
            QPushButton:enabled:hover {{ background-color: {c['primary_hover']}; }}
        """)

    def _make_field(self, label_text: str, widget, icon_name: str, color_key: str, height: int = 38):
        c = theme_manager.colors()
        icon_color = c[color_key]
        vbox = QVBoxLayout()
        vbox.setSpacing(3)

        lbl = QLabel(label_text)
        lbl.setStyleSheet(
            f"font-size: 10px; font-weight: 600; color: {c['text_secondary']};"
            " background: transparent; border: none;"
        )
        vbox.addWidget(lbl)

        wrapper = QFrame()
        wrapper.setObjectName("inputWrapper")
        wrapper.setFixedHeight(height)
        self._apply_wrapper_style(wrapper)

        hbox = QHBoxLayout(wrapper)
        hbox.setContentsMargins(6, 4, 6, 4)
        hbox.setSpacing(6)

        badge = QFrame()
        badge.setFixedSize(24, 24)
        badge.setStyleSheet(f"background-color: {icon_color}20; border-radius: 6px; border: none;")
        bl = QHBoxLayout(badge)
        bl.setContentsMargins(0, 0, 0, 0)
        ico_lbl = QLabel()
        ico_lbl.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(12, 12))
        ico_lbl.setAlignment(Qt.AlignCenter)
        ico_lbl.setStyleSheet("border: none; background: transparent;")
        bl.addWidget(ico_lbl, alignment=Qt.AlignCenter)

        # Stocker pour mise à jour lors du changement de thème
        if not hasattr(self, '_field_badges'):
            self._field_badges = []
        self._field_badges.append((badge, ico_lbl, icon_name, color_key))

        self._clear_widget_style(widget, c)
        hbox.addWidget(badge, 0, Qt.AlignVCenter)
        hbox.addWidget(widget, 1)
        vbox.addWidget(wrapper)

        # Label d'erreur avec hauteur fixe pour éviter le décalage
        err_lbl = QLabel("")
        err_lbl.setFixedHeight(12)
        err_lbl.setStyleSheet(f"color: {c['danger']}; font-size: 9px; font-style: italic; background: transparent;")
        err_lbl.setVisible(False)
        vbox.addWidget(err_lbl)

        return vbox, wrapper, err_lbl

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
        if isinstance(widget, QLineEdit):
            widget.setStyleSheet(f"QLineEdit {{ {base} padding: 0; }}")
        elif isinstance(widget, QDateEdit):
            widget.setStyleSheet(f"QDateEdit {{ {base} padding: 0; }}")
        else:
            # Pour QComboBox et autres widgets
            from PySide6.QtWidgets import QComboBox
            if isinstance(widget, QComboBox):
                widget.setStyleSheet(f"""
                    QComboBox {{
                        {base}
                        padding: 2px 8px;
                    }}
                    QComboBox::drop-down {{
                        border: none;
                        width: 20px;
                    }}
                    QComboBox::down-arrow {{
                        image: none;
                        border: none;
                    }}
                """)

    def _section_form(self, parent_layout):
        c = theme_manager.colors()
        card = QFrame()
        self._form_card = card  # référence pour apply_theme()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {c['bg_card']};
                border: 1.5px solid {c['border_light']};
                border-radius: 12px;
            }}
        """)
        
        main_layout = QHBoxLayout(card)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(12)

        # Colonne gauche : formulaire personnel
        left_col = QVBoxLayout()
        left_col.setSpacing(10)

        # Titre section
        hdr = QHBoxLayout()
        self._form_ico = QLabel()
        self._form_ico.setPixmap(qta.icon("fa5s.clipboard-list", color=c['primary']).pixmap(14, 14))
        self._form_ico.setStyleSheet("border: none; background: transparent;")
        self._form_lbl = QLabel("Informations du personnel")
        self._form_lbl.setStyleSheet(
            f"font-size: 12px; font-weight: bold; color: {c['primary']};"
            " background: transparent; border: none;"
        )
        hdr.addWidget(self._form_ico)
        hdr.addSpacing(6)
        hdr.addWidget(self._form_lbl)
        hdr.addStretch()
        left_col.addLayout(hdr)

        # Rangée 1 : Nom | Prénom
        row1 = QHBoxLayout()
        row1.setSpacing(12)
        self.edit_nom = QLineEdit()
        self.edit_nom.setPlaceholderText("Ex: Diallo")
        vb_nom, self._wrap_nom, self._err_nom = self._make_field("Nom", self.edit_nom, "fa5s.user", "info")
        row1.addLayout(vb_nom, 1)

        self.edit_prenom = QLineEdit()
        self.edit_prenom.setPlaceholderText("Ex: Mamadou")
        vb_prenom, self._wrap_prenom, self._err_prenom = self._make_field("Prénom", self.edit_prenom, "fa5s.user", "primary")
        row1.addLayout(vb_prenom, 1)
        left_col.addLayout(row1)

        # Rangée 2 : Fonction | Contact
        row2 = QHBoxLayout()
        row2.setSpacing(12)
        self.edit_fonction = QLineEdit()
        self.edit_fonction.setPlaceholderText("Ex: Médecin")
        vb_fonction, self._wrap_fonction, self._err_fonction = self._make_field("Fonction", self.edit_fonction, "fa5s.briefcase", "accent")
        row2.addLayout(vb_fonction, 1)

        self.edit_contact = QLineEdit()
        self.edit_contact.setPlaceholderText("Ex: +224 123 456 789")
        vb_contact, self._wrap_contact, self._err_contact = self._make_field("Contact", self.edit_contact, "fa5s.phone", "secondary")
        row2.addLayout(vb_contact, 1)
        left_col.addLayout(row2)

        # Rangée 3 : Email | Adresse
        row3 = QHBoxLayout()
        row3.setSpacing(12)
        self.edit_mail = QLineEdit()
        self.edit_mail.setPlaceholderText("Ex: personnel@example.com")
        vb_mail, self._wrap_mail, self._err_mail = self._make_field("Email", self.edit_mail, "fa5s.envelope", "success")
        row3.addLayout(vb_mail, 1)

        self.edit_adresse = QLineEdit()
        self.edit_adresse.setPlaceholderText("Ex: Conakry, Guinée")
        vb_adresse, self._wrap_adresse, self._err_adresse = self._make_field("Adresse", self.edit_adresse, "fa5s.map-marker-alt", "danger")
        row3.addLayout(vb_adresse, 1)
        left_col.addLayout(row3)

        # Date de naissance
        self.date_naissance = QDateEdit()
        self.date_naissance.setDisplayFormat("yyyy-MM-dd")
        self.date_naissance.setCalendarPopup(True)
        self.date_naissance.setDate(QDate.currentDate())
        vb_date, self._wrap_date, self._err_date = self._make_field("Date de naissance", self.date_naissance, "fa5s.calendar-alt", "warning")
        left_col.addLayout(vb_date)

        # Checkbox Est responsable
        from PySide6.QtWidgets import QCheckBox
        self.check_responsable = QCheckBox("Est responsable")
        self.check_responsable.setStyleSheet(f"""
            QCheckBox {{
                font-size: 11px;
                font-weight: 600;
                color: {c['text_primary']};
                background: transparent;
                border: none;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {c['border']};
                border-radius: 4px;
                background: {c['bg_input']};
            }}
            QCheckBox::indicator:checked {{
                background: {c['primary']};
                border-color: {c['primary']};
            }}
        """)
        left_col.addWidget(self.check_responsable)

        main_layout.addLayout(left_col, 2)

        # Colonne milieu : compte utilisateur
        middle_col = QVBoxLayout()
        middle_col.setSpacing(10)
        
        # Titre section compte
        compte_hdr = QHBoxLayout()
        self._compte_ico = QLabel()
        self._compte_ico.setPixmap(qta.icon("fa5s.user-lock", color=c['primary']).pixmap(14, 14))
        self._compte_ico.setStyleSheet("border: none; background: transparent;")
        self._compte_lbl = QLabel("Compte utilisateur")
        self._compte_lbl.setStyleSheet(
            f"font-size: 12px; font-weight: bold; color: {c['primary']};"
            " background: transparent; border: none;"
        )
        compte_hdr.addWidget(self._compte_ico)
        compte_hdr.addSpacing(6)
        compte_hdr.addWidget(self._compte_lbl)
        compte_hdr.addStretch()
        middle_col.addLayout(compte_hdr)
        
        # Options
        self.radio_nouveau = QCheckBox("Nouveau compte")
        self.radio_nouveau.setStyleSheet(f"""
            QCheckBox {{
                font-size: 10px;
                font-weight: 600;
                color: {c['text_secondary']};
                background: transparent;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border: 2px solid {c['border']};
                border-radius: 4px;
            }}
            QCheckBox::indicator:checked {{
                background: {c['primary']};
                border-color: {c['primary']};
            }}
        """)
        self.radio_nouveau.stateChanged.connect(self._toggle_mode_compte)
        middle_col.addWidget(self.radio_nouveau)
        
        self.radio_existant = QCheckBox("Personnel existant")
        self.radio_existant.setStyleSheet(self.radio_nouveau.styleSheet())
        self.radio_existant.stateChanged.connect(self._toggle_mode_compte)
        middle_col.addWidget(self.radio_existant)
        
        # Container nouveau compte
        self.nouveau_compte_container = QWidget()
        self.nouveau_compte_container.setStyleSheet("background: transparent;")
        nouveau_layout = QVBoxLayout(self.nouveau_compte_container)
        nouveau_layout.setContentsMargins(0, 0, 0, 0)
        nouveau_layout.setSpacing(10)
        
        self.edit_mdp = QLineEdit()
        self.edit_mdp.setPlaceholderText("Mot de passe")
        self.edit_mdp.setEchoMode(QLineEdit.Password)
        vb_mdp, self._wrap_mdp, self._err_mdp = self._make_field("Mot de passe", self.edit_mdp, "fa5s.lock", "danger")
        nouveau_layout.addLayout(vb_mdp)
        
        from PySide6.QtWidgets import QComboBox
        self.combo_role = QComboBox()
        self.combo_role.addItems([
            "Directeur Général",
            "Médecin",
            "Chirurgien",
            "Laborantin",
            "Caissière",
            "personnel"
        ])
        vb_role, self._wrap_role, self._err_role = self._make_field("Rôle", self.combo_role, "fa5s.user-tag", "secondary")
        nouveau_layout.addLayout(vb_role)
        
        self.nouveau_compte_container.setVisible(False)
        middle_col.addWidget(self.nouveau_compte_container)
        
        # Container personnel existant
        self.existant_compte_container = QWidget()
        self.existant_compte_container.setStyleSheet("background: transparent;")
        existant_layout = QVBoxLayout(self.existant_compte_container)
        existant_layout.setContentsMargins(0, 0, 0, 0)
        existant_layout.setSpacing(10)
        
        self.combo_personnel = QComboBox()
        self._charger_personnels_sans_compte()
        self.combo_personnel.currentIndexChanged.connect(self._charger_personnel_selectionne)
        vb_perso, self._wrap_perso, self._err_perso = self._make_field("Personnel", self.combo_personnel, "fa5s.user", "info")
        existant_layout.addLayout(vb_perso)
        
        self.edit_mdp_existant = QLineEdit()
        self.edit_mdp_existant.setPlaceholderText("Mot de passe")
        self.edit_mdp_existant.setEchoMode(QLineEdit.Password)
        vb_mdp_ex, self._wrap_mdp_ex, self._err_mdp_ex = self._make_field("Mot de passe", self.edit_mdp_existant, "fa5s.lock", "danger")
        existant_layout.addLayout(vb_mdp_ex)
        
        self.combo_role_existant = QComboBox()
        self.combo_role_existant.addItems([
            "Directeur Général",
            "Médecin",
            "Chirurgien",
            "Laborantin",
            "Caissière",
            "personnel"
        ])
        vb_role_ex, self._wrap_role_ex, self._err_role_ex = self._make_field("Rôle", self.combo_role_existant, "fa5s.user-tag", "secondary")
        existant_layout.addLayout(vb_role_ex)
        
        self.existant_compte_container.setVisible(False)
        middle_col.addWidget(self.existant_compte_container)
        
        middle_col.addStretch()
        main_layout.addLayout(middle_col, 1)

        # Colonne droite : photo compacte
        right_col = QVBoxLayout()
        right_col.setSpacing(10)

        self.photo_label = QLabel()
        self.photo_label.setFixedSize(120, 140)
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setStyleSheet(
            f"background: {c['bg_input']}; border: 1px dashed {c['border_focus']}; border-radius: 10px;"
        )
        self.photo_label.setPixmap(qta.icon("fa5s.user-circle", color=c['text_muted']).pixmap(60, 60))
        right_col.addWidget(self.photo_label, 0, Qt.AlignTop)

        self.btn_photo = QPushButton(qta.icon("fa5s.camera", color=c['primary']), " Photo")
        self.btn_photo.setFixedHeight(36)
        self.btn_photo.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['bg_main']};
                color: {c['primary']};
                border-radius: 8px;
                border: 1px solid {c['border_light']};
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: {c['hover']}; }}
        """)
        self.btn_photo.clicked.connect(self._selectionner_photo)
        right_col.addWidget(self.btn_photo)
        
        right_col.addStretch()
        main_layout.addLayout(right_col, 1)

        parent_layout.addWidget(card)



    def _connecter_validations(self):
        self.edit_nom.textChanged.connect(self._valider_formulaire)
        self.edit_prenom.textChanged.connect(self._valider_formulaire)
        self.edit_fonction.textChanged.connect(self._valider_formulaire)
        self.edit_contact.textChanged.connect(self._valider_formulaire)
        self.edit_mail.textChanged.connect(self._valider_email_complet)
        self.edit_adresse.textChanged.connect(self._valider_formulaire)
        self.date_naissance.dateChanged.connect(self._valider_formulaire)
        self.edit_mdp.textChanged.connect(self._valider_formulaire)
        self.edit_mdp_existant.textChanged.connect(self._valider_formulaire)
    
    def _toggle_mode_compte(self):
        """Bascule entre création nouveau compte et association à personnel existant"""
        if self.sender() == self.radio_nouveau:
            if self.radio_nouveau.isChecked():
                self.radio_existant.setChecked(False)
                self.nouveau_compte_container.setVisible(True)
                self.existant_compte_container.setVisible(False)
            else:
                self.nouveau_compte_container.setVisible(False)
        elif self.sender() == self.radio_existant:
            if self.radio_existant.isChecked():
                self.radio_nouveau.setChecked(False)
                self.nouveau_compte_container.setVisible(False)
                self.existant_compte_container.setVisible(True)
                self._charger_personnels_sans_compte()
            else:
                self.existant_compte_container.setVisible(False)
        
        self._valider_formulaire()
    
    def _charger_personnels_sans_compte(self):
        """Charge la liste des personnels qui n'ont pas encore de compte utilisateur"""
        try:
            self.combo_personnel.clear()
            self.combo_personnel.addItem("-- Sélectionnez un personnel --", None)
            
            # Récupérer tous les personnels
            personnels = self.controleur.lister_tout()
            
            # Filtrer les personnels sans compte
            for p in personnels:
                code = p.get("code")
                nom_complet = f"{p.get('prenom', '')} {p.get('nom', '')} ({code})"
                self.combo_personnel.addItem(nom_complet, code)
                
        except Exception as e:
            print(f"Erreur chargement personnels: {e}")
    
    def _charger_personnel_selectionne(self):
        """Charge les données du personnel sélectionné dans le formulaire"""
        code_personnel = self.combo_personnel.currentData()
        if not code_personnel:
            self.mode_modification = False
            return
        
        try:
            # Activer le mode modification
            self.mode_modification = True
            
            # Récupérer les données du personnel
            personnel = self.controleur.obtenir_par_code(code_personnel)
            if personnel:
                # Remplir les champs
                self.edit_nom.setText(str(personnel.get("nom", "")))
                self.edit_prenom.setText(str(personnel.get("prenom", "")))
                self.edit_fonction.setText(str(personnel.get("fonction", "")))
                self.edit_contact.setText(str(personnel.get("contact", "")))
                self.edit_mail.setText(str(personnel.get("mail", "")))
                self.edit_adresse.setText(str(personnel.get("adresse", "")))
                
                # Date
                date_val = personnel.get("date_naissance")
                if date_val:
                    self.date_naissance.setDate(self._date_to_qdate(date_val))
                
                # Responsable
                est_responsable = personnel.get("est_responsable", 0)
                self.check_responsable.setChecked(bool(est_responsable))
                
                # Photo
                photo_path = personnel.get("photo_path")
                if photo_path:
                    import os
                    full_path = os.path.join(self.controleur.service.image_folder, photo_path)
                    self._set_photo_preview(full_path)
                
                # NE PAS renseigner le mot de passe pour des raisons de sécurité
                # L'utilisateur devra le saisir à nouveau s'il veut créer/modifier le compte
                self.edit_mdp_existant.clear()
                
        except Exception as e:
            print(f"Erreur chargement personnel: {e}")
            self.mode_modification = False

    def _valider_formulaire(self):
        tout_valide = True

        nom = self.edit_nom.text().strip()
        ok, msg = self.controleur._valider_nom_prenom_fonction(nom)
        self._set_field_state(self._wrap_nom, self._err_nom, ok, msg, bool(nom))
        if not ok:
            tout_valide = False

        prenom = self.edit_prenom.text().strip()
        ok, msg = self.controleur._valider_nom_prenom_fonction(prenom)
        self._set_field_state(self._wrap_prenom, self._err_prenom, ok, msg, bool(prenom))
        if not ok:
            tout_valide = False

        fonction = self.edit_fonction.text().strip()
        ok, msg = self.controleur._valider_nom_prenom_fonction(fonction)
        self._set_field_state(self._wrap_fonction, self._err_fonction, ok, msg, bool(fonction))
        if not ok:
            tout_valide = False

        contact = self.edit_contact.text().strip()
        ok, msg = self.controleur._valider_contact(contact)
        self._set_field_state(self._wrap_contact, self._err_contact, ok, msg, bool(contact))
        if not ok:
            tout_valide = False

        mail = self.edit_mail.text().strip()
        ok, msg = self.controleur._valider_email(mail)
        if ok and not self._mail_disponible(mail):
            ok = False
            msg = "Email déjà utilisé."
        self._set_field_state(self._wrap_mail, self._err_mail, ok, msg, bool(mail))
        if not ok:
            tout_valide = False

        adresse = self.edit_adresse.text().strip()
        ok, msg = self.controleur._valider_adresse(adresse)
        self._set_field_state(self._wrap_adresse, self._err_adresse, ok, msg, bool(adresse))
        if not ok:
            tout_valide = False

        date_str = self.date_naissance.date().toString("yyyy-MM-dd")
        ok, msg = self.controleur._valider_date(date_str)
        self._set_field_state(self._wrap_date, self._err_date, ok, msg, True)
        if not ok:
            tout_valide = False
        
        # Validation mot de passe si compte à créer
        if self.radio_nouveau.isChecked():
            mdp = self.edit_mdp.text().strip()
            if len(mdp) < 6:
                self._set_field_state(self._wrap_mdp, self._err_mdp, False, "Minimum 6 caractères", bool(mdp))
                tout_valide = False
            else:
                self._set_field_state(self._wrap_mdp, self._err_mdp, True, "", True)
        
        # Validation pour personnel existant
        if self.radio_existant.isChecked():
            if self.combo_personnel.currentIndex() == 0:  # Aucun personnel sélectionné
                tout_valide = False
            mdp_ex = self.edit_mdp_existant.text().strip()
            if len(mdp_ex) < 6:
                self._set_field_state(self._wrap_mdp_ex, self._err_mdp_ex, False, "Minimum 6 caractères", bool(mdp_ex))
                tout_valide = False
            else:
                self._set_field_state(self._wrap_mdp_ex, self._err_mdp_ex, True, "", True)

        self.btn_save.setEnabled(tout_valide)
        self._apply_save_btn_style()

    def _valider_email_complet(self):
        """Validation complète de l'email incluant la vérification d'unicité"""
        mail = self.edit_mail.text().strip()
        
        # Validation du format
        ok, msg = self.controleur._valider_email(mail)
        
        # Vérification de l'unicité si le format est valide
        if ok and mail and not self._mail_disponible(mail):
            ok = False
            # Trouver le personnel qui utilise cet email
            for personnel in self.controleur.get_all_personnels():
                if personnel.get("mail", "").strip().lower() == mail.lower():
                    code_courant = self.personnel_obj.get("code") if self.personnel_obj else None
                    if self.radio_existant.isChecked():
                        code_courant = self.combo_personnel.currentData()
                    if personnel.get("code") != code_courant:
                        nom_prenom = f"{personnel.get('prenom', '')} {personnel.get('nom', '')}"
                        msg = f"Email utilisé par {nom_prenom}"
                        break
        
        self._set_field_state(self._wrap_mail, self._err_mail, ok, msg, bool(mail))
        self._valider_formulaire()

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

    def _mail_disponible(self, mail):
        mail_normalise = (mail or "").strip().lower()
        if not mail_normalise:
            return False
        
        # En mode modification, on récupère le code du personnel qu'on modifie
        code_courant = None
        
        # Si on modifie un personnel (personnel_obj est défini)
        if self.personnel_obj:
            code_courant = self.personnel_obj.get("code")
        
        # Si on est en mode personnel existant (modification via combo)
        if self.radio_existant.isChecked():
            code_selectionne = self.combo_personnel.currentData()
            if code_selectionne:
                code_courant = code_selectionne
        
        # Vérifier si l'email est utilisé par un autre personnel
        for personnel in self.controleur.get_all_personnels():
            if (personnel.get("mail", "").strip().lower() == mail_normalise and
                    personnel.get("code") != code_courant):
                return False
        return True

    def _remplir_champs(self):
        self.edit_nom.setText(str(self.personnel_obj.get("nom", "")))
        self.edit_prenom.setText(str(self.personnel_obj.get("prenom", "")))
        self.edit_fonction.setText(str(self.personnel_obj.get("fonction", "")))
        self.edit_contact.setText(str(self.personnel_obj.get("contact", "")))
        self.edit_mail.setText(str(self.personnel_obj.get("mail", "")))
        self.edit_adresse.setText(str(self.personnel_obj.get("adresse", "")))
        
        # Checkbox responsable
        est_responsable = self.personnel_obj.get("est_responsable", 0)
        self.check_responsable.setChecked(bool(est_responsable))
        
        date_val = self.personnel_obj.get("date_naissance")
        if date_val:
            self.date_naissance.setDate(self._date_to_qdate(date_val))

    def _date_to_qdate(self, value):
        if isinstance(value, QDate):
            return value
        texte = str(value or "").strip()
        for fmt in ("yyyy-MM-dd", "dd/MM/yyyy"):
            qdate = QDate.fromString(texte, fmt)
            if qdate.isValid():
                return qdate
        return QDate.currentDate()

    def _selectionner_photo(self):
        chemin, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner une photo", "", "Images (*.png *.jpg *.jpeg)"
        )
        if not chemin:
            return
        self.selected_photo_path = chemin
        self._set_photo_preview(chemin)

    def _set_photo_preview(self, chemin):
        c = theme_manager.colors()
        if chemin and os.path.exists(chemin):
            from PySide6.QtGui import QPixmap
            pix = QPixmap(chemin).scaled(110, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.photo_label.setPixmap(pix)
        else:
            self.photo_label.setPixmap(qta.icon("fa5s.user-circle", color=c['text_muted']).pixmap(60, 60))

    def _on_cancel(self):
        self.edit_nom.clear()
        self.edit_prenom.clear()
        self.edit_fonction.clear()
        self.edit_contact.clear()
        self.edit_mail.clear()
        self.edit_adresse.clear()
        self.date_naissance.setDate(QDate.currentDate())
        self.check_responsable.setChecked(False)
        self.radio_nouveau.setChecked(False)
        self.radio_existant.setChecked(False)
        self.edit_mdp.clear()
        self.edit_mdp_existant.clear()
        self.combo_role.setCurrentIndex(0)
        self.combo_role_existant.setCurrentIndex(0)
        self.combo_personnel.setCurrentIndex(0)
        self.selected_photo_path = None
        self.mode_modification = False
        c = theme_manager.colors()
        self.photo_label.setPixmap(qta.icon("fa5s.user-circle", color=c['text_muted']).pixmap(60, 60))

    def _soumettre(self):
        try:
            # Mode 1: Créer compte pour personnel existant
            if self.radio_existant.isChecked():
                code_personnel = self.combo_personnel.currentData()
                if not code_personnel:
                    CustomMessageBox("Erreur", "Veuillez sélectionner un personnel.", False, self).exec()
                    return
                
                mdp = self.edit_mdp_existant.text().strip()
                role = self.combo_role_existant.currentText()
                
                # Créer le compte utilisateur
                result = self.controleur.user_ctrl.gerer_creation(mdp, role, code_personnel)
                if result.get('status') == 'success':
                    code_user = result.get('code', '')
                    CustomMessageBox("Succès", f"Compte utilisateur {code_user} créé avec succès pour le personnel {code_personnel}.", True, self).exec()
                    self._on_cancel()
                    self.personnel_saved.emit()
                else:
                    CustomMessageBox("Erreur", result.get('message', "Impossible de créer le compte utilisateur."), False, self).exec()
                return
            
            # Mode 2: Créer personnel + compte (ou juste personnel)
            data = {
                "nom": self.edit_nom.text().strip(),
                "prenom": self.edit_prenom.text().strip(),
                "date_naissance": self.date_naissance.date().toString("yyyy-MM-dd"),
                "adresse": self.edit_adresse.text().strip(),
                "contact": self.edit_contact.text().strip(),
                "mail": self.edit_mail.text().strip(),
                "fonction": self.edit_fonction.text().strip(),
                "photo_path": self.selected_photo_path,
                "est_responsable": 1 if self.check_responsable.isChecked() else 0,
            }
            
            # Données compte utilisateur si demandé
            if self.radio_nouveau.isChecked():
                data["creer_compte"] = True
                data["mot_de_passe"] = self.edit_mdp.text().strip()
                data["role"] = self.combo_role.currentText()

            statut, msg = self.controleur.valider_champs(data)
            if not statut:
                CustomMessageBox("Erreur", msg, False, self).exec()
                return

            if not self._mail_disponible(data["mail"]):
                CustomMessageBox("Erreur", "Cet email est déjà utilisé par un autre personnel.", False, self).exec()
                return

            if self.personnel_obj:
                statut, msg = self.controleur.modifier_personnel(self.personnel_obj["code"], data)
            else:
                statut, msg = self.controleur.ajouter_personnel(data)

            if statut:
                CustomMessageBox("Succès", msg, True, self).exec()
                self._on_cancel()
                self.personnel_saved.emit()
            else:
                CustomMessageBox("Erreur", msg, False, self).exec()

        except Exception as e:
            CustomMessageBox("Erreur Système", str(e), False, self).exec()

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"""
            PersonnelFormWidget {{
                background-color: {c['bg_main']};
            }}
            QLabel {{
                background: transparent;
                color: {c['text_primary']};
                border: none;
            }}
        """)

        # Carte principale du formulaire
        if hasattr(self, '_form_card'):
            self._form_card.setStyleSheet(f"""
                QFrame {{
                    background-color: {c['bg_card']};
                    border: 1.5px solid {c['border_light']};
                    border-radius: 12px;
                }}
            """)

        # Titres de sections
        _checkbox_style = f"""
            QCheckBox {{
                font-size: 10px; font-weight: 600;
                color: {c['text_secondary']}; background: transparent;
            }}
            QCheckBox::indicator {{
                width: 14px; height: 14px;
                border: 2px solid {c['border']}; border-radius: 4px;
            }}
            QCheckBox::indicator:checked {{
                background: {c['primary']}; border-color: {c['primary']};
            }}
        """
        if hasattr(self, '_form_ico'):
            self._form_ico.setPixmap(qta.icon("fa5s.clipboard-list", color=c['primary']).pixmap(14, 14))
        if hasattr(self, '_form_lbl'):
            self._form_lbl.setStyleSheet(
                f"font-size: 12px; font-weight: bold; color: {c['primary']};"
                " background: transparent; border: none;"
            )
        if hasattr(self, '_compte_ico'):
            self._compte_ico.setPixmap(qta.icon("fa5s.user-lock", color=c['primary']).pixmap(14, 14))
        if hasattr(self, '_compte_lbl'):
            self._compte_lbl.setStyleSheet(
                f"font-size: 12px; font-weight: bold; color: {c['primary']};"
                " background: transparent; border: none;"
            )

        # Checkboxes
        if hasattr(self, 'radio_nouveau'):
            self.radio_nouveau.setStyleSheet(_checkbox_style)
        if hasattr(self, 'radio_existant'):
            self.radio_existant.setStyleSheet(_checkbox_style)
        if hasattr(self, 'check_responsable'):
            self.check_responsable.setStyleSheet(f"""
                QCheckBox {{
                    font-size: 11px; font-weight: 600;
                    color: {c['text_primary']}; background: transparent; border: none;
                }}
                QCheckBox::indicator {{
                    width: 16px; height: 16px;
                    border: 2px solid {c['border']}; border-radius: 4px;
                    background: {c['bg_input']};
                }}
                QCheckBox::indicator:checked {{
                    background: {c['primary']}; border-color: {c['primary']};
                }}
            """)

        # Photo label
        if hasattr(self, 'photo_label'):
            self.photo_label.setStyleSheet(
                f"background: {c['bg_input']}; border: 1px dashed {c['border_focus']}; border-radius: 10px;"
            )

        # Badges de champs
        if hasattr(self, '_field_badges'):
            for badge, ico_lbl, icon_name, color_key in self._field_badges:
                color = c[color_key]
                badge.setStyleSheet(f"background-color: {color}20; border-radius: 6px; border: none;")
                ico_lbl.setPixmap(qta.icon(icon_name, color=color).pixmap(12, 12))

        # Header
        if hasattr(self, 'header_frame'):
            self.header_frame.setStyleSheet(f"""
                background-color: {c['bg_card']};
                border-radius: 12px;
                border: none;
            """)
        if hasattr(self, '_icon_box'):
            self._icon_box.setStyleSheet(f"""
                background-color: {c['bg_input']};
                border-radius: 10px;
                border: 1px solid {c['border_light']};
            """)
        if hasattr(self, 'btn_cancel'):
            self.btn_cancel.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c['bg_card']};
                    color: {c['text_secondary']};
                    border: 1.5px solid {c['border']};
                    border-radius: 10px;
                    font-size: 13px;
                    font-weight: 500;
                }}
                QPushButton:hover {{ background-color: {c['hover']}; }}
            """)
            self.btn_cancel.setIcon(qta.icon("fa5s.times", color=c['text_secondary']))
        if hasattr(self, 'btn_save'):
            self.btn_save.setIcon(qta.icon("fa5s.save", color=c["text_inverse"]))
            self._apply_save_btn_style()
        if hasattr(self, 'btn_photo'):
            self.btn_photo.setIcon(qta.icon("fa5s.camera", color=c['primary']))
            self.btn_photo.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c['bg_card']};
                    color: {c['primary']};
                    border-radius: 8px;
                    border: 1px solid {c['border_light']};
                    font-weight: bold;
                    font-size: 11px;
                }}
                QPushButton:hover {{ background-color: {c['hover']}; }}
            """)

        # ── Re-styler tous les wrappers et champs de saisie ──────────────────
        # Champs principaux (toujours présents)
        if hasattr(self, '_wrap_nom'):
            for wrapper in [self._wrap_nom, self._wrap_prenom, self._wrap_fonction,
                             self._wrap_contact, self._wrap_mail, self._wrap_adresse,
                             self._wrap_date]:
                self._apply_wrapper_style(wrapper)
            for widget in [self.edit_nom, self.edit_prenom, self.edit_fonction,
                            self.edit_contact, self.edit_mail, self.edit_adresse,
                            self.date_naissance]:
                self._clear_widget_style(widget, c)

        # Champs "nouveau compte"
        if hasattr(self, '_wrap_mdp'):
            self._apply_wrapper_style(self._wrap_mdp)
            self._apply_wrapper_style(self._wrap_role)
            self._clear_widget_style(self.edit_mdp, c)
            self._clear_widget_style(self.combo_role, c)

        # Champs "personnel existant"
        if hasattr(self, '_wrap_perso'):
            self._apply_wrapper_style(self._wrap_perso)
            self._apply_wrapper_style(self._wrap_mdp_ex)
            self._apply_wrapper_style(self._wrap_role_ex)
            self._clear_widget_style(self.combo_personnel, c)
            self._clear_widget_style(self.edit_mdp_existant, c)
            self._clear_widget_style(self.combo_role_existant, c)
