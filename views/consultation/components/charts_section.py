"""
Charts Section - 6 graphiques pour consultation
Ligne 1 (3 graphiques):
1. Nombre de consultations par mois (barres) - ConsultationAnalyseGraph
2. Montant des consultations par mois (scatter) - MontantConsultationsGraph
3. Moyenne journalière par mois (scatter) - MoyenneJournaliereGraph

Ligne 2 (3 graphiques):
4. Répartition par statut facture (camembert)
5. Top 5 diagnostiques (barres horizontales)
6. Consultations par personnel (barres)
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from views.shared.theme_manager import theme_manager
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from views.consultation.graphe_consultation import (
    ConsultationAnalyseGraph,
    MontantConsultationsGraph,
    MoyenneJournaliereGraph
)



class StatutFactureGraph(FigureCanvas):
    """Graphique camembert - Répartition par statut facture"""
    
    def __init__(self, parent=None, width=4, height=3, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor="none")
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        
    def update_graph(self, data):
        """data: dict avec clés 'Facturee', 'Non facturee', 'En attente'"""
        self.axes.clear()
        
        if not data or sum(data.values()) == 0:
            self.axes.text(0.5, 0.5, 'Aucune donnée', 
                          ha='center', va='center', fontsize=12)
            self.draw()
            return
        
        c = theme_manager.colors()
        colors = [c['success'], c['warning'], c['info']]
        labels = list(data.keys())
        values = list(data.values())
        
        self.axes.pie(values, labels=labels, autopct='%1.1f%%',
                     colors=colors, startangle=90,
                     textprops={'fontsize': 9, 'weight': 'bold'})
        self.axes.axis('equal')
        
        self.fig.tight_layout()
        self.draw()


class Top5DiagnosticsGraph(FigureCanvas):
    """Graphique barres horizontales - Top 5 diagnostiques"""
    
    def __init__(self, parent=None, width=4, height=3, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor="none")
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        
    def update_graph(self, data):
        """data: dict {diagnostic: count}"""
        self.axes.clear()
        
        if not data:
            self.axes.text(0.5, 0.5, 'Aucune donnée', 
                          ha='center', va='center', fontsize=12)
            self.draw()
            return
        
        # Trier et prendre top 5
        sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:5]
        diagnostics = [item[0][:20] + '...' if len(item[0]) > 20 else item[0] 
                      for item in sorted_data]
        counts = [item[1] for item in sorted_data]
        
        c = theme_manager.colors()
        self.axes.barh(diagnostics, counts, color=c['primary'], alpha=0.8)
        self.axes.set_xlabel('Nombre', fontsize=9, color=c['text_secondary'])
        self.axes.tick_params(axis='both', labelsize=8, colors=c['text_secondary'])
        self.axes.spines['top'].set_visible(False)
        self.axes.spines['right'].set_visible(False)
        self.axes.grid(axis='x', alpha=0.3)
        
        self.fig.tight_layout()
        self.draw()


class ConsultationParPersonnelGraph(FigureCanvas):
    """Graphique barres verticales - Consultations par personnel"""
    
    def __init__(self, parent=None, width=4, height=3, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor="none")
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        
    def update_graph(self, data):
        """data: dict {nom_personnel: count}"""
        self.axes.clear()
        
        if not data:
            self.axes.text(0.5, 0.5, 'Aucune donnée', 
                          ha='center', va='center', fontsize=12)
            self.draw()
            return
        
        noms = [nom[:15] + '...' if len(nom) > 15 else nom for nom in data.keys()]
        counts = list(data.values())
        
        c = theme_manager.colors()
        self.axes.bar(noms, counts, color=c['accent'], alpha=0.8)
        self.axes.set_ylabel('Nombre', fontsize=9, color=c['text_secondary'])
        self.axes.tick_params(axis='both', labelsize=8, colors=c['text_secondary'])
        self.axes.tick_params(axis='x', rotation=45)
        self.axes.spines['top'].set_visible(False)
        self.axes.spines['right'].set_visible(False)
        self.axes.grid(axis='y', alpha=0.3)
        
        self.fig.tight_layout()
        self.draw()


class ChartsSection(QWidget):
    """Section contenant les 6 graphiques en 2 lignes"""
    
    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)
        
        # 3 graphiques en ligne horizontale
        
        # Graphique 1: Nombre de consultations par mois (barres)
        self.chart1_frame = self._create_chart_frame("Nombre de consultations par mois")
        self.chart1_graph = ConsultationAnalyseGraph(self.chart1_frame, width=6, height=4, dpi=100)
        self.chart1_frame.layout().addWidget(self.chart1_graph)
        
        # Graphique 2: Montant des consultations par mois (scatter)
        self.chart2_frame = self._create_chart_frame("Montant des consultations par mois")
        self.chart2_graph = MontantConsultationsGraph(self.chart2_frame, width=6, height=4, dpi=100)
        self.chart2_frame.layout().addWidget(self.chart2_graph)
        
        # Graphique 3: Moyenne journalière par mois (scatter)
        self.chart3_frame = self._create_chart_frame("Moyenne journalière par mois")
        self.chart3_graph = MoyenneJournaliereGraph(self.chart3_frame, width=6, height=4, dpi=100)
        self.chart3_frame.layout().addWidget(self.chart3_graph)
        
        main_layout.addWidget(self.chart1_frame, 1)
        main_layout.addWidget(self.chart2_frame, 1)
        main_layout.addWidget(self.chart3_frame, 1)
    
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
    
    def update_data(self, code_session):
        """Met à jour les 3 graphiques"""
        if not code_session:
            return
        
        try:
            nombre_data = self.ctrl.obtenir_nombre_par_mois(code_session)
            self.chart1_graph.update_graph(nombre_data or {})
        except:
            self.chart1_graph.update_graph({})
        
        try:
            montant_data = self.ctrl.obtenir_montant_par_mois(code_session)
            self.chart2_graph.update_graph(montant_data or {})
        except:
            self.chart2_graph.update_graph({})
        
        try:
            moyenne_data = self.ctrl.obtenir_moyenne_journaliere_par_mois(code_session)
            self.chart3_graph.update_graph(moyenne_data or {})
        except:
            self.chart3_graph.update_graph({})
    
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
