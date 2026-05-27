"""
accueil_view.py
---------------
Vue principale de la page d'accueil.
"""

from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea

from views.shared.theme_manager import theme_manager
from views.home.sections import HeroSection, ServicesSection, StatsSection
from views.home.navigation_handler import NavigationHandler


class _StatsWorker(QThread):
    """Thread de chargement des statistiques — ne bloque pas l'UI."""
    stats_chargees = Signal(int, int, int, int)

    def __init__(self, ctrl):
        super().__init__()
        self._ctrl = ctrl

    def run(self):
        try:
            medecins = self._ctrl.obtenir_nombre_medecins()
            patients = self._ctrl.obtenir_nombre_patients_satisfaits()
            experience = self._ctrl.obtenir_annees_experience()
            satisfaction = self._ctrl.obtenir_taux_satisfaction()
            self.stats_chargees.emit(medecins, patients, experience, satisfaction)
        except Exception:
            pass


class AccueilView(QWidget):
    """
    Vue principale de la page d'accueil.
    Assemble les sections Hero, Services et Stats.
    Les statistiques sont chargées en arrière-plan (non-bloquant).
    """

    navigate_to = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Import différé : AccueilControleur est lourd (8 services)
        # mais son __init__ ne fait pas de SQL → acceptable ici
        from controllers.controleur_accueil import AccueilControleur
        self.ctrl = AccueilControleur()
        self.nav_handler = NavigationHandler(self)
        self._worker = None

        self._setup_ui()
        self._connect_signals()
        self._apply_theme()
        theme_manager.theme_changed.connect(self._apply_theme)

        # Chargement SQL en arrière-plan — UI déjà visible avec valeurs par défaut
        self._charger_stats_async()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFrameShape(QScrollArea.NoFrame)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        self.hero_section = HeroSection()
        container_layout.addWidget(self.hero_section)

        self.services_section = ServicesSection()
        container_layout.addWidget(self.services_section)

        self.stats_section = StatsSection()
        container_layout.addWidget(self.stats_section)

        container_layout.addStretch()

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _connect_signals(self):
        self.hero_section.prendre_rdv_clicked.connect(
            self.nav_handler.navigate_to_rendez_vous
        )
        self.hero_section.voir_services_clicked.connect(self._scroll_to_services)
        self.hero_section.service_selected.connect(self._on_service_clicked)
        self.services_section.service_clicked.connect(self._on_service_clicked)
        self.nav_handler.navigate_requested.connect(self.navigate_to.emit)

    def _charger_stats_async(self):
        """Lance le chargement des stats dans un thread séparé."""
        self._worker = _StatsWorker(self.ctrl)
        self._worker.stats_chargees.connect(self.stats_section.update_stats)
        self._worker.start()

    def _scroll_to_services(self):
        pass

    def _on_service_clicked(self, service_name: str):
        service_map = {
            'Consultation': self.nav_handler.navigate_to_consultation,
            'Examens': self.nav_handler.navigate_to_examen,
            'Chirurgie': self.nav_handler.navigate_to_chirurgie,
            'Optique': self.nav_handler.navigate_to_lunette,
            'Lunettes': self.nav_handler.navigate_to_lunette,
            'Pharmacie': self.nav_handler.navigate_to_pharmacie,
            'Rendez-vous': self.nav_handler.navigate_to_rendez_vous,
        }
        nav_method = service_map.get(service_name)
        if nav_method:
            nav_method()

    def _apply_theme(self):
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
        self._apply_theme()
