import sys
import os
import logging
from typing import Dict, Optional, List, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service_metier.facture_fournisseur_service import FactureFournisseurService
from models.modele_factureFournisseur import FactureFournisseur


class FactureFournisseurControleur:
    """
    Contrôleur MVC pour la gestion des factures fournisseurs.
    Délègue toute la logique métier à FactureFournisseurService.
    """

    def __init__(self):
        self.service = FactureFournisseurService()
        self.logger  = logging.getLogger(__name__)

    # --------- VALIDATION ---------
    def valider_telephone(self, telephone: str) -> Tuple[bool, str]:
        return self.service.valider_telephone(telephone)

    def valider_mode_payement(self, mode_payement: str) -> Tuple[bool, str]:
        return self.service.valider_mode_payement(mode_payement)

    def valider_codes_obligatoires(self, facture: FactureFournisseur) -> Tuple[bool, str]:
        return self.service.valider_codes_obligatoires(facture)

    def valider_finalisation(self, facture: FactureFournisseur) -> Tuple[bool, str]:
        return self.service.valider_finalisation(facture)

    # --------- CRUD ---------
    def creer_facture(self, facture: FactureFournisseur) -> Tuple[bool, str]:
        return self.service.creer_facture(facture)

    def finaliser_facture(self, facture: FactureFournisseur) -> Tuple[bool, str]:
        return self.service.finaliser_facture(facture)

    def modifier_facture(self, facture: FactureFournisseur) -> Tuple[bool, str]:
        return self.service.modifier_facture(facture)

    def supprimer_facture(self, code_facture_four: str) -> Tuple[bool, str]:
        return self.service.supprimer_facture(code_facture_four)

    # --------- RECUPERATION ---------
    def obtenir_par_code(self, code_facture_four: str) -> Optional[FactureFournisseur]:
        return self.service.obtenir_par_code(code_facture_four)

    def lister_factures(self, code_session: str) -> List[FactureFournisseur]:
        return self.service.lister_factures(code_session)

    def lister_par_fournisseur(self, code_fournisseur: str, code_session: str) -> List[FactureFournisseur]:
        return self.service.lister_par_fournisseur(code_fournisseur, code_session)

    def obtenir_facture_complete(self, code_facture_four: str) -> Optional[Dict]:
        return self.service.obtenir_facture_complete(code_facture_four)

    def rechercher_facture(self, critere: str, code_session: str) -> List[FactureFournisseur]:
        return self.service.rechercher_facture(critere, code_session)

    def obtenir_dernieres_factures(self, code_session: str, limite: int = 10) -> List[Dict]:
        return self.service.obtenir_dernieres_factures(code_session, limite)

    # --------- STATISTIQUES CARDS ---------
    def obtenir_factures_aujourd_hui(self, code_session: str) -> int:
        return self.service.obtenir_factures_aujourd_hui(code_session)

    def obtenir_total_factures_session(self, code_session: str) -> int:
        return self.service.obtenir_total_factures_session(code_session)

    def obtenir_montant_total_session(self, code_session: str) -> float:
        return self.service.obtenir_montant_total_session(code_session)

    def obtenir_montant_aujourd_hui(self, code_session: str) -> float:
        return self.service.obtenir_montant_aujourd_hui(code_session)

    # --------- STATISTIQUES GRAPHES ---------
    def obtenir_factures_par_mois(self, code_session: str) -> Dict[str, int]:
        return self.service.obtenir_factures_par_mois(code_session)

    # --------- CABINET ---------
    def get_cabinet_info(self) -> Dict[str, Optional[str]]:
        return self.service.get_cabinet_info()

    # --------- RAPPORTS PDF LISTE FACTURES ---------
    def generer_rapport_pdf_par_date(self, code_session: str) -> str:
        return self.service.generer_rapport_pdf_par_date(code_session)

    def generer_rapport_pdf_date_precise(self, code_session: str, date_cible) -> str:
        return self.service.generer_rapport_pdf_date_precise(code_session, date_cible)

