"""
KPI Cards Analyse - 6 cartes d'indicateurs clés
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import qtawesome as qta
from views.shared.theme_manager import theme_manager


class KpiCardAnalyse(QFrame):
    """Carte KPI individuelle"""
    
    def __init__(self, title, icon_name, color, parent=None):
        super().__init__(parent)
        self.color = color
        self.title_text = title
        self.icon_name = icon_name
        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def init_ui(self):
        self.setFixedHeight(120)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # Icône circulaire
        icon_container = QFrame()
        icon_container.setObjectName("IconCircle")
        icon_container.setFixedSize(60, 60)
        icon_layout = QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(self.icon_label)
        
        # Textes
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        self.title_label = QLabel(self.title_text)
        self.title_label.setObjectName("KpiTitle")
        
        self.value_label = QLabel("—")
        self.value_label.setObjectName("KpiValue")
        font_value = QFont()
        font_value.setPointSize(28)
        font_value.setBold(True)
        self.value_label.setFont(font_value)
        
        self.subtitle_label = QLabel("")
        self.subtitle_label.setObjectName("KpiSubtitle")
        
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.value_label)
        text_layout.addWidget(self.subtitle_label)
        text_layout.addStretch()
        
        layout.addWidget(icon_container)
        layout.addLayout(text_layout, 1)
    
    def set_value(self, value, subtitle=""):
        self.value_label.setText(str(value))
        self.subtitle_label.setText(subtitle)
    
    def apply_theme(self):
        c = theme_manager.colors()
        
        self.setStyleSheet(f"""
            QFrame {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 15px;
            }}
            QFrame:hover {{
                border: 1px solid {self.color};
                background: {c['hover']};
            }}
            QFrame#IconCircle {{
                background: {self.color}20;
                border: 2px solid {self.color}40;
                border-radius: 30px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
            QLabel#KpiTitle {{
                color: {c['text_secondary']};
                font-size: 12px;
                font-weight: 600;
            }}
            QLabel#KpiValue {{
                color: {self.color};
            }}
            QLabel#KpiSubtitle {{
                color: {c['text_muted']};
                font-size: 11px;
            }}
        """)
        
        self.icon_label.setPixmap(qta.icon(self.icon_name, color=self.color).pixmap(28, 28))


class KpiCardsAnalyse(QWidget):
    """Section contenant les 6 KPI cards"""
    
    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 20)
        layout.setSpacing(15)
        
        c = theme_manager.colors()
        
        # 6 cartes KPI
        self.card_today = KpiCardAnalyse("Consultations du jour", "fa5s.calendar-day", c['info'])
        self.card_session = KpiCardAnalyse("Session en cours", "fa5s.users", c['success'])
        self.card_waiting = KpiCardAnalyse("Patients en attente", "fa5s.hourglass-half", c['warning'])
        self.card_amount_today = KpiCardAnalyse("Montant du jour", "fa5s.wallet", c['accent'])
        self.card_amount_session = KpiCardAnalyse("Montant session", "fa5s.coins", c['primary'])
        self.card_avg_monthly = KpiCardAnalyse("Revenu moyen mensuel", "fa5s.chart-line", c['info'])
        
        layout.addWidget(self.card_today)
        layout.addWidget(self.card_session)
        layout.addWidget(self.card_waiting)
        layout.addWidget(self.card_amount_today)
        layout.addWidget(self.card_amount_session)
        layout.addWidget(self.card_avg_monthly)
    
    def update_data(self, stats):
        """Met à jour les valeurs des cartes"""
        # Consultations du jour
        today_count = stats.get('today_count', 0)
        today_vs_yesterday = stats.get('today_vs_yesterday', 0)
        self.card_today.set_value(today_count, f"+{today_vs_yesterday}% vs hier" if today_vs_yesterday > 0 else f"{today_vs_yesterday}% vs hier")
        
        # Session en cours
        session_count = stats.get('session_count', 0)
        self.card_session.set_value(session_count, "Consultations totales")
        
        # Patients en attente
        waiting_count = stats.get('waiting_count', 0)
        self.card_waiting.set_value(waiting_count, "Sans consultation")
        
        # Montant du jour
        amount_today = stats.get('amount_today', 0)
        self.card_amount_today.set_value(f"{amount_today:,.0f} GNF", "Frais consultations")
        
        # Montant session
        amount_session = stats.get('amount_session', 0)
        self.card_amount_session.set_value(f"{amount_session:,.0f} GNF", "Total année")
        
        # Revenu moyen mensuel
        avg_monthly = stats.get('avg_monthly', 0)
        self.card_avg_monthly.set_value(f"{avg_monthly:,.0f} GNF", "Par mois")
    
    def rafraichir(self, code_session):
        """Rafraîchit les données des KPI"""
        # Récupérer les statistiques depuis le contrôleur
        stats = {
            'today_count': self.ctrl.obtenir_consultations_aujourd_hui(code_session),
            'today_vs_yesterday': 12,  # À calculer
            'session_count': self.ctrl.obtenir_nombre_total(code_session),
            'waiting_count': self.ctrl.obtenir_nombre_patients_en_attente(code_session),
            'amount_today': self.ctrl.obtenir_montant_aujourd_hui(code_session),
            'amount_session': self.ctrl.obtenir_montant_session(code_session),
            'avg_monthly': self._calculer_revenu_moyen_mensuel(code_session)
        }
        self.update_data(stats)
    
    def _calculer_revenu_moyen_mensuel(self, code_session):
        """Calcule le revenu moyen mensuel"""
        montant_par_mois = self.ctrl.obtenir_montant_par_mois(code_session)
        if not montant_par_mois:
            return 0
        montants = [v for v in montant_par_mois.values() if v > 0]
        return sum(montants) / len(montants) if montants else 0
