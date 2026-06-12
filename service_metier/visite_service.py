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
from data.dao_rendez_vous import RendezVousDAO
from models.modele_rendez_vous import RendezVous as RendezVousModele


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
        self.rdv_dao = RendezVousDAO()
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

    def _valider_date_visite_import(self, date_visite) -> Tuple[bool, str]:
        """Valide le format de la date pour import — accepte les dates passées."""
        if isinstance(date_visite, datetime):
            return True, date_visite.strftime("%Y-%m-%d %H:%M:%S")

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

        return True, dt_obj.strftime("%Y-%m-%d %H:%M:%S")

    def _valider_date_dans_session(self, date_obj: datetime, plage: dict) -> str | None:
        """Retourne un message d'erreur si la date est hors session ou dans le futur, None si OK."""
        aujourd_hui = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
        nom = plage.get("nom_session", "session active")
        if date_obj > aujourd_hui:
            return f"Date {date_obj.date()} dans le futur — importation refusée."
        date_debut = plage.get("date_debut")
        date_fin   = plage.get("date_fin")
        if isinstance(date_debut, datetime) and date_obj < date_debut:
            return f"Date {date_obj.date()} antérieure au début de la session '{nom}' ({date_debut.date()})."
        if isinstance(date_fin, datetime) and date_obj > date_fin:
            return f"Date {date_obj.date()} postérieure à la fin de la session '{nom}' ({date_fin.date()})."
        return None

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
            code_session = self._session_code()
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
        code_session = self._session_code()
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

    def get_stat_visites_par_age(self) -> Dict:
        """Récupère la répartition des visites par tranche d'âge."""
        code_session = self._session_code()
        stats_defaut = {'enfants': [0]*12, 'jeunes': [0]*12, 'adultes': [0]*12}
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
        code_session = self._session_code()
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
            "Attente consultation",
            "Attente examen",
            "Attente chirurgie",
            "Attente rendez-vous",
            "Attente rendez-vous chirurgie",
            "Attente commande lunette",
            "Attente prescription",
            "Attente paiement",
            "Libéré"
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
        code_session = self._session_code()
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
        code_session = self._session_code()
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

    def verifier_alertes_temps_attente_batch(self, codes_visites: List[str], seuil_minutes: int = 20) -> List[Dict]:
        """
        Vérifie si plusieurs patients dépassent le temps d'attente critique en une seule requête.
        """
        if not codes_visites:
            return []
        try:
            alertes = self.dao.verifier_alertes_batch(codes_visites, seuil_minutes)
            for alerte in alertes:
                self.logger.warning(f"Alerte temps d'attente: Patient {alerte['code_visite']} - {alerte['temps_attente']}min - {alerte['statut']}")
            return alertes
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification d'alerte batch: {e}")
            return []

    # =========================================================================
    # PERFORMANCE
    # =========================================================================

    def obtenir_bilan_performance_session(self) -> Dict:
        """Génère un rapport de performance pour la session actuelle."""
        code_session = self._session_code()
        if not code_session:
            return {'moyenne_globale': 0, 'details_par_statut': []}
        try:
            return self.dao.get_analyse_performance_soiree(code_session)
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse de performance: {e}")
            return {'moyenne_globale': 0, 'details_par_statut': []}

    def obtenir_visites_actives_avec_duree(self) -> List[Dict]:
        """Retourne les visites actives de la session courante avec durée écoulée."""
        code_session = self._session_code()
        if not code_session:
            return []
        try:
            return self.dao.get_visites_actives_avec_duree(code_session)
        except Exception as e:
            self.logger.error(f"Erreur obtenir_visites_actives_avec_duree: {e}")
            return []

    # =========================================================================
    # SESSION
    # =========================================================================

    def _session_code(self) -> str | None:
        """Session effective : override DG si défini, sinon session En_cours en base."""
        try:
            from core import session_manager
            return session_manager.get_session_courante(self.dao.get_code_session_active)
        except Exception:
            return self.dao.get_code_session_active()

    def verifier_session_active(self) -> Tuple[bool, str]:
        """
        Retourne (True, code_session) pour la session à utiliser.
        Si le DG a sélectionné une session via session_manager, c'est elle qui est
        retournée ; sinon on récupère la session "En_cours" en base.
        """
        code_session = self._session_code()
        if not code_session:
            return False, "Aucune session active. Veuillez ouvrir une session."
        return True, code_session

    def lister_sessions_completes(self) -> list:
        """Retourne toutes les sessions avec leurs détails (code, nom, dates, statut)."""
        try:
            return self.dao.lister_sessions_completes()
        except Exception as e:
            self.logger.error(f"Erreur lister_sessions_completes: {e}")
            return []

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

    def obtenir_statistiques_performance(self) -> Dict:
        """
        Récupère les statistiques de performance pour le monitoring.
        
        Returns:
            Dict: Statistiques de performance
        """
        code_session = self._session_code()
        
        if not code_session:
            return {
                'duree_moyenne': 0,
                'attente_max': 0,
                'visites_actives': 0,
                'tendance': '+0%',
                'efficacite': 0,
                'satisfaction': 0
            }
        
        try:
            stats = self.dao.get_statistiques_performance_session(code_session)
            return stats
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des stats de performance: {e}")
            return {
                'duree_moyenne': 0,
                'attente_max': 0,
                'visites_actives': 0,
                'tendance': '+0%',
                'efficacite': 0,
                'satisfaction': 0
            }
    
    def obtenir_nombre_visites_aujourdhui(self) -> int:
        """
        Récupère le nombre de visites créées aujourd'hui.
        
        Returns:
            int: Nombre de visites aujourd'hui
        """
        code_session = self._session_code()
        if not code_session:
            return 0
        try:
            return self.dao.get_nombre_visites_aujourdhui(code_session)
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du nombre de visites aujourd'hui: {e}")
            return 0
    
    def obtenir_nombre_visites_terminees(self) -> int:
        """
        Récupère le nombre total de visites terminées.
        
        Returns:
            int: Nombre de visites terminées
        """
        code_session = self._session_code()
        if not code_session:
            return 0
        try:
            return self.dao.get_nombre_visites_terminees(code_session)
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du nombre de visites terminées: {e}")
            return 0
    
    def obtenir_nombre_urgences(self) -> int:
        """
        Récupère le nombre de visites urgentes.
        
        Returns:
            int: Nombre d'urgences
        """
        code_session = self._session_code()
        if not code_session:
            return 0
        try:
            return self.dao.get_nombre_urgences(code_session)
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du nombre d'urgences: {e}")
            return 0

    def demarrer_consultation(self, code_visite: str) -> tuple:
        """
        Démarre la consultation pour une visite :
          - Renseigne date_debut_consultation
          - Change statut_patient à 'En consultation'

        Returns:
            tuple: (bool, message)
        """
        if not code_visite:
            return False, "Code visite invalide"
        try:
            return self.dao.demarrer_consultation(code_visite)
        except Exception as e:
            self.logger.error(f"Erreur demarrer_consultation {code_visite}: {e}")
            return False, str(e)

    def terminer_consultation(self, code_visite: str) -> tuple:
        """
        Termine la consultation : statut_patient → 'Consultation terminée'.
        """
        if not code_visite:
            return False, "Code visite invalide"
        try:
            ok = self.dao.update_progression_visite(code_visite, "Consultation terminée")
            if ok:
                return True, "Consultation terminée avec succès"
            return False, "Échec de la mise à jour du statut"
        except Exception as e:
            self.logger.error(f"Erreur terminer_consultation {code_visite}: {e}")
            return False, str(e)

    def demarrer_examen(self, code_visite: str) -> tuple:
        """Démarre l'examen : statut_patient → 'En examen'."""
        if not code_visite:
            return False, "Code visite invalide"
        try:
            ok = self.dao.update_progression_visite(code_visite, "En examen")
            if ok:
                return True, "Examen démarré avec succès"
            return False, "Échec de la mise à jour du statut"
        except Exception as e:
            self.logger.error(f"Erreur demarrer_examen {code_visite}: {e}")
            return False, str(e)

    def terminer_examen(self, code_visite: str) -> tuple:
        """Termine l'examen : statut_patient → 'Examen terminé'."""
        if not code_visite:
            return False, "Code visite invalide"
        try:
            ok = self.dao.update_progression_visite(code_visite, "Examen terminé")
            if ok:
                return True, "Examen terminé avec succès"
            return False, "Échec de la mise à jour du statut"
        except Exception as e:
            self.logger.error(f"Erreur terminer_examen {code_visite}: {e}")
            return False, str(e)

    def demarrer_chirurgie(self, code_visite: str) -> tuple:
        """Démarre la chirurgie : statut_patient → 'En chirurgie'."""
        if not code_visite:
            return False, "Code visite invalide"
        try:
            ok = self.dao.update_progression_visite(code_visite, "En chirurgie")
            if ok:
                return True, "Chirurgie démarrée avec succès"
            return False, "Échec de la mise à jour du statut"
        except Exception as e:
            self.logger.error(f"Erreur demarrer_chirurgie {code_visite}: {e}")
            return False, str(e)

    def terminer_chirurgie(self, code_visite: str) -> tuple:
        """Termine la chirurgie : statut_patient → 'Chirurgie terminée'."""
        if not code_visite:
            return False, "Code visite invalide"
        try:
            ok = self.dao.update_progression_visite(code_visite, "Chirurgie terminée")
            if ok:
                return True, "Chirurgie terminée avec succès"
            return False, "Échec de la mise à jour du statut"
        except Exception as e:
            self.logger.error(f"Erreur terminer_chirurgie {code_visite}: {e}")
            return False, str(e)

    def demarrer_prescription(self, code_visite: str) -> tuple:
        """Démarre la pharmacie : statut_patient → 'En pharmacie'."""
        if not code_visite:
            return False, "Code visite invalide"
        try:
            ok = self.dao.update_progression_visite(code_visite, "En pharmacie")
            if ok:
                return True, "Prise en charge pharmacie démarrée"
            return False, "Échec de la mise à jour du statut"
        except Exception as e:
            self.logger.error(f"Erreur demarrer_prescription {code_visite}: {e}")
            return False, str(e)

    def terminer_prescription(self, code_visite: str) -> tuple:
        """Termine la pharmacie : statut_patient → 'Pharmacie terminée'."""
        if not code_visite:
            return False, "Code visite invalide"
        try:
            ok = self.dao.update_progression_visite(code_visite, "Pharmacie terminée")
            if ok:
                return True, "Pharmacie terminée avec succès"
            return False, "Échec de la mise à jour du statut"
        except Exception as e:
            self.logger.error(f"Erreur terminer_prescription {code_visite}: {e}")
            return False, str(e)

    def demarrer_lunette(self, code_visite: str) -> tuple:
        """Démarre le service optique : statut_patient → 'En lunette'."""
        if not code_visite:
            return False, "Code visite invalide"
        try:
            ok = self.dao.update_progression_visite(code_visite, "En lunette")
            if ok:
                return True, "Prise en charge optique démarrée"
            return False, "Échec de la mise à jour du statut"
        except Exception as e:
            self.logger.error(f"Erreur demarrer_lunette {code_visite}: {e}")
            return False, str(e)

    def terminer_lunette(self, code_visite: str) -> tuple:
        """Termine le service optique : statut_patient → 'Lunette terminée'."""
        if not code_visite:
            return False, "Code visite invalide"
        try:
            ok = self.dao.update_progression_visite(code_visite, "Lunette terminée")
            if ok:
                return True, "Service optique terminé avec succès"
            return False, "Échec de la mise à jour du statut"
        except Exception as e:
            self.logger.error(f"Erreur terminer_lunette {code_visite}: {e}")
            return False, str(e)

    def lister_visites_par_patient(self, code_patient: str) -> List[Visite]:
        """
        Récupère toutes les visites d'un patient.
        
        Args:
            code_patient: Code du patient
            
        Returns:
            Liste d'objets Visite
        """
        if not code_patient:
            return []
        try:
            toutes_visites = self.dao.reedAllvisite()
            return [v for v in toutes_visites if v.get_code_patient() == code_patient]
        except Exception as e:
            self.logger.error(f"Erreur lister_visites_par_patient: {e}")
            return []
    
    def obtenir_visite(self, code_visite: str) -> Optional[Visite]:
        """
        Récupère une visite par son code.

        Args:
            code_visite: Code de la visite

        Returns:
            Objet Visite ou None
        """
        if not code_visite:
            return None
        try:
            return self.dao.reeVisite_ByCode_visite(code_visite)
        except Exception as e:
            self.logger.error(f"Erreur obtenir_visite: {e}")
            return None

    # =========================================================================
    # EXPORT / IMPORT
    # =========================================================================

    def _save_visite_import(self, visite_objet: Visite) -> Tuple[bool, str]:
        """save_visite sans restriction de date passée — réservé à l'import."""
        try:
            valid_type, msg_type = self._valider_type_visite(visite_objet.get_type_visite())
            if not valid_type:
                return False, msg_type

            valid_urgent, msg_urgent = self._valider_urgent(visite_objet.get_urgent())
            if not valid_urgent:
                return False, msg_urgent

            valid_date, result_date = self._valider_date_visite_import(visite_objet.get_date_visite())
            if not valid_date:
                return False, result_date

            visite_objet.set_date_visite(result_date)

            code_session = self._session_code()
            if not code_session:
                return False, "Aucune session active"

            visite_objet.set_code_session(code_session)

            nouveau_code = self.dao.generate_code_visite()
            visite_objet.set_code_visite(nouveau_code)

            return self.dao.createVisite(visite_objet)

        except Exception as e:
            self.logger.error(f"Erreur _save_visite_import: {e}")
            return False, "Erreur lors de l'enregistrement"

    def _creer_rdv_import(self, code_visite: str, code_personnel: str,
                          date_rendez_vous_str: str, code_session: str) -> Tuple[bool, str]:
        """
        Crée un rendez-vous lié à une visite importée.
        La disponibilité du personnel est vérifiée — un conflit retourne (False, motif).
        """
        try:
            valid, date_formatee = self._valider_date_visite_import(date_rendez_vous_str)
            if not valid:
                return False, f"Date rendez-vous invalide : {date_rendez_vous_str}"

            rdv = RendezVousModele(
                code_visite=code_visite,
                code_personnel=code_personnel,
                code_session=code_session,
                date_rendez_vous=date_formatee,
                statut_rendez_vous="attente"
            )
            return self.rdv_dao.ajouter_import(rdv)
        except Exception as e:
            self.logger.error(f"Erreur _creer_rdv_import: {e}")
            return False, str(e)

    def obtenir_donnees_pour_export(self) -> List[Dict]:
        """Retourne les données de toutes les visites formatées pour aperçu/export."""
        try:
            visites = self.dao.reedAllvisite()
            return [
                {
                    "code_visite":   v.get_code_visite(),
                    "code_patient":  v.get_code_patient(),
                    "type_visite":   v.get_type_visite(),
                    "urgent":        v.get_urgent(),
                    "date_visite":   str(v.get_date_visite()),
                    "statut_visite": v.get_statut_visite(),
                    "statut_patient": v.get_statut_patient(),
                }
                for v in visites
            ]
        except Exception as e:
            self.logger.error(f"Erreur obtenir_donnees_pour_export: {e}")
            return []

    def export_to_excel(self, chemin: str) -> Tuple[bool, str]:
        """Exporte toutes les visites de la session active vers un fichier Excel."""
        try:
            import pandas as pd

            visites = self.dao.reedAllvisite()
            if not visites:
                return False, "Aucune visite à exporter"

            data = []
            for v in visites:
                data.append({
                    "code_visite": v.get_code_visite(),
                    "code_patient": v.get_code_patient(),
                    "type_visite": v.get_type_visite(),
                    "urgent": v.get_urgent(),
                    "date_visite": str(v.get_date_visite()),
                    "statut_visite": v.get_statut_visite(),
                    "statut_patient": v.get_statut_patient(),
                    "code_personnel": "",
                    "date_rendez_vous": ""
                })

            df = pd.DataFrame(data)
            df.to_excel(chemin, index=False)
            return True, f"{len(data)} visite(s) exportée(s) avec succès"

        except Exception as e:
            self.logger.error(f"Erreur export_to_excel visite: {e}")
            return False, f"Erreur lors de l'export : {e}"

    def export_to_csv(self, chemin: str) -> Tuple[bool, str]:
        """Exporte toutes les visites de la session active vers un fichier CSV."""
        try:
            import pandas as pd

            visites = self.dao.reedAllvisite()
            if not visites:
                return False, "Aucune visite à exporter"

            data = []
            for v in visites:
                data.append({
                    "code_visite": v.get_code_visite(),
                    "code_patient": v.get_code_patient(),
                    "type_visite": v.get_type_visite(),
                    "urgent": v.get_urgent(),
                    "date_visite": str(v.get_date_visite()),
                    "statut_visite": v.get_statut_visite(),
                    "statut_patient": v.get_statut_patient(),
                    "code_personnel": "",
                    "date_rendez_vous": ""
                })

            df = pd.DataFrame(data)
            df.to_csv(chemin, index=False, encoding="utf-8-sig")
            return True, f"{len(data)} visite(s) exportée(s) avec succès"

        except Exception as e:
            self.logger.error(f"Erreur export_to_csv visite: {e}")
            return False, f"Erreur lors de l'export : {e}"

    def import_from_excel(self, chemin: str) -> Tuple[bool, str]:
        """
        Importe des visites depuis un fichier Excel.
        Colonnes requises : code_patient, type_visite, urgent, date_visite
        Colonnes optionnelles (VIP/RDV) : code_personnel, date_rendez_vous
        """
        try:
            import pandas as pd

            df = pd.read_excel(chemin)
            df.columns = [c.strip().lower() for c in df.columns]

            colonnes_requises = ["code_patient", "type_visite", "urgent", "date_visite"]
            for col in colonnes_requises:
                if col not in df.columns:
                    return False, f"Colonne manquante dans le fichier : '{col}'"

            code_session = self._session_code()
            if not code_session:
                return False, "Aucune session active — impossible d'importer"

            plage_session = self.dao.get_plage_session(code_session)

            succes_count = 0
            rdv_count = 0
            rdv_manquants = 0
            erreurs = []

            for index, row in df.iterrows():
                ligne = index + 2
                try:
                    code_patient = str(row.get("code_patient", "")).strip()
                    type_visite  = str(row.get("type_visite", "")).strip()
                    urgent       = str(row.get("urgent", "Non")).strip()
                    date_visite  = row.get("date_visite", "")

                    if not code_patient:
                        erreurs.append(f"Ligne {ligne} : code_patient vide")
                        continue

                    patients = self.patient_dao.reed_by_code_patient(code_patient)
                    if not patients:
                        erreurs.append(f"Ligne {ligne} : patient '{code_patient}' introuvable")
                        continue

                    valid_type, msg_type = self._valider_type_visite(type_visite)
                    if not valid_type:
                        erreurs.append(f"Ligne {ligne} : {msg_type}")
                        continue

                    valid_urgent, msg_urgent = self._valider_urgent(urgent)
                    if not valid_urgent:
                        erreurs.append(f"Ligne {ligne} : {msg_urgent}")
                        continue

                    valid_date, msg_date = self._valider_date_visite_import(date_visite)
                    if not valid_date:
                        erreurs.append(f"Ligne {ligne} : {msg_date}")
                        continue

                    if plage_session:
                        date_obj_v = datetime.strptime(msg_date, "%Y-%m-%d %H:%M:%S")
                        err_plage = self._valider_date_dans_session(date_obj_v, plage_session)
                        if err_plage:
                            erreurs.append(f"Ligne {ligne} : {err_plage}")
                            continue

                    nouvelle_visite = Visite(
                        code_visite="",
                        code_patient=code_patient,
                        code_session="",
                        type_visite=type_visite,
                        urgent=urgent,
                        date_visite=msg_date
                    )

                    ok, msg = self._save_visite_import(nouvelle_visite)
                    if not ok:
                        erreurs.append(f"Ligne {ligne} : {msg}")
                        continue

                    succes_count += 1
                    code_visite_cree = nouvelle_visite.get_code_visite()

                    # Création du rendez-vous pour VIP / RDV
                    type_lower = type_visite.lower()
                    if type_lower in ["vip", "rendez-vous", "rendez vous"]:
                        code_personnel = str(row.get("code_personnel", "")).strip()
                        date_rdv       = str(row.get("date_rendez_vous", "")).strip()

                        if code_personnel and date_rdv and date_rdv not in ("", "nan", "None"):
                            cree, msg_rdv = self._creer_rdv_import(
                                code_visite_cree, code_personnel, date_rdv, code_session
                            )
                            if cree:
                                rdv_count += 1
                            else:
                                rdv_manquants += 1
                                erreurs.append(
                                    f"Ligne {ligne} : visite {code_visite_cree} créée "
                                    f"mais rendez-vous rejeté — {msg_rdv}"
                                )
                        else:
                            rdv_manquants += 1

                except Exception as e:
                    erreurs.append(f"Ligne {ligne} : erreur inattendue — {e}")

            return self._construire_message_import(
                succes_count, rdv_count, rdv_manquants, erreurs, source="excel"
            )

        except Exception as e:
            self.logger.error(f"Erreur import_from_excel visite: {e}")
            return False, f"Erreur lors de l'import : {e}"

    def import_from_csv(self, chemin: str) -> Tuple[bool, str]:
        """
        Importe des visites depuis un fichier CSV.
        Colonnes requises : code_patient, type_visite, urgent, date_visite
        Colonnes optionnelles (VIP/RDV) : code_personnel, date_rendez_vous
        """
        try:
            import pandas as pd

            df = pd.read_csv(chemin, encoding="utf-8-sig")
            df.columns = [c.strip().lower() for c in df.columns]

            colonnes_requises = ["code_patient", "type_visite", "urgent", "date_visite"]
            for col in colonnes_requises:
                if col not in df.columns:
                    return False, f"Colonne manquante dans le fichier : '{col}'"

            code_session = self._session_code()
            if not code_session:
                return False, "Aucune session active — impossible d'importer"

            plage_session = self.dao.get_plage_session(code_session)

            succes_count = 0
            rdv_count = 0
            rdv_manquants = 0
            erreurs = []

            for index, row in df.iterrows():
                ligne = index + 2
                try:
                    code_patient = str(row.get("code_patient", "")).strip()
                    type_visite  = str(row.get("type_visite", "")).strip()
                    urgent       = str(row.get("urgent", "Non")).strip()
                    date_visite  = row.get("date_visite", "")

                    if not code_patient:
                        erreurs.append(f"Ligne {ligne} : code_patient vide")
                        continue

                    patients = self.patient_dao.reed_by_code_patient(code_patient)
                    if not patients:
                        erreurs.append(f"Ligne {ligne} : patient '{code_patient}' introuvable")
                        continue

                    valid_type, msg_type = self._valider_type_visite(type_visite)
                    if not valid_type:
                        erreurs.append(f"Ligne {ligne} : {msg_type}")
                        continue

                    valid_urgent, msg_urgent = self._valider_urgent(urgent)
                    if not valid_urgent:
                        erreurs.append(f"Ligne {ligne} : {msg_urgent}")
                        continue

                    valid_date, msg_date = self._valider_date_visite_import(date_visite)
                    if not valid_date:
                        erreurs.append(f"Ligne {ligne} : {msg_date}")
                        continue

                    if plage_session:
                        date_obj_v = datetime.strptime(msg_date, "%Y-%m-%d %H:%M:%S")
                        err_plage = self._valider_date_dans_session(date_obj_v, plage_session)
                        if err_plage:
                            erreurs.append(f"Ligne {ligne} : {err_plage}")
                            continue

                    nouvelle_visite = Visite(
                        code_visite="",
                        code_patient=code_patient,
                        code_session="",
                        type_visite=type_visite,
                        urgent=urgent,
                        date_visite=msg_date
                    )

                    ok, msg = self._save_visite_import(nouvelle_visite)
                    if not ok:
                        erreurs.append(f"Ligne {ligne} : {msg}")
                        continue

                    succes_count += 1
                    code_visite_cree = nouvelle_visite.get_code_visite()

                    # Création du rendez-vous pour VIP / RDV
                    type_lower = type_visite.lower()
                    if type_lower in ["vip", "rendez-vous", "rendez vous"]:
                        code_personnel = str(row.get("code_personnel", "")).strip()
                        date_rdv       = str(row.get("date_rendez_vous", "")).strip()

                        if code_personnel and date_rdv and date_rdv not in ("", "nan", "None"):
                            cree, msg_rdv = self._creer_rdv_import(
                                code_visite_cree, code_personnel, date_rdv, code_session
                            )
                            if cree:
                                rdv_count += 1
                            else:
                                rdv_manquants += 1
                                erreurs.append(
                                    f"Ligne {ligne} : visite {code_visite_cree} créée "
                                    f"mais rendez-vous rejeté — {msg_rdv}"
                                )
                        else:
                            rdv_manquants += 1

                except Exception as e:
                    erreurs.append(f"Ligne {ligne} : erreur inattendue — {e}")

            return self._construire_message_import(
                succes_count, rdv_count, rdv_manquants, erreurs, source="csv"
            )

        except Exception as e:
            self.logger.error(f"Erreur import_from_csv visite: {e}")
            return False, f"Erreur lors de l'import : {e}"

    def _construire_message_import(self, succes: int, rdv: int,
                                   rdv_manquants: int, erreurs: list,
                                   source: str = "") -> Tuple[bool, str]:
        """Construit le message de résultat après un import."""
        if succes == 0:
            msg = "Aucune visite importée."
            if erreurs:
                msg += "\nErreurs :\n" + "\n".join(erreurs[:5])
            return False, msg

        msg = f"{succes} visite(s) importée(s) avec succès."

        if rdv > 0:
            msg += f"\n{rdv} rendez-vous créé(s) automatiquement."

        # Séparer : rdv manquants par colonnes absentes vs rdv rejetés par erreur
        nb_erreurs_rdv = sum(
            1 for e in erreurs if "rendez-vous rejeté" in e
        )
        nb_colonnes_absentes = rdv_manquants - nb_erreurs_rdv

        if nb_colonnes_absentes > 0:
            msg += (
                f"\n{nb_colonnes_absentes} visite(s) VIP/RDV sans rendez-vous "
                f"(colonnes 'code_personnel' ou 'date_rendez_vous' non renseignées — "
                f"à créer manuellement)."
            )

        if nb_erreurs_rdv > 0:
            msg += (
                f"\n{nb_erreurs_rdv} rendez-vous rejeté(s) : le code personnel "
                f"n'existe pas dans la table personnel ou conflit de planning. "
                f"Vérifiez les codes personnel dans votre fichier."
            )

        if erreurs:
            lignes_affichees = [e[:120] for e in erreurs[:3]]
            msg += f"\nDétail ({len(erreurs)} erreur(s)) :\n" + "\n".join(lignes_affichees)
            if len(erreurs) > 3:
                msg += f"\n... et {len(erreurs) - 3} autre(s) — consultez les logs."
            return False, msg

        return True, msg
