"""
services_section.py
-------------------
Section grille des services de la page d'accueil.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel

from views.shared.theme_manager import theme_manager
from views.home.components import ServiceCard


class ServicesSection(QWidget):
    """
    Section affichant la grille des 6 services principaux.
    """
    
    service_clicked = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._apply_theme()
        theme_manager.theme_changed.connect(self._apply_theme)
    
    def _setup_ui(self):
        """Configure l'interface de la section services."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 8, 20, 10)
        layout.setSpacing(20)
        
        # Grille des services (1x6 - tous sur une ligne)
        grid = QGridLayout()
        grid.setSpacing(3)
        grid.setHorizontalSpacing(3)
        grid.setVerticalSpacing(3)
        
        # Définition des services
        services = [
            ('fa5s.user-md', 'Consultation', 
             'Examen complet de la vue\net diagnostic précis', '#3B82F6'),
            ('fa5s.microscope', 'Examens', 
             'Tests approfondis avec des\néquipements de pointe', '#10B981'),
            ('fa5s.procedures', 'Chirurgie', 
             'Traitements chirurgicaux\nsûrs et personnalisés', '#8B5CF6'),
            ('fa5s.glasses', 'Optique', 
             'Large choix de montures\net verres de qualité', '#F59E0B'),
            ('fa5s.pills', 'Pharmacie', 
             'Médicaments et produits\nspécialisés', '#EF4444'),
            ('fa5s.calendar-check', 'Rendez-vous', 
             'Prenez rendez-vous\nen ligne facilement', '#06B6D4'),
        ]
        
        # Créer les cartes - toutes sur une seule ligne
        for i, (icon, title, desc, color) in enumerate(services):
            card = ServiceCard(icon, title, desc, color)
            card.clicked.connect(self.service_clicked.emit)
            grid.addWidget(card, 0, i)
        
        layout.addLayout(grid)
    
    def _apply_theme(self):
        """Applique le thème actuel."""
        c = theme_manager.colors()
        self.setStyleSheet(f"""
            ServicesSection {{
                background-color: {c['bg_main']};
                border: none;
            }}
        """)
