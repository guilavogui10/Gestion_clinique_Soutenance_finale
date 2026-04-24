from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QToolTip
from PySide6.QtCore import QTimer, Qt, QPoint
from PySide6.QtGui import QColor

from views.shared.theme_manager import theme_manager


class PerformanceMonitor(QWidget):
    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.controleur = controleur
        self.code_visite = None
        self.seuil_alerte = 20  # Ce seuil sera affiné par le DAO
        
        # Timer de rafraîchissement (60 secondes pour le temps médical)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_logic)
        
        self.setup_ui()
        theme_manager.theme_changed.connect(self._apply_theme)

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Le label qui affiche le temps (ex: 0h 15min)
        self.time_display = QLabel("h --min")
        self.time_display.setAlignment(Qt.AlignCenter)
        self.time_display.setWordWrap(False) 
        self.time_display.setMinimumWidth(120)
        
        # Petit indicateur visuel (point ou texte réduit)
        self.alert_dot = QLabel("●")
        self.alert_dot.setAlignment(Qt.AlignCenter)
        
        self.layout.addWidget(self.time_display)
        self.layout.addWidget(self.alert_dot)

        self._apply_theme()

    def start_monitoring(self, code_visite: str):
        self.code_visite = code_visite
        self.refresh_logic()
        self.timer.start(60000)

    def refresh_logic(self):
        """Récupère les données du contrôleur et met à jour l'interface."""
        if not self.code_visite:
            return

        # 1. Obtenir le temps écoulé (Affichage simple)
        duree_actuelle = self.controleur.obtenir_temps_ecoule(self.code_visite)
        self.time_display.setText(duree_actuelle)

        # 2. Vérifier si le temps dépasse le seuil du DAO
        # Retourne (alerte: bool, temps: int, statut: str)
        alerte, temps_attente, statut_service = self.controleur.verifier_temps_attente_critique(
            self.code_visite, self.seuil_alerte
        )

        self._appliquer_alerte(alerte, temps_attente, statut_service)

    def _appliquer_alerte(self, est_alerte: bool, temps: int, service: str):
        """Modifie l'aspect visuel et prépare le message de survol."""
        c = theme_manager.colors()
        nom_service = service if service else "Accueil"

        if est_alerte:
            color = c['danger'] if temps > 40 else c['warning']
            self.time_display.setStyleSheet(
                f"color: {color}; font-weight: bold; font-size: 11px;"
            )
            self.alert_dot.setStyleSheet(f"color: {color}; font-size: 10px;")
            
            msg = (f"⚠️ ALERTE : Temps dépassé !\n"
                f"Service : {nom_service}\n"
                f"En attente depuis : {temps} minutes")
        else:
            self.time_display.setStyleSheet(
                f"color: {c['text_secondary']}; font-weight: bold; font-size: 11px;"
            )
            self.alert_dot.setStyleSheet(f"color: {c['success']}; font-size: 10px;")
            msg = f"Statut : {nom_service}\nTemps passé : {temps} min"

        self.setToolTip(msg)

    def _apply_theme(self):
        """Applique le thème courant sur les éléments par défaut."""
        c = theme_manager.colors()
        self.time_display.setStyleSheet(
            f"font-weight: bold; font-family: 'Segoe UI', sans-serif;"
            f"color: {c['text_secondary']}; font-size: 11px;"
        )
        self.alert_dot.setStyleSheet(f"color: {c['border']}; font-size: 10px;")