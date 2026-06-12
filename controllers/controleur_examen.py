import sys
import os
import logging
from typing import Dict, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service_metier.examen_service import ExamenService
from models.modeles_examen import Examen


class ExamenControleur:
    """
    Contrôleur MVC pour la gestion des examens.
    Délègue toute la logique métier à ExamenService.
    """

    def __init__(self):
        self.service = ExamenService()
        self.logger  = logging.getLogger(__name__)

    # --------- VALIDATION ---------
    def valider_texte(self, texte: str, nom_champ: str, min_longueur: int = 3) -> tuple:
        return self.service.valider_texte(texte, nom_champ, min_longueur)

    def valider_date(self, date_examen) -> tuple:
        return self.service.valider_date(date_examen)

    def valider_frais(self, frais) -> tuple:
        return self.service.valider_frais(frais)

    def valider_codes_obligatoires(self, examen: Examen) -> tuple:
        return self.service.valider_codes_obligatoires(examen)

    def valider_examen(self, examen: Examen) -> tuple:
        return self.service.valider_examen(examen)

    # --------- CRUD ---------
    def creer_examen(self, examen: Examen) -> tuple:
        return self.service.creer_examen(examen)

    def modifier_examen(self, examen: Examen) -> tuple:
        return self.service.modifier_examen(examen)

    def supprimer_examen(self, code: str) -> tuple:
        return self.service.supprimer_examen(code)

    # --------- RECUPERATION ---------
    def obtenir_par_code(self, code: str):
        return self.service.obtenir_par_code(code)

    def obtenir_par_acte(self, code_acte: str):
        return self.service.obtenir_par_acte(code_acte)

    def obtenir_par_visite(self, code_visite: str):
        return self.service.obtenir_par_visite(code_visite)

    def lister_examens(self, code_session: str) -> list:
        return self.service.lister_examens(code_session)

    def rechercher_examen(self, critere: str, code_session: str) -> list:
        return self.service.rechercher_examen(critere, code_session)

    def obtenir_examen_complet(self, code_examen: str):
        return self.service.obtenir_examen_complet(code_examen)

    def obtenir_consultation_complete(self, code_examen: str):
        return self.service.obtenir_consultation_complete(code_examen)

    def obtenir_services_lies(self, code_examen: str) -> dict:
        return self.service.obtenir_services_lies(code_examen)

    def obtenir_historique_patient(self, code_patient: str) -> list:
        return self.service.obtenir_historique_patient(code_patient)

    # --------- PATIENTS ---------
    def obtenir_codes_patients_session(self, code_session: str) -> list:
        return self.service.obtenir_codes_patients_session(code_session)

    def obtenir_patients_attente_examen(self, code_session: str) -> list:
        return self.service.obtenir_patients_attente_examen(code_session)

    # --------- STATISTIQUES CARDS ---------
    def obtenir_examens_aujourd_hui(self, code_session: str) -> int:
        return self.service.obtenir_examens_aujourd_hui(code_session)

    def obtenir_total_examens_session(self, code_session: str) -> int:
        return self.service.obtenir_total_examens_session(code_session)

    def obtenir_examens_en_attente(self, code_session: str) -> int:
        return self.service.obtenir_examens_en_attente(code_session)

    def obtenir_nombre_patients_en_attente(self, code_session: str) -> int:
        return self.service.obtenir_nombre_patients_en_attente(code_session)

    # --------- STATISTIQUES GRAPHES ---------
    def obtenir_examens_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_examens_par_mois(code_session)

    def obtenir_nombre_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_nombre_par_mois(code_session)

    def obtenir_revenu_total(self, code_session: str, date_debut=None, date_fin=None) -> float:
        return self.service.obtenir_revenu_total(code_session, date_debut, date_fin)

    def obtenir_top_libelles(self, code_session: str, limite: int = 10) -> list:
        return self.service.obtenir_top_libelles(code_session, limite)

    def obtenir_examens_par_personnel(self, code_session: str) -> list:
        return self.service.obtenir_examens_par_personnel(code_session)

    def obtenir_top_diagnostics(self, code_session: str, limite: int = 10) -> list:
        return self.service.obtenir_top_diagnostics(code_session, limite)

    def obtenir_consultations_par_personnel(self, code_session: str) -> list:
        return self.service.obtenir_consultations_par_personnel(code_session)

    def obtenir_montant_aujourd_hui(self, code_session: str) -> float:
        return self.service.obtenir_montant_aujourd_hui(code_session)

    def obtenir_montant_session(self, code_session: str) -> float:
        return self.service.obtenir_montant_session(code_session)

    def obtenir_montant_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_montant_par_mois(code_session)

    def obtenir_revenu_moyen_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_revenu_moyen_par_mois(code_session)

    def obtenir_nombre_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        return self.service.obtenir_nombre_par_jour(code_session, annee, mois)

    def obtenir_montant_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        return self.service.obtenir_montant_par_jour(code_session, annee, mois)

    def obtenir_moyenne_examens_journaliers_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_moyenne_examens_journaliers_par_mois(code_session)

    def obtenir_moyenne_nombre_journalier_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_moyenne_nombre_journalier_par_mois(code_session)

    def obtenir_moyenne_examens_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_moyenne_examens_par_mois(code_session)

    def obtenir_moyenne_consultations_journalieres_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_moyenne_consultations_journalieres_par_mois(code_session)

    def obtenir_moyenne_consultations_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_moyenne_consultations_par_mois(code_session)

    # --------- WORKFLOW PATIENT ---------
    def demarrer_examen(self, code_visite: str) -> tuple:
        from service_metier.visite_service import VisiteService
        return VisiteService().demarrer_examen(code_visite)

    def terminer_examen(self, code_visite: str) -> tuple:
        from service_metier.visite_service import VisiteService
        return VisiteService().terminer_examen(code_visite)

    # --------- CABINET / PERSONNEL ---------
    def get_cabinet_info(self) -> Dict[str, Optional[str]]:
        return self.service.get_cabinet_info()

    def lister_personnel(self) -> list:
        return self.service.lister_personnel()

    def lister_personnel_par_roles(self, roles: list) -> list:
        return self.service.lister_personnel_par_roles(roles)

    def rechercher_entre_dates(self, code_session: str, date_debut, date_fin) -> list:
        return self.service.rechercher_entre_dates(code_session, date_debut, date_fin)

    # --------- RAPPORTS PDF LISTE EXAMENS ---------

    def generer_pdf_rapport_examens_par_date(self, code_session):
        """
        Récupère tous les examens de la session, les enrichit
        et génère un PDF groupé par date avec totaux.
        Retourne le chemin du PDF généré.
        """
        from services.pdf_rapports.rapport_examen import RapportExamenPDF
        examens = self.lister_examens(code_session) or []
        info_cabinet = self.get_cabinet_info()
        details_list = []
        for e in examens:
            detail = self.obtenir_examen_complet(e.code)
            if detail:
                details_list.append(detail)
        return RapportExamenPDF.generer_pdf_examens_par_date(
            details_list, info_cabinet
        )

    # =========================================================================
    # EXPORT / IMPORT EXAMENS
    # =========================================================================

    def obtenir_donnees_export(self) -> list:
        from service_metier.acte_import_export_service import obtenir_donnees_export
        return obtenir_donnees_export("examen")

    def export_to_excel(self, chemin: str) -> tuple:
        from service_metier.acte_import_export_service import export_examens_excel
        return export_examens_excel(chemin)

    def export_to_csv(self, chemin: str) -> tuple:
        from service_metier.acte_import_export_service import export_examens_csv
        return export_examens_csv(chemin)

    def import_examens(self, chemin: str, format_fichier: str) -> tuple:
        from service_metier.acte_import_export_service import import_examens
        return import_examens(chemin, format_fichier)

    def generer_pdf_rapport_date_precise_examens(self, code_session, date_cible):
        """
        Récupère les examens de la session pour une date précise,
        les enrichit et génère un PDF pour cette date avec total.
        date_cible : datetime.date ou str YYYY-MM-DD.
        Retourne le chemin du PDF généré.
        """
        from services.pdf_rapports.rapport_examen import RapportExamenPDF
        examens = self.rechercher_entre_dates(code_session, date_cible, date_cible) or []
        info_cabinet = self.get_cabinet_info()
        details_list = []
        for e in examens:
            detail = self.obtenir_examen_complet(e.code)
            if detail:
                details_list.append(detail)
        return RapportExamenPDF.generer_pdf_examens_date_precise(
            details_list, date_cible, info_cabinet
        )
