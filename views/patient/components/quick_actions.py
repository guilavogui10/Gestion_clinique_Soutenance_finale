"""
Quick Actions - Barre d'actions rapides en bas de l'interface
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal
import qtawesome as qta
from views.shared.theme_manager import theme_manager


class QuickActions(QWidget):
    """Barre d'actions rapides"""
    
    # Signaux
    new_patient_clicked = Signal()
    refresh_clicked = Signal()
    stats_clicked = Signal()
    export_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        
        # Boutons d'actions rapides
        self.btn_new = self._create_button("Nouveau Patient", "fa5s.plus-circle")
        self.btn_refresh = self._create_button("Actualiser", "fa5s.sync-alt")
        self.btn_stats = self._create_button("Statistiques", "fa5s.chart-bar")
        self.btn_export = self._create_button("Exporter", "fa5s.file-export")
        
        # Connexions
        self.btn_new.clicked.connect(self.new_patient_clicked.emit)
        self.btn_refresh.clicked.connect(self.refresh_clicked.emit)
        self.btn_stats.clicked.connect(self.stats_clicked.emit)
        self.btn_export.clicked.connect(self.export_clicked.emit)
        
        # Ajouter au layout
        layout.addWidget(self.btn_new)
        layout.addWidget(self.btn_refresh)
        layout.addWidget(self.btn_stats)
        layout.addWidget(self.btn_export)
        layout.addStretch()
    
    def _create_button(self, text, icon_name):
        """Crée un bouton d'action rapide"""
        btn = QPushButton(f"  {text}")
        btn.setFixedHeight(40)
        btn.setMinimumWidth(140)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setProperty("icon_name", icon_name)
        return btn
    
    def apply_theme(self):
        """Applique le thème actuel"""
        c = theme_manager.colors()

        self.setStyleSheet(f"""
            QWidget {{
                background: {c['bg_card']};
                border-top: 1px solid {c['border_light']};
            }}
        """)

        btn_style = f"""
            QPushButton {{
                background: {c['bg_card']};
                color: {c['text_primary']};
                border: none;
                border-radius: 8px;
                padding: 0 16px;
                font-size: 13px;
                font-weight: 600;
                text-align: left;
            }}
            QPushButton:hover {{
                background: {c['hover']};
            }}
            QPushButton:pressed {{
                background: {c['primary_light']};
            }}
        """
        
        for btn in [self.btn_new, self.btn_refresh, self.btn_stats, self.btn_export]:
            btn.setStyleSheet(btn_style)
            icon_name = btn.property("icon_name")
            if icon_name:
                color_map = {
                    "fa5s.plus-circle": c['success'],
                    "fa5s.sync-alt": c['info'],
                    "fa5s.chart-bar": c['primary'],
                    "fa5s.file-export": c['warning']
                }
                btn.setIcon(qta.icon(icon_name, color=color_map.get(icon_name, c['primary'])))
