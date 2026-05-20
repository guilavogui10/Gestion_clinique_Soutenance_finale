"""
Charts Section - 3 graphiques d'analyse consultation
Nombre par mois | Montant par mois | Moyenne journalière
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QLineSeries, QValueAxis, QBarCategoryAxis
import qtawesome as qta
from views.shared.theme_manager import theme_manager


class ChartFrame(QFrame):
    """Frame conteneur pour un graphique"""
    
    def __init__(self, title, icon_name, parent=None):
        super().__init__(parent)
        self.title_text = title
        self.icon_name = icon_name
        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header
        header = QHBoxLayout()
        header.setSpacing(8)
        
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(20, 20)
        
        self.title_label = QLabel(self.title_text)
        self.title_label.setObjectName("ChartTitle")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.title_label.setFont(font)
        
        header.addWidget(self.icon_label)
        header.addWidget(self.title_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Chart container
        self.chart_container = QVBoxLayout()
        self.chart_container.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.chart_container, 1)
    
    def apply_theme(self):
        c = theme_manager.colors()
        
        self.setStyleSheet(f"""
            QFrame {{
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
        
        self.icon_label.setPixmap(qta.icon(self.icon_name, color=c['primary']).pixmap(20, 20))


class ChartsAnalyseSection(QWidget):
    """Section contenant les 3 graphiques"""
    
    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 20)
        layout.setSpacing(15)
        
        # Graphique 1 : Nombre consultations par mois
        self.frame_nombre = ChartFrame("Nombre de consultations par mois", "fa5s.chart-bar")
        self.chart_nombre = self._create_bar_chart()
        self.chart_view_nombre = QChartView(self.chart_nombre)
        self.chart_view_nombre.setRenderHint(self.chart_view_nombre.renderHints())
        self.chart_view_nombre.setFixedHeight(250)
        self.frame_nombre.chart_container.addWidget(self.chart_view_nombre)
        
        # Graphique 2 : Montant consultations par mois
        self.frame_montant = ChartFrame("Montant des consultations par mois (GNF)", "fa5s.chart-line")
        self.chart_montant = self._create_line_chart()
        self.chart_view_montant = QChartView(self.chart_montant)
        self.chart_view_montant.setRenderHint(self.chart_view_montant.renderHints())
        self.chart_view_montant.setFixedHeight(250)
        self.frame_montant.chart_container.addWidget(self.chart_view_montant)
        
        # Graphique 3 : Moyenne journalière par mois
        self.frame_moyenne = ChartFrame("Moyenne journalière (par mois)", "fa5s.chart-area")
        self.chart_moyenne = self._create_line_chart()
        self.chart_view_moyenne = QChartView(self.chart_moyenne)
        self.chart_view_moyenne.setRenderHint(self.chart_view_moyenne.renderHints())
        self.chart_view_moyenne.setFixedHeight(250)
        self.frame_moyenne.chart_container.addWidget(self.chart_view_moyenne)
        
        layout.addWidget(self.frame_nombre)
        layout.addWidget(self.frame_montant)
        layout.addWidget(self.frame_moyenne)
    
    def _create_bar_chart(self):
        """Crée un graphique en barres"""
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setVisible(False)
        chart.setBackgroundVisible(False)
        return chart
    
    def _create_line_chart(self):
        """Crée un graphique en lignes"""
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.setBackgroundVisible(False)
        return chart
    
    def update_nombre_chart(self, data):
        """Met à jour le graphique nombre"""
        self.chart_nombre.removeAllSeries()
        
        months = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]
        values = [data.get(m, 0) for m in months]
        
        bar_set = QBarSet("Consultations")
        for v in values:
            bar_set.append(v)
        
        series = QBarSeries()
        series.append(bar_set)
        
        self.chart_nombre.addSeries(series)
        
        axis_x = QBarCategoryAxis()
        axis_x.append(months)
        self.chart_nombre.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, max(values) * 1.2 if values else 100)
        self.chart_nombre.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
    
    def update_montant_chart(self, data):
        """Met à jour le graphique montant"""
        self.chart_montant.removeAllSeries()
        
        months = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]
        values = [data.get(m, 0) for m in months]
        
        series = QLineSeries()
        series.setName("Montant (GNF)")
        for i, v in enumerate(values):
            series.append(i, v)
        
        self.chart_montant.addSeries(series)
        
        axis_x = QValueAxis()
        axis_x.setRange(0, 11)
        axis_x.setLabelFormat("%d")
        self.chart_montant.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, max(values) * 1.2 if values else 1000)
        self.chart_montant.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
    
    def update_moyenne_chart(self, data):
        """Met à jour le graphique moyenne"""
        self.chart_moyenne.removeAllSeries()
        
        months = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]
        values = [data.get(m, 0) for m in months]
        
        series = QLineSeries()
        series.setName("Moyenne / jour")
        for i, v in enumerate(values):
            series.append(i, v)
        
        self.chart_moyenne.addSeries(series)
        
        axis_x = QValueAxis()
        axis_x.setRange(0, 11)
        axis_x.setLabelFormat("%d")
        self.chart_moyenne.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, max(values) * 1.2 if values else 10)
        self.chart_moyenne.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
    
    def rafraichir(self, code_session):
        """Rafraîchit les 3 graphiques"""
        # Nombre par mois
        nombre_par_mois = self.ctrl.obtenir_nombre_par_mois(code_session)
        self.update_nombre_chart(nombre_par_mois)
        
        # Montant par mois
        montant_par_mois = self.ctrl.obtenir_montant_par_mois(code_session)
        self.update_montant_chart(montant_par_mois)
        
        # Moyenne journalière par mois
        moyenne_par_mois = self.ctrl.obtenir_moyenne_nombre_journalier_par_mois(code_session)
        self.update_moyenne_chart(moyenne_par_mois)
