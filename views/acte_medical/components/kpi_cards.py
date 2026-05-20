"""
KPI cards — Vue Acte Médical.
"""
import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from views.shared.theme_manager import theme_manager


class KpiCard(QFrame):
    def __init__(self, title, icon_name, color_key, parent=None):
        super().__init__(parent)
        self.title_text = title
        self.icon_name = icon_name
        self.color_key = color_key
        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    def init_ui(self):
        self.setFixedHeight(82)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        self.icon_circle = QFrame()
        self.icon_circle.setObjectName("KpiIconCircle")
        self.icon_circle.setFixedSize(42, 42)
        icon_layout = QHBoxLayout(self.icon_circle)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignCenter)
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(22, 22)
        icon_layout.addWidget(self.icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        self.title_label = QLabel(self.title_text)
        self.title_label.setObjectName("KpiTitle")
        self.value_label = QLabel("--")
        self.value_label.setObjectName("KpiValue")
        font_value = QFont()
        font_value.setPointSize(15)
        font_value.setBold(True)
        self.value_label.setFont(font_value)
        self.subtitle_label = QLabel("")
        self.subtitle_label.setObjectName("KpiSubtitle")
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.value_label)
        text_layout.addWidget(self.subtitle_label)

        layout.addWidget(self.icon_circle)
        layout.addLayout(text_layout, 1)

    def set_value(self, value, subtitle=""):
        self.value_label.setText(str(value))
        self.subtitle_label.setText(subtitle)

    def apply_theme(self):
        c = theme_manager.colors()
        accent = c.get(self.color_key, c["primary"])
        self.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border: none;
                border-radius: 16px;
            }}
            QLabel#KpiTitle {{
                color: {c['text_secondary']};
                font-size: 11px;
                font-weight: 500;
                background: transparent;
            }}
            QLabel#KpiValue {{
                color: {c['text_primary']};
                background: transparent;
            }}
            QLabel#KpiSubtitle {{
                color: {c['text_muted']};
                font-size: 10px;
                background: transparent;
            }}
            QFrame#KpiIconCircle {{
                background: {accent}22;
                border-radius: 21px;
                border: none;
            }}
        """)
        self.icon_label.setPixmap(
            qta.icon(self.icon_name, color=accent).pixmap(20, 20)
        )


class KpiCardsSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 4)
        layout.setSpacing(10)

        self.card_total     = KpiCard("Total actes",       "fa5s.clipboard-list",   "primary")
        self.card_attente   = KpiCard("En attente",        "fa5s.hourglass-half",   "warning")
        self.card_cours     = KpiCard("En cours",          "fa5s.spinner",          "info")
        self.card_termines  = KpiCard("Terminés",          "fa5s.check-circle",     "success")
        self.card_planifies = KpiCard("Planifiés (RDV)",   "fa5s.calendar-check",   "accent")
        self.card_refuses   = KpiCard("Refusés / Ailleurs","fa5s.times-circle",     "danger")

        for card in (self.card_total, self.card_attente, self.card_cours,
                     self.card_termines, self.card_planifies, self.card_refuses):
            layout.addWidget(card)

    def update_kpis(self, stats: dict):
        """Mise à jour depuis un dict {statut: nb}."""
        total = sum(stats.values())
        self.card_total.set_value(total)
        self.card_attente.set_value(stats.get("en_attente", 0))
        self.card_cours.set_value(stats.get("en_cours", 0))
        self.card_termines.set_value(stats.get("termine", 0))
        self.card_planifies.set_value(stats.get("planifie", 0))
        self.card_refuses.set_value(stats.get("refuse", 0))
