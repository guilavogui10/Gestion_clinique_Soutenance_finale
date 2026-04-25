"""
Composant ModernPaymentDialog - Dialogue moderne pour la finalisation de facture.
Responsabilité : Saisie du mode de paiement et téléphone avec design compact.
Inspiré de CustomMessageBox.
"""

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QComboBox, QLineEdit
)


class ModernPaymentDialog(QDialog):
    """
    Dialogue moderne compact pour la finalisation de facture.
    Design inspiré de CustomMessageBox.
    """
    
    def __init__(self, parent=None, vert_principal="#003f20"):
        super().__init__(parent)
        
        self.vert_principal = vert_principal
        self.mode_paiement = None
        self.telephone = None
        
        # Configuration de base
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        
        # Construction de l'interface
        self._init_ui()
    
    def _init_ui(self):
        """Initialise l'interface du dialogue."""
        # Layout principal avec marge pour l'ombre
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Le cadre arrondi (Container)
        self.frame = QFrame()
        self.frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {self.vert_principal};
                border-radius: 15px;
            }}
        """)
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(25, 25, 25, 25)
        frame_layout.setSpacing(15)
        
        # Icône
        icon_label = QLabel()
        icon_label.setPixmap(
            qta.icon("fa5s.credit-card", color=self.vert_principal).pixmap(50, 50)
        )
        icon_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(icon_label)
        
        # Titre
        title_label = QLabel("Finalisation de la Facture")
        title_label.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {self.vert_principal};"
        )
        title_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(title_label)
        
        # Sous-titre
        subtitle_label = QLabel("Veuillez compléter les informations")
        subtitle_label.setStyleSheet("font-size: 12px; color: #666;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(subtitle_label)
        
        # Séparateur
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background: #e0e0e0; border: none;")
        line.setFixedHeight(1)
        frame_layout.addWidget(line)
        
        # Mode de paiement
        self._create_payment_mode_section(frame_layout)
        
        # Téléphone
        self._create_phone_section(frame_layout)
        
        # Boutons
        self._create_buttons(frame_layout)
        
        layout.addWidget(self.frame)
    
    def _create_payment_mode_section(self, layout):
        """Crée la section mode de paiement."""
        # Label avec icône
        label_layout = QHBoxLayout()
        label_layout.setSpacing(8)
        
        icon_label = QLabel()
        icon_label.setPixmap(
            qta.icon("fa5s.credit-card", color="#333").pixmap(16, 16)
        )
        
        label = QLabel("Mode de paiement")
        label.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #333;"
        )
        
        label_layout.addWidget(icon_label)
        label_layout.addWidget(label)
        label_layout.addStretch()
        
        layout.addLayout(label_layout)
        
        # Combo
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Espèces", "Chèque", "Virement", "Mobile Money"])
        self.combo_mode.setFixedHeight(40)
        self.combo_mode.setStyleSheet(f"""
            QComboBox {{
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding-left: 12px;
                background: white;
                font-size: 13px;
                color: #333;
            }}
            QComboBox:focus {{
                border: 2px solid {self.vert_principal};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background: white;
                selection-background-color: {self.vert_principal};
                selection-color: white;
            }}
        """)
        layout.addWidget(self.combo_mode)
    
    def _create_phone_section(self, layout):
        """Crée la section téléphone."""
        # Label avec icône
        label_layout = QHBoxLayout()
        label_layout.setSpacing(8)
        
        icon_label = QLabel()
        icon_label.setPixmap(
            qta.icon("fa5s.phone", color="#333").pixmap(16, 16)
        )
        
        label = QLabel("Numéro de téléphone")
        label.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #333;"
        )
        
        label_layout.addWidget(icon_label)
        label_layout.addWidget(label)
        label_layout.addStretch()
        
        layout.addLayout(label_layout)
        
        # Input
        self.input_tel = QLineEdit()
        self.input_tel.setPlaceholderText("Ex: 628123456")
        self.input_tel.setFixedHeight(40)
        self.input_tel.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding-left: 12px;
                background: white;
                font-size: 13px;
                color: #333;
            }}
            QLineEdit:focus {{
                border: 2px solid {self.vert_principal};
            }}
            QLineEdit::placeholder {{
                color: #999;
            }}
        """)
        
        # Validation en temps réel
        self.input_tel.textChanged.connect(self._validate_phone)
        
        layout.addWidget(self.input_tel)
        
        # Message d'aide avec icône
        help_layout = QHBoxLayout()
        help_layout.setSpacing(6)
        
        help_icon = QLabel()
        help_icon.setPixmap(
            qta.icon("fa5s.info-circle", color="#999").pixmap(12, 12)
        )
        
        help_label = QLabel("Entrez 9 chiffres sans indicatif")
        help_label.setStyleSheet(
            "font-size: 11px; color: #999; font-style: italic;"
        )
        
        help_layout.addWidget(help_icon)
        help_layout.addWidget(help_label)
        help_layout.addStretch()
        
        layout.addLayout(help_layout)
    
    def _validate_phone(self, text):
        """Valide le numéro de téléphone en temps réel."""
        # Garder seulement les chiffres
        cleaned = ''.join(filter(str.isdigit, text))
        
        if cleaned != text:
            self.input_tel.blockSignals(True)
            self.input_tel.setText(cleaned)
            self.input_tel.blockSignals(False)
    
    def _create_buttons(self, layout):
        """Crée les boutons Annuler et Valider."""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        # Bouton Annuler
        btn_cancel = QPushButton("Annuler")
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
        
        # Bouton Valider
        btn_validate = QPushButton("Valider")
        btn_validate.setFixedSize(110, 38)
        btn_validate.setCursor(Qt.PointingHandCursor)
        btn_validate.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.vert_principal};
                color: white;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: #005a2e; }}
        """)
        btn_validate.clicked.connect(self._on_validate)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_validate)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
    
    def _on_validate(self):
        """Validation et fermeture du dialogue."""
        # Récupérer les valeurs
        self.mode_paiement = self.combo_mode.currentText().lower().replace("è", "e")
        self.telephone = self.input_tel.text().strip()
        
        # Validation basique
        if not self.telephone:
            from views.shared.message_box import CustomMessageBox
            CustomMessageBox.warning(
                self,
                "Attention",
                "Veuillez entrer un numéro de téléphone",
                self.vert_principal
            )
            return
        
        if len(self.telephone) != 9:
            from views.shared.message_box import CustomMessageBox
            CustomMessageBox.warning(
                self,
                "Attention",
                "Le numéro de téléphone doit contenir exactement 9 chiffres",
                self.vert_principal
            )
            return
        
        # Accepter le dialogue
        self.accept()
    
    def get_data(self):
        """Retourne les données saisies."""
        return {
            'mode_paiement': self.mode_paiement,
            'telephone': self.telephone
        }
