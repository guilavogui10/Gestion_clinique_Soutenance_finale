import sys
import os
import logging
from typing import Dict, Optional, List, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.modele_panier_facture import PanierFacture
from service_metier.panier_facture_patient_service import PanierFacturePatientService


class PanierFacturePatientControleur:
    """
    Controleur MVC pour la gestion des lignes panier de la facture patient.
    Délègue toute la logique métier au service PanierFacturePatientService.
    """

    def __init__(self):
        self.service = PanierFacturePatientService()
        self.logger  = logging.getLogger(__name__)

    # =========================================================================
    # VALIDATION — délégation au service
    # =========================================================================

    def valider_designation(self, designation: str) -> Tuple[bool, str]:
        return self.service.valider_designation(designation)

    def valider_quantite(self, quantite) -> Tuple[bool, str]:
        return self.service.valider_quantite(quantite)

    def valider_prix(self, prix) -> Tuple[bool, str]:
        return self.service.valider_prix(prix)

    def valider_codes_obligatoires(self, ligne: PanierFacture) -> Tuple[bool, str]:
        return self.service.valider_codes_obligatoires(ligne)

    def valider_ligne(self, ligne: PanierFacture) -> Tuple[bool, str]:
        return self.service.valider_ligne(ligne)

    # =========================================================================
    # CRUD
    # =========================================================================

    def ajouter_ligne(self, ligne: PanierFacture) -> Tuple[bool, str]:
        return self.service.ajouter_ligne(ligne)

    def modifier_ligne(self, ligne: PanierFacture) -> Tuple[bool, str]:
        return self.service.modifier_ligne(ligne)

    def supprimer_ligne(self, code_paniere: str) -> Tuple[bool, str]:
        return self.service.supprimer_ligne(code_paniere)

    def supprimer_lignes_facture(self, code_facture: str) -> Tuple[bool, str]:
        return self.service.supprimer_lignes_facture(code_facture)

    # =========================================================================
    # RÉCUPÉRATION
    # =========================================================================

    def obtenir_par_code(self, code_paniere: str) -> Optional[PanierFacture]:
        return self.service.obtenir_par_code(code_paniere)

    def lister_par_facture(self, code_facture: str) -> List[PanierFacture]:
        return self.service.lister_par_facture(code_facture)

    # =========================================================================
    # STATISTIQUES
    # =========================================================================

    def obtenir_total_facture(self, code_facture: str) -> float:
        return self.service.obtenir_total_facture(code_facture)

    def obtenir_repartition_par_service(self, code_session: str) -> List[Dict]:
        return self.service.obtenir_repartition_par_service(code_session)

    def obtenir_resume_economie_session(self, code_session: str) -> Dict:
        return self.service.obtenir_resume_economie_session(code_session)

    def obtenir_top_services_par_revenus(self, code_session: str, limite: int = 5) -> List[Dict]:
        return self.service.obtenir_top_services_par_revenus(code_session, limite)

    def obtenir_volume_vs_revenus_par_service(self, code_session: str) -> List[Dict]:
        return self.service.obtenir_volume_vs_revenus_par_service(code_session)

    def obtenir_top_services_par_volume(self, code_session: str, limite: int = 10) -> List[Dict]:
        return self.service.obtenir_top_services_par_volume(code_session, limite)

    def obtenir_evolution_chiffre_affaires_par_mois(self, code_session: str) -> Dict:
        return self.service.obtenir_evolution_chiffre_affaires_par_mois(code_session)

    def obtenir_apercu_facture_detail(self, code_facture: str) -> Dict:
        return self.service.obtenir_apercu_facture_detail(code_facture)

    def obtenir_derniere_facture_payee_apercu(self, code_session: str) -> Dict:
        return self.service.obtenir_derniere_facture_payee_apercu(code_session)

    # =========================================================================
    # INFORMATIONS CABINET
    # =========================================================================

    def get_cabinet_info(self) -> Dict[str, Optional[str]]:
        return self.service.get_cabinet_info()
