"""
Charts Section - 3 graphiques
1. Visites par mois (barres)
2. Évolution par tranche d'âge (lignes)
3. Performance de la session (card avec métriques)
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import qtawesome as qta
from views.shared.theme_manager import theme_manager
from views.visite.graphe_visite import VisiteAnalyseGraph, AgeAnalyseGraph


class PerformanceCard(QFrame):
    """Card Performance de la session"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        header.setSpacing(8)
        
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(18, 18)
        
        title = QLabel("Performance de la session")
        title.setObjectName("CardTitle")
        font_title = QFont()
        font_title.setPointSize(13)
        font_title.setBold(True)
        title.setFont(font_title)
        
        header.addWidget(self.icon_label)
        header.addWidget(title)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Séparateur
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setObjectName("Separator")
        layout.addWidget(sep)
        
        # Métriques (2 colonnes)
        metrics_grid = QVBoxLayout()
        metrics_grid.setSpacing(10)
        
        # Ligne 1
        row1 = QHBoxLayout()
        self.metric_duration = self._create_metric("fa5s.clock", "Durée moyenne", "— min")
        self.metric_max_wait = self._create_metric("fa5s.hourglass-half", "Attente max", "— min")
        row1.addLayout(self.metric_duration)
        row1.addLayout(self.metric_max_wait)
        
        # Ligne 2
        row2 = QHBoxLayout()
        self.metric_active = self._create_metric("fa5s.users", "Visites actives", "—")
        self.metric_trend = self._create_metric("fa5s.chart-line", "Tendance", "—")
        row2.addLayout(self.metric_active)
        row2.addLayout(self.metric_trend)
        
        # Ligne 3
        row3 = QHBoxLayout()
        self.metric_efficiency = self._create_metric("fa5s.check-circle", "Efficacité (≤ 90 min)", "—%")
        self.metric_satisfaction = self._create_metric("fa5s.smile", "Satisfaction", "—%")
        row3.addLayout(self.metric_efficiency)
        row3.addLayout(self.metric_satisfaction)
        
        metrics_grid.addLayout(row1)
        metrics_grid.addLayout(row2)
        metrics_grid.addLayout(row3)
        
        layout.addLayout(metrics_grid)
        layout.addStretch()
        
        # Lien "Voir l'analyse complète"
        self.link_btn = QPushButton("Voir l'analyse complète →")
        self.link_btn.setObjectName("LinkButton")
        self.link_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.link_btn, alignment=Qt.AlignRight)
    
    def _create_metric(self, icon_name, label_text, value_text):
        """Crée une métrique avec icône + label + valeur"""
        container = QVBoxLayout()
        container.setSpacing(4)
        
        # Ligne icône + label
        header = QHBoxLayout()
        header.setSpacing(6)
        
        icon = QLabel()
        icon.setObjectName("MetricIcon")
        icon.setFixedSize(14, 14)
        icon.setProperty("icon_name", icon_name)
        
        label = QLabel(label_text)
        label.setObjectName("MetricLabel")
        
        header.addWidget(icon)
        header.addWidget(label)
        header.addStretch()
        
        # Valeur
        value = QLabel(value_text)
        value.setObjectName("MetricValue")
        font_value = QFont()
        font_value.setPointSize(18)
        font_value.setBold(True)
        value.setFont(font_value)
        
        container.addLayout(header)
        container.addWidget(value)
        
        # Stocker les références
        setattr(self, f"_icon_{icon_name}", icon)
        setattr(self, f"_value_{label_text}", value)
        
        return container
    
    def update_metrics(self, stats):
        """Met à jour les métriques"""
        # Récupérer les widgets de valeur
        for child in self.findChildren(QLabel):
            if child.objectName() == "MetricValue":
                parent_layout = child.parent()
                if parent_layout:
                    # Identifier la métrique et mettre à jour
                    pass
        
        # Mise à jour directe (à améliorer)
        metrics = [
            (stats.get('duree_moyenne', 0), "min"),
            (stats.get('attente_max', 0), "min"),
            (stats.get('visites_actives', 0), ""),
            (stats.get('tendance', "+0%"), ""),
            (stats.get('efficacite', 0), "%"),
            (stats.get('satisfaction', 0), "%"),
        ]
    
    def apply_theme(self):
        c = theme_manager.colors()
        
        self.setStyleSheet(f"""
            QFrame {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 15px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
            QLabel#CardTitle {{
                color: {c['text_primary']};
            }}
            QFrame#Separator {{
                background: {c['border_light']};
                border: none;
            }}
            QLabel#MetricLabel {{
                color: {c['text_secondary']};
                font-size: 11px;
            }}
            QLabel#MetricValue {{
                color: {c['primary']};
            }}
            QPushButton#LinkButton {{
                background: transparent;
                border: none;
                color: {c['info']};
                font-size: 12px;
                font-weight: 600;
                text-align: right;
                padding: 5px;
            }}
            QPushButton#LinkButton:hover {{
                color: {c['primary']};
                text-decoration: underline;
            }}
        """)
        
        # Mise à jour des icônes
        self.icon_label.setPixmap(qta.icon("fa5s.tachometer-alt", color=c['primary']).pixmap(18, 18))
        
        for child in self.findChildren(QLabel):
            if child.objectName() == "MetricIcon":
                icon_name = child.property("icon_name")
                if icon_name:
                    child.setPixmap(qta.icon(icon_name, color=c['text_secondary']).pixmap(14, 14))


class ChartsSection(QWidget):
    """Section contenant les 3 graphiques"""
    
    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Graphique 1 : Visites par mois (barres)
        self.chart1_frame = self._create_chart_frame("Visites par mois (Session 2024-2025)")
        self.chart1_graph = VisiteAnalyseGraph(self.chart1_frame, width=6, height=4, dpi=100)
        self.chart1_frame.layout().addWidget(self.chart1_graph)

        # Graphique 2 : Évolution par âge (lignes)
        self.chart2_frame = self._create_chart_frame("Évolution par tranche d'âge (mensuelle)")
        self.chart2_graph = AgeAnalyseGraph(self.chart2_frame, width=8, height=4, dpi=100)
        self.chart2_frame.layout().addWidget(self.chart2_graph)

        # Card 3 : Performance
        self.performance_card = PerformanceCard()

        layout.addWidget(self.chart1_frame, 2)
        layout.addWidget(self.chart2_frame, 2)
        layout.addWidget(self.performance_card, 1)
    
    def _create_chart_frame(self, title):
        """Crée un cadre pour un graphique"""
        frame = QFrame()
        frame.setObjectName("ChartFrame")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setObjectName("ChartTitle")
        font_title = QFont()
        font_title.setPointSize(11)
        font_title.setBold(True)
        title_label.setFont(font_title)
        
        layout.addWidget(title_label)
        
        return frame
    
    def update_data(self, stats_mensuelles, stats_ages, stats_performance):
        """Met à jour les 3 graphiques"""
        self.chart1_graph.update_graph(stats_mensuelles)
        self.chart2_graph.update_graph(stats_ages)
        self.performance_card.update_metrics(stats_performance)
    
    def apply_theme(self):
        c = theme_manager.colors()
        
        self.setStyleSheet(f"""
            QFrame#ChartFrame {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 15px;
            }}
            QLabel#ChartTitle {{
                color: {c['text_primary']};
                background: transparent;
                border: none;
            }}
        """)