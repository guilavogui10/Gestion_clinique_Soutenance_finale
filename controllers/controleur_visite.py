import logging
from typing import List, Dict, Tuple, Optional

from models.model_visite import Visite
from service_metier.visite_service import VisiteService


class VisiteControleur:
    """
    Contrôleur pour la gestion des visites médicales.
    Délègue toute la logique métier à VisiteService (couche service).
    Responsabilités propres au contrôleur :
    - Surveillance multi-visites (alertes agrégées)
    - Calcul de sévérité d'alerte
    """

    def __init__(self):
        self.service = VisiteService()
        self.logger = logging.getLogger(__name__)
        
    # =========================================================================
    # CRUD
    # =========================================================================

    def save_visite(self, visite_objet: Visite) -> Tuple[bool, str]:
        return self.service.save_visite(visite_objet)

    def update_visite(self, visite_update: Visite) -> Tuple[bool, str]:
        return self.service.update_visite(visite_update)

    # =========================================================================
    # PATIENTS
    # =========================================================================

    def read_by_code_patient(self, code_patient: str) -> List:
        return self.service.read_by_code_patient(code_patient)

    # =========================================================================
    # VISITES
    # =========================================================================

    def obtenir_visites_prioritaires(self) -> List[Visite]:
        return self.service.obtenir_visites_prioritaires()

    def rechercher_visites(self, mot_cle: str) -> List[Visite]:
        return self.service.rechercher_visites(mot_cle)

    def lister_suivi_progression(self) -> List[Visite]:
        return self.service.lister_suivi_progression()

    def changer_etape_visite(self, code_visite: str, nouveau_statut: str) -> Tuple[bool, str]:
        return self.service.changer_etape_visite(code_visite, nouveau_statut)

    def obtenir_dossier_complet_visite(self, code_visite: str) -> Dict:
        return self.service.obtenir_dossier_complet_visite(code_visite)

    # =========================================================================
    # STATISTIQUES
    # =========================================================================

    def obtenir_stats_mensuelles(self) -> Dict[str, int]:
        return self.service.obtenir_stats_mensuelles()

    def get_stat_visites_par_age(self) -> Dict:
        return self.service.get_stat_visites_par_age()

    def obtenir_statistiques_performance(self) -> Dict:
        return self.service.obtenir_statistiques_performance()

    def obtenir_bilan_performance_session(self) -> Dict:
        return self.service.obtenir_bilan_performance_session()

    def obtenir_visites_actives_avec_duree(self) -> List[Dict]:
        return self.service.obtenir_visites_actives_avec_duree()

    def obtenir_nombre_visites_aujourdhui(self) -> int:
        return self.service.obtenir_nombre_visites_aujourdhui()

    def obtenir_nombre_visites_terminees(self) -> int:
        return self.service.obtenir_nombre_visites_terminees()

    def obtenir_nombre_urgences(self) -> int:
        return self.service.obtenir_nombre_urgences()

    # =========================================================================
    # DURÉES ET TEMPS
    # =========================================================================

    def obtenir_temps_ecoule(self, code_visite: str) -> str:
        return self.service.obtenir_temps_ecoule(code_visite)

    def obtenir_bilan_temporel_visite(self, code_visite: str) -> str:
        return self.service.obtenir_bilan_temporel_visite(code_visite)

    def obtenir_analyse_flux_hebdomadaire(self) -> List[Dict]:
        return self.service.obtenir_analyse_flux_hebdomadaire()

    def verifier_temps_attente_critique(self, code_visite: str, seuil_minutes: int = 20) -> Tuple[bool, int, Optional[str]]:
        return self.service.verifier_temps_attente_critique(code_visite, seuil_minutes)

    # =========================================================================
    # SESSION & CABINET
    # =========================================================================

    def verifier_session_active(self) -> Tuple[bool, str]:
        return self.service.verifier_session_active()

    def get_cabinet_info(self) -> Dict[str, Optional[str]]:
        return self.service.get_cabinet_info()

    # =========================================================================
    # SURVEILLANCE MULTI-VISITES (logique propre au contrôleur)
    # =========================================================================

    def obtenir_visites_surveillance_active(self) -> List[str]:
        """Retourne les codes des visites non terminées nécessitant surveillance."""
        try:
            visites = self.service.obtenir_visites_prioritaires()
            return [
                v.get_code_visite() for v in visites
                if v.get_statut_visite().lower() not in ('terminée', 'libéré')
            ]
        except Exception as e:
            self.logger.error(f"Erreur surveillance active: {e}")
            return []

    def verifier_alertes_temps_attente(self, codes_visites: List[str], seuil_minutes: int = 45) -> List[Dict]:
        """Vérifie les alertes de temps d'attente pour plusieurs visites."""
        alertes = []
        for code_visite in codes_visites:
            try:
                est_alerte, temps, statut = self.service.verifier_temps_attente_critique(code_visite, seuil_minutes)
                if est_alerte:
                    alertes.append({
                        'code_visite': code_visite,
                        'temps_attente': temps,
                        'statut': statut,
                        'severite': self._determiner_severite_alerte(temps)
                    })
            except Exception as e:
                self.logger.error(f"Erreur alerte {code_visite}: {e}")
        return alertes

    def _determiner_severite_alerte(self, temps_attente: int) -> str:
        """Détermine la sévérité d'une alerte selon le temps d'attente."""
        if temps_attente > 90:
            return "critique"
        elif temps_attente > 60:
            return "elevee"
        elif temps_attente > 30:
            return "moyenne"
        return "faible"
