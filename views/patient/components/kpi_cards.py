"""
KPI Cards Section - Affiche les statistiques des patients
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout
from PySide6.QtCore import Qt
from views.shared.stat_card import StatCard
from views.shared.theme_manager import theme_manager


class KpiCardsSection(QWidget):
    """Section des cartes KPI pour les statistiques patients"""
    
    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.controleur = controleur
        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)  # Centrer horizontalement
        
        c = theme_manager.colors()
        
        # Créer les cartes KPI
        self.card_total = StatCard("Total Patients", "0", "fa5s.users", c['primary'])
        self.card_femmes = StatCard("Femmes", "0", "fa5s.venus", c['danger'])
        self.card_hommes = StatCard("Hommes", "0", "fa5s.mars", c['info'])
        
        # Ajouter au layout
        layout.addWidget(self.card_total)
        layout.addWidget(self.card_femmes)
        layout.addWidget(self.card_hommes)
        layout.addStretch()
    
    def rafraichir(self):
        """Rafraîchit les statistiques"""
        try:
            stats = self.controleur.statistique()
            self.card_total.lbl_value.setText(str(stats.get('total', 0)))
            self.card_femmes.lbl_value.setText(str(stats.get('filles', 0)))
            self.card_hommes.lbl_value.setText(str(stats.get('garçons', 0)))
        except Exception as e:
            print(f"Erreur rafraîchissement KPI: {e}")
    
    def apply_theme(self):
        """Applique le thème actuel"""
        c = theme_manager.colors()
        self.setStyleSheet(f"background: transparent;")
        
        # Mettre à jour les couleurs des cartes
        if hasattr(self, 'card_total'):
            self.card_total.icon_color = c['primary']
            self.card_femmes.icon_color = c['danger']
            self.card_hommes.icon_color = c['info']
