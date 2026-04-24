from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
import qtawesome as qta
import os
from models.modele_fournisseur import Fournisseur
from views.shared.message_box import CustomMessageBox
from views.shared.theme_manager import theme_manager


class FournisseurFormDialog(QDialog):
    def __init__(self, controleur, fournisseur_obj=None, parent=None):
        super().__init__(parent)
        self.controleur = controleur
        self.fournisseur_obj = fournisseur_obj
        self.info_cabinet = self.controleur.get_cabinet_info()

        # Fenetre
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(550, 560)

        self.init_ui()
        if self.fournisseur_obj:
            self.remplir_champs()
        theme_manager.theme_changed.connect(self.apply_theme)

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.container = QFrame()
        self.container.setObjectName("MainContainer")

        self._apply_container_style()

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

        logo_path = self.info_cabinet.get('logo_url')
        if logo_path and os.path.exists(logo_path):
            logo_lbl = QLabel()
            logo_lbl.setStyleSheet("background: transparent;")
            pix = QPixmap(logo_path).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            logo_lbl.setAlignment(Qt.AlignCenter)
            header.addWidget(logo_lbl)

        header_container.addLayout(header)

        title_form = QLabel("FORMULAIRE FOURNISSEUR")
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

        # Form
        form_grid = QVBoxLayout()
        form_grid.setSpacing(15)

        row1 = QHBoxLayout()
        self.edit_mail = self.add_field(row1, "Email", "fa5s.envelope")
        self.edit_nom = self.add_field(row1, "Entreprise", "fa5s.building")
        form_grid.addLayout(row1)

        row2 = QHBoxLayout()
        self.edit_tel = self.add_field(row2, "Telephone", "fa5s.phone")
        self.edit_adresse = self.add_field(row2, "Adresse", "fa5s.map-marker-alt")
        form_grid.addLayout(row2)

        body.addLayout(form_grid)
        body.addSpacing(20)

        # Validation temps reel
        self.edit_mail.textChanged.connect(self.valider_email_complet)
        self.edit_nom.textChanged.connect(
            lambda: self.appliquer_validation(self.edit_nom, self.controleur._valider_nom, self.edit_nom.text())
        )
        self.edit_tel.textChanged.connect(
            lambda: self.appliquer_validation(self.edit_tel, self.controleur._valider_telephone, self.edit_tel.text())
        )
        self.edit_adresse.textChanged.connect(
            lambda: self.appliquer_validation(self.edit_adresse, self.controleur._valider_adresse, self.edit_adresse.text())
        )

        # Boutons
        actions = QHBoxLayout()

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setObjectName("CancelBtn")
        self.btn_cancel.setFixedHeight(45)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Enregistrer")
        self.btn_save.setObjectName("SaveBtn")
        self.btn_save.setFixedHeight(45)
        self.btn_save.setIcon(qta.icon("fa5s.check", color="white"))

        est_valide = True if self.fournisseur_obj else False
        self.btn_save.setEnabled(est_valide)
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
            QLineEdit {{
                padding: 10px; border: 1px solid {c['border']}; border-radius: 10px;
                background-color: {c['bg_input']}; color: {c['text_primary']}; font-size: 14px;
            }}
            QLineEdit:focus {{ border: 2px solid {c['border_focus']}; background-color: {c['bg_card']}; }}
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
        vbox.setSpacing(2)
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

        err_lbl = QLabel("")
        err_lbl.setStyleSheet(f"color: {c['danger']}; font-size: 10px; font-style: italic;")
        err_lbl.setVisible(False)
        vbox.addWidget(err_lbl)

        edit.error_label = err_lbl
        layout.addLayout(vbox)
        return edit

    def _get_obj_value(self, key):
        if self.fournisseur_obj is None:
            return ""
        if isinstance(self.fournisseur_obj, dict):
            return self.fournisseur_obj.get(key, "")
        getter_map = {
            "email_fournisseur": "get_mail_fournisseur",
            "nom_entreprise": "get_nom",
            "telephone": "get_telephone",
            "adresse": "get_adresse",
        }
        getter = getter_map.get(key)
        if getter and hasattr(self.fournisseur_obj, getter):
            return getattr(self.fournisseur_obj, getter)()
        return ""

    def remplir_champs(self):
        self.btn_save.setText("Mettre a jour")
        self.edit_mail.setText(self._get_obj_value("email_fournisseur"))
        self.edit_nom.setText(self._get_obj_value("nom_entreprise"))
        self.edit_tel.setText(self._get_obj_value("telephone"))
        self.edit_adresse.setText(self._get_obj_value("adresse"))
        self.edit_mail.setEnabled(False)

    def soumettre(self):
        donnees = {
            "email_fournisseur": self.edit_mail.text().strip(),
            "nom_entreprise": self.edit_nom.text().strip(),
            "telephone": self.edit_tel.text().strip(),
            "adresse": self.edit_adresse.text().strip()
        }

        if self.fournisseur_obj:
            ok, msg = self.controleur.update_fournisseur(donnees)
        else:
            ok, msg = self.controleur.add_new_fournisseur(donnees)

        if ok:
            self.show_message(True, "Le fournisseur a ete enregistre avec succes.")
            self.accept()
        else:
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
            widget.setStyleSheet(f"border: 2px solid {cv['border_focus']}; background-color: {cv['bg_card']}; color: {cv['text_primary']};")
            widget.error_label.setVisible(False)

        self.verifier_formulaire_complet()
        return valide

    def valider_email_complet(self):
        mail = self.edit_mail.text().strip()
        valide, msg = self.controleur._valider_mail(mail)
        if valide and not self.fournisseur_obj:
            existe = self.controleur.get_fournisseur_by_mail(mail)
            if existe:
                valide = False
                msg = "Email deja utilise."
        self.appliquer_validation(self.edit_mail, lambda x: (valide, msg), mail)

    def verifier_formulaire_complet(self):
        v_mail, _ = self.controleur._valider_mail(self.edit_mail.text().strip())
        v_nom, _ = self.controleur._valider_nom(self.edit_nom.text().strip())
        v_tel, _ = self.controleur._valider_telephone(self.edit_tel.text().strip())
        v_adr, _ = self.controleur._valider_adresse(self.edit_adresse.text().strip())

        mail_dispo = True
        if not self.fournisseur_obj:
            if v_mail and self.controleur.get_fournisseur_by_mail(self.edit_mail.text().strip()):
                mail_dispo = False

        tous_valides = all([v_mail, v_nom, v_tel, v_adr]) and mail_dispo
        self.btn_save.setEnabled(tous_valides)

    def show_message(self, reussite, message):
        titre = "Succes" if reussite else "Information / Erreur"
        dialog = CustomMessageBox(titre, message, is_success=reussite, parent=self)
        dialog.exec()
