"""
Quick Actions - Footer avec 5 boutons d'actions rapides
1. Nouvelle visite
2. Suivi progression
3. Priorités & urgences
4. Détails d'une visite
5. Exporter rapport
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal
import qtawesome as qta
from views.shared.theme_manager import theme_manager


class QuickActions(QWidget):
    """Barre d'actions rapides"""
    
    new_visit_clicked = Signal()
    progression_clicked = Signal()
    priorities_clicked = Signal()
    details_clicked = Signal()
    export_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(8)
        
        # 5 boutons d'actions
        self.btn_new_visit = self._create_action_button(
            "fa5s.plus-circle",
            "Nouvelle visite",
            theme_manager.colors()['primary']
        )
        self.btn_new_visit.clicked.connect(self.new_visit_clicked.emit)
        
        self.btn_progression = self._create_action_button(
            "fa5s.tasks",
            "Suivi progression",
            theme_manager.colors()['success']
        )
        self.btn_progression.clicked.connect(self.progression_clicked.emit)
        
        self.btn_priorities = self._create_action_button(
            "fa5s.bell",
            "Priorités & urgences",
            theme_manager.colors()['danger']
        )
        self.btn_priorities.clicked.connect(self.priorities_clicked.emit)
        
        self.btn_details = self._create_action_button(
            "fa5s.file-alt",
            "Détails d'une visite",
            theme_manager.colors()['info']
        )
        self.btn_details.clicked.connect(self.details_clicked.emit)
        
        self.btn_export = self._create_action_button(
            "fa5s.download",
            "Exporter rapport",
            theme_manager.colors()['accent']
        )
        self.btn_export.clicked.connect(self.export_clicked.emit)
        
        layout.addWidget(self.btn_new_visit)
        layout.addWidget(self.btn_progression)
        layout.addWidget(self.btn_priorities)
        layout.addWidget(self.btn_details)
        layout.addWidget(self.btn_export)
    
    def _create_action_button(self, icon_name, text, color):
        """Crée un bouton d'action"""
        btn = QPushButton(f"  {text}")
        btn.setObjectName("ActionButton")
        btn.setFixedHeight(40)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setProperty("color", color)
        
        # Stocker l'icône pour la mise à jour du thème
        btn.setProperty("icon_name", icon_name)
        btn.setIcon(qta.icon(icon_name, color=color))
        
        return btn
    
    def apply_theme(self):
        c = theme_manager.colors()
        
        self.setStyleSheet(f"""
            QPushButton#ActionButton {{
                background: white;
                border: none;
                border-radius: 8px;
                color: {c['text_primary']};
                font-size: 12px;
                font-weight: 600;
                text-align: left;
                padding-left: 15px;
            }}
            QPushButton#ActionButton:hover {{
                background: {c['bg_card']};
            }}
        """)
        
        # Mise à jour des icônes
        for btn in self.findChildren(QPushButton):
            if btn.objectName() == "ActionButton":
                icon_name = btn.property("icon_name")
                color = btn.property("color")
                if icon_name and color:
                    btn.setIcon(qta.icon(icon_name, color=color))
