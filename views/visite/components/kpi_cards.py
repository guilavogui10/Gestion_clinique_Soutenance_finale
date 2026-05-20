"""
KPI Cards Section - 5 cartes d'indicateurs clés
Visites aujourd'hui | Terminées | En cours | Urgences | Durée moyenne
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import qtawesome as qta
from views.shared.theme_manager import theme_manager


class KpiCard(QFrame):
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
        self.setFixedHeight(85)  # Réduit de 100 à 85
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)  # Réduit encore les marges
        layout.setSpacing(10)  # Réduit l'espacement
        
        # Icône circulaire
        icon_container = QFrame()
        icon_container.setObjectName("IconCircle")
        icon_container.setFixedSize(45, 45)  # Réduit de 50 à 45
        icon_layout = QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(self.icon_label)
        
        # Textes
        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)  # Réduit l'espacement
        
        self.title_label = QLabel(self.title_text)
        self.title_label.setObjectName("KpiTitle")
        
        self.value_label = QLabel("—")
        self.value_label.setObjectName("KpiValue")
        font_value = QFont()
        font_value.setPointSize(22)  # Réduit de 24 à 22
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
                border-radius: 22px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
            QLabel#KpiTitle {{
                color: {c['text_secondary']};
                font-size: 10px;
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
        
        self.icon_label.setPixmap(qta.icon(self.icon_name, color=self.color).pixmap(24, 24))


class KpiCardsSection(QWidget):
    """Section contenant les 5 KPI cards"""
    
    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)  # Réduit encore la marge du bas
        layout.setSpacing(10)  # Réduit l'espacement entre les cards
        
        c = theme_manager.colors()
        
        # 5 cartes KPI
        self.card_today = KpiCard("Visites aujourd'hui", "fa5s.users", c['info'])
        self.card_completed = KpiCard("Visites terminées", "fa5s.check-circle", c['success'])
        self.card_ongoing = KpiCard("Visites en cours", "fa5s.clock", c['warning'])
        self.card_urgent = KpiCard("Urgences", "fa5s.exclamation-triangle", c['danger'])
        self.card_duration = KpiCard("Durée moyenne", "fa5s.stopwatch", c['accent'])
        
        layout.addWidget(self.card_today)
        layout.addWidget(self.card_completed)
        layout.addWidget(self.card_ongoing)
        layout.addWidget(self.card_urgent)
        layout.addWidget(self.card_duration)
    
    def update_data(self, stats):
        """Met à jour les valeurs des cartes"""
        # Visites aujourd'hui
        today_count = stats.get('today_count', 0)
        today_vs_yesterday = stats.get('today_vs_yesterday', 0)
        self.card_today.set_value(today_count, f"+{today_vs_yesterday}% vs hier" if today_vs_yesterday > 0 else f"{today_vs_yesterday}% vs hier")
        
        # Visites terminées
        completed_count = stats.get('completed_count', 0)
        completed_pct = stats.get('completed_pct', 0)
        self.card_completed.set_value(completed_count, f"{completed_pct}% du total")
        
        # Visites en cours
        ongoing_count = stats.get('ongoing_count', 0)
        self.card_ongoing.set_value(ongoing_count, "En attente")
        
        # Urgences
        urgent_count = stats.get('urgent_count', 0)
        self.card_urgent.set_value(urgent_count, "Action requise" if urgent_count > 0 else "Aucune urgence")
        
        # Durée moyenne
        avg_duration = stats.get('avg_duration', 0)
        self.card_duration.set_value(f"{avg_duration} min", "Visites terminées")
