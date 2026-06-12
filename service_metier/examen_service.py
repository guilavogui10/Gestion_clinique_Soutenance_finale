"""
Module service métier pour la gestion des examens.

Centralise toute la logique métier (validation, CRUD, statistiques)
liée aux examens ophtalmologiques. Suit le patron d'injection de
dépendances : le DAO est injecté via le constructeur.
"""

import os
import logging
import re
from datetime import datetime
from typing import Dict, Optional

from data.dao_examen import ExamenDAO
from models.modeles_examen import Examen
from parametre.dao_param import CabinetDAO


class ExamenService:
    """
    Service métier pour les examens.
    Contient la validation, le nettoyage, les opérations CRUD,
    les statistiques et les informations cabinet.
    """

    def __init__(self, dao=None, cabinet_dao=None):
        """
        Initialise le service avec injection optionnelle des DAOs.

        Args:
            dao: Instance de ExamenDAO (créée par défaut si non fournie).
            cabinet_dao: Instance de CabinetDAO (créée par défaut si non fournie).
        """
        self.dao = dao or ExamenDAO()
        self.cabinetdao = cabinet_dao or CabinetDAO()
        self.logger = logging.getLogger(__name__)
        # Import différé du DAO visite pour éviter les imports circulaires
        from data.dao_visite import Visitedao
        self.dao_visite = Visitedao()

    # =========================================================================
    # METHODES DE VALIDATION (LOGIQUE METIER)
    # =========================================================================

    def valider_texte(self, texte: str, nom_champ: str, min_longueur: int = 3) -> tuple:
        """Valide qu'un champ texte est non vide et sans caractères interdits."""
        if not texte or texte.strip() == "":
            return False, f"Le champ {nom_champ} est obligatoire"

        if len(texte.strip()) < min_longueur:
            return False, f"Le {nom_champ} doit contenir au moins {min_longueur} caracteres"

        # Refuse les caractères spéciaux dangereux
        if re.search(r'[<>{}[\]\\|`~]', texte):
            return False, f"Le {nom_champ} contient des caracteres speciaux interdits"

        return True, ""

    def valider_date(self, date_examen) -> tuple:
        """Valide que la date d'examen est exactement celle d'aujourd'hui."""
        if not date_examen:
            return False, "La date d examen est obligatoire"
        try:
            if isinstance(date_examen, str):
                date_obj = datetime.strptime(date_examen, "%d/%m/%Y").date()
            else:
                date_obj = date_examen.date() if hasattr(date_examen, "date") else date_examen

            aujourdhui = datetime.now().date()

            if date_obj < aujourdhui:
                return False, "La date d examen ne peut pas etre dans le passe"
            if date_obj > aujourdhui:
                return False, "La date d examen ne peut pas etre dans le futur"

            return True, ""

        except Exception:
            return False, "Format de date invalide (attendu: JJ/MM/AAAA)"

    def valider_frais(self, frais) -> tuple:
        """Valide que les frais sont un nombre positif."""
        try:
            frais_float = float(frais)
            if frais_float < 0:
                return False, "Les frais ne peuvent pas etre negatifs"
            return True, ""
        except Exception:
            return False, "Les frais doivent etre un nombre valide"

    def valider_codes_obligatoires(self, examen: Examen) -> tuple:
        """Valide que les codes session, personnel et acte sont renseignés."""
        if not examen.code_session or not examen.code_personnel:
            return False, "Tous les codes (session, personnel) sont obligatoires"
        if not examen.code_acte:
            return False, "Le code acte medical est obligatoire"
        return True, ""

    def valider_examen(self, examen: Examen) -> tuple:
        """
        Regroupe toutes les validations communes à la création et à la modification.
        Évite la duplication de code entre créer et modifier.
        """
        valide, msg = self.valider_texte(examen.libelle_examen, "libelle examen")
        if not valide:
            return False, msg

        valide, msg = self.valider_date(examen.date_examen)
        if not valide:
            return False, msg

        valide, msg = self.valider_frais(examen.frais_examen)
        if not valide:
            return False, msg

        return True, ""

    # =========================================================================
    # METHODES UTILITAIRES (NETTOYAGE & WORKFLOW)
    # =========================================================================

    def _nettoyer_examen(self, examen: Examen) -> None:
        """Nettoie les champs texte (supprime les espaces superflus)."""
        examen.libelle_examen = examen.libelle_examen.strip()
        if examen.conclusion_medicale:
            examen.conclusion_medicale = examen.conclusion_medicale.strip()

    # =========================================================================
    # METHODES CRUD
    # =========================================================================

    def creer_examen(self, examen: Examen) -> tuple:
        """
        Valide et crée un nouvel examen.
        Le DAO met automatiquement à jour le statut de la visite.
        """
        valide, msg = self.valider_examen(examen)
        if not valide:
            return False, msg

        valide, msg = self.valider_codes_obligatoires(examen)
        if not valide:
            return False, msg

        # Vérifie qu'un examen n'existe pas déjà pour cette consultation
        if self.dao.obtenir_par_acte(examen.code_acte):
            return False, "Un examen existe deja pour cet acte medical"

        self._nettoyer_examen(examen)

        if self.dao.ajouter(examen):
            self.logger.info(f"Examen {examen.code} cree pour acte {examen.code_acte}")
            return True, "Examen cree avec succes"

        return False, "Erreur lors de la creation de l examen"

    def modifier_examen(self, examen: Examen) -> tuple:
        """
        Valide et met à jour un examen existant.
        La date n'est pas revalidee (peut etre dans le passe).
        """
        valide, msg = self.valider_texte(examen.libelle_examen, "libelle examen")
        if not valide:
            return False, msg

        valide, msg = self.valider_frais(examen.frais_examen)
        if not valide:
            return False, msg

        self._nettoyer_examen(examen)

        if self.dao.modifier(examen):
            self.logger.info(f"Examen {examen.code} modifie")
            return True, "Examen modifie avec succes"

        return False, "Erreur lors de la modification de l examen"

    def supprimer_examen(self, code: str) -> tuple:
        """Supprime un examen par son code."""
        if not code:
            return False, "Code d examen invalide"
        if self.dao.supprimer(code):
            return True, "Examen supprime avec succes"
        return False, "Erreur lors de la suppression de l examen"

    # =========================================================================
    # METHODES DE RECUPERATION
    # =========================================================================

    def obtenir_par_code(self, code: str):
        """Retourne un examen par son code."""
        return self.dao.obtenir_par_code(code)

    def obtenir_par_acte(self, code_acte: str):
        """Retourne l'examen lié à un acte medical."""
        return self.dao.obtenir_par_acte(code_acte)

    def obtenir_par_visite(self, code_visite: str):
        """Retourne l'examen lié à une visite."""
        return self.dao.obtenir_par_visite(code_visite)

    def lister_examens(self, code_session: str) -> list:
        """Retourne tous les examens d'une session."""
        return self.dao.lister_par_session(code_session)

    def rechercher_examen(self, critere: str, code_session: str) -> list:
        """Recherche des examens par critère dans une session."""
        return self.dao.rechercher_par_critere(critere, code_session)

    def obtenir_examen_complet(self, code_examen: str):
        """Retourne un examen avec les infos patient et personnel."""
        return self.dao.examen_complet(code_examen)

    def obtenir_consultation_complete(self, code_examen: str):
        """
        Alias de compatibilite avec les vues basees sur consultation.
        """
        return self.dao.consultation_complete(code_examen)

    def obtenir_services_lies(self, code_examen: str) -> dict:
        """Retourne les services liés à l'examen."""
        return self.dao.services_lies(code_examen)

    def obtenir_historique_patient(self, code_patient: str) -> list:
        """Retourne l'historique complet des examens d'un patient."""
        return self.dao.historique_patient(code_patient)

    # =========================================================================
    # METHODES PATIENTS (LISTES FILTREES)
    # =========================================================================

    def obtenir_patients_attente_examen(self, code_session: str) -> list:
        """Retourne les patients en attente d'examen (statut_patient = Attente examen)."""
        return self.dao.patients_en_attente_examen(code_session)

    # =========================================================================
    # METHODES STATISTIQUES CARDS
    # =========================================================================

    def obtenir_examens_aujourd_hui(self, code_session: str) -> int:
        """Card Examens du Jour : nombre d'examens créés aujourd'hui."""
        return self.dao.nombre_examens_aujourd_hui(code_session)

    def obtenir_total_examens_session(self, code_session: str) -> int:
        """Card Total Session : nombre total d'examens de la session."""
        return self.dao.nombre_total_par_session(code_session)

    def obtenir_examens_en_attente(self, code_session: str) -> int:
        """Card Examens en Attente : visites avec statut_patient = Attente examen sans examen enregistré."""
        return self.dao.nombre_examens_en_attente(code_session)

    def obtenir_nombre_patients_en_attente(self, code_session: str) -> int:
        """Alias de compatibilite consultation pour les cards."""
        return self.dao.nombre_patients_en_attente(code_session)

    # =========================================================================
    # METHODES STATISTIQUES & GRAPHES
    # =========================================================================

    def obtenir_examens_par_mois(self, code_session: str) -> dict:
        """
        Retourne le nombre d'examens par mois pour le graphe mensuel.
        Format : {Jan: 5, Fev: 8, Mar: 0, ...}
        """
        return self.dao.nombre_par_mois(code_session)

    def obtenir_nombre_par_mois(self, code_session: str) -> dict:
        """Alias pour obtenir_examens_par_mois (compatibilité tableau)."""
        return self.dao.nombre_par_mois(code_session)

    def obtenir_revenu_total(self, code_session: str, date_debut=None, date_fin=None) -> float:
        """Retourne le total des frais d'examens pour une session."""
        return self.dao.revenu_total(code_session, date_debut, date_fin)

    def obtenir_top_libelles(self, code_session: str, limite: int = 10) -> list:
        """Retourne les libellés d'examens les plus fréquents pour une session."""
        return self.dao.top_libelles(code_session, limite)

    def obtenir_top_diagnostics(self, code_session: str, limite: int = 10) -> list:
        """Alias de compatibilite consultation."""
        return self.dao.top_diagnostics(code_session, limite)

    def obtenir_examens_par_personnel(self, code_session: str) -> list:
        """Retourne le nombre d'examens groupé par personnel."""
        return self.dao.examens_par_personnel(code_session)

    def obtenir_consultations_par_personnel(self, code_session: str) -> list:
        """Alias de compatibilite consultation."""
        return self.dao.consultations_par_personnel(code_session)

    # =========================================================================
    # INFORMATIONS CABINET
    # =========================================================================

    def get_cabinet_info(self) -> Dict[str, Optional[str]]:
        """Récupère les informations du cabinet médical."""
        try:
            info            = self.cabinetdao.get_info_cabinet() or {}
            nom_cabinet     = info.get("nom_cabinet", "Cabinet ophtalmologique")
            adresse_cabinet = info.get("adresse", "")
            logo_cabinet    = info.get("logo", None)

            final_logo = None
            if logo_cabinet:
                try:
                    base_dir  = os.path.dirname(os.path.dirname(__file__))
                    logo_path = os.path.join(base_dir, "connexion", "image", logo_cabinet)
                    if os.path.exists(logo_path) and os.path.isfile(logo_path):
                        final_logo = os.path.abspath(logo_path)
                except Exception as e:
                    self.logger.warning(f"Erreur chemin logo: {e}")

            return {
                "nom_cabinet":     nom_cabinet,
                "adresse_cabinet": adresse_cabinet,
                "logo_url":        final_logo
            }

        except Exception as e:
            self.logger.error(f"Erreur get_cabinet_info: {e}")
            return {
                "nom_cabinet":     "Cabinet ophtalmologique",
                "adresse_cabinet": "",
                "logo_url":        None
            }

    def lister_personnel(self) -> list:
        """Retourne la liste du personnel pour le formulaire."""
        return self.dao.lister_personnel()

    def lister_personnel_par_roles(self, roles: list) -> list:
        from data.dao_user import UserDAO
        return UserDAO().lister_personnel_par_roles(roles)

    # =========================================================================
    # MÉTHODES ANALYSES ET TABLEAUX (analogue ConsultationService)
    # =========================================================================

    def obtenir_montant_aujourd_hui(self, code_session: str) -> float:
        return self.dao.montant_examens_aujourd_hui(code_session)

    def obtenir_montant_session(self, code_session: str) -> float:
        return self.dao.montant_examens_session(code_session)

    def obtenir_montant_par_mois(self, code_session: str) -> dict:
        return self.dao.montant_par_mois(code_session)

    def obtenir_nombre_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        return self.dao.nombre_par_jour(code_session, annee, mois)

    def obtenir_montant_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        return self.dao.montant_par_jour(code_session, annee, mois)

    def obtenir_moyenne_examens_journaliers_par_mois(self, code_session: str) -> dict:
        return self.dao.moyenne_examens_journaliers_mois(code_session)

    def obtenir_moyenne_nombre_journalier_par_mois(self, code_session: str) -> dict:
        """
        Alias de compatibilite avec les vues analyse inspirees de consultation.
        """
        return self.dao.moyenne_examens_journaliers_mois(code_session)

    def obtenir_moyenne_examens_par_mois(self, code_session: str) -> dict:
        """
        Alias metier explicite pour la moyenne journaliere du nombre d'examens.
        """
        return self.dao.moyenne_examens_par_mois(code_session)

    def obtenir_moyenne_montant_journalier_par_mois(self, code_session: str) -> dict:
        return self.dao.moyenne_montant_journalier_mois(code_session)

    def obtenir_revenu_moyen_par_mois(self, code_session: str) -> dict:
        """
        Alias de compatibilite avec les anciens noms utilises dans certaines vues.
        """
        return self.dao.revenu_moyen_par_mois(code_session)

    def obtenir_resume_session(self, code_session: str) -> dict:
        return self.dao.resume_session(code_session)

    def obtenir_rechercher_entre_dates(self, code_session: str, date_debut, date_fin) -> list:
        return self.dao.rechercher_entre_dates(code_session, date_debut, date_fin)

    def rechercher_entre_dates(self, code_session: str, date_debut, date_fin) -> list:
        return self.dao.rechercher_entre_dates(code_session, date_debut, date_fin)

    def obtenir_rechercher_par_libelle(self, code_session: str, libelle: str = None) -> list:
        return self.dao.rechercher_par_libelle(code_session, libelle)

    def rechercher_par_libelle(self, code_session: str, libelle: str = None) -> list:
        return self.dao.rechercher_par_libelle(code_session, libelle)

    def obtenir_nombre_par_mois_filtre(self, code_session: str, libelle: str = None) -> dict:
        return self.dao.nombre_par_mois_filtre(code_session, libelle)

    def obtenir_examens_par_patient_par_mois(self, code_session: str, code_patient: str = None) -> dict:
        return self.dao.examens_par_patient_par_mois(code_session, code_patient)

    def obtenir_consultations_par_patient_par_mois(self, code_session: str, code_patient: str = None) -> dict:
        """Alias de compatibilite consultation."""
        return self.dao.consultations_par_patient_par_mois(code_session, code_patient)

    def obtenir_codes_patients_session(self, code_session: str) -> list:
        return self.dao.codes_patients_session(code_session)

    def obtenir_patients_en_attente(self, code_session: str) -> list:
        return self.dao.patients_en_attente(code_session)

    def obtenir_patients_examen(self, code_session: str) -> list:
        return self.dao.patients_pour_examen(code_session)

    def obtenir_moyenne_consultations_journalieres_par_mois(self, code_session: str) -> dict:
        return self.dao.moyenne_consultations_journalieres_mois(code_session)

    def obtenir_moyenne_consultations_par_mois(self, code_session: str) -> dict:
        return self.dao.moyenne_consultations_par_mois(code_session)
