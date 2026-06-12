import sys
import os
import logging
from typing import Dict, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service_metier.chirurgie_service import ChirurgieService
from models.modeles_chirurgie import Chirurgie


class ChirurgieControleur:
    """
    Contrôleur MVC pour la gestion des chirurgies.
    Délègue toute la logique métier à ChirurgieService.
    """

    def __init__(self):
        self.service = ChirurgieService()
        self.logger  = logging.getLogger(__name__)

    # --------- VALIDATION ---------
    def valider_texte(self, texte: str, nom_champ: str, min_longueur: int = 3) -> tuple:
        return self.service.valider_texte(texte, nom_champ, min_longueur)

    def valider_date(self, date_chururgie) -> tuple:
        return self.service.valider_date(date_chururgie)

    def valider_frais(self, frais) -> tuple:
        return self.service.valider_frais(frais)

    def valider_codes_obligatoires(self, chururgie: Chirurgie) -> tuple:
        return self.service.valider_codes_obligatoires(chururgie)

    def valider_chururgie(self, chururgie: Chirurgie) -> tuple:
        return self.service.valider_chururgie(chururgie)

    # --------- CRUD ---------
    def creer_chururgie(self, chururgie: Chirurgie) -> tuple:
        return self.service.creer_chururgie(chururgie)

    def modifier_chururgie(self, chururgie: Chirurgie) -> tuple:
        return self.service.modifier_chururgie(chururgie)

    def supprimer_chururgie(self, code: str) -> tuple:
        return self.service.supprimer_chururgie(code)

    # --------- RECUPERATION ---------
    def obtenir_par_code(self, code: str):
        return self.service.obtenir_par_code(code)

    def obtenir_par_acte(self, code_acte: str):
        return self.service.obtenir_par_acte(code_acte)

    def lister_chururgies(self, code_session: str) -> list:
        return self.service.lister_chururgies(code_session)

    def rechercher_chururgie(self, critere: str, code_session: str) -> list:
        return self.service.rechercher_chururgie(critere, code_session)

    def rechercher_par_libelle(self, code_session: str, libelle: str) -> list:
        return self.service.rechercher_par_libelle(code_session, libelle)

    def obtenir_chururgie_complete(self, code_chururgie: str):
        return self.service.obtenir_chururgie_complete(code_chururgie)

    def obtenir_historique_patient(self, code_patient: str) -> list:
        return self.service.obtenir_historique_patient(code_patient)

    # --------- PATIENTS ---------
    def obtenir_patients_attente_chururgie(self, code_session: str) -> list:
        return self.service.obtenir_patients_attente_chururgie(code_session)

    # --------- STATISTIQUES CARDS ---------
    def obtenir_chururgies_aujourd_hui(self, code_session: str) -> int:
        return self.service.obtenir_chururgies_aujourd_hui(code_session)

    def obtenir_total_chururgies_session(self, code_session: str) -> int:
        return self.service.obtenir_total_chururgies_session(code_session)

    def obtenir_chururgies_en_attente(self, code_session: str) -> int:
        return self.service.obtenir_chururgies_en_attente(code_session)

    def obtenir_montant_total_aujourdhui(self, code_session: str) -> float:
        return self.service.obtenir_montant_total_aujourdhui(code_session)

    def obtenir_montant_total_par_session(self, code_session: str) -> float:
        return self.service.obtenir_montant_total_par_session(code_session)

    def obtenir_revenu_total(self, code_session: str, date_debut=None, date_fin=None) -> float:
        return self.service.obtenir_revenu_total(code_session)

    # --------- STATISTIQUES GRAPHES ---------
    def obtenir_nombre_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        return self.service.obtenir_nombre_par_jour(code_session, annee, mois)

    def obtenir_nombre_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_nombre_par_mois(code_session)

    def obtenir_chururgies_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_chururgies_par_mois(code_session)

    def obtenir_montant_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        return self.service.obtenir_montant_par_jour(code_session, annee, mois)

    def obtenir_montant_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_montant_par_mois(code_session)

    def obtenir_revenu_moyen_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_revenu_moyen_par_mois(code_session)

    def obtenir_moyenne_montant_journalier_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_moyenne_montant_journalier_par_mois(code_session)

    def obtenir_moyenne_chirurgie_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_moyenne_chirurgie_par_mois(code_session)

    def obtenir_moyenne_nombre_journalier_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_moyenne_nombre_journalier_par_mois(code_session)

    def obtenir_top_libelles(self, code_session: str, limite: int = 10) -> list:
        return self.service.obtenir_top_libelles(code_session, limite)

    def obtenir_chururgies_par_personnel(self, code_session: str) -> list:
        return self.service.obtenir_chururgies_par_personnel(code_session)

    # --------- RECHERCHE AVANCÉE ---------
    def rechercher_entre_dates(self, code_session: str, date_debut, date_fin) -> list:
        return self.service.rechercher_entre_dates(code_session, date_debut, date_fin)

    # --------- RAPPORTS PDF LISTE CHIRURGIES ---------

    def generer_pdf_rapport_chururgies_par_date(self, code_session):
        """Récupère toutes les chirurgies de la session et génère un PDF groupé par date."""
        from services.pdf_rapports.rapport_chirurgie import RapportChirurgiePDF
        chirurgies = self.lister_chururgies(code_session) or []
        info_cabinet = self.get_cabinet_info()
        details_list = []
        for c in chirurgies:
            detail = self.obtenir_chururgie_complete(c.code)
            if detail:
                details_list.append(detail)
        return RapportChirurgiePDF.generer_pdf_chururgies_par_date(details_list, info_cabinet)

    def generer_pdf_rapport_date_precise_chururgies(self, code_session, date_cible):
        """Génère un PDF des chirurgies pour une date précise."""
        from services.pdf_rapports.rapport_chirurgie import RapportChirurgiePDF
        chirurgies = self.rechercher_entre_dates(code_session, date_cible, date_cible) or []
        info_cabinet = self.get_cabinet_info()
        details_list = []
        for c in chirurgies:
            detail = self.obtenir_chururgie_complete(c.code)
            if detail:
                details_list.append(detail)
        return RapportChirurgiePDF.generer_pdf_chururgies_date_precise(details_list, date_cible, info_cabinet)

    def chirurgies_par_patient_par_mois(self, code_session: str, code_patient: str = None) -> dict:
        return self.service.chirurgies_par_patient_par_mois(code_session, code_patient)

    def codes_patients_session(self, code_session: str) -> list:
        return self.service.codes_patients_session(code_session)

    # --------- WORKFLOW PATIENT ---------
    def demarrer_chirurgie(self, code_visite: str) -> tuple:
        from service_metier.visite_service import VisiteService
        return VisiteService().demarrer_chirurgie(code_visite)

    def terminer_chirurgie(self, code_visite: str) -> tuple:
        from service_metier.visite_service import VisiteService
        return VisiteService().terminer_chirurgie(code_visite)

    # --------- CABINET / PERSONNEL ---------
    def get_cabinet_info(self) -> Dict[str, Optional[str]]:
        return self.service.get_cabinet_info()

    def lister_personnel(self) -> list:
        return self.service.lister_personnel()

    def lister_personnel_par_roles(self, roles: list) -> list:
        return self.service.lister_personnel_par_roles(roles)

    # =========================================================================
    # EXPORT / IMPORT CHIRURGIES
    # =========================================================================

    def obtenir_donnees_export(self) -> list:
        from service_metier.acte_import_export_service import obtenir_donnees_export
        return obtenir_donnees_export("chirurgie")

    def export_to_excel(self, chemin: str) -> tuple:
        from service_metier.acte_import_export_service import export_chirurgies_excel
        return export_chirurgies_excel(chemin)

    def export_to_csv(self, chemin: str) -> tuple:
        from service_metier.acte_import_export_service import export_chirurgies_csv
        return export_chirurgies_csv(chemin)

    def import_chirurgies(self, chemin: str, format_fichier: str) -> tuple:
        from service_metier.acte_import_export_service import import_chirurgies
        return import_chirurgies(chemin, format_fichier)

