"""
Composant ModernMessageBox - Boîtes de dialogue modernes et élégantes.
Responsabilité : Affichage de messages avec design premium style e-commerce.
Inspiré de CustomMessageBox avec améliorations.
"""

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)


class ModernMessageBox(QDialog):
    """
    Boîte de dialogue moderne compacte et élégante.
    Design inspiré de CustomMessageBox avec améliorations.
    """
    
    # Types de messages
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    QUESTION = "question"
    
    def __init__(self, parent=None, message_type=INFO, title="", message="", 
                 vert_principal="#003f20", show_cancel=False):
        super().__init__(parent)
        
        self.message_type = message_type
        self.vert_principal = vert_principal
        self.result_value = False
        self.show_cancel = show_cancel
        
        # Configuration de base
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        
        # Construction de l'interface
        self._init_ui(title, message)
    
    def _init_ui(self, title, message):
        """Initialise l'interface de la boîte de dialogue."""
        # Layout principal avec marge pour l'ombre
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Le cadre arrondi (Container)
        self.frame = QFrame()
        
        # Couleurs selon le type
        colors = {
            self.SUCCESS: ("#09af61", "#078d4e", "fa5s.check-circle"),
            self.ERROR: ("#e74c3c", "#c0392b", "fa5s.times-circle"),
            self.WARNING: ("#f39c12", "#e67e22", "fa5s.exclamation-triangle"),
            self.INFO: (self.vert_principal, "#005a2e", "fa5s.info-circle"),
            self.QUESTION: ("#3498db", "#2980b9", "fa5s.question-circle")
        }
        
        self.color, self.hover_color, self.icon_name = colors.get(
            self.message_type, colors[self.INFO]
        )
        
        # Style du cadre avec bordure colorée
        self.frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {self.color};
                border-radius: 15px;
            }}
        """)
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(25, 25, 25, 25)
        frame_layout.setSpacing(15)
        
        # Icône
        icon_label = QLabel()
        icon_label.setPixmap(
            qta.icon(self.icon_name, color=self.color).pixmap(50, 50)
        )
        icon_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(icon_label)
        
        # Titre
        title_label = QLabel(title or self._get_default_title())
        title_label.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {self.color};"
        )
        title_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(title_label)
        
        # Message
        message_label = QLabel(message)
        message_label.setStyleSheet("font-size: 14px; color: #333;")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        frame_layout.addWidget(message_label)
        
        # Boutons
        if self.message_type == self.QUESTION or self.show_cancel:
            self._create_buttons_row(frame_layout)
        else:
            self._create_ok_button(frame_layout)
        
        layout.addWidget(self.frame)
    
    def _create_ok_button(self, layout):
        """Crée le bouton OK simple."""
        btn_ok = QPushButton("D'accord")
        btn_ok.setFixedSize(120, 38)
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color};
                color: white;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: {self.hover_color}; }}
        """)
        btn_ok.clicked.connect(self.accept)
        
        # Centrer le bouton
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _create_buttons_row(self, layout):
        """Crée les boutons Oui/Non ou OK/Annuler."""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        # Bouton Annuler/Non
        btn_cancel = QPushButton("Annuler" if self.show_cancel else "Non")
        btn_cancel.setFixedSize(110, 38)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        btn_cancel.clicked.connect(self.reject)
        
        # Bouton OK/Oui
        btn_ok = QPushButton("OK" if self.show_cancel else "Oui")
        btn_ok.setFixedSize(110, 38)
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color};
                color: white;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: {self.hover_color}; }}
        """)
        btn_ok.clicked.connect(self._on_yes_clicked)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
    
    def _on_yes_clicked(self):
        """Callback pour le bouton Oui/OK."""
        self.result_value = True
        self.accept()
    
    def _get_default_title(self):
        """Retourne le titre par défaut selon le type."""
        titles = {
            self.SUCCESS: "Succès",
            self.ERROR: "Erreur",
            self.WARNING: "Attention",
            self.INFO: "Information",
            self.QUESTION: "Confirmation"
        }
        return titles.get(self.message_type, "Message")
    
    # =========================================================================
    # MÉTHODES STATIQUES POUR FACILITER L'UTILISATION
    # =========================================================================
    
    @staticmethod
    def success(parent, title, message, vert_principal="#003f20"):
        """Affiche un message de succès."""
        dialog = ModernMessageBox(
            parent, 
            ModernMessageBox.SUCCESS, 
            title, 
            message, 
            vert_principal
        )
        dialog.exec()
    
    @staticmethod
    def error(parent, title, message, vert_principal="#003f20"):
        """Affiche un message d'erreur."""
        dialog = ModernMessageBox(
            parent, 
            ModernMessageBox.ERROR, 
            title, 
            message, 
            vert_principal
        )
        dialog.exec()
    
    @staticmethod
    def warning(parent, title, message, vert_principal="#003f20"):
        """Affiche un message d'avertissement."""
        dialog = ModernMessageBox(
            parent, 
            ModernMessageBox.WARNING, 
            title, 
            message, 
            vert_principal
        )
        dialog.exec()
    
    @staticmethod
    def info(parent, title, message, vert_principal="#003f20"):
        """Affiche un message d'information."""
        dialog = ModernMessageBox(
            parent, 
            ModernMessageBox.INFO, 
            title, 
            message, 
            vert_principal
        )
        dialog.exec()
    
    @staticmethod
    def question(parent, title, message, vert_principal="#003f20"):
        """Affiche une question avec boutons Oui/Non. Retourne True si Oui."""
        dialog = ModernMessageBox(
            parent, 
            ModernMessageBox.QUESTION, 
            title, 
            message, 
            vert_principal
        )
        result = dialog.exec()
        return result == QDialog.Accepted and dialog.result_value
