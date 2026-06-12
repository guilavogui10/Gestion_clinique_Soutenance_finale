"""
Charts Section - 3 graphiques pour chirurgie
1. Nombre de chirurgies par mois (barres)
2. Montant des chirurgies par mois (scatter)
3. Moyenne journalière par mois (barres)
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from views.shared.theme_manager import theme_manager
from views.chirurgie.graphe_chirurgie import (
    ChirurgieAnalyseGraph,
    MontantChirurgiesGraph,
    MoyenneJournaliereChirurgiesGraph
)


class ChartsSection(QWidget):
    """Section contenant les 3 graphiques en ligne horizontale"""
    
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
        
        # Graphique 1: Nombre de chirurgies par mois (barres)
        self.chart1_frame = self._create_chart_frame("Nombre de chirurgies par mois")
        self.chart1_graph = ChirurgieAnalyseGraph(self.chart1_frame, width=6, height=4, dpi=100)
        self.chart1_frame.layout().addWidget(self.chart1_graph)
        
        # Graphique 2: Montant des chirurgies par mois (scatter)
        self.chart2_frame = self._create_chart_frame("Montant des chirurgies par mois")
        self.chart2_graph = MontantChirurgiesGraph(self.chart2_frame, width=6, height=4, dpi=100)
        self.chart2_frame.layout().addWidget(self.chart2_graph)
        
        # Graphique 3: Revenu moyen journalier
        self.chart3_frame = self._create_chart_frame("Revenu moyen journalier")
        self.chart3_graph = MoyenneJournaliereChirurgiesGraph(self.chart3_frame, width=6, height=4, dpi=100)
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
            moyenne_data = self.ctrl.obtenir_revenu_moyen_par_mois(code_session)
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
