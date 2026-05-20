"""
stat_card.py
------------
Composant carte statistique (KPI) pour la page d'accueil.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtGui import QFont

from views.shared.theme_manager import theme_manager


class StatCard(QFrame):
    """
    Carte statistique affichant un KPI avec icône, valeur et label.
    """
    
    def __init__(self, icon_name: str, value: str, label: str, 
                 color: str = "#3B82F6", parent=None):
        super().__init__(parent)
        self.color = color
        self._setup_ui(icon_name, value, label)
        self._apply_theme()
        theme_manager.theme_changed.connect(self._apply_theme)
    
    def _setup_ui(self, icon_name: str, value: str, label: str):
        """Configure l'interface de la carte."""
        self.setFixedSize(260, 120)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # Icône
        icon_container = QFrame()
        icon_container.setFixedSize(70, 70)
        icon_container.setObjectName("icon_container")
        icon_container.setStyleSheet(f"""
            QFrame#icon_container {{
                background-color: {self.color}20;
                border-radius: 35px;
            }}
        """)
        
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color=self.color).pixmap(QSize(36, 36)))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(icon_label)
        
        layout.addWidget(icon_container)
        
        # Texte (valeur + label)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)
        
        # Valeur
        self.value_label = QLabel(value)
        self.value_label.setObjectName("stat_value")
        font = QFont()
        font.setPointSize(28)
        font.setBold(True)
        self.value_label.setFont(font)
        text_layout.addWidget(self.value_label)
        
        # Label
        label_widget = QLabel(label)
        label_widget.setObjectName("stat_label")
        label_widget.setWordWrap(True)
        text_layout.addWidget(label_widget)
        
        text_layout.addStretch()
        layout.addLayout(text_layout)
    
    def _apply_theme(self):
        """Applique le thème actuel."""
        c = theme_manager.colors()
        
        self.setStyleSheet(f"""
            StatCard {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border_light']};
                border-radius: 12px;
            }}
            QLabel#stat_value {{
                color: {self.color};
                background: transparent;
                border: none;
            }}
            QLabel#stat_label {{
                color: {c['text_secondary']};
                font-size: 13px;
                font-weight: 500;
                background: transparent;
                border: none;
            }}
        """)
    
    def update_value(self, new_value: str):
        """Met à jour la valeur affichée."""
        self.value_label.setText(new_value)
