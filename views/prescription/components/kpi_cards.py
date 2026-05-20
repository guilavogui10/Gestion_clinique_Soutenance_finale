"""
KPI Cards Section pour les statistiques de prescription
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

        self.card_today = KpiCard("Prescriptions du jour", "fa5s.calendar-day", "info")
        self.card_session = KpiCard("Total Session", "fa5s.prescription", "success")
        self.card_waiting = KpiCard("En Attente Pharmacie", "fa5s.hourglass-half", "warning")
        self.card_amount_today = KpiCard("Montant du jour", "fa5s.wallet", "accent")
        self.card_amount_session = KpiCard("Montant session", "fa5s.coins", "primary")
        self.card_avg_monthly = KpiCard("Revenu moyen mensuel", "fa5s.chart-line", "info")

        for card in (
            self.card_today,
            self.card_session,
            self.card_waiting,
            self.card_amount_today,
            self.card_amount_session,
            self.card_avg_monthly,
        ):
            layout.addWidget(card, 1)

    def rafraichir(self, code_session):
        if not code_session:
            return

        # Card 1: Prescriptions du jour
        today_count = self.ctrl.obtenir_nombre_prescriptions_aujourd_hui(code_session)
        self.card_today.set_value(today_count, "Patients servis")

        # Card 2: Total session
        session_count = self.ctrl.obtenir_nombre_total_session(code_session)
        self.card_session.set_value(session_count, "Prescriptions totales")

        # Card 3: En attente
        waiting_count = self.ctrl.obtenir_nombre_en_attente(code_session)
        self.card_waiting.set_value(waiting_count, "Sans prescription")

        # Card 4: Montant du jour (utiliser revenu_total avec date du jour)
        from datetime import date
        today_str = date.today().strftime("%Y-%m-%d")
        amount_today = self.ctrl.obtenir_revenu_total(code_session, today_str, today_str)
        self.card_amount_today.set_value(f"{amount_today:,.0f} GNF".replace(",", " "), "Montant aujourd'hui")

        # Card 5: Montant session
        amount_session = self.ctrl.obtenir_montant_total_session(code_session)
        self.card_amount_session.set_value(f"{amount_session:,.0f} GNF".replace(",", " "), "Total session")

        # Card 6: Revenu moyen mensuel
        try:
            prescriptions_par_mois = self.ctrl.obtenir_prescriptions_par_mois(code_session)
            if prescriptions_par_mois:
                avg_value = sum(prescriptions_par_mois.values()) / len(prescriptions_par_mois) if prescriptions_par_mois else 0
                self.card_avg_monthly.set_value(f"{avg_value:,.0f}".replace(",", " "), "Prescriptions/mois")
            else:
                self.card_avg_monthly.set_value("0", "Prescriptions/mois")
        except Exception:
            self.card_avg_monthly.set_value("0", "Prescriptions/mois")
