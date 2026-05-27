"""
Module service métier pour la gestion des chirurgies.

Centralise toute la logique métier (validation, CRUD, statistiques)
liée aux interventions chirurgicales. Suit le patron d'injection de
dépendances : le DAO est injecté via le constructeur.
"""

import os
import logging
import re
from datetime import datetime
from typing import Dict, Optional

from data.dao_chirurgie import ChirurgieDAO
from models.modeles_chirurgie import Chirurgie
from parametre.dao_param import CabinetDAO


class ChirurgieService:
    """
    Service métier pour les chirurgies.
    Contient la validation, le nettoyage, les opérations CRUD,
    la mise à jour du workflow visite, les statistiques et les infos cabinet.
    """

    def __init__(self, dao=None, cabinet_dao=None):
        """
        Initialise le service avec injection optionnelle des DAOs.

        Args:
            dao: Instance de ChirurgieDAO (créée par défaut si non fournie).
            cabinet_dao: Instance de CabinetDAO (créée par défaut si non fournie).
        """
        self.dao = dao or ChirurgieDAO()
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

    def valider_date(self, date_chururgie) -> tuple:
        """Valide que la date de chirurgie est exactement celle d'aujourd'hui."""
        if not date_chururgie:
            return False, "La date de chirurgie est obligatoire"
        try:
            if isinstance(date_chururgie, str):
                date_obj = datetime.strptime(date_chururgie, "%d/%m/%Y").date()
            else:
                date_obj = date_chururgie.date() if hasattr(date_chururgie, "date") else date_chururgie

            aujourdhui = datetime.now().date()

            if date_obj < aujourdhui:
                return False, "La date de chirurgie ne peut pas etre dans le passe"
            if date_obj > aujourdhui:
                return False, "La date de chirurgie ne peut pas etre dans le futur"

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

    def valider_codes_obligatoires(self, chururgie: Chirurgie) -> tuple:
        """Valide que les codes session, personnel et acte sont renseignés."""
        if not chururgie.code_session or not chururgie.code_personnel:
            return False, "Tous les codes (session, personnel) sont obligatoires"
        if not chururgie.code_acte:
            return False, "Le code acte medical est obligatoire"
        return True, ""

    def valider_chururgie(self, chururgie: Chirurgie) -> tuple:
        """
        Regroupe toutes les validations communes à la création et à la modification.
        Évite la duplication de code entre créer et modifier.
        """
        valide, msg = self.valider_texte(chururgie.libelle_chururgie, "libelle chirurgie")
        if not valide:
            return False, msg

        valide, msg = self.valider_date(chururgie.date_chururgie)
        if not valide:
            return False, msg

        valide, msg = self.valider_frais(chururgie.frais_chururgie)
        if not valide:
            return False, msg

        return True, ""

    # =========================================================================
    # METHODES UTILITAIRES (NETTOYAGE & WORKFLOW)
    # =========================================================================

    def _nettoyer_chururgie(self, chururgie: Chirurgie) -> None:
        """Nettoie les champs texte (supprime les espaces superflus)."""
        chururgie.libelle_chururgie = chururgie.libelle_chururgie.strip()
        if chururgie.compte_rendu_operatoire:
            chururgie.compte_rendu_operatoire = chururgie.compte_rendu_operatoire.strip()

    # =========================================================================
    # METHODES CRUD
    # =========================================================================

    def creer_chururgie(self, chururgie: Chirurgie) -> tuple:
        """Valide et crée une nouvelle chirurgie."""
        valide, msg = self.valider_chururgie(chururgie)
        if not valide:
            return False, msg

        valide, msg = self.valider_codes_obligatoires(chururgie)
        if not valide:
            return False, msg

        if self.dao.obtenir_par_acte(chururgie.code_acte):
            return False, "Une chirurgie existe deja pour cet acte medical"

        self._nettoyer_chururgie(chururgie)

        if self.dao.ajouter(chururgie):
            self.logger.info(f"Chirurgie {chururgie.code} cree pour acte {chururgie.code_acte}")
            return True, "Chirurgie cree avec succes"

        return False, "Erreur lors de la creation de la chirurgie"

    def modifier_chururgie(self, chururgie: Chirurgie) -> tuple:
        """Valide et met à jour une chirurgie existante."""
        valide, msg = self.valider_chururgie(chururgie)
        if not valide:
            return False, msg

        self._nettoyer_chururgie(chururgie)

        if self.dao.modifier(chururgie):
            self.logger.info(f"Chirurgie {chururgie.code} modifie")
            return True, "Chirurgie modifie avec succes"

        return False, "Erreur lors de la modification de la chirurgie"

    def supprimer_chururgie(self, code: str) -> tuple:
        """Supprime une chirurgie par son code."""
        if not code:
            return False, "Code de chirurgie invalide"
        if self.dao.supprimer(code):
            return True, "Chirurgie supprime avec succes"
        return False, "Erreur lors de la suppression de la chirurgie"

    # =========================================================================
    # METHODES DE RECUPERATION
    # =========================================================================

    def obtenir_par_code(self, code: str):
        """Retourne une chirurgie par son code."""
        return self.dao.obtenir_par_code(code)

    def obtenir_par_acte(self, code_acte: str):
        """Retourne la chirurgie liée à un acte medical."""
        return self.dao.obtenir_par_acte(code_acte)

    def lister_chururgies(self, code_session: str) -> list:
        """Retourne toutes les chirurgies d'une session."""
        return self.dao.lister_par_session(code_session)

    def rechercher_chururgie(self, critere: str, code_session: str) -> list:
        """Recherche des chirurgies par critère dans une session."""
        return self.dao.rechercher_par_critere(critere, code_session)

    def obtenir_chururgie_complete(self, code_chururgie: str):
        """Retourne une chirurgie avec les infos patient et personnel."""
        return self.dao.chururgie_complete(code_chururgie)

    def obtenir_historique_patient(self, code_patient: str) -> list:
        """Retourne l'historique complet des chirurgies d'un patient."""
        return self.dao.historique_patient(code_patient)

    # =========================================================================
    # METHODES PATIENTS (LISTES FILTREES)
    # =========================================================================

    def obtenir_patients_attente_chururgie(self, code_session: str) -> list:
        """Retourne les patients en attente de chirurgie (statut_patient = Attente chirurgie)."""
        return self.dao.patients_en_attente_chururgie(code_session)

    # =========================================================================
    # MÉTHODES STATISTIQUES (CARDS)
    # =========================================================================

    def obtenir_chururgies_aujourd_hui(self, code_session: str) -> int:
        """Card 'Chirurgies du Jour' : nombre de chirurgies créées aujourd'hui."""
        return self.dao.nombre_chururgies_aujourd_hui(code_session)

    def obtenir_total_chururgies_session(self, code_session: str) -> int:
        """Card 'Total Session' : nombre total de chirurgies de la session."""
        return self.dao.nombre_total_par_session(code_session)

    def obtenir_chururgies_en_attente(self, code_session: str) -> int:
        """Card 'Chirurgies en Attente' : visites avec statut 'Attente chirurgie' sans chirurgie enregistrée."""
        return self.dao.nombre_chururgies_en_attente(code_session)

    def obtenir_montant_total_aujourdhui(self, code_session: str) -> float:
        """Card 'Montant du Jour' : montant total des chirurgies d'aujourd'hui."""
        return self.dao.montant_total_chirurgie_aujourdhui(code_session)

    def obtenir_montant_total_par_session(self, code_session: str) -> float:
        """Card 'Montant Session' : montant total de toutes les chirurgies de la session."""
        return self.dao.montant_total_chirurgie_par_session(code_session)

    def obtenir_revenu_total(self, code_session: str, date_debut=None, date_fin=None) -> float:
        """Alias pour obtenir_montant_total_par_session (compatibilité)."""
        return self.dao.revenu_total(code_session)

    # =========================================================================
    # MÉTHODES STATISTIQUES & GRAPHES - NOMBRE PAR PÉRIODE
    # =========================================================================

    def obtenir_nombre_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        """
        Retourne le nombre de chirurgies par jour pour un mois donné.
        Les jours sans activité sont inclus avec 0.
        - Si annee/mois non fournis: mois courant.
        - Pour le mois courant: jours 1..aujourd'hui.
        - Pour un autre mois: jours 1..fin du mois.
        """
        return self.dao.nombre_par_jour(code_session, annee, mois)

    def obtenir_nombre_par_mois(self, code_session: str) -> dict:
        """
        Retourne le nombre de chirurgies par mois pour le graphe mensuel.
        Format : {Jan: 5, Fév: 8, Mar: 0, ...}
        """
        return self.dao.nombre_par_mois(code_session)

    def obtenir_chururgies_par_mois(self, code_session: str) -> dict:
        """Alias pour obtenir_nombre_par_mois (compatibilité)."""
        return self.dao.nombre_par_mois(code_session)
    # =========================================================================
    # MÉTHODES STATISTIQUES & GRAPHES - MONTANT PAR PÉRIODE
    # =========================================================================

    def obtenir_montant_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        """
        Retourne le montant des chirurgies par jour pour un mois donné.
        Les jours sans activité sont inclus avec 0.
        - Si annee/mois non fournis: mois courant.
        - Pour le mois courant: jours 1..aujourd'hui.
        - Pour un autre mois: jours 1..fin du mois.
        """
        return self.dao.montant_par_jour(code_session, annee, mois)

    def obtenir_montant_par_mois(self, code_session: str) -> dict:
        """
        Retourne le montant total des chirurgies par mois pour le graphe mensuel.
        Format : {Jan: 1500.0, Fév: 2300.0, Mar: 0.0, ...}
        """
        return self.dao.montant_par_mois(code_session)
    # =========================================================================
    # MÉTHODES STATISTIQUES & GRAPHES - MOYENNES
    # =========================================================================

    def obtenir_revenu_moyen_par_mois(self, code_session: str) -> dict:
        """
        Retourne la moyenne journalière des montants par mois (jours sans activité inclus).
        - Mois courant: division par le nombre de jours écoulés (1..aujourd'hui)
        - Mois passés: division par le nombre total de jours du mois
        """
        return self.dao.revenu_moyen_par_mois(code_session)

    def obtenir_moyenne_montant_journalier_par_mois(self, code_session: str) -> dict:
        """Alias pour obtenir_revenu_moyen_par_mois (compatibilité)."""
        return self.dao.moyenne_montant_journalier_mois(code_session)

    def obtenir_moyenne_chirurgie_par_mois(self, code_session: str) -> dict:
        """
        Retourne la moyenne journalière du nombre de chirurgies par mois (jours sans activité inclus).
        - Mois courant: division par le nombre de jours écoulés (1..aujourd'hui)
        - Mois passés: division par le nombre total de jours du mois
        """
        return self.dao.moyenne_chirurgies_par_mois(code_session)

    def obtenir_moyenne_nombre_journalier_par_mois(self, code_session: str) -> dict:
        """Alias pour obtenir_moyenne_chirurgie_par_mois (compatibilité)."""
        return self.dao.moyenne_chirurgies_journalieres_mois(code_session)

    # =========================================================================
    # MÉTHODES STATISTIQUES & GRAPHES - ANALYSES COMPLÉMENTAIRES
    # =========================================================================

    def obtenir_top_libelles(self, code_session: str, limite: int = 10) -> list:
        """Retourne les libellés de chirurgies les plus fréquents pour une session."""
        return self.dao.top_libelles(code_session, limite)

    def obtenir_chururgies_par_personnel(self, code_session: str) -> list:
        """Retourne le nombre de chirurgies groupé par personnel."""
        return self.dao.chururgies_par_personnel(code_session)

    # =========================================================================
    # INFORMATIONS CABINET & PERSONNEL
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

    def rechercher_par_libelle(self, code_session: str, libelle: str) -> list:
        """Recherche des chirurgies par libellé (LIKE) dans une session."""
        return self.dao.rechercher_par_libelle(code_session, libelle)

    def codes_patients_session(self, code_session: str) -> list:
        """Liste les patients avec indicateur de chirurgie dans la session."""
        return self.dao.codes_patients_session(code_session)

    def rechercher_entre_dates(self, code_session: str, date_debut, date_fin) -> list:
        """Retourne les chirurgies entre deux dates (incluses) pour une session."""
        try:
            return self.dao.rechercher_entre_dates(code_session, date_debut, date_fin) or []
        except Exception as e:
            self.logger.error(f"Erreur rechercher_entre_dates chirurgie: {e}")
            return []