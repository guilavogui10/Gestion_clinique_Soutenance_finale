"""
visite_service.py
------------------
Service métier — Gestion des visites médicales.

Responsabilités :
  - Validation des données de visite (type, urgence, date)
  - CRUD : ajout, mise à jour
  - Gestion du workflow patient (changement d'étape)
  - Statistiques (mensuelles, par âge, performance)
  - Récupération de dossier complet, suivi progression
  - Vérification session active
  - Informations cabinet
"""

import re
import os
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional

from data.dao_visite import Visitedao
from models.model_visite import Visite
from parametre.dao_param import CabinetDAO
from data.dao_patient import PatientDao


class VisiteService:
    """
    Service métier pour la gestion des visites médicales.
    Contient la validation, le CRUD, le workflow patient et les statistiques.
    """

    def __init__(self, dao=None, cabinet_dao=None, patient_dao=None):
        """
        Initialise le service avec injection optionnelle des DAOs.

        Args:
            dao: Instance de Visitedao (injection pour tests).
            cabinet_dao: Instance de CabinetDAO (injection pour tests).
            patient_dao: Instance de PatientDao (injection pour tests).
        """
        self.dao = dao or Visitedao()
        self.cabinet_dao = cabinet_dao or CabinetDAO()
        self.patient_dao = patient_dao or PatientDao()
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # MÉTHODES DE VALIDATION (LOGIQUE MÉTIER)
    # =========================================================================

    def _valider_type_visite(self, type_visite: str) -> Tuple[bool, str]:
        """Valide le type de visite (min 3 caractères, lettres uniquement)."""
        if not type_visite or len(type_visite.strip()) < 3:
            return False, "Le type de visite doit contenir au moins 3 caractères"
        if not re.match(r"^[a-zA-ZÀ-ÿ\s\-]+$", type_visite.strip()):
            return False, "Le type de visite ne doit contenir que des lettres, espaces et tirets"
        return True, ""

    def _valider_urgent(self, urgent: str) -> Tuple[bool, str]:
        """Valide le champ urgent (Oui ou Non)."""
        valeurs_valides = ["Oui", "Non"]
        if urgent not in valeurs_valides:
            return False, f"Le champ urgent doit être: {', '.join(valeurs_valides)}"
        return True, ""

    def _valider_date_visite(self, date_visite) -> Tuple[bool, str]:
        """Valide et formate la date de visite."""
        if isinstance(date_visite, datetime):
            dt_obj = date_visite
        else:
            dt_obj = None
            formats = ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y")
            for fmt in formats:
                try:
                    dt_obj = datetime.strptime(str(date_visite), fmt)
                    break
                except ValueError:
                    continue

        if dt_obj is None:
            return False, "Format de date invalide (YYYY-MM-DD ou DD/MM/YYYY)"

        limite_passee = datetime.now().replace(day=1)
        if dt_obj < limite_passee:
            return False, "La date ne peut pas être antérieure au début du mois courant"

        return True, dt_obj.strftime("%Y-%m-%d %H:%M:%S")

    # =========================================================================
    # MÉTHODES CRUD
    # =========================================================================

    def save_visite(self, visite_objet: Visite) -> Tuple[bool, str]:
        """
        Valide et enregistre une nouvelle visite.
        Génère automatiquement le code_visite et récupère la session active.

        Args:
            visite_objet (Visite): Objet Visite à enregistrer.

        Returns:
            Tuple[bool, str]: (succès, message)
        """
        try:
            # Validation des données
            valid_type, msg_type = self._valider_type_visite(visite_objet.get_type_visite())
            if not valid_type:
                return False, msg_type

            valid_urgent, msg_urgent = self._valider_urgent(visite_objet.get_urgent())
            if not valid_urgent:
                return False, msg_urgent

            valid_date, result_date = self._valider_date_visite(visite_objet.get_date_visite())
            if not valid_date:
                return False, result_date

            visite_objet.set_date_visite(result_date)

            # Récupération de la session active
            code_session = self.dao.get_code_session_active()
            if not code_session:
                return False, "Aucune session active. Veuillez ouvrir une session."

            visite_objet.set_code_session(code_session)

            # Génération du code visite
            nouveau_code = self.dao.generate_code_visite()
            visite_objet.set_code_visite(nouveau_code)

            # Enregistrement
            return self.dao.createVisite(visite_objet)

        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement de la visite: {e}")
            return False, "Erreur lors de l'enregistrement"

    def update_visite(self, visite_update: Visite) -> Tuple[bool, str]:
        """
        Valide et met à jour une visite existante.
        Vérifie que la visite n'est pas terminée avant modification.

        Args:
            visite_update (Visite): Objet Visite avec les modifications.

        Returns:
            Tuple[bool, str]: (succès, message)
        """
        try:
            valid_type, msg_type = self._valider_type_visite(visite_update.get_type_visite())
            if not valid_type:
                return False, msg_type

            valid_urgent, msg_urgent = self._valider_urgent(visite_update.get_urgent())
            if not valid_urgent:
                return False, msg_urgent

            valid_date, result_date = self._valider_date_visite(visite_update.get_date_visite())
            if not valid_date:
                return False, result_date

            visite_update.set_date_visite(result_date)

            # Vérification de l'existence
            visite_en_base = self.dao.reeVisite_ByCode_visite(visite_update.get_code_visite())
            if not visite_en_base:
                return False, "Visite introuvable"

            # Préservation de la session
            if not visite_update.get_code_session():
                visite_update.set_code_session(visite_en_base.get_code_session())

            # Vérification du statut
            if visite_en_base.get_statut_visite() == "terminée":
                return False, "Impossible de modifier une visite terminée"

            return self.dao.updateVisite(visite_update)

        except Exception as e:
            self.logger.error(f"Erreur lors de la mise à jour: {e}")
            return False, "Erreur lors de la mise à jour"

    # =========================================================================
    # MÉTHODES PATIENT
    # =========================================================================

    def read_by_code_patient(self, code_patient: str) -> List:
        """Recherche un patient par son code."""
        if not code_patient or not code_patient.strip():
            return self.patient_dao.reedAllPatient()
        return self.patient_dao.reed_by_code_patient(code_patient.strip())

    # =========================================================================
    # STATISTIQUES
    # =========================================================================

    def obtenir_stats_mensuelles(self) -> Dict[str, int]:
        """Récupère les statistiques mensuelles de visites."""
        code_session = self.dao.get_code_session_active()
        stats_defaut = {
            'Jan': 0, 'Fév': 0, 'Mar': 0, 'Avr': 0, 'Mai': 0, 'Juin': 0,
            'Juil': 0, 'Août': 0, 'Sep': 0, 'Oct': 0, 'Nov': 0, 'Déc': 0
        }
        if not code_session:
            return stats_defaut
        try:
            return self.dao.stat_visites_mensuelles(code_session)
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des stats: {e}")
            return stats_defaut

    def get_stat_visites_par_age(self) -> Dict[str, int]:
        """Récupère la répartition des visites par tranche d'âge."""
        code_session = self.dao.get_code_session_active()
        stats_defaut = {'enfants': 0, 'jeunes': 0, 'adultes': 0}
        if not code_session:
            return stats_defaut
        try:
            return self.dao.stat_evolutive_par_age(code_session)
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des stats par âge: {e}")
            return stats_defaut

    # =========================================================================
    # DOSSIER ET SUIVI
    # =========================================================================

    def obtenir_dossier_complet_visite(self, code_visite: str) -> Dict:
        """Récupère l'historique médical complet d'une visite."""
        if not code_visite or not code_visite.strip():
            return {
                'consultations': [], 'examens': [], 'chirurgies': [],
                'prescriptions': [], 'lunettes': []
            }
        try:
            return self.dao.get_details_complets_visite(code_visite)
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du dossier: {e}")
            return {
                'consultations': [], 'examens': [], 'chirurgies': [],
                'prescriptions': [], 'lunettes': []
            }

    def lister_suivi_progression(self) -> List[Visite]:
        """Récupère la liste des visites pour le suivi de progression."""
        code_session = self.dao.get_code_session_active()
        if not code_session:
            return []
        try:
            return self.dao.get_all_visites_suivi(code_session)
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du suivi: {e}")
            return []

    # =========================================================================
    # WORKFLOW PATIENT — CHANGEMENT D'ÉTAPE
    # =========================================================================

    def changer_etape_visite(self, code_visite: str, nouveau_statut: str) -> Tuple[bool, str]:
        """
        Change l'étape de progression d'une visite dans le workflow patient.

        Args:
            code_visite (str): Code de la visite.
            nouveau_statut (str): Nouveau statut à appliquer.

        Returns:
            Tuple[bool, str]: (succès, message)
        """
        if not code_visite or not code_visite.strip():
            return False, "Code visite requis"

        statuts_valides = [
            "Attente consultation", "Attente examen", "Attente chirurgie",
            "Attente lunette", "Attente pharmacie", "Attente payement",
            "Attente rendez-vous", "Libéré"
        ]
        if nouveau_statut not in statuts_valides:
            return False, f"Statut invalide. Statuts autorisés: {', '.join(statuts_valides)}"

        try:
            succes = self.dao.update_progression_visite(code_visite, nouveau_statut)
            if succes:
                if nouveau_statut.lower() == "libéré":
                    return True, "Visite terminée et patient libéré"
                return True, f"Statut mis à jour: {nouveau_statut}"
            else:
                return False, "Échec de la mise à jour"
        except Exception as e:
            self.logger.error(f"Erreur lors du changement d'étape: {e}")
            return False, "Erreur lors de la mise à jour"

    # =========================================================================
    # VISITES PRIORITAIRES ET RECHERCHE
    # =========================================================================

    def obtenir_visites_prioritaires(self) -> List[Visite]:
        """Récupère les visites triées par priorité."""
        code_session = self.dao.get_code_session_active()
        if not code_session:
            return []
        try:
            return self.dao.getAllVisitesPrioritaires(code_session)
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des visites prioritaires: {e}")
            return []

    def rechercher_visites(self, mot_cle: str) -> List[Visite]:
        """Recherche des visites par mot-clé."""
        if not mot_cle or len(mot_cle.strip()) < 2:
            return []
        code_session = self.dao.get_code_session_active()
        if not code_session:
            return []
        try:
            return self.dao.searchVisitesByKeyword(code_session, mot_cle.strip())
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche: {e}")
            return []

    # =========================================================================
    # TEMPS ET DURÉES
    # =========================================================================

    def obtenir_temps_ecoule(self, code_visite: str) -> str:
        """Récupère le temps écoulé depuis le début d'une visite."""
        if not code_visite or not code_visite.strip():
            return "0h 0min"
        try:
            return self.dao.calculer_duree_actuelle(code_visite)
        except Exception as e:
            self.logger.error(f"Erreur lors du calcul de durée: {e}")
            return "0h 0min"

    def obtenir_analyse_flux_hebdomadaire(self) -> List[Dict]:
        """Récupère l'analyse du flux de visites par jour de la semaine."""
        try:
            return self.dao.get_analyse_flux_hebdomadaire()
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse du flux: {e}")
            return []

    def obtenir_bilan_temporel_visite(self, code_visite: str) -> str:
        """Récupère la durée totale d'une visite terminée."""
        if not code_visite or not code_visite.strip():
            return "Code visite invalide"
        try:
            return self.dao.get_duree_totale_visite(code_visite)
        except Exception as e:
            self.logger.error(f"Erreur lors du calcul de durée totale: {e}")
            return "Erreur de calcul"

    def verifier_temps_attente_critique(self, code_visite: str, seuil_minutes: int = 20) -> Tuple[bool, int, Optional[str]]:
        """
        Vérifie si un patient dépasse le temps d'attente critique.

        Args:
            code_visite (str): Code de la visite.
            seuil_minutes (int): Seuil d'alerte en minutes.

        Returns:
            Tuple[bool, int, Optional[str]]: (alerte, temps_attente, statut)
        """
        if not code_visite or not code_visite.strip():
            return False, 0, None
        try:
            est_en_alerte, temps, statut = self.dao.verifier_alerte_statut_patient(code_visite, seuil_minutes)
            if est_en_alerte:
                self.logger.warning(f"Alerte temps d'attente: Patient {code_visite} - {temps}min - {statut}")
            return est_en_alerte, temps, statut
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification d'alerte: {e}")
            return False, 0, None

    # =========================================================================
    # PERFORMANCE
    # =========================================================================

    def obtenir_bilan_performance_session(self) -> Dict:
        """Génère un rapport de performance pour la session actuelle."""
        code_session = self.dao.get_code_session_active()
        if not code_session:
            return {'moyenne_globale': 0, 'details_par_statut': []}
        try:
            return self.dao.get_analyse_performance_soiree(code_session)
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse de performance: {e}")
            return {'moyenne_globale': 0, 'details_par_statut': []}

    # =========================================================================
    # SESSION
    # =========================================================================

    def verifier_session_active(self) -> Tuple[bool, str]:
        """Vérifie qu'une session de travail est active."""
        try:
            code_session = self.dao.get_code_session_active()
            if not code_session:
                return False, "Aucune session active. Veuillez ouvrir une session."
            return True, code_session
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification de session: {e}")
            return False, "Erreur de vérification de session"

    # =========================================================================
    # INFORMATIONS CABINET
    # =========================================================================

    def get_cabinet_info(self) -> Dict[str, Optional[str]]:
        """Récupère les informations du cabinet médical."""
        try:
            info = self.cabinet_dao.get_info_cabinet() or {}
            nom_cabinet = info.get("nom_cabinet", "Cabinet ophtalmologique")
            adresse_cabinet = info.get("adresse", "")
            logo_cabinet = info.get("logo", None)

            final_logo = None
            if logo_cabinet:
                try:
                    base_dir = os.path.dirname(os.path.dirname(__file__))
                    logo_path = os.path.join(base_dir, "connexion", "image", logo_cabinet)
                    if os.path.exists(logo_path) and os.path.isfile(logo_path):
                        final_logo = os.path.abspath(logo_path)
                except Exception as e:
                    self.logger.warning(f"Erreur chemin logo: {e}")

            return {
                "nom_cabinet": nom_cabinet,
                "adresse_cabinet": adresse_cabinet,
                "logo_url": final_logo
            }
        except Exception as e:
            self.logger.error(f"Erreur get_cabinet_info: {e}")
            return {
                "nom_cabinet": "Cabinet ophtalmologique",
                "adresse_cabinet": "",
                "logo_url": None
            }
