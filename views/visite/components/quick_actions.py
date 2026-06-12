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
            "fa5s.plus-circle", "Nouvelle visite",    'primary'
        )
        self.btn_new_visit.clicked.connect(self.new_visit_clicked.emit)

        self.btn_progression = self._create_action_button(
            "fa5s.tasks",      "Suivi progression",   'success'
        )
        self.btn_progression.clicked.connect(self.progression_clicked.emit)

        self.btn_priorities = self._create_action_button(
            "fa5s.bell",       "Priorités & urgences",'danger'
        )
        self.btn_priorities.clicked.connect(self.priorities_clicked.emit)

        self.btn_details = self._create_action_button(
            "fa5s.file-alt",   "Détails d'une visite",'info'
        )
        self.btn_details.clicked.connect(self.details_clicked.emit)

        self.btn_export = self._create_action_button(
            "fa5s.download",   "Exporter rapport",    'accent'
        )
        self.btn_export.clicked.connect(self.export_clicked.emit)
        
        layout.addWidget(self.btn_new_visit)
        layout.addWidget(self.btn_progression)
        layout.addWidget(self.btn_priorities)
        layout.addWidget(self.btn_details)
        layout.addWidget(self.btn_export)
    
    def _create_action_button(self, icon_name, text, color_key):
        btn = QPushButton(f"  {text}")
        btn.setObjectName("ActionButton")
        btn.setFixedHeight(40)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setProperty("icon_name", icon_name)
        btn.setProperty("color_key", color_key)
        return btn

    def apply_theme(self):
        c = theme_manager.colors()

        self.setStyleSheet(f"""
            QWidget {{
                background: {c['bg_card']};
                border-top: 1px solid {c['border_light']};
            }}
            QPushButton#ActionButton {{
                background: {c['bg_card']};
                border: none;
                border-radius: 8px;
                color: {c['text_primary']};
                font-size: 12px;
                font-weight: 600;
                text-align: left;
                padding-left: 15px;
            }}
            QPushButton#ActionButton:hover {{
                background: {c['hover']};
            }}
            QPushButton#ActionButton:pressed {{
                background: {c['primary_light']};
            }}
        """)

        for btn in self.findChildren(QPushButton):
            if btn.objectName() == "ActionButton":
                icon_name = btn.property("icon_name")
                color_key = btn.property("color_key")
                if icon_name and color_key:
                    btn.setIcon(qta.icon(icon_name, color=c.get(color_key, c['primary'])))
