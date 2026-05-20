"""
accueil_view.py
---------------
Vue principale de la page d'accueil.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea

from views.shared.theme_manager import theme_manager
from views.home.sections import HeroSection, ServicesSection, StatsSection
from views.home.navigation_handler import NavigationHandler
from controllers.controleur_accueil import AccueilControleur


class AccueilView(QWidget):
    """
    Vue principale de la page d'accueil.
    Assemble les sections Hero, Services et Stats.
    """
    
    navigate_to = Signal(str)  # Signal pour naviguer vers une autre page
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ctrl = AccueilControleur()
        self.nav_handler = NavigationHandler(self)
        self._setup_ui()
        self._connect_signals()
        self._load_data()
        self._apply_theme()
        theme_manager.theme_changed.connect(self._apply_theme)
    
    def _setup_ui(self):
        """Configure l'interface de la vue."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Scroll area pour le contenu
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        # Container pour les sections
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Section Hero
        self.hero_section = HeroSection()
        container_layout.addWidget(self.hero_section)
        
        # Section Services
        self.services_section = ServicesSection()
        container_layout.addWidget(self.services_section)
        
        # Section Stats
        self.stats_section = StatsSection()
        container_layout.addWidget(self.stats_section)
        
        container_layout.addStretch()
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
    
    def _connect_signals(self):
        """Connecte les signaux."""
        # Boutons Hero
        self.hero_section.prendre_rdv_clicked.connect(
            self.nav_handler.navigate_to_rendez_vous
        )
        self.hero_section.voir_services_clicked.connect(
            self._scroll_to_services
        )
        self.hero_section.service_selected.connect(self._on_service_clicked)
        
        # Cartes de services
        self.services_section.service_clicked.connect(self._on_service_clicked)
        
        # Connecter le signal de navigation du handler au signal de la vue
        self.nav_handler.navigate_requested.connect(self.navigate_to.emit)
    
    def _load_data(self):
        """Charge les données depuis le contrôleur."""
        try:
            # Vérifier la session
            actif, code_session = self.ctrl.verifier_session_active()
            
            # Charger les statistiques globales
            medecins = self.ctrl.obtenir_nombre_medecins()
            patients = self.ctrl.obtenir_nombre_patients_satisfaits()
            experience = self.ctrl.obtenir_annees_experience()
            satisfaction = self.ctrl.obtenir_taux_satisfaction()
            
            # Mettre à jour l'affichage
            self.stats_section.update_stats(medecins, patients, experience, satisfaction)
            
        except Exception as e:
            print(f"Erreur lors du chargement des données: {e}")
    
    def _scroll_to_services(self):
        """Scroll vers la section services."""
        # TODO: Implémenter le scroll automatique
        pass
    
    def _on_service_clicked(self, service_name: str):
        """Gère le clic sur une carte de service ou sélection du menu."""
        # Mapper les noms de services vers les méthodes de navigation
        service_map = {
            'Consultation': self.nav_handler.navigate_to_consultation,
            'Examens': self.nav_handler.navigate_to_examen,
            'Chirurgie': self.nav_handler.navigate_to_chirurgie,
            'Optique': self.nav_handler.navigate_to_lunette,
            'Lunettes': self.nav_handler.navigate_to_lunette,  # Alias
            'Pharmacie': self.nav_handler.navigate_to_pharmacie,
            'Rendez-vous': self.nav_handler.navigate_to_rendez_vous
        }
        
        nav_method = service_map.get(service_name)
        if nav_method:
            nav_method()
    
    def _apply_theme(self):
        """Applique le thème actuel."""
        c = theme_manager.colors()
        self.setStyleSheet(f"""
            AccueilView {{
                background-color: {c['bg_main']};
                border: none;
            }}
            QScrollArea {{
                background-color: {c['bg_main']};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {c['bg_main']};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {c['border']};
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {c['primary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
    
    def apply_theme(self):
        """Méthode publique pour appliquer le thème (appelée par DashboardView)."""
        self._apply_theme()
