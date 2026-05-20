"""
Widget formulaire fournisseur (version non-modale pour onglet)
Design identique à FournisseurFormDialog mais intégré directement dans l'onglet.
"""
import os
import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QTextEdit
)
from models.modele_fournisseur import Fournisseur
from views.shared.message_box import CustomMessageBox
from views.shared.theme_manager import theme_manager


class FournisseurFormWidget(QWidget):
    """
    Widget formulaire fournisseur intégré dans l'onglet 'Nouveau'.
    Même design que FournisseurFormDialog mais sans fenêtre modale.
    """

    fournisseur_saved = Signal()

    def __init__(self, controleur, fournisseur_obj=None, parent=None):
        super().__init__(parent)
        self.controleur = controleur
        self.fournisseur_obj = fournisseur_obj
        self.info_cabinet = self.controleur.get_cabinet_info()

        self._init_ui()
        self._connecter_validations()

        if self.fournisseur_obj:
            self._remplir_champs()

        theme_manager.theme_changed.connect(self.apply_theme)

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

        # Icône truck
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
        ico_lbl.setPixmap(qta.icon("fa5s.truck", color=c['primary']).pixmap(22, 22))
        ico_lbl.setAlignment(Qt.AlignCenter)
        ib_layout.addWidget(ico_lbl, alignment=Qt.AlignCenter)

        # Titre + sous-titre
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        lbl_main = QLabel("Enregistrement d'un fournisseur")
        lbl_main.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {c['text_primary']}; background: transparent; border: none;")
        lbl_sub = QLabel("Saisissez les informations du fournisseur")
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
        label_save = " Enregistrer" if not self.fournisseur_obj else " Mettre à jour"
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
        if isinstance(widget, QLineEdit):
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
        lbl_t = QLabel("Informations du fournisseur")
        lbl_t.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {c['primary']};"
            " background: transparent; border: none;"
        )
        hdr.addWidget(ico)
        hdr.addSpacing(8)
        hdr.addWidget(lbl_t)
        hdr.addStretch()
        vbox.addLayout(hdr)

        # Rangée 1 : Email | Entreprise
        row1 = QHBoxLayout()
        row1.setSpacing(16)
        row1.setAlignment(Qt.AlignTop)

        self.edit_mail = QLineEdit()
        self.edit_mail.setPlaceholderText("Ex: fournisseur@example.com")
        vb_mail, self._wrap_mail = self._make_field(
            "Email", self.edit_mail, "fa5s.envelope", "#3498db"
        )
        self._err_mail = self._err_label()
        vb_mail.addWidget(self._err_mail)
        row1.addWidget(self._field_widget(vb_mail), 1, Qt.AlignTop)

        self.edit_nom = QLineEdit()
        self.edit_nom.setPlaceholderText("Ex: Entreprise ABC")
        vb_nom, self._wrap_nom = self._make_field(
            "Entreprise", self.edit_nom, "fa5s.building", "#1abc9c"
        )
        self._err_nom = self._err_label()
        vb_nom.addWidget(self._err_nom)
        row1.addWidget(self._field_widget(vb_nom), 1, Qt.AlignTop)

        vbox.addLayout(row1)
        vbox.addSpacing(10)

        # Rangée 2 : Téléphone | Adresse
        row2 = QHBoxLayout()
        row2.setSpacing(16)

        self.edit_tel = QLineEdit()
        self.edit_tel.setPlaceholderText("Ex: +224 123 456 789")
        vb_tel, self._wrap_tel = self._make_field(
            "Téléphone", self.edit_tel, "fa5s.phone", "#e67e22"
        )
        self._err_tel = self._err_label()
        vb_tel.addWidget(self._err_tel)
        row2.addWidget(self._field_widget(vb_tel), 1, Qt.AlignTop)

        self.edit_adresse = QLineEdit()
        self.edit_adresse.setPlaceholderText("Ex: Conakry, Guinée")
        vb_adr, self._wrap_adresse = self._make_field(
            "Adresse", self.edit_adresse, "fa5s.map-marker-alt", "#9b59b6"
        )
        self._err_adresse = self._err_label()
        vb_adr.addWidget(self._err_adresse)
        row2.addWidget(self._field_widget(vb_adr), 1, Qt.AlignTop)

        vbox.addLayout(row2)
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
        t2 = QLabel("Veuillez remplir tous les champs obligatoires avant d'enregistrer le fournisseur.")
        t2.setStyleSheet(f"font-size: 11px; color: {c['text_secondary']}; background: transparent;")
        txt.addWidget(t1)
        txt.addWidget(t2)

        hbox.addWidget(ico_frame)
        hbox.addLayout(txt)
        hbox.addStretch()
        parent_layout.addWidget(card)

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

    def _connecter_validations(self):
        self.edit_mail.textChanged.connect(self._valider_email_complet)
        self.edit_nom.textChanged.connect(self._valider_formulaire)
        self.edit_tel.textChanged.connect(self._valider_formulaire)
        self.edit_adresse.textChanged.connect(self._valider_formulaire)

    def _valider_formulaire(self):
        tout_valide = True

        mail = self.edit_mail.text().strip()
        ok, msg = self.controleur._valider_mail(mail)
        if not self.fournisseur_obj and ok:
            existe = self.controleur.get_fournisseur_by_mail(mail)
            if existe:
                ok = False
                msg = "Email déjà utilisé."
        self._set_field_state(self._wrap_mail, self._err_mail, ok, msg, bool(mail))
        if not ok:
            tout_valide = False

        nom = self.edit_nom.text().strip()
        ok, msg = self.controleur._valider_nom(nom)
        self._set_field_state(self._wrap_nom, self._err_nom, ok, msg, bool(nom))
        if not ok:
            tout_valide = False

        tel = self.edit_tel.text().strip()
        ok, msg = self.controleur._valider_telephone(tel)
        self._set_field_state(self._wrap_tel, self._err_tel, ok, msg, bool(tel))
        if not ok:
            tout_valide = False

        adr = self.edit_adresse.text().strip()
        ok, msg = self.controleur._valider_adresse(adr)
        self._set_field_state(self._wrap_adresse, self._err_adresse, ok, msg, bool(adr))
        if not ok:
            tout_valide = False

        self.btn_save.setEnabled(tout_valide)
        self._apply_save_btn_style()

    def _valider_email_complet(self):
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

    def _remplir_champs(self):
        if isinstance(self.fournisseur_obj, dict):
            self.edit_mail.setText(self.fournisseur_obj.get("email_fournisseur", ""))
            self.edit_nom.setText(self.fournisseur_obj.get("nom_entreprise", ""))
            self.edit_tel.setText(self.fournisseur_obj.get("telephone", ""))
            self.edit_adresse.setText(self.fournisseur_obj.get("adresse", ""))
        self.edit_mail.setEnabled(False)

    def _on_cancel(self):
        self.edit_mail.clear()
        self.edit_nom.clear()
        self.edit_tel.clear()
        self.edit_adresse.clear()
        self.edit_mail.setEnabled(True)

    def _soumettre(self):
        try:
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
                CustomMessageBox("Succès", msg, True, self).exec()
                self._on_cancel()
                self.fournisseur_saved.emit()
            else:
                CustomMessageBox("Erreur", msg, False, self).exec()

        except Exception as e:
            CustomMessageBox("Erreur Système", str(e), False, self).exec()

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"""
            QWidget {{
                background: {c['bg_main']};
                color: {c['text_primary']};
            }}
        """)
        if hasattr(self, '_wrap_mail'):
            for w in (self._wrap_mail, self._wrap_nom, self._wrap_tel, self._wrap_adresse):
                self._apply_wrapper_style(w)
        if hasattr(self, 'edit_mail'):
            for w in (self.edit_mail, self.edit_nom, self.edit_tel, self.edit_adresse):
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
