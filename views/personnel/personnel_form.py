import os
import qtawesome as qta
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QPixmap, QGuiApplication
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QGraphicsDropShadowEffect, QFileDialog, QDateEdit
)

from views.shared.message_box import CustomMessageBox
from views.shared.theme_manager import theme_manager


class PersonnelFormDialog(QDialog):
    def __init__(self, controleur, personnel_obj=None, parent=None):
        super().__init__(parent)
        self.controleur = controleur
        self.personnel_obj = personnel_obj or {}
        self.info_cabinet = (
            self.controleur.get_cabinet_info()
            if hasattr(self.controleur, "get_cabinet_info") else {}
        )
        self.selected_photo_path = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._apply_dialog_size()

        self.init_ui()
        if self.personnel_obj:
            self.remplir_champs()
        self.verifier_formulaire_complet()
        theme_manager.theme_changed.connect(self.apply_theme)

    def _apply_dialog_size(self):
        width, height = 740, 560
        screen = QGuiApplication.primaryScreen()
        if screen:
            available = screen.availableGeometry()
            width = min(width, max(660, available.width() - 90))
            height = min(height, max(500, available.height() - 120))
        self.setFixedSize(width, height)

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.container = QFrame()
        self.container.setObjectName("MainContainer")

        self._apply_container_style()

    def _apply_container_style(self):
        c = theme_manager.colors()
        self.container.setStyleSheet(f"""
            QFrame#MainContainer {{
                background-color: {c['bg_card']};
                border-radius: 22px;
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
            QLineEdit, QDateEdit {{
                padding: 10px;
                border: 1px solid {c['border']};
                border-radius: 10px;
                background-color: {c['bg_input']};
                color: {c['text_primary']};
                font-size: 14px;
            }}
            QLineEdit:focus, QDateEdit:focus {{
                border: 2px solid {c['border_focus']};
                background-color: {c['bg_card']};
            }}
            QPushButton#SaveBtn {{
                background-color: {c['primary']};
                color: {c['text_inverse']};
                border-radius: 10px; font-weight: bold; font-size: 15px;
            }}
            QPushButton#SaveBtn:hover {{ background-color: {c['primary']}; opacity: 0.9; }}
            QPushButton#SaveBtn:disabled {{
                background-color: {c['border_light']};
                color: {c['text_muted']};
            }}
            QPushButton#CancelBtn {{
                background-color: {c['bg_main']};
                color: {c['text_secondary']};
                border-radius: 10px; border: 1px solid {c['border']};
            }}
            QPushButton#CancelBtn:hover {{ background-color: {c['hover']}; }}
            QPushButton#PhotoBtn {{
                background-color: {c['bg_main']};
                color: {c['primary']};
                border-radius: 10px;
                border: 1px solid {c['border_light']};
                font-weight: bold;
            }}
            QPushButton#PhotoBtn:hover {{ background-color: {c['hover']}; }}
        """)

    def apply_theme(self):
        c = theme_manager.colors()
        self._apply_container_style()
        if hasattr(self, '_header_card'):
            self._header_card.setStyleSheet(f"QFrame {{ border: none; border-top-left-radius: 22px; border-top-right-radius: 22px; background: {c['bg_card']}; }}")
        if hasattr(self, '_title_form'):
            self._title_form.setStyleSheet(f"color: {c['primary']}; font-size: 21px; font-weight: 900; letter-spacing: 0.8px;")
        if hasattr(self, '_accent'):
            self._accent.setStyleSheet(f"background: {c['border_focus']}; border: none; border-radius: 0px;")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 18)
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

        logo_path = self.info_cabinet.get("logo_url")
        if logo_path and os.path.exists(logo_path):
            logo_lbl = QLabel()
            pix = QPixmap(logo_path).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            logo_lbl.setAlignment(Qt.AlignCenter)
            header.addWidget(logo_lbl)

        header_container.addLayout(header)

        title_form = QLabel("FORMULAIRE PERSONNEL")
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
        accent.setStyleSheet(
            f"background: {c['border_focus']}; border: none; border-radius: 0px;"
        )
        self._accent = accent
        header_container.addWidget(accent)

        layout.addWidget(header_card)

        body = QVBoxLayout()
        body.setContentsMargins(26, 12, 26, 0)
        body.setSpacing(0)

        form_grid = QHBoxLayout()
        form_grid.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(10)

        row1 = QHBoxLayout()
        self.edit_nom = self.add_field(row1, "Nom", "fa5s.user")
        self.edit_prenom = self.add_field(row1, "Prenom", "fa5s.user")
        left.addLayout(row1)

        row2 = QHBoxLayout()
        self.edit_fonction = self.add_field(row2, "Fonction", "fa5s.briefcase")
        self.edit_contact = self.add_field(row2, "Contact", "fa5s.phone")
        left.addLayout(row2)

        row3 = QHBoxLayout()
        self.edit_mail = self.add_field(row3, "Email", "fa5s.envelope")
        self.edit_adresse = self.add_field(row3, "Adresse", "fa5s.map-marker-alt")
        left.addLayout(row3)

        date_box = QVBoxLayout()
        date_box.setSpacing(2)
        lbl_date = QLabel("Date de naissance")
        lbl_date.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']};")
        date_box.addWidget(lbl_date)

        self.date_naissance = QDateEdit()
        self.date_naissance.setDisplayFormat("yyyy-MM-dd")
        self.date_naissance.setCalendarPopup(True)
        self.date_naissance.setDate(QDate.currentDate())
        self.date_naissance.setFixedHeight(40)
        date_box.addWidget(self.date_naissance)

        self.date_error = QLabel("")
        self.date_error.setStyleSheet(f"color: {c['danger']}; font-size: 10px; font-style: italic;")
        self.date_error.setVisible(False)
        date_box.addWidget(self.date_error)
        left.addLayout(date_box)

        form_grid.addLayout(left, 2)

        right = QVBoxLayout()
        right.setSpacing(10)

        right.addWidget(self._photo_card(), 1)

        self.btn_photo = QPushButton(qta.icon("fa5s.camera", color="#1384B6"), " Choisir une photo")
        self.btn_photo.setObjectName("PhotoBtn")
        self.btn_photo.setFixedHeight(42)
        self.btn_photo.clicked.connect(self.selectionner_photo)
        right.addWidget(self.btn_photo)

        form_grid.addLayout(right, 1)

        body.addLayout(form_grid)
        body.addSpacing(14)

        self.edit_nom.textChanged.connect(
            lambda: self.appliquer_validation(self.edit_nom, self.controleur._valider_nom_prenom_fonction, self.edit_nom.text())
        )
        self.edit_prenom.textChanged.connect(
            lambda: self.appliquer_validation(self.edit_prenom, self.controleur._valider_nom_prenom_fonction, self.edit_prenom.text())
        )
        self.edit_fonction.textChanged.connect(
            lambda: self.appliquer_validation(self.edit_fonction, self.controleur._valider_nom_prenom_fonction, self.edit_fonction.text())
        )
        self.edit_contact.textChanged.connect(
            lambda: self.appliquer_validation(self.edit_contact, self.controleur._valider_contact, self.edit_contact.text())
        )
        self.edit_mail.textChanged.connect(self.valider_email_complet)
        self.edit_adresse.textChanged.connect(
            lambda: self.appliquer_validation(self.edit_adresse, self.controleur._valider_adresse, self.edit_adresse.text())
        )
        self.date_naissance.dateChanged.connect(self.valider_date)

        actions = QHBoxLayout()

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setObjectName("CancelBtn")
        self.btn_cancel.setFixedHeight(45)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Enregistrer")
        self.btn_save.setObjectName("SaveBtn")
        self.btn_save.setFixedHeight(45)
        self.btn_save.setIcon(qta.icon("fa5s.check", color="white"))
        self.btn_save.clicked.connect(self.soumettre)

        actions.addWidget(self.btn_cancel, 1)
        actions.addWidget(self.btn_save, 2)
        body.addLayout(actions)

        layout.addLayout(body)

        self.main_layout.addWidget(self.container)

    def _photo_card(self):
        c = theme_manager.colors()
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {c['bg_main']};
                border-radius: 16px;
                border: 1px solid {c['border']};
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        title = QLabel("Photo du personnel")
        title.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {c['text_primary']};")
        layout.addWidget(title)

        self.photo_label = QLabel()
        self.photo_label.setFixedSize(180, 210)
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setStyleSheet(
            f"background: {c['bg_card']}; border: 1px dashed {c['border_focus']}; border-radius: 12px;"
        )
        self.photo_label.setPixmap(qta.icon("fa5s.user-circle", color=c['text_muted']).pixmap(96, 96))
        layout.addWidget(self.photo_label, 0, Qt.AlignCenter)

        self.photo_hint = QLabel("Photo optionnelle")
        self.photo_hint.setAlignment(Qt.AlignCenter)
        self.photo_hint.setStyleSheet(f"font-size: 11px; color: {c['text_muted']};")
        layout.addWidget(self.photo_hint)

        return card

    def add_field(self, layout, label_text, icon_name):
        c = theme_manager.colors()
        vbox = QVBoxLayout()
        vbox.setSpacing(2)

        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']};")
        vbox.addWidget(lbl)

        edit = QLineEdit()
        edit.setPlaceholderText(f"Entrez le {label_text.lower()}...")
        edit.setFixedHeight(38)
        icon = qta.icon(icon_name, color=c['primary'])
        edit.addAction(icon, QLineEdit.LeadingPosition)
        vbox.addWidget(edit)

        err_lbl = QLabel("")
        err_lbl.setStyleSheet(f"color: {c['danger']}; font-size: 10px; font-style: italic;")
        err_lbl.setVisible(False)
        vbox.addWidget(err_lbl)

        edit.error_label = err_lbl
        layout.addLayout(vbox)
        return edit

    def _date_to_qdate(self, value):
        if isinstance(value, QDate):
            return value
        texte = str(value or "").strip()
        for fmt in ("yyyy-MM-dd", "dd/MM/yyyy"):
            qdate = QDate.fromString(texte, fmt)
            if qdate.isValid():
                return qdate
        return QDate.currentDate()

    def _photo_existante_absolue(self):
        photo_name = self.personnel_obj.get("photo_path")
        if not photo_name:
            return None
        script_dir = os.path.dirname(__file__)
        photo_path = os.path.normpath(
            os.path.join(script_dir, "..", "..", "connexion", "image", photo_name)
        )
        return photo_path if os.path.exists(photo_path) else None

    def _set_photo_preview(self, chemin):
        if chemin and os.path.exists(chemin):
            pix = QPixmap(chemin).scaled(170, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.photo_label.setPixmap(pix)
            self.photo_hint.setText(os.path.basename(chemin))
        else:
            self.photo_label.setPixmap(qta.icon("fa5s.user-circle", color="#A8B7C6").pixmap(96, 96))
            self.photo_hint.setText("Photo optionnelle")

    def remplir_champs(self):
        self.btn_save.setText("Mettre a jour")
        self.edit_nom.setText(str(self.personnel_obj.get("nom", "")))
        self.edit_prenom.setText(str(self.personnel_obj.get("prenom", "")))
        self.edit_fonction.setText(str(self.personnel_obj.get("fonction", "")))
        self.edit_contact.setText(str(self.personnel_obj.get("contact", "")))
        self.edit_mail.setText(str(self.personnel_obj.get("mail", "")))
        self.edit_adresse.setText(str(self.personnel_obj.get("adresse", "")))
        self.date_naissance.setDate(self._date_to_qdate(self.personnel_obj.get("date_naissance")))
        self._set_photo_preview(self._photo_existante_absolue())

    def selectionner_photo(self):
        chemin, _ = QFileDialog.getOpenFileName(
            self, "Selectionner une photo", "", "Images (*.png *.jpg *.jpeg)"
        )
        if not chemin:
            return
        self.selected_photo_path = chemin
        self._set_photo_preview(chemin)
        self.verifier_formulaire_complet()

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
            widget.setStyleSheet(f"border: 2px solid {cv['border_focus']}; background-color: {cv['bg_card']}; color: {cv['text_primary']};")
            widget.error_label.setVisible(False)

        self.verifier_formulaire_complet()
        return valide

    def _mail_disponible(self, mail):
        mail_normalise = (mail or "").strip().lower()
        if not mail_normalise:
            return False
        code_courant = self.personnel_obj.get("code") if self.personnel_obj else None
        for personnel in self.controleur.get_all_personnels():
            if (personnel.get("mail", "").strip().lower() == mail_normalise and
                    personnel.get("code") != code_courant):
                return False
        return True

    def valider_email_complet(self):
        mail = self.edit_mail.text().strip()
        valide, msg = self.controleur._valider_email(mail)
        if valide and not self._mail_disponible(mail):
            valide = False
            msg = "Email deja utilise."
        self.appliquer_validation(self.edit_mail, lambda x: (valide, msg), mail)

    def valider_date(self, revalider_formulaire=True):
        texte = self.date_naissance.date().toString("yyyy-MM-dd")
        valide, message = self.controleur._valider_date(texte)
        cv = theme_manager.colors()
        if not valide:
            self.date_naissance.setStyleSheet(f"border: 1px solid {cv['danger']}; background-color: {cv['danger_bg']};")
            self.date_error.setText(message)
            self.date_error.setVisible(True)
        else:
            self.date_naissance.setStyleSheet(f"border: 2px solid {cv['border_focus']}; background-color: {cv['bg_card']}; color: {cv['text_primary']};")
            self.date_error.setVisible(False)
        if revalider_formulaire:
            self.verifier_formulaire_complet()
        return valide

    def verifier_formulaire_complet(self):
        v_nom, _ = self.controleur._valider_nom_prenom_fonction(self.edit_nom.text().strip())
        v_prenom, _ = self.controleur._valider_nom_prenom_fonction(self.edit_prenom.text().strip())
        v_fonction, _ = self.controleur._valider_nom_prenom_fonction(self.edit_fonction.text().strip())
        v_contact, _ = self.controleur._valider_contact(self.edit_contact.text().strip())
        v_mail, _ = self.controleur._valider_email(self.edit_mail.text().strip())
        v_adresse, _ = self.controleur._valider_adresse(self.edit_adresse.text().strip())
        v_date = self.valider_date(revalider_formulaire=False)
        mail_dispo = self._mail_disponible(self.edit_mail.text().strip())

        tous_valides = all([
            v_nom, v_prenom, v_fonction, v_contact, v_mail, v_adresse, v_date, mail_dispo
        ])
        self.btn_save.setEnabled(tous_valides)

    def soumettre(self):
        data = {
            "nom": self.edit_nom.text().strip(),
            "prenom": self.edit_prenom.text().strip(),
            "date_naissance": self.date_naissance.date().toString("yyyy-MM-dd"),
            "adresse": self.edit_adresse.text().strip(),
            "contact": self.edit_contact.text().strip(),
            "mail": self.edit_mail.text().strip(),
            "fonction": self.edit_fonction.text().strip(),
            "photo_path": self.selected_photo_path,
        }

        statut, msg = self.controleur.valider_champs(data)
        if not statut:
            self.show_message(False, msg)
            return

        if not self._mail_disponible(data["mail"]):
            self.show_message(False, "Cet email est deja utilise par un autre personnel.")
            return

        if self.personnel_obj:
            statut, msg = self.controleur.modifier_personnel(self.personnel_obj["code"], data)
        else:
            statut, msg = self.controleur.ajouter_personnel(data)

        self.show_message(statut, msg)
        if statut:
            self.accept()

    def show_message(self, reussite, message):
        titre = "Succes" if reussite else "Information / Erreur"
        dialog = CustomMessageBox(titre, message, is_success=reussite, parent=self)
        dialog.exec()
