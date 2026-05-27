"""
Quick actions section for examen page.
"""
import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from views.shared.theme_manager import theme_manager


class QuickActions(QWidget):
    new_examen_clicked = Signal()
    patients_waiting_clicked = Signal()
    advanced_search_clicked = Signal()
    reports_clicked = Signal()
    patient_history_clicked = Signal()
    imprimer_tous_rapports_clicked = Signal()
    imprimer_rapport_date_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.buttons = []
        self.btn_imprimer_rapport = None
        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(8)

        actions = [
            ("fa5s.plus-circle", "Nouvel examen", "primary", self.new_examen_clicked),
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

        # Bouton Imprimer rapport avec menu déroulant
        self.btn_imprimer_rapport = QPushButton("  Imprimer rapport")
        self.btn_imprimer_rapport.setCursor(Qt.PointingHandCursor)
        self.btn_imprimer_rapport.setFixedHeight(40)
        self.btn_imprimer_rapport.setObjectName("QuickActionButton")
        self.btn_imprimer_rapport.setProperty("color_key", "primary")
        self.btn_imprimer_rapport.setProperty("icon_name", "fa5s.print")
        self.btn_imprimer_rapport.clicked.connect(self._show_imprimer_menu)
        self.buttons.append(self.btn_imprimer_rapport)
        layout.addWidget(self.btn_imprimer_rapport)

    def _show_imprimer_menu(self):
        from PySide6.QtWidgets import QMenu
        c = theme_manager.colors()

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: white;
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 6px 0;
            }}
            QMenu::item {{
                padding: 10px 20px;
                color: {c['text_primary']};
                font-size: 13px;
                font-weight: 500;
            }}
            QMenu::item:selected {{
                background: {c['primary_light']};
                color: {c['primary']};
                border-radius: 4px;
            }}
            QMenu::separator {{
                height: 1px;
                background: {c['border_light']};
                margin: 4px 8px;
            }}
        """)

        action_tous = menu.addAction(
            qta.icon("fa5s.file-pdf", color=c['primary']),
            "  Imprimer tous les rapports"
        )
        action_tous.triggered.connect(self.imprimer_tous_rapports_clicked.emit)

        menu.addSeparator()

        action_date = menu.addAction(
            qta.icon("fa5s.calendar-day", color=c['success']),
            "  Imprimer rapport par date..."
        )
        action_date.triggered.connect(self.imprimer_rapport_date_clicked.emit)

        btn = self.btn_imprimer_rapport
        pos = btn.mapToGlobal(btn.rect().topLeft())
        pos.setY(pos.y() - menu.sizeHint().height())
        menu.exec(pos)

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
