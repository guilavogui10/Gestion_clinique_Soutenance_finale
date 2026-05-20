"""
Header Section - Service Visite Fidèle
Contient : Titre, sélecteur de session, notifications, avatar utilisateur
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import qtawesome as qta
from views.shared.theme_manager import theme_manager


class HeaderSection(QWidget):
    """Header avec titre, session, notifications et utilisateur"""
    
    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 10)  # Réduit de 20 à 10
        layout.setSpacing(15)  # Réduit de 20 à 15
        
        # Partie gauche : Titre + sous-titre
        left_section = QVBoxLayout()
        left_section.setSpacing(2)  # Réduit de 4 à 2
        
        self.title = QLabel("Service Visite Fidèle")
        self.title.setObjectName("MainTitle")
        font_title = QFont()
        font_title.setPointSize(20)  # Réduit de 24 à 20
        font_title.setBold(True)
        self.title.setFont(font_title)
        
        self.subtitle = QLabel("Gestion et suivi des visites médicales")
        self.subtitle.setObjectName("Subtitle")
        
        left_section.addWidget(self.title)
        left_section.addWidget(self.subtitle)
        
        layout.addLayout(left_section, 3)
        layout.addStretch(2)
        
        # Partie droite : Session + Notifications + Avatar
        right_section = QHBoxLayout()
        right_section.setSpacing(12)  # Réduit de 15 à 12
        
        # Sélecteur de session
        self.session_combo = QComboBox()
        self.session_combo.setObjectName("SessionCombo")
        self.session_combo.setFixedHeight(40)  # Réduit de 45 à 40
        self.session_combo.setMinimumWidth(230)  # Réduit de 250 à 230
        self.session_combo.addItem(
            qta.icon("fa5s.calendar-alt", color=theme_manager.colors()['primary']),
            "Session active\n2024-2025 (En cours)"
        )
        
        # Bouton notifications avec badge
        self.notif_btn = QPushButton()
        self.notif_btn.setObjectName("NotifButton")
        self.notif_btn.setFixedSize(40, 40)  # Réduit de 45 à 40
        self.notif_btn.setText("3")  # Badge count
        
        # Avatar utilisateur
        self.user_btn = QPushButton()
        self.user_btn.setObjectName("UserButton")
        self.user_btn.setFixedSize(40, 40)  # Réduit de 45 à 40
        
        user_info = QVBoxLayout()
        user_info.setSpacing(0)
        self.user_name = QLabel("Dr. Fidèle")
        self.user_name.setObjectName("UserName")
        self.user_role = QLabel("Administrateur")
        self.user_role.setObjectName("UserRole")
        user_info.addWidget(self.user_name, alignment=Qt.AlignRight)
        user_info.addWidget(self.user_role, alignment=Qt.AlignRight)
        
        right_section.addWidget(self.session_combo)
        right_section.addWidget(self.notif_btn)
        right_section.addLayout(user_info)
        right_section.addWidget(self.user_btn)
        
        layout.addLayout(right_section, 2)
    
    def apply_theme(self):
        c = theme_manager.colors()
        
        self.setStyleSheet(f"""
            QLabel#MainTitle {{
                color: {c['text_primary']};
                background: transparent;
                border: none;
            }}
            QLabel#Subtitle {{
                color: {c['text_secondary']};
                font-size: 12px;
                background: transparent;
                border: none;
            }}
            QComboBox#SessionCombo {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 8px 15px;
                color: {c['text_primary']};
                font-size: 13px;
                font-weight: 600;
            }}
            QComboBox#SessionCombo::drop-down {{
                border: none;
                padding-right: 10px;
            }}
            QComboBox#SessionCombo::down-arrow {{
                image: none;
                border: none;
            }}
            QPushButton#NotifButton {{
                background: {c['bg_card']};
                border: 2px solid {c['danger']};
                border-radius: 22px;
                color: {c['danger']};
                font-weight: 800;
                font-size: 12px;
            }}
            QPushButton#NotifButton:hover {{
                background: {c['danger_bg']};
            }}
            QPushButton#UserButton {{
                background: {c['primary']};
                border: 2px solid {c['primary_light']};
                border-radius: 22px;
            }}
            QPushButton#UserButton:hover {{
                background: {c['primary_hover']};
            }}
            QLabel#UserName {{
                color: {c['text_primary']};
                font-size: 13px;
                font-weight: 700;
                background: transparent;
                border: none;
            }}
            QLabel#UserRole {{
                color: {c['text_muted']};
                font-size: 11px;
                background: transparent;
                border: none;
            }}
        """)
        
        # Mise à jour des icônes
        self.notif_btn.setIcon(qta.icon("fa5s.bell", color=c['danger']))
        self.user_btn.setIcon(qta.icon("fa5s.user-circle", color=c['text_inverse']))
