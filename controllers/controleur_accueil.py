"""
controleur_accueil.py
---------------------
Contrôleur pour la gestion de la page d'accueil.

Responsabilités:
- Coordination entre la vue d'accueil et le service métier
- Récupération des statistiques globales
- Gestion des informations du cabinet
"""

import logging
from typing import Dict, Optional, Tuple

from service_metier.accueil_service import AccueilService


class AccueilControleur:
    """
    Contrôleur pour la page d'accueil.
    Fait le pont entre la vue et le service métier.
    """

    def __init__(self):
        """Initialise le contrôleur avec le service d'accueil."""
        self.service = AccueilService()
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # STATISTIQUES GLOBALES (Section bas - KPIs)
    # =========================================================================

    def obtenir_nombre_medecins(self) -> int:
        """
        Récupère le nombre de médecins spécialistes.
        
        Returns:
            int: Nombre de médecins
        """
        try:
            return self.service.obtenir_nombre_medecins()
        except Exception as e:
            self.logger.error(f"Erreur obtenir_nombre_medecins: {e}")
            return 15

    def obtenir_nombre_patients_satisfaits(self) -> int:
        """
        Récupère le nombre de patients satisfaits.
        
        Returns:
            int: Nombre de patients
        """
        try:
            return self.service.obtenir_nombre_patients_satisfaits()
        except Exception as e:
            self.logger.error(f"Erreur obtenir_nombre_patients_satisfaits: {e}")
            return 10000

    def obtenir_annees_experience(self) -> int:
        """
        Récupère le nombre d'années d'expérience du cabinet.
        
        Returns:
            int: Années d'expérience
        """
        try:
            return self.service.obtenir_annees_experience()
        except Exception as e:
            self.logger.error(f"Erreur obtenir_annees_experience: {e}")
            return 25

    def obtenir_taux_satisfaction(self) -> int:
        """
        Récupère le taux de satisfaction en pourcentage.
        
        Returns:
            int: Taux de satisfaction (0-100)
        """
        try:
            return self.service.obtenir_taux_satisfaction()
        except Exception as e:
            self.logger.error(f"Erreur obtenir_taux_satisfaction: {e}")
            return 98

    # =========================================================================
    # STATISTIQUES PAR SERVICE (Section milieu - cartes)
    # =========================================================================

    def obtenir_nombre_consultations(self, code_session: str) -> int:
        """
        Récupère le nombre de consultations.
        
        Args:
            code_session: Code de la session active
            
        Returns:
            int: Nombre de consultations
        """
        try:
            return self.service.obtenir_nombre_consultations(code_session)
        except Exception as e:
            self.logger.error(f"Erreur obtenir_nombre_consultations: {e}")
            return 0

    def obtenir_nombre_examens(self, code_session: str) -> int:
        """
        Récupère le nombre d'examens.
        
        Args:
            code_session: Code de la session active
            
        Returns:
            int: Nombre d'examens
        """
        try:
            return self.service.obtenir_nombre_examens(code_session)
        except Exception as e:
            self.logger.error(f"Erreur obtenir_nombre_examens: {e}")
            return 0

    def obtenir_nombre_chirurgies(self, code_session: str) -> int:
        """
        Récupère le nombre de chirurgies.
        
        Args:
            code_session: Code de la session active
            
        Returns:
            int: Nombre de chirurgies
        """
        try:
            return self.service.obtenir_nombre_chirurgies(code_session)
        except Exception as e:
            self.logger.error(f"Erreur obtenir_nombre_chirurgies: {e}")
            return 0

    def obtenir_nombre_commandes_lunettes(self, code_session: str) -> int:
        """
        Récupère le nombre de commandes de lunettes.
        
        Args:
            code_session: Code de la session active
            
        Returns:
            int: Nombre de commandes
        """
        try:
            return self.service.obtenir_nombre_commandes_lunettes(code_session)
        except Exception as e:
            self.logger.error(f"Erreur obtenir_nombre_commandes_lunettes: {e}")
            return 0

    def obtenir_nombre_prescriptions(self, code_session: str) -> int:
        """
        Récupère le nombre de prescriptions.
        
        Args:
            code_session: Code de la session active
            
        Returns:
            int: Nombre de prescriptions
        """
        try:
            return self.service.obtenir_nombre_prescriptions(code_session)
        except Exception as e:
            self.logger.error(f"Erreur obtenir_nombre_prescriptions: {e}")
            return 0

    def obtenir_nombre_rendez_vous(self, code_session: str) -> int:
        """
        Récupère le nombre de rendez-vous.
        
        Args:
            code_session: Code de la session active
            
        Returns:
            int: Nombre de rendez-vous
        """
        try:
            return self.service.obtenir_nombre_rendez_vous(code_session)
        except Exception as e:
            self.logger.error(f"Erreur obtenir_nombre_rendez_vous: {e}")
            return 0

    # =========================================================================
    # INFORMATIONS CABINET
    # =========================================================================

    def obtenir_info_cabinet(self) -> Dict[str, Optional[str]]:
        """
        Récupère les informations du cabinet.
        
        Returns:
            Dict: Informations du cabinet (nom, adresse, logo)
        """
        try:
            return self.service.obtenir_info_cabinet()
        except Exception as e:
            self.logger.error(f"Erreur obtenir_info_cabinet: {e}")
            return {
                "nom_cabinet": "VisionCare",
                "adresse_cabinet": "Clinique Ophtalmologique",
                "logo_url": None
            }

    # =========================================================================
    # VÉRIFICATION SESSION
    # =========================================================================

    def verifier_session_active(self) -> Tuple[bool, str]:
        """
        Vérifie qu'une session de travail est active.
        
        Returns:
            Tuple: (session_active, code_session_ou_message)
        """
        try:
            return self.service.verifier_session_active()
        except Exception as e:
            self.logger.error(f"Erreur verifier_session_active: {e}")
            return False, "Erreur de vérification de session"
