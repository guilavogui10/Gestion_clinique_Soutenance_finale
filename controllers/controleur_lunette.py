import sys
import logging
from typing import Dict, Optional

sys.path.append(__import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))))

from service_metier.lunette_service import CommandeLunetteService


class CommandeLunetteControleur:
    """
    Controleur MVC pour la gestion des commandes de lunettes.
    Delegue toutes les operations au service metier.
    """

    def __init__(self):
        self.service = CommandeLunetteService()
        self.logger  = logging.getLogger(__name__)

    # =========================================================================
    # METHODES CRUD
    # =========================================================================

    def creer_commande(self, commande):
        return self.service.creer_commande(commande)

    def modifier_commande(self, commande):
        return self.service.modifier_commande(commande)

    def supprimer_commande(self, code: str):
        return self.service.supprimer_commande(code)

    # =========================================================================
    # METHODES DE RECUPERATION
    # =========================================================================

    def obtenir_par_code(self, code: str):
        return self.service.obtenir_par_code(code)

    def obtenir_par_acte(self, code_acte: str):
        return self.service.obtenir_par_acte(code_acte)

    def lister_commandes(self, code_session: str) -> list:
        return self.service.lister_commandes(code_session)

    def lister_commandes_completes(self, code_session: str) -> list:
        return self.service.lister_commandes_completes(code_session)

    def rechercher_commande(self, critere: str, code_session: str) -> list:
        return self.service.rechercher_commande(critere, code_session)

    def obtenir_commande_complete(self, code_commande: str):
        return self.service.obtenir_commande_complete(code_commande)

    def obtenir_historique_patient(self, code_patient: str) -> list:
        return self.service.obtenir_historique_patient(code_patient)

    def obtenir_derniere_commande_patient(self, code_visite: str):
        return self.service.obtenir_derniere_commande_patient(code_visite)

    def rechercher_entre_dates(self, code_session: str, date_debut, date_fin) -> list:
        return self.service.rechercher_entre_dates(code_session, date_debut, date_fin)

    # =========================================================================
    # METHODES PATIENTS (LISTES FILTREES)
    # =========================================================================

    def obtenir_patients_attente_lunette(self, code_session: str) -> list:
        return self.service.obtenir_patients_attente_lunette(code_session)

    def obtenir_patients_commandes_multiples(self, code_session: str) -> list:
        return self.service.obtenir_patients_commandes_multiples(code_session)

    def obtenir_commandes_par_patient_par_mois(
        self, code_session: str, code_patient: str = None
    ) -> dict:
        return self.service.obtenir_commandes_par_patient_par_mois(code_session, code_patient)

    def obtenir_codes_patients_session(self, code_session: str) -> list:
        return self.service.obtenir_codes_patients_session(code_session)

    # =========================================================================
    # METHODES STATISTIQUES CARDS
    # =========================================================================

    def obtenir_commandes_en_attente_livraison(self, code_session: str) -> int:
        return self.service.obtenir_commandes_en_attente_livraison(code_session)

    def obtenir_total_commandes_session(self, code_session: str) -> int:
        return self.service.obtenir_total_commandes_session(code_session)

    def obtenir_commandes_en_attente(self, code_session: str) -> int:
        return self.service.obtenir_commandes_en_attente(code_session)

    def obtenir_montant_total_aujourdhui(self, code_session: str) -> float:
        return self.service.obtenir_montant_total_aujourdhui(code_session)

    def obtenir_montant_total_par_session(self, code_session: str) -> float:
        return self.service.obtenir_montant_total_par_session(code_session)

    # =========================================================================
    # METHODES STATISTIQUES & GRAPHES
    # =========================================================================

    def obtenir_commandes_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_commandes_par_mois(code_session)

    def obtenir_nombre_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_nombre_par_mois(code_session)

    def obtenir_nombre_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        return self.service.obtenir_nombre_par_jour(code_session, annee, mois)

    def obtenir_montant_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_montant_par_mois(code_session)

    def obtenir_montant_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        return self.service.obtenir_montant_par_jour(code_session, annee, mois)

    def obtenir_revenu_moyen_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_revenu_moyen_par_mois(code_session)

    def obtenir_moyenne_montant_journalier_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_moyenne_montant_journlier_par_mois(code_session)

    def obtenir_moyenne_commande_par_mois(self, code_session: str) -> dict:
        return self.service.obtnir_moyenne_commande_par_mois(code_session)

    def obtenir_moyenne_nombre_journalier_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_moyenne_nombre_journalier_par_mois(code_session)

    def obtenir_revenu_total(self, code_session: str, date_debut=None, date_fin=None) -> float:
        return self.service.obtenir_revenu_total(code_session, date_debut, date_fin)

    def obtenir_top_numeros_verre(self, code_session: str, limite: int = 10) -> list:
        return self.service.obtenir_top_numeros_verre(code_session, limite)

    def obtenir_commandes_par_personnel(self, code_session: str) -> list:
        return self.service.obtenir_commandes_par_personnel(code_session)

    # =========================================================================
    # METHODES SUIVI LIVRAISON
    # =========================================================================

    def marquer_comme_livree(self, code: str) -> tuple:
        return self.service.marquer_comme_livree(code)

    def obtenir_commandes_en_retard(self, code_session: str) -> list:
        return self.service.obtenir_commandes_en_retard(code_session)

    def obtenir_commandes_a_livrer_dans_deux_jours(self, code_session: str) -> list:
        return self.service.obtenir_commandes_a_livrer_dans_deux_jours(code_session)

    def obtenir_commande_en_attente_complete(self, code_commande: str):
        return self.service.obtenir_commande_en_attente_complete(code_commande)

    def obtenir_toutes_commandes_attente_livraison(self, code_session: str) -> list:
        return self.service.obtenir_toutes_commandes_attente_livraison(code_session)

    # =========================================================================
    # METHODES FINANCIERES
    # =========================================================================

    def obtenir_revenu_recouvre_vs_en_attente(self, code_session: str) -> dict:
        return self.service.obtenir_revenu_recouvre_vs_en_attente(code_session)

    def obtenir_commandes_par_statut_facture(self, code_session: str) -> list:
        return self.service.obtenir_commandes_par_statut_facture(code_session)

    # =========================================================================
    # METHODES PERFORMANCE
    # =========================================================================

    def obtenir_delai_moyen_livraison(self, code_session: str) -> dict:
        return self.service.obtenir_delai_moyen_livraison(code_session)

    # =========================================================================
    # INFORMATIONS CABINET + PERSONNEL
    # =========================================================================

    def get_cabinet_info(self) -> Dict[str, Optional[str]]:
        return self.service.get_cabinet_info()

    def lister_personnel(self) -> list:
        return self.service.lister_personnel()

    # =========================================================================
    # RAPPORTS PDF LISTE COMMANDES
    # =========================================================================

    def generer_pdf_rapport_commandes_par_date(self, code_session):
        """Récupère toutes les commandes de la session et génère un PDF groupé par date."""
        from services.pdf_rapports.rapport_lunette import RapportLunettePDF
        commandes = self.lister_commandes(code_session) or []
        info_cabinet = self.get_cabinet_info()
        details_list = []
        for c in commandes:
            detail = self.obtenir_commande_complete(c.code)
            if detail:
                details_list.append(detail)
        return RapportLunettePDF.generer_pdf_commandes_par_date(details_list, info_cabinet)

    def generer_pdf_rapport_date_precise_commandes(self, code_session, date_cible):
        """Génère un PDF des commandes de lunettes pour une date précise."""
        from services.pdf_rapports.rapport_lunette import RapportLunettePDF
        commandes = self.rechercher_entre_dates(code_session, date_cible, date_cible) or []
        info_cabinet = self.get_cabinet_info()
        details_list = []
        for c in commandes:
            detail = self.obtenir_commande_complete(c.code)
            if detail:
                details_list.append(detail)
        return RapportLunettePDF.generer_pdf_commandes_date_precise(details_list, date_cible, info_cabinet)

    # =========================================================================
    # WORKFLOW PATIENT
    # =========================================================================

    def demarrer_lunette(self, code_visite: str) -> tuple:
        from service_metier.visite_service import VisiteService
        return VisiteService().demarrer_lunette(code_visite)

    def terminer_lunette(self, code_visite: str) -> tuple:
        from service_metier.visite_service import VisiteService
        return VisiteService().terminer_lunette(code_visite)