"""
Module service métier pour la gestion des commandes de lunettes.

Centralise toute la logique métier (validation, CRUD, suivi livraison,
statistiques financières et de performance) liée aux commandes de lunettes.
Suit le patron d'injection de dépendances : le DAO est injecté via le
constructeur.
"""

import os
import logging
import re
from datetime import datetime
from typing import Dict, Optional

from data.dao_commande_lunette import CommandeLunetteDAO
from models.modeles_lunette import CommandeLunette
from parametre.dao_param import CabinetDAO


class CommandeLunetteService:
    """
    Service métier pour les commandes de lunettes.
    Contient la validation, le nettoyage, les opérations CRUD,
    le suivi de livraison, les statistiques financières / performance
    et les informations cabinet.
    """

    def __init__(self, dao=None, cabinet_dao=None):
        """
        Initialise le service avec injection optionnelle des DAOs.

        Args:
            dao: Instance de CommandeLunetteDAO (créée par défaut si non fournie).
            cabinet_dao: Instance de CabinetDAO (créée par défaut si non fournie).
        """
        self.dao = dao or CommandeLunetteDAO()
        self.cabinetdao = cabinet_dao or CabinetDAO()
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # METHODES DE VALIDATION (LOGIQUE METIER)
    # =========================================================================

    def valider_texte(self, texte: str, nom_champ: str, min_longueur: int = 2) -> tuple:
        """Valide qu'un champ texte est non vide et sans caractères interdits."""
        if not texte or texte.strip() == "":
            return False, f"Le champ {nom_champ} est obligatoire"

        if len(texte.strip()) < min_longueur:
            return False, f"Le {nom_champ} doit contenir au moins {min_longueur} caracteres"

        # Refuse les caractères spéciaux dangereux
        if re.search(r'[<>{}[\]\\|`~]', texte):
            return False, f"Le {nom_champ} contient des caracteres speciaux interdits"

        return True, ""

    def valider_date_livraison(self, date_livraison) -> tuple:
        """Valide que la date de livraison est strictement dans le futur."""
        if not date_livraison:
            return False, "La date de livraison est obligatoire"
        try:
            if isinstance(date_livraison, str):
                date_obj = datetime.strptime(date_livraison, "%d/%m/%Y").date()
            else:
                date_obj = date_livraison.date() if hasattr(date_livraison, "date") else date_livraison

            aujourdhui = datetime.now().date()

            if date_obj <= aujourdhui:
                return False, "La date de livraison doit etre dans le futur"

            return True, ""

        except Exception:
            return False, "Format de date invalide (attendu: JJ/MM/AAAA)"

    def valider_prix(self, prix) -> tuple:
        """Valide que le prix est un nombre positif."""
        try:
            prix_float = float(prix)
            if prix_float < 0:
                return False, "Le prix ne peut pas etre negatif"
            return True, ""
        except Exception:
            return False, "Le prix doit etre un nombre valide"

    def valider_codes_obligatoires(self, commande: CommandeLunette) -> tuple:
        """Valide que les codes acte, session et personnel sont renseignés."""
        if not commande.code_acte or not commande.code_session or not commande.code_personnel:
            return False, "Tous les codes (acte, session, personnel) sont obligatoires"
        return True, ""

    def valider_commande(self, commande: CommandeLunette) -> tuple:
        """
        Regroupe toutes les validations communes à la création et à la modification.
        Évite la duplication de code entre créer et modifier.
        """
        valide, msg = self.valider_texte(commande.numero_cadre, "numero cadre")
        if not valide:
            return False, msg

        valide, msg = self.valider_texte(commande.numero_verre, "numero verre")
        if not valide:
            return False, msg

        valide, msg = self.valider_date_livraison(commande.date_livraison)
        if not valide:
            return False, msg

        valide, msg = self.valider_prix(commande.prix)
        if not valide:
            return False, msg

        return True, ""

    # =========================================================================
    # METHODES UTILITAIRES (NETTOYAGE)
    # =========================================================================

    def _nettoyer_commande(self, commande: CommandeLunette) -> None:
        """Nettoie les champs texte et fixe la date de commande à l'instant présent."""
        commande.numero_cadre  = commande.numero_cadre.strip()
        commande.numero_verre  = commande.numero_verre.strip()
        commande.date_commande = datetime.now()

    # =========================================================================
    # METHODES CRUD
    # =========================================================================

    def creer_commande(self, commande: CommandeLunette) -> tuple:
        """
        Valide et crée une nouvelle commande de lunettes.
        La date_commande est fixée automatiquement à l'instant présent.
        Après création, met à jour automatiquement le statut de la visite (dans le DAO).
        """
        valide, msg = self.valider_commande(commande)
        if not valide:
            return False, msg

        valide, msg = self.valider_codes_obligatoires(commande)
        if not valide:
            return False, msg

        # Vérifie qu'une commande n'existe pas déjà pour cet acte
        if self.dao.obtenir_par_acte(commande.code_acte):
            return False, "Une commande de lunettes existe deja pour cet acte"

        self._nettoyer_commande(commande)

        if self.dao.ajouter(commande):
            self.logger.info(
                f"Commande lunette {commande.code} cree — acte {commande.code_acte}"
            )
            return True, "Commande lunette cree avec succes"

        return False, "Erreur lors de la creation de la commande de lunettes"

    def modifier_commande(self, commande: CommandeLunette) -> tuple:
        """
        Valide et met à jour une commande de lunettes existante.
        """
        valide, msg = self.valider_commande(commande)
        if not valide:
            return False, msg

        self._nettoyer_commande(commande)

        if self.dao.modifier(commande):
            self.logger.info(
                f"Commande lunette {commande.code} modifie — acte {commande.code_acte}"
            )
            return True, "Commande de lunettes modifie avec succes"

        return False, "Erreur lors de la modification de la commande de lunettes"

    def supprimer_commande(self, code: str) -> tuple:
        """Supprime une commande de lunettes par son code."""
        if not code:
            return False, "Code de commande invalide"
        if self.dao.supprimer(code):
            return True, "Commande de lunettes supprime avec succes"
        return False, "Erreur lors de la suppression de la commande de lunettes"

    # =========================================================================
    # METHODES DE RECUPERATION
    # =========================================================================

    def obtenir_par_code(self, code: str):
        """Retourne une commande par son code."""
        return self.dao.obtenir_par_code(code)

    def obtenir_par_acte(self, code_acte: str):
        """Retourne la commande de lunettes liée à un acte médical."""
        return self.dao.obtenir_par_acte(code_acte)

    def lister_commandes(self, code_session: str) -> list:
        """Retourne toutes les commandes de lunettes d'une session."""
        return self.dao.lister_par_session(code_session)

    def lister_commandes_completes(self, code_session: str) -> list:
        """Retourne toutes les commandes avec informations complètes (patient, personnel)."""
        return self.dao.lister_par_session_complet(code_session)

    def rechercher_commande(self, critere: str, code_session: str) -> list:
        """Recherche des commandes par critère dans une session."""
        return self.dao.rechercher_par_critere(critere, code_session)

    def obtenir_commande_complete(self, code_commande: str):
        """Retourne une commande avec les infos patient et personnel."""
        return self.dao.commande_complete(code_commande)

    def obtenir_historique_patient(self, code_patient: str) -> list:
        """Retourne l'historique complet des commandes de lunettes d'un patient."""
        return self.dao.historique_patient(code_patient)

    def obtenir_derniere_commande_patient(self, code_visite: str):
        """Retourne la dernière commande de lunettes d'un patient identifié par sa visite."""
        return self.dao.derniere_commande_patient(code_visite)

    def rechercher_entre_dates(self, code_session: str, date_debut, date_fin) -> list:
        """
        Recherche les commandes de lunettes passées entre deux dates (incluses).

        Args:
            code_session: Code de la session active.
            date_debut: Date de début (datetime.date ou str au format YYYY-MM-DD).
            date_fin:   Date de fin   (datetime.date ou str au format YYYY-MM-DD).

        Returns:
            Liste d'objets CommandeLunette correspondant aux critères.
        """
        if not code_session or not date_debut or not date_fin:
            return []
        return self.dao.rechercher_entre_dates(code_session, date_debut, date_fin)

    # =========================================================================
    # METHODES PATIENTS (LISTES FILTREES)
    # =========================================================================

    def obtenir_patients_attente_lunette(self, code_session: str) -> list:
        """Retourne les patients en attente de lunettes (statut_patient = Attente lunette)."""
        return self.dao.patients_en_attente_lunette(code_session)

    def obtenir_patients_commandes_multiples(self, code_session: str) -> list:
        """Retourne les patients ayant passé plus d'une commande de lunettes sur la session."""
        return self.dao.patients_avec_commandes_multiples(code_session)

    def obtenir_commandes_par_patient_par_mois(
        self, code_session: str, code_patient: str = None
    ) -> dict:
        """
        Retourne le nombre de commandes de lunettes par mois pour chaque patient
        ou pour un patient spécifique.

        Args:
            code_session:  Code de la session active.
            code_patient:  (Optionnel) Code patient pour filtrer sur un seul patient.

        Returns:
            Si code_patient fourni : { "Jan": 2, "Fév": 1, ... }
            Sinon                  : { "Jan": { "P001": 2, "P002": 1 }, ... }
        """
        return self.dao.commandes_par_patient_par_mois(code_session, code_patient)

    def obtenir_codes_patients_session(self, code_session: str) -> list:
        """
        Retourne la liste de tous les patients avec un indicateur (a_consulte)
        précisant s'ils ont déjà une commande de lunettes enregistrée
        dans la session donnée.

        Utile pour alimenter les listes déroulantes ou tableaux de sélection
        dans les formulaires de la vue.

        Args:
            code_session: Code de la session active.

        Returns:
            Liste de dicts : [{'code_patient', 'nom', 'prenom', 'a_consulte'}, ...]
        """
        return self.dao.codes_patients_session(code_session)

    # =========================================================================
    # METHODES STATISTIQUES CARDS
    # =========================================================================

    def obtenir_commandes_en_attente_livraison(self, code_session: str) -> int:
        """Card Attente de Livraisons : nombre de commandes avec statut attente."""
        return self.dao.nombre_commandes_en_attente_livraison(code_session)

    def obtenir_total_commandes_session(self, code_session: str) -> int:
        """Card Commandes Lunettes Total Session : nombre total de commandes de la session."""
        return self.dao.nombre_total_par_session(code_session)

    def obtenir_commandes_en_attente(self, code_session: str) -> int:
        """Card Commandes en Attente : visites avec statut_patient = Attente lunette sans commande enregistrée."""
        return self.dao.nombre_commandes_en_attente(code_session)

    def obtenir_montant_total_aujourdhui(self, code_session: str) -> float:
        """
        Card Montant du Jour : montant total des commandes de lunettes
        enregistrées aujourd'hui pour la session.

        Indicateur de performance en temps réel exploitable sur le dashboard.

        Args:
            code_session: Code de la session active.

        Returns:
            Montant total (float) des commandes du jour, 0.0 si aucune.
        """
        return self.dao.montant_total_commandes_aujourdhui(code_session)

    def obtenir_montant_total_par_session(self, code_session: str) -> float:
        """
        Card Montant Total Session : montant cumulé de toutes les commandes
        de lunettes de la session, sans filtre de date.

        Indicateur global de performance financière exploitable sur le dashboard.

        Args:
            code_session: Code de la session active.

        Returns:
            Montant total (float) de la session, 0.0 si aucune commande.
        """
        return self.dao.montant_total_commandes_par_session(code_session)

    # Les methodes statistiques et analyses

    def obtenir_nombre_par_mois(self, code_session: str) -> dict:
        """Card Commandes par Mois : nombre de commandes groupé par mois pour la session."""
        return self.dao.nombre_par_mois(code_session)

    def obtenir_nombre_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        """Card Commandes par Jour : nombre de commandes groupé par jour pour la session."""
        return self.dao.nombre_par_jour(code_session, annee, mois)

    def obtenir_montant_par_mois(self, code_session: str) -> dict:
        """Card Montant par Mois : montant total des commandes groupé par mois pour la session."""
        return self.dao.montant_par_mois(code_session)

    def obtenir_montant_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        """Card Montant par Jour : montant total des commandes groupé par jour pour la session."""
        return self.dao.montant_par_jour(code_session, annee, mois)

    def obtenir_revenu_moyen_par_mois(self, code_session: str) -> float:
        """Card Revenu Moyen par Mois : revenu moyen par mois pour la session."""
        return self.dao.revenu_moyen_par_mois(code_session)

    def obtenir_moyenne_montant_journlier_par_mois(self, code_session: str) -> dict:
        """Card Moyenne Montant Journalier par Mois : moyenne du montant journalier par mois pour la session."""
        return self.dao.moyenne_montant_journalier_mois(code_session)

    def obtnir_moyenne_commande_par_mois(self, code_session: str) -> dict:
        """Card Moyenne Commande par Mois : moyenne du nombre de commandes par mois pour la session."""
        return self.dao.moyenne_commandes_par_mois(code_session)

    def obtenir_moyenne_nombre_journalier_par_mois(self, code_session: str) -> dict:
        """Card Moyenne Nombre Journalier par Mois : moyenne du nombre de commandes journalier par mois pour la session."""
        return self.dao.moyenne_commandes_journalieres_mois(code_session)

    # =========================================================================
    # METHODES STATISTIQUES & GRAPHES
    # =========================================================================

    def obtenir_commandes_par_mois(self, code_session: str) -> dict:
        """
        Retourne le nombre de commandes par mois pour le graphe mensuel.
        Format : {Jan: 5, Fev: 8, Mar: 0, ...}
        """
        return self.dao.nombre_par_mois(code_session)

    def obtenir_revenu_total(self, code_session: str, date_debut=None, date_fin=None) -> float:
        """Retourne le total des prix des commandes de lunettes pour une session."""
        return self.dao.revenu_total(code_session, date_debut, date_fin)

    def obtenir_top_numeros_verre(self, code_session: str, limite: int = 10) -> list:
        """Retourne les numéros de verre prescrits les plus fréquents pour une session."""
        return self.dao.top_numeros_verre(code_session, limite)

    def obtenir_commandes_par_personnel(self, code_session: str) -> list:
        """Retourne le nombre de commandes groupé par personnel."""
        return self.dao.commandes_par_personnel(code_session)

    # =========================================================================
    # METHODES SUIVI LIVRAISON
    # =========================================================================

    def marquer_comme_livree(self, code: str) -> tuple:
        """
        Marque une commande comme livrée et enregistre la date de livraison réelle.
        Retourne un tuple (succès, message).
        """
        if not code:
            return False, "Code de commande invalide"
        if self.dao.marquer_comme_livree(code):
            self.logger.info(f"Commande lunette {code} marquee comme livree")
            return True, "Commande marquee comme livree avec succes"
        return False, "Erreur : commande introuvable ou deja livree"

    def obtenir_commandes_en_retard(self, code_session: str) -> list:
        """Retourne les commandes dont la date de livraison prévue est dépassée."""
        return self.dao.commandes_en_retard(code_session)

    def obtenir_commandes_a_livrer_dans_deux_jours(self, code_session: str) -> list:
        """Retourne les commandes à livrer dans les deux prochains jours (alerte préventive)."""
        return self.dao.commandes_a_livrer_dans_deux_jours(code_session)

    def obtenir_commande_en_attente_complete(self, code_commande: str):
        """Retourne les informations complètes d'une commande en attente de livraison."""
        return self.dao.commande_en_attente_complete(code_commande)

    def obtenir_toutes_commandes_attente_livraison(self, code_session: str) -> list:
        """Retourne toutes les commandes en attente de livraison avec infos complètes."""
        return self.dao.lister_commandes_en_attente_livraison_completes(code_session)

    # =========================================================================
    # METHODES FINANCIERES
    # =========================================================================

    def obtenir_revenu_recouvre_vs_en_attente(self, code_session: str) -> dict:
        """
        Retourne le montant encaissé et le montant en attente de paiement.
        Format : {'recouvre': float, 'en_attente': float, 'total': float}
        """
        return self.dao.revenu_recouvre_vs_en_attente(code_session)

    def obtenir_commandes_par_statut_facture(self, code_session: str) -> list:
        """
        Retourne pour chaque statut de facturation le nombre de commandes
        et le montant total. Exploitable directement pour un graphique.
        """
        return self.dao.commandes_par_statut_facture(code_session)

    # =========================================================================
    # METHODES PERFORMANCE
    # =========================================================================

    def obtenir_delai_moyen_livraison(self, code_session: str) -> dict:
        """
        Retourne le délai moyen, minimum et maximum de livraison en jours
        ainsi que le nombre de commandes livrées sur lesquelles la moyenne est calculée.
        Format : {'moyen': float, 'minimum': int, 'maximum': int, 'nombre_livrees': int}
        """
        return self.dao.delai_moyen_livraison(code_session)

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