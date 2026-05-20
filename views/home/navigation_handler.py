"""
navigation_handler.py
---------------------
Gestionnaire de navigation pour la page d'accueil.
Gère les redirections vers les différentes pages du dashboard.
"""

from PySide6.QtCore import QObject, Signal


class NavigationHandler(QObject):
    """
    Gestionnaire de navigation pour la page d'accueil.
    Émet des signaux pour demander la navigation vers d'autres pages.
    """
    
    # Signal pour demander la navigation vers une page
    navigate_requested = Signal(str)  # Nom de la page
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def navigate_to_rendez_vous(self):
        """Navigue vers la page Rendez-vous."""
        self.navigate_requested.emit("Rendez-vous")
    
    def navigate_to_consultation(self):
        """Navigue vers la page Consultations."""
        self.navigate_requested.emit("Consultations")
    
    def navigate_to_examen(self):
        """Navigue vers la page Examens."""
        self.navigate_requested.emit("Examens")
    
    def navigate_to_chirurgie(self):
        """Navigue vers la page Chirurgies."""
        self.navigate_requested.emit("Chirurgies")
    
    def navigate_to_lunette(self):
        """Navigue vers la page Lunettes."""
        self.navigate_requested.emit("Lunettes")
    
    def navigate_to_pharmacie(self):
        """Navigue vers la page Pharmacie."""
        self.navigate_requested.emit("Pharmacie")
