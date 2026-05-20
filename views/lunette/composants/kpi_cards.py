"""
KPI cards pour les commandes de lunettes.
Même structure que consultation/components/kpi_cards.py
"""
import qtawesome as qta
from PySide6.QtCore    import Qt
from PySide6.QtGui     import QFont
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget
)
from views.shared.theme_manager import theme_manager


class KpiCard(QFrame):
    def __init__(self, title: str, icon_name: str, color_key: str, parent=None):
        super().__init__(parent)
        self.title_text = title
        self.icon_name  = icon_name
        self.color_key  = color_key
        self._init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    def _init_ui(self):
        self.setFixedHeight(82)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        self.icon_circle = QFrame()
        self.icon_circle.setObjectName("KpiIconCircle")
        self.icon_circle.setFixedSize(42, 42)
        ic_lay = QHBoxLayout(self.icon_circle)
        ic_lay.setContentsMargins(0, 0, 0, 0)
        ic_lay.setAlignment(Qt.AlignCenter)
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(22, 22)
        ic_lay.addWidget(self.icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        self.title_label = QLabel(self.title_text)
        self.title_label.setObjectName("KpiTitle")

        self.value_label = QLabel("--")
        self.value_label.setObjectName("KpiValue")
        f = QFont()
        f.setPointSize(15)
        f.setBold(True)
        self.value_label.setFont(f)

        self.subtitle_label = QLabel("")
        self.subtitle_label.setObjectName("KpiSubtitle")

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.value_label)
        text_layout.addWidget(self.subtitle_label)

        layout.addWidget(self.icon_circle)
        layout.addLayout(text_layout, 1)

    def set_value(self, value, subtitle: str = ""):
        self.value_label.setText(str(value))
        self.subtitle_label.setText(subtitle)

    def apply_theme(self):
        c = theme_manager.colors()
        accent = c.get(self.color_key, c["primary"])
        self.setStyleSheet(f"""
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
        """)
        self.icon_circle.setStyleSheet(
            f"background: {accent}; border: none; border-radius: 21px;"
        )
        self.icon_label.setPixmap(
            qta.icon(self.icon_name, color="white").pixmap(22, 22)
        )


class LunetteKpiCardsSection(QWidget):
    """6 cartes KPI pour les statistiques lunettes."""

    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.card_attente_livraison = KpiCard(
            "Attente livraison",    "fa5s.truck",          "warning")
        self.card_total_session     = KpiCard(
            "Total session",        "fa5s.glasses",        "success")
        self.card_patients_attente  = KpiCard(
            "Patients en attente",  "fa5s.hourglass-half", "danger")
        self.card_montant_jour      = KpiCard(
            "Montant du jour",      "fa5s.wallet",         "accent")
        self.card_montant_session   = KpiCard(
            "Montant session",      "fa5s.coins",          "primary")
        self.card_revenu_moyen      = KpiCard(
            "Revenu moyen mensuel", "fa5s.chart-line",     "info")

        for card in (
            self.card_attente_livraison,
            self.card_total_session,
            self.card_patients_attente,
            self.card_montant_jour,
            self.card_montant_session,
            self.card_revenu_moyen,
        ):
            layout.addWidget(card, 1)

    def rafraichir(self, code_session: str):
        if not code_session:
            return

        try:
            n = self.ctrl.obtenir_commandes_en_attente_livraison(code_session)
            self.card_attente_livraison.set_value(n, "En cours de livraison")
        except Exception:
            self.card_attente_livraison.set_value("--")

        try:
            n = self.ctrl.obtenir_total_commandes_session(code_session)
            self.card_total_session.set_value(n, "Commandes totales")
        except Exception:
            self.card_total_session.set_value("--")

        try:
            n = self.ctrl.obtenir_commandes_en_attente(code_session)
            self.card_patients_attente.set_value(n, "Sans commande")
        except Exception:
            self.card_patients_attente.set_value("--")

        try:
            m = self.ctrl.obtenir_montant_total_aujourdhui(code_session)
            self.card_montant_jour.set_value(
                f"{m:,.0f} GNF".replace(",", " "), "Frais commandes"
            )
        except Exception:
            self.card_montant_jour.set_value("--")

        try:
            m = self.ctrl.obtenir_montant_total_par_session(code_session)
            self.card_montant_session.set_value(
                f"{m:,.0f} GNF".replace(",", " "), "Total année"
            )
        except Exception:
            self.card_montant_session.set_value("--")

        try:
            avg_data = self.ctrl.obtenir_revenu_moyen_par_mois(code_session)
            if avg_data:
                avg = sum(avg_data.values()) / len(avg_data)
                self.card_revenu_moyen.set_value(
                    f"{avg:,.0f} GNF".replace(",", " "), "Par mois"
                )
            else:
                self.card_revenu_moyen.set_value("0 GNF", "Par mois")
        except Exception:
            self.card_revenu_moyen.set_value("--")
