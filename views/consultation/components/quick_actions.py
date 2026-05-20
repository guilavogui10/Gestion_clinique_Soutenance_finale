"""
Quick actions section for consultation page.
"""
import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from views.shared.theme_manager import theme_manager


class QuickActions(QWidget):
    new_consultation_clicked = Signal()
    patients_waiting_clicked = Signal()
    advanced_search_clicked = Signal()
    reports_clicked = Signal()
    patient_history_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.buttons = []
        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(8)

        actions = [
            ("fa5s.plus-circle", "Nouvelle consultation", "primary", self.new_consultation_clicked),
            ("fa5s.hourglass-half", "Patients en attente", "warning", self.patients_waiting_clicked),
            ("fa5s.search-plus", "Recherche avancée", "accent", self.advanced_search_clicked),
            ("fa5s.file-export", "Rapports & exports", "success", self.reports_clicked),
            ("fa5s.history", "Historique patient", "text_secondary", self.patient_history_clicked),
        ]

        for icon_name, text, color_key, signal in actions:
            btn = QPushButton(f"  {text}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(40)
            btn.setObjectName("QuickActionButton")
            btn.setProperty("color_key", color_key)
            btn.setProperty("icon_name", icon_name)
            btn.clicked.connect(signal.emit)
            self.buttons.append(btn)
            layout.addWidget(btn)

    def apply_theme(self):
        c = theme_manager.colors()

        for btn in self.buttons:
            color_key = btn.property("color_key") or "primary"
            color = c.get(color_key, c["primary"])
            btn.setIcon(qta.icon(btn.property("icon_name") or "fa5s.circle", color=color))
            btn.setStyleSheet(
                f"""
                QPushButton#QuickActionButton {{
                    background: white;
                    border: none;
                    border-radius: 8px;
                    padding-left: 15px;
                    text-align: left;
                    font-size: 12px;
                    font-weight: 600;
                    color: {c['text_primary']};
                }}
                QPushButton#QuickActionButton:hover {{
                    background: {c['bg_card']};
                }}
                """
            )
