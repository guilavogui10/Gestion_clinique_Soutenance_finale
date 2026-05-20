"""
Charts Section - Section des graphiques statistiques
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from views.shared.graph_factory import PatientGraphs
from views.shared.theme_manager import theme_manager


class ChartsSection(QWidget):
    """Section des graphiques"""
    
    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.controleur = controleur
        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Graphiques
        self.graph_factory = PatientGraphs()
        layout.addWidget(self.graph_factory)
    
    def update_data(self):
        """Met à jour les graphiques avec les nouvelles données"""
        try:
            stats = self.controleur.statistique()
            self.graph_factory.update_charts(stats)
        except Exception as e:
            print(f"Erreur mise à jour graphiques: {e}")
    
    def apply_theme(self):
        """Applique le thème actuel"""
        self.setStyleSheet("background: transparent;")
