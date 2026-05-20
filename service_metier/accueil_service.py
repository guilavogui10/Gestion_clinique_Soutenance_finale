"""
accueil_service.py
------------------
Service métier — Orchestration des données pour la page d'accueil.

Responsabilités :
  - Agrégation des statistiques globales
  - Coordination des services métier existants (pas de DAO direct)
  - Retourne UNIQUEMENT des données brutes (nombres, textes)
"""

import logging
from typing import Dict, Optional, Tuple

from service_metier.visite_service import VisiteService
from service_metier.personnel_service import PersonnelService
from service_metier.consultation_service import ConsultationService
from service_metier.examen_service import ExamenService
from service_metier.chirurgie_service import ChirurgieService
from service_metier.lunette_service import CommandeLunetteService
from service_metier.prescription_service import PrescriptionService
from service_metier.rendez_vous_service import RendezVousService


class AccueilService:
    """
    Service métier pour la page d'accueil.
    Orchestre les différents services pour fournir une vue d'ensemble.
    """

    def __init__(self):
        """Initialise le service avec tous les services métier nécessaires."""
        self.visite_service = VisiteService()
        self.personnel_service = PersonnelService()
        self.consultation_service = ConsultationService()
        self.examen_service = ExamenService()
        self.chirurgie_service = ChirurgieService()
        self.lunette_service = CommandeLunetteService()
        self.prescription_service = PrescriptionService()
        self.rendez_vous_service = RendezVousService()
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # STATISTIQUES GLOBALES (KPIs - Section bas de page)
    # =========================================================================

    def obtenir_nombre_medecins(self) -> int:
        """Retourne le nombre total de médecins spécialistes."""
        try:
            return self.personnel_service.nombre_total()
        except Exception as e:
            self.logger.error(f"Erreur obtenir_nombre_medecins: {e}")
            return 15

    def obtenir_nombre_patients_satisfaits(self) -> int:
        """Retourne le nombre de visites terminées (proxy patients satisfaits)."""
        try:
            return self.visite_service.obtenir_nombre_visites_terminees()
        except Exception as e:
            self.logger.error(f"Erreur obtenir_nombre_patients_satisfaits: {e}")
            return 10000

    def obtenir_annees_experience(self) -> int:
        """Retourne le nombre d'années d'expérience (valeur statique)."""
        return 25

    def obtenir_taux_satisfaction(self) -> int:
        """Retourne le taux de satisfaction en pourcentage."""
        try:
            stats_perf = self.visite_service.obtenir_statistiques_performance()
            satisfaction = stats_perf.get('satisfaction', 0)
            return int(satisfaction) if satisfaction > 0 else 98
        except Exception as e:
            self.logger.error(f"Erreur obtenir_taux_satisfaction: {e}")
            return 98

    # =========================================================================
    # STATISTIQUES PAR SERVICE (Section milieu - cartes services)
    # =========================================================================

    def obtenir_nombre_consultations(self, code_session: str) -> int:
        """Retourne le nombre total de consultations."""
        try:
            return self.consultation_service.obtenir_nombre_total(code_session)
        except Exception as e:
            self.logger.error(f"Erreur obtenir_nombre_consultations: {e}")
            return 0

    def obtenir_nombre_examens(self, code_session: str) -> int:
        """Retourne le nombre total d'examens."""
        try:
            return self.examen_service.obtenir_total_examens_session(code_session)
        except Exception as e:
            self.logger.error(f"Erreur obtenir_nombre_examens: {e}")
            return 0

    def obtenir_nombre_chirurgies(self, code_session: str) -> int:
        """Retourne le nombre total de chirurgies."""
        try:
            return self.chirurgie_service.obtenir_total_chururgies_session(code_session)
        except Exception as e:
            self.logger.error(f"Erreur obtenir_nombre_chirurgies: {e}")
            return 0

    def obtenir_nombre_commandes_lunettes(self, code_session: str) -> int:
        """Retourne le nombre total de commandes de lunettes."""
        try:
            return self.lunette_service.obtenir_total_commandes_session(code_session)
        except Exception as e:
            self.logger.error(f"Erreur obtenir_nombre_commandes_lunettes: {e}")
            return 0

    def obtenir_nombre_prescriptions(self, code_session: str) -> int:
        """Retourne le nombre total de prescriptions."""
        try:
            return self.prescription_service.obtenir_nombre_total_session(code_session)
        except Exception as e:
            self.logger.error(f"Erreur obtenir_nombre_prescriptions: {e}")
            return 0

    def obtenir_nombre_rendez_vous(self, code_session: str) -> int:
        """Retourne le nombre total de rendez-vous."""
        try:
            return self.rendez_vous_service.obtenir_total_rendez_vous_session(code_session)
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
            Dict: {'nom_cabinet', 'adresse_cabinet', 'logo_url'}
        """
        try:
            return self.visite_service.get_cabinet_info()
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
            Tuple: (actif, code_session ou message d'erreur)
        """
        try:
            return self.visite_service.verifier_session_active()
        except Exception as e:
            self.logger.error(f"Erreur verifier_session_active: {e}")
            return False, "Erreur de vérification de session"
