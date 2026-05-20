"""
badge_confiance.py
------------------
Composant badge de confiance pour la section hero.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel

from views.shared.theme_manager import theme_manager


class BadgeConfiance(QFrame):
    """
    Badge de confiance avec icône et texte (ex: "Soins de qualité").
    """
    
    def __init__(self, icon_name: str, title: str, subtitle: str, 
                 color: str = "#3B82F6", parent=None):
        super().__init__(parent)
        self.color = color
        self._setup_ui(icon_name, title, subtitle)
        self._apply_theme()
        theme_manager.theme_changed.connect(self._apply_theme)
    
    def _setup_ui(self, icon_name: str, title: str, subtitle: str):
        """Configure l'interface du badge."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Icône
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color=self.color).pixmap(QSize(32, 32)))
        layout.addWidget(icon_label)
        
        # Texte
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setObjectName("badge_title")
        text_layout.addWidget(title_label)
        
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("badge_subtitle")
        text_layout.addWidget(subtitle_label)
        
        layout.addLayout(text_layout)
    
    def _apply_theme(self):
        """Applique le thème actuel."""
        c = theme_manager.colors()
        
        self.setStyleSheet(f"""
            BadgeConfiance {{
                background: transparent;
                border: none;
            }}
            QLabel#badge_title {{
                color: {c['text_primary']};
                font-size: 14px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
            QLabel#badge_subtitle {{
                color: {c['text_secondary']};
                font-size: 11px;
                background: transparent;
                border: none;
            }}
        """)
