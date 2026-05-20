"""
KPI cards pour les statistiques fournisseurs
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

        self.setStyleSheet(
            f"""
            QFrame {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 16px;
            }}
            QLabel#KpiTitle {{
                color: {c['text_secondary']};
                font-size: 11px;
                font-weight: 500;
                background: transparent;
                border: none;
            }}
            QLabel#KpiValue {{
                color: {c['text_primary']};
                background: transparent;
                border: none;
            }}
            QLabel#KpiSubtitle {{
                color: {c['text_secondary']};
                font-size: 10px;
                background: transparent;
                border: none;
            }}
            """
        )
        self.icon_circle.setStyleSheet(
            f"background: {accent}; border: none; border-radius: 21px;"
        )
        self.icon_label.setPixmap(qta.icon(self.icon_name, color="white").pixmap(22, 22))


class KpiCardsSection(QWidget):
    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.card_total = KpiCard("Total Fournisseurs", "fa5s.truck", "primary")
        self.card_actifs = KpiCard("Fournisseurs Actifs", "fa5s.check-circle", "success")
        self.card_inactifs = KpiCard("Fournisseurs Inactifs", "fa5s.times-circle", "warning")

        for card in (self.card_total, self.card_actifs, self.card_inactifs):
            layout.addWidget(card, 1)

    def rafraichir(self, code_session):
        if not code_session:
            return

        stats = self.ctrl.get_fournisseur_stats(code_session)
        
        total = stats.get("total", 0)
        self.card_total.set_value(total, "Fournisseurs enregistrés")

        actifs = stats.get("actifs", 0)
        self.card_actifs.set_value(actifs, "Avec commandes")

        inactifs = stats.get("inactifs", 0)
        self.card_inactifs.set_value(inactifs, "Sans commandes")
