"""
service_card.py
---------------
Composant carte de service pour la page d'accueil.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtGui import QCursor

from views.shared.theme_manager import theme_manager


class ServiceCard(QFrame):
    """
    Carte de service cliquable avec icône, titre, description et lien.
    """
    
    clicked = Signal(str)  # Émet le nom du service cliqué
    
    def __init__(self, icon_name: str, title: str, description: str, 
                 color: str = "#3B82F6", parent=None):
        super().__init__(parent)
        self.service_name = title
        self.color = color
        self._setup_ui(icon_name, title, description)
        self._apply_theme()
        theme_manager.theme_changed.connect(self._apply_theme)
    
    def _setup_ui(self, icon_name: str, title: str, description: str):
        """Configure l'interface de la carte."""
        self.setFixedSize(200, 180)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 18)
        layout.setSpacing(10)
        
        # Icône (sans fond)
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color=self.color).pixmap(QSize(40, 40)))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        layout.addSpacing(3)
        
        # Titre
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        title_label.setObjectName("service_title")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setObjectName("service_desc")
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        # Lien "En savoir plus"
        link_layout = QHBoxLayout()
        link_layout.addStretch()
        
        link_label = QLabel("En savoir plus")
        link_label.setObjectName("service_link")
        link_layout.addWidget(link_label)
        
        arrow_label = QLabel()
        arrow_label.setPixmap(qta.icon('fa5s.arrow-right', color=self.color).pixmap(QSize(12, 12)))
        link_layout.addWidget(arrow_label)
        
        link_layout.addStretch()
        layout.addLayout(link_layout)
    
    def _apply_theme(self):
        """Applique le thème actuel."""
        c = theme_manager.colors()
        
        self.setStyleSheet(f"""
            ServiceCard {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border_light']};
                border-radius: 12px;
            }}
            ServiceCard:hover {{
                background-color: {c['hover']};
                border: 2px solid {self.color};
            }}
            QLabel#service_title {{
                color: {c['text_primary']};
                font-size: 16px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
            QLabel#service_desc {{
                color: {c['text_secondary']};
                font-size: 12px;
                background: transparent;
                border: none;
            }}
            QLabel#service_link {{
                color: {self.color};
                font-size: 13px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
    
    def mousePressEvent(self, event):
        """Gère le clic sur la carte."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.service_name)
        super().mousePressEvent(event)
