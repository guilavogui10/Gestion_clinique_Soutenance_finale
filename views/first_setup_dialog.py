"""
first_setup_dialog.py
-------------------------
Dialogue modal pour créer le tout premier utilisateur administrateur.
Design inspiré de l'interface de connexion.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QGraphicsDropShadowEffect,
    QComboBox,
    QDateEdit,
    QScrollArea,
    QWidget
)
from views.shared.message_box import CustomMessageBox
from controllers.controleur_personnel import ControllerPersonnel

class FirstSetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.controleur = ControllerPersonnel()
        
        self.setWindowTitle("Configuration initiale")
        self.setModal(True)
        self.setFixedSize(500, 650)
        
        # Enlever la barre de titre par défaut
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._init_ui()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 80))
        container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Header
        self._build_header(container_layout)
        
        # Scroll Area pour les champs
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                border: none;
                background: #F1F5F9;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94A3B8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(35, 20, 35, 20)
        self.content_layout.setSpacing(15)
        
        self._build_form()
        
        scroll.setWidget(content_widget)
        container_layout.addWidget(scroll)
        
        # Footer avec boutons
        self._build_footer(container_layout)
        
        main_layout.addWidget(container)

    def _build_header(self, parent_layout):
        header = QFrame()
        header.setFixedHeight(120)
        header.setStyleSheet("""
            QFrame {
                background-color: #3ECFCF;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
            }
        """)
        h_layout = QVBoxLayout(header)
        h_layout.setAlignment(Qt.AlignCenter)
        
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon("fa5s.user-shield", color="white").pixmap(45, 45))
        icon_lbl.setAlignment(Qt.AlignCenter)
        h_layout.addWidget(icon_lbl)
        
        title = QLabel("Création de l'Administrateur")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        h_layout.addWidget(title)
        
        subtitle = QLabel("Ceci est le premier compte du système")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 12px;")
        h_layout.addWidget(subtitle)
        
        parent_layout.addWidget(header)

    def _build_form(self):
        # Informations personnelles
        self._add_section_title("Informations Personnelles", "fa5s.user")
        
        row1 = QHBoxLayout()
        self.edit_nom, frame_nom = self._create_input("Nom", "fa5s.id-card")
        self.edit_prenom, frame_prenom = self._create_input("Prénom", "fa5s.id-card")
        row1.addWidget(frame_nom)
        row1.addWidget(frame_prenom)
        self.content_layout.addLayout(row1)
        
        row2 = QHBoxLayout()
        self.edit_fonction, frame_fonction = self._create_input("Fonction", "fa5s.briefcase")
        self.edit_fonction.setText("Directeur Général") # Par défaut
        self.edit_contact, frame_contact = self._create_input("Contact", "fa5s.phone")
        row2.addWidget(frame_fonction)
        row2.addWidget(frame_contact)
        self.content_layout.addLayout(row2)
        
        self.edit_mail, frame_mail = self._create_input("Email", "fa5s.envelope")
        self.content_layout.addWidget(frame_mail)
        
        self.edit_adresse, frame_adresse = self._create_input("Adresse", "fa5s.map-marker-alt")
        self.content_layout.addWidget(frame_adresse)
        
        # Date de naissance
        date_frame = QFrame()
        date_frame.setFixedHeight(45)
        date_frame.setStyleSheet("QFrame { background-color: #F8F9FA; border: 1px solid #E9ECEF; border-radius: 8px; }")
        date_layout = QHBoxLayout(date_frame)
        date_layout.setContentsMargins(10, 0, 10, 0)
        date_ico = QLabel()
        date_ico.setPixmap(qta.icon("fa5s.calendar-alt", color="#3ECFCF").pixmap(16, 16))
        date_layout.addWidget(date_ico)
        self.date_naissance = QDateEdit()
        self.date_naissance.setCalendarPopup(True)
        self.date_naissance.setDisplayFormat("yyyy-MM-dd")
        self.date_naissance.setDate(QDate.currentDate())
        self.date_naissance.setStyleSheet("border: none; background: transparent; color: #2C3E50;")
        date_layout.addWidget(self.date_naissance, 1)
        self.content_layout.addWidget(date_frame)
        
        self.content_layout.addSpacing(10)
        
        # Compte Utilisateur
        self._add_section_title("Paramètres du Compte", "fa5s.lock")
        
        # Role
        role_frame = QFrame()
        role_frame.setFixedHeight(45)
        role_frame.setStyleSheet("QFrame { background-color: #F8F9FA; border: 1px solid #E9ECEF; border-radius: 8px; }")
        role_layout = QHBoxLayout(role_frame)
        role_layout.setContentsMargins(10, 0, 10, 0)
        role_ico = QLabel()
        role_ico.setPixmap(qta.icon("fa5s.user-tag", color="#3ECFCF").pixmap(16, 16))
        role_layout.addWidget(role_ico)
        
        self.combo_role = QComboBox()
        self.combo_role.addItems(["Directeur Général", "Administrateur"])
        self.combo_role.setStyleSheet("""
            QComboBox { border: none; background: transparent; color: #2C3E50; }
            QComboBox::drop-down { border: none; }
        """)
        role_layout.addWidget(self.combo_role, 1)
        self.content_layout.addWidget(role_frame)
        
        # Mot de passe
        self.edit_mdp, frame_mdp = self._create_input("Mot de passe", "fa5s.key", is_password=True)
        self.content_layout.addWidget(frame_mdp)

    def _add_section_title(self, title, icon_name):
        layout = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(qta.icon(icon_name, color="#3ECFCF").pixmap(14, 14))
        lbl = QLabel(title)
        lbl.setStyleSheet("color: #3ECFCF; font-size: 13px; font-weight: bold;")
        layout.addWidget(ico)
        layout.addWidget(lbl)
        layout.addStretch()
        self.content_layout.addLayout(layout)

    def _create_input(self, placeholder, icon_name, is_password=False):
        frame = QFrame()
        frame.setFixedHeight(45)
        frame.setStyleSheet("QFrame { background-color: #F8F9FA; border: 1px solid #E9ECEF; border-radius: 8px; }")
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)
        
        ico = QLabel()
        ico.setPixmap(qta.icon(icon_name, color="#3ECFCF").pixmap(16, 16))
        layout.addWidget(ico)
        
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setStyleSheet("QLineEdit { border: none; background: transparent; color: #2C3E50; }")
        if is_password:
            inp.setEchoMode(QLineEdit.Password)
            
            # Bouton toggle
            toggle = QPushButton()
            toggle.setCursor(Qt.PointingHandCursor)
            toggle.setIcon(qta.icon("fa5s.eye", color="#95A5A6"))
            toggle.setStyleSheet("border:none; background:transparent;")
            toggle.clicked.connect(lambda: self._toggle_password(inp, toggle))
            layout.addWidget(inp, 1)
            layout.addWidget(toggle)
        else:
            layout.addWidget(inp, 1)
            
        return inp, frame

    def _toggle_password(self, inp, toggle_btn):
        if inp.echoMode() == QLineEdit.Password:
            inp.setEchoMode(QLineEdit.Normal)
            toggle_btn.setIcon(qta.icon("fa5s.eye-slash", color="#3D9B9B"))
        else:
            inp.setEchoMode(QLineEdit.Password)
            toggle_btn.setIcon(qta.icon("fa5s.eye", color="#95A5A6"))

    def _build_footer(self, parent_layout):
        footer = QFrame()
        footer.setStyleSheet("background-color: #F8F9FA; border-bottom-left-radius: 20px; border-bottom-right-radius: 20px;")
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(30, 15, 30, 15)
        
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setFixedHeight(40)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #E2E8F0; color: #64748B; border: none;
                border-radius: 20px; font-weight: bold; padding: 0 20px;
            }
            QPushButton:hover { background-color: #CBD5E1; }
        """)
        btn_cancel.clicked.connect(self.reject)
        f_layout.addWidget(btn_cancel)
        
        f_layout.addStretch()
        
        btn_save = QPushButton("Créer le compte")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setFixedHeight(40)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #3ECFCF; color: white; border: none;
                border-radius: 20px; font-weight: bold; padding: 0 20px;
            }
            QPushButton:hover { background-color: #35B8B8; }
        """)
        btn_save.clicked.connect(self._soumettre)
        f_layout.addWidget(btn_save)
        
        parent_layout.addWidget(footer)

    def _soumettre(self):
        # Valider basiquement les champs obligatoires
        nom = self.edit_nom.text().strip()
        prenom = self.edit_prenom.text().strip()
        mail = self.edit_mail.text().strip()
        mdp = self.edit_mdp.text().strip()
        
        if not nom or not prenom or not mail or not mdp:
            CustomMessageBox("Erreur", "Veuillez remplir tous les champs obligatoires (Nom, Prénom, Email, Mot de passe).", False, self).exec()
            return
            
        if len(mdp) < 6:
            CustomMessageBox("Erreur", "Le mot de passe doit contenir au moins 6 caractères.", False, self).exec()
            return
            
        if "@" not in mail:
            CustomMessageBox("Erreur", "L'adresse email n'est pas valide.", False, self).exec()
            return

        data = {
            "nom": nom,
            "prenom": prenom,
            "date_naissance": self.date_naissance.date().toString("yyyy-MM-dd"),
            "adresse": self.edit_adresse.text().strip(),
            "contact": self.edit_contact.text().strip(),
            "mail": mail,
            "fonction": self.edit_fonction.text().strip(),
            "photo_path": None,
            "est_responsable": 1,
            "creer_compte": True,
            "mot_de_passe": mdp,
            "role": self.combo_role.currentText()
        }
        
        statut, msg = self.controleur.ajouter_personnel(data)
        
        if statut:
            CustomMessageBox("Succès", "Premier compte créé avec succès ! Vous pouvez maintenant vous connecter.", True, self).exec()
            self.accept()
        else:
            CustomMessageBox("Erreur", msg, False, self).exec()
