"""
stats_section.py
----------------
Section statistiques (KPIs) de la page d'accueil.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from views.shared.theme_manager import theme_manager
from views.home.components import StatCard


class StatsSection(QWidget):
    """
    Section affichant les 4 KPIs principaux.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._apply_theme()
        theme_manager.theme_changed.connect(self._apply_theme)
    
    def _setup_ui(self):
        """Configure l'interface de la section stats."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 10, 30, 20)
        layout.setSpacing(0)
        
        # Ligne des 4 KPIs
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(30)
        
        # Créer les 4 cartes statistiques
        self.card_medecins = StatCard(
            'fa5s.user-md',
            '15+',
            'Médecins spécialistes',
            '#3B82F6'
        )
        stats_layout.addWidget(self.card_medecins)
        
        self.card_patients = StatCard(
            'fa5s.users',
            '10K+',
            'Patients satisfaits',
            '#10B981'
        )
        stats_layout.addWidget(self.card_patients)
        
        self.card_experience = StatCard(
            'fa5s.calendar-alt',
            '25+',
            'Années d\'expérience',
            '#8B5CF6'
        )
        stats_layout.addWidget(self.card_experience)
        
        self.card_satisfaction = StatCard(
            'fa5s.trophy',
            '98%',
            'Taux de satisfaction',
            '#F59E0B'
        )
        stats_layout.addWidget(self.card_satisfaction)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
    
    def _apply_theme(self):
        """Applique le thème actuel."""
        c = theme_manager.colors()
        self.setStyleSheet(f"""
            StatsSection {{
                background-color: {c['bg_main']};
                border: none;
            }}
        """)
    
    def update_stats(self, medecins: int, patients: int, experience: int, satisfaction: int):
        """Met à jour les valeurs des statistiques."""
        self.card_medecins.update_value(f"{medecins}+")
        self.card_patients.update_value(f"{patients//1000}K+" if patients >= 1000 else f"{patients}+")
        self.card_experience.update_value(f"{experience}+")
        self.card_satisfaction.update_value(f"{satisfaction}%")
