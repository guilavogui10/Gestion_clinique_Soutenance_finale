"""
Charts Section - 3 graphiques pour fournisseurs
1. Nombre de fournisseurs par mois (barres)
2. Montant des commandes par mois (scatter)
3. Top 5 fournisseurs par quantité (barres horizontales)
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from views.shared.theme_manager import theme_manager
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np


class BaseFournisseurGraph(FigureCanvas):
    """Classe de base pour les graphiques fournisseurs"""
    
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor="none")
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor("none")
        super().__init__(self.fig)
        self.setParent(parent)
        self._setup_style()
        theme_manager.theme_changed.connect(self._on_theme_change)
        
    def _setup_style(self):
        c = theme_manager.colors()
        for spine in self.axes.spines.values():
            spine.set_visible(False)
        
        self.axes.grid(True, axis="y", linestyle="-", alpha=0.1,
                      color=c["border"], linewidth=0.8)
        
        self.axes.tick_params(
            colors=c["text_secondary"],
            labelsize=9,
            length=0,
            pad=8
        )
        
        self.fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.15)
    
    def _on_theme_change(self):
        if hasattr(self, '_last_data'):
            self.update_graph(self._last_data)


class NombreFournisseursGraph(BaseFournisseurGraph):
    """Graphique barres - Nombre de fournisseurs ajoutés par mois"""
    
    def __init__(self, parent=None, width=6, height=4, dpi=100):
        super().__init__(parent, width, height, dpi)
        self.month_labels = [
            'Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin',
            'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'
        ]
        self._last_data = {}
    
    def update_graph(self, data):
        """data: dict {mois: nombre}"""
        self._last_data = data or {}
        self.axes.clear()
        self._setup_style()
        
        if not data:
            self.axes.text(0.5, 0.5, 'Aucune donnée', 
                          ha='center', va='center', fontsize=12)
            self.draw()
            return
        
        values = [data.get(mois, 0) for mois in self.month_labels]
        x = np.arange(len(self.month_labels))
        
        c = theme_manager.colors()
        color = c["primary"]
        
        bars = self.axes.bar(x, values, width=0.6, color=color,
                            edgecolor='none', alpha=0.8)
        
        for bar, value in zip(bars, values):
            if value > 0:
                self.axes.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.5,
                    str(int(value)),
                    ha='center', va='bottom',
                    fontsize=8, fontweight='600',
                    color=c["text_primary"]
                )
        
        self.axes.set_xticks(x)
        self.axes.set_xticklabels(self.month_labels, rotation=0)
        self.axes.set_xlim(-0.8, len(self.month_labels) - 0.2)
        
        max_val = max(values) if values else 10
        self.axes.set_ylim(0, max_val * 1.2 if max_val > 0 else 10)
        
        self.axes.set_ylabel(
            "Nombre de fournisseurs",
            color=c["text_secondary"],
            fontsize=10,
            fontweight="500"
        )
        
        self.fig.tight_layout()
        self.draw()


class MontantCommandesGraph(BaseFournisseurGraph):
    """Graphique scatter - Montant des commandes par mois"""
    
    def __init__(self, parent=None, width=6, height=4, dpi=100):
        super().__init__(parent, width, height, dpi)
        self.month_labels = [
            'Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin',
            'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'
        ]
        self._last_data = {}
    
    def update_graph(self, data):
        """data: dict {mois: montant}"""
        self._last_data = data or {}
        self.axes.clear()
        self._setup_style()
        
        if not data:
            self.axes.text(0.5, 0.5, 'Aucune donnée', 
                          ha='center', va='center', fontsize=12)
            self.draw()
            return
        
        values = [data.get(mois, 0) for mois in self.month_labels]
        x = np.arange(len(self.month_labels))
        y = np.array(values, dtype=float)
        
        c = theme_manager.colors()
        color = c["success"]
        
        # Ligne
        self.axes.plot(x, y, color=color, linewidth=2.5, alpha=0.8, marker='o', markersize=6)
        self.axes.fill_between(x, y, color=color, alpha=0.1)
        
        self.axes.set_xticks(x)
        self.axes.set_xticklabels(self.month_labels, rotation=0)
        self.axes.set_xlim(-0.8, len(self.month_labels) - 0.2)
        
        max_val = max(values) if values else 10
        self.axes.set_ylim(0, max_val * 1.2 if max_val > 0 else 10)
        
        self.axes.set_ylabel(
            "Montant (GNF)",
            color=c["text_secondary"],
            fontsize=10,
            fontweight="500"
        )
        
        self.fig.tight_layout()
        self.draw()


class TopFournisseursGraph(BaseFournisseurGraph):
    """Graphique barres horizontales - Top 5 fournisseurs"""
    
    def __init__(self, parent=None, width=6, height=4, dpi=100):
        super().__init__(parent, width, height, dpi)
        self._last_data = {}
    
    def update_graph(self, data):
        """data: dict {nom_fournisseur: quantite_totale}"""
        self._last_data = data or {}
        self.axes.clear()
        self._setup_style()
        
        if not data:
            self.axes.text(0.5, 0.5, 'Aucune donnée', 
                          ha='center', va='center', fontsize=12)
            self.draw()
            return
        
        # Trier et prendre top 5
        sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:5]
        noms = [item[0][:20] + '...' if len(item[0]) > 20 else item[0] 
                for item in sorted_data]
        quantites = [item[1] for item in sorted_data]
        
        c = theme_manager.colors()
        self.axes.barh(noms, quantites, color=c['accent'], alpha=0.8)
        self.axes.set_xlabel('Quantité totale', fontsize=9, color=c['text_secondary'])
        self.axes.tick_params(axis='both', labelsize=8, colors=c['text_secondary'])
        self.axes.spines['top'].set_visible(False)
        self.axes.spines['right'].set_visible(False)
        self.axes.grid(axis='x', alpha=0.3)
        
        self.fig.tight_layout()
        self.draw()


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
        
        # Graphique 1: Nombre de fournisseurs par mois
        self.chart1_frame = self._create_chart_frame("Fournisseurs ajoutés par mois")
        self.chart1_graph = NombreFournisseursGraph(self.chart1_frame, width=6, height=4, dpi=100)
        self.chart1_frame.layout().addWidget(self.chart1_graph)
        
        # Graphique 2: Montant des commandes par mois
        self.chart2_frame = self._create_chart_frame("Montant des commandes par mois")
        self.chart2_graph = MontantCommandesGraph(self.chart2_frame, width=6, height=4, dpi=100)
        self.chart2_frame.layout().addWidget(self.chart2_graph)
        
        # Graphique 3: Top 5 fournisseurs
        self.chart3_frame = self._create_chart_frame("Top 5 fournisseurs par quantité")
        self.chart3_graph = TopFournisseursGraph(self.chart3_frame, width=6, height=4, dpi=100)
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
        
        # Graphique 1: Nombre de fournisseurs par mois
        try:
            if hasattr(self.ctrl, 'get_fournisseurs_par_mois'):
                nombre_data = self.ctrl.get_fournisseurs_par_mois(code_session)
                self.chart1_graph.update_graph(nombre_data or {})
            else:
                self.chart1_graph.update_graph({})
        except:
            self.chart1_graph.update_graph({})
        
        # Graphique 2: Montant des commandes par mois
        try:
            if hasattr(self.ctrl, 'get_montant_commandes_par_mois'):
                montant_data = self.ctrl.get_montant_commandes_par_mois(code_session)
                self.chart2_graph.update_graph(montant_data or {})
            else:
                self.chart2_graph.update_graph({})
        except:
            self.chart2_graph.update_graph({})
        
        # Graphique 3: Top 5 fournisseurs
        try:
            if hasattr(self.ctrl, 'get_top_fournisseurs'):
                top_data = self.ctrl.get_top_fournisseurs(code_session)
                self.chart3_graph.update_graph(top_data or {})
            else:
                self.chart3_graph.update_graph({})
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
