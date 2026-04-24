from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QFrame, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QColor
import qtawesome as qta

class LoginView(QWidget):
    # Signal envoyé à la MainWindow quand la connexion réussit
    login_success = Signal(dict)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 1. Background (Image de fond comme dans ton CTk)
        self.bg_label = QLabel(self)
        pixmap = QPixmap("image/background1.png") # Chemin vers ton image
        self.bg_label.setPixmap(pixmap.scaled(1920, 1080, Qt.KeepAspectRatioByExpanding))
        self.bg_label.setScaledContents(True)

        # 2. Layout Principal
        main_layout = QHBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        # 3. La "Carte" de connexion (Le cadre blanc central)
        self.card = QFrame()
        self.card.setFixedSize(450, 550)
        self.card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
            }
            QLabel { color: #2c3e50; }
        """)
        
        # Effet d'ombre (Senior touch)
        shadow = QGraphicsDropShadowEffect(blurRadius=25, xOffset=0, yOffset=10)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(15)

        # --- TITRE ---
        title = QLabel("BIENVENUE")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #006633; margin-bottom: 10px;")
        card_layout.addWidget(title)

        subtitle = QLabel("Accédez à votre espace de travail")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 13px; color: #7f8c8d; margin-bottom: 20px;")
        card_layout.addWidget(subtitle)

        # --- CHAMPS DE SAISIE ---
        # Service (Rôles)
        card_layout.addWidget(QLabel("Service / Rôle"))
        self.combo_role = QComboBox()
        self.combo_role.addItems(["DG", "caissiere", "laboratin", "chirurgien"])
        self.combo_role.setFixedHeight(40)
        card_layout.addWidget(self.combo_role)

        # Mot de passe
        card_layout.addWidget(QLabel("Mot de passe"))
        pass_layout = QHBoxLayout()
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.Password)
        self.input_password.setFixedHeight(40)
        self.input_password.setPlaceholderText("••••••••")
        
        # Icône avec QtAwesome
        eye_icon = qta.icon('fa5s.eye', color='#7f8c8d')
        self.btn_show_pass = QPushButton(eye_icon, "")
        self.btn_show_pass.setFixedWidth(40)
        self.btn_show_pass.setCursor(Qt.PointingHandCursor)
        self.btn_show_pass.clicked.connect(self.toggle_password)
        
        pass_layout.addWidget(self.input_password)
        pass_layout.addWidget(self.btn_show_pass)
        card_layout.addLayout(pass_layout)

        # --- BOUTON LOGIN ---
        card_layout.addSpacing(20)
        self.btn_login = QPushButton("SE CONNECTER")
        self.btn_login.setFixedHeight(45)
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setStyleSheet("""
            QPushButton {
                background-color: #006633;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #004d26; }
        """)
        self.btn_login.clicked.connect(self.handle_login)
        card_layout.addWidget(self.btn_login)

        main_layout.addWidget(self.card)
        self.setLayout(main_layout)

    def toggle_password(self):
        if self.input_password.echoMode() == QLineEdit.Password:
            self.input_password.setEchoMode(QLineEdit.Normal)
            self.btn_show_pass.setIcon(qta.icon('fa5s.eye-slash', color='#006633'))
        else:
            self.input_password.setEchoMode(QLineEdit.Password)
            self.btn_show_pass.setIcon(qta.icon('fa5s.eye', color='#7f8c8d'))

    def handle_login(self):
        # Ici on appellera ton UserController
        role = self.combo_role.currentText()
        pwd = self.input_password.text()
        print(f"Tentative de connexion : {role}")
        # Simulation de succès (on branchera ton DAO ici)
        self.login_success.emit({"role": role, "nom": "Docteur"})

    def resizeEvent(self, event):
        # Redimensionne le background pour qu'il suive la fenêtre
        self.bg_label.resize(self.size())