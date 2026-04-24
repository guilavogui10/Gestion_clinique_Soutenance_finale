"""
facture_fournisseur_service.py
-------------------------------
Service métier — Gestion des factures fournisseurs.

Responsabilités :
  - Validation des données (téléphone, mode paiement, codes obligatoires)
  - CRUD : créer, finaliser, modifier, supprimer
  - Récupération : par code, session, fournisseur, recherche, facture complète
  - Statistiques cards et graphes
  - Informations cabinet
"""

import os
import logging
import re
from typing import Dict, Optional, List, Tuple

from data.dao_factureFournisseur import FactureFournisseurDAO
from models.modele_factureFournisseur import FactureFournisseur
from parametre.dao_param import CabinetDAO


class FactureFournisseurService:
    """
    Service métier pour la gestion des factures fournisseurs.
    Logique :
        creer()     → appelée une seule fois quand le fournisseur est sélectionné
        finaliser() → appelée quand l'utilisateur valide la livraison
        supprimer() → supprime la facture ET toutes ses lignes panier en cascade
    """

    MODES_PAYEMENT_VALIDES = ['especes', 'cheque', 'virement', 'mobile money']

    def __init__(self, dao=None, cabinet_dao=None):
        self.dao = dao or FactureFournisseurDAO()
        self.cabinetdao = cabinet_dao or CabinetDAO()
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def valider_telephone(self, telephone: str) -> Tuple[bool, str]:
        """Valide que le téléphone contient uniquement des chiffres (8 à 15)."""
        if not telephone or telephone.strip() == "":
            return False, "Le telephone est obligatoire"
        tel = telephone.strip().replace(" ", "").replace("-", "")
        if not tel.isdigit():
            return False, "Le telephone doit contenir uniquement des chiffres"
        if not (8 <= len(tel) <= 15):
            return False, "Le telephone doit contenir entre 8 et 15 chiffres"
        return True, ""

    def valider_mode_payement(self, mode_payement: str) -> Tuple[bool, str]:
        """Valide que le mode de paiement est parmi les valeurs autorisées."""
        if not mode_payement or mode_payement.strip() == "":
            return False, "Le mode de payement est obligatoire"
        if mode_payement.lower().strip() not in self.MODES_PAYEMENT_VALIDES:
            return False, f"Le mode de payement doit etre : {', '.join(self.MODES_PAYEMENT_VALIDES)}"
        return True, ""

    def valider_codes_obligatoires(self, facture: FactureFournisseur) -> Tuple[bool, str]:
        """Valide que les codes fournisseur et session sont renseignés."""
        if not facture.code_fournisseur:
            return False, "Le fournisseur est obligatoire"
        if not facture.code_session:
            return False, "La session est obligatoire"
        return True, ""

    def valider_finalisation(self, facture: FactureFournisseur) -> Tuple[bool, str]:
        """Validations pour la finalisation (mode_payement + téléphone)."""
        valide, msg = self.valider_mode_payement(facture.mode_payement)
        if not valide:
            return False, msg
        valide, msg = self.valider_telephone(facture.telephone)
        if not valide:
            return False, msg
        return True, ""

    def _nettoyer_facture(self, facture: FactureFournisseur) -> None:
        """Nettoie et normalise les champs texte."""
        if facture.mode_payement:
            facture.mode_payement = facture.mode_payement.strip().lower()
        if facture.telephone:
            facture.telephone = facture.telephone.strip().replace(" ", "").replace("-", "")

    # =========================================================================
    # CRUD
    # =========================================================================

    def creer_facture(self, facture: FactureFournisseur) -> Tuple[bool, str]:
        """
        Valide et crée une nouvelle entête de facture fournisseur.
        Le montant_total démarre à 0 — il sera recalculé par PanierFactureFourniDAO.
        """
        valide, msg = self.valider_codes_obligatoires(facture)
        if not valide:
            return False, msg

        if self.dao.creer(facture):
            self.logger.info(f"Facture {facture.code_facture_four} creee pour fournisseur {facture.code_fournisseur}")
            return True, facture.code_facture_four

        return False, "Erreur lors de la creation de la facture fournisseur"

    def finaliser_facture(self, facture: FactureFournisseur) -> Tuple[bool, str]:
        """Valide et finalise la facture avec mode de paiement et téléphone."""
        if not facture.code_facture_four:
            return False, "Code facture invalide"

        valide, msg = self.valider_finalisation(facture)
        if not valide:
            return False, msg

        self._nettoyer_facture(facture)

        if self.dao.finaliser(facture):
            self.logger.info(f"Facture {facture.code_facture_four} finalisee")
            return True, "Facture finalisee avec succes"

        return False, "Erreur lors de la finalisation de la facture"

    def modifier_facture(self, facture: FactureFournisseur) -> Tuple[bool, str]:
        """
        Valide et modifie une facture existante.
        Ne touche pas au montant_total géré par PanierFactureFourniDAO.
        """
        if not facture.code_facture_four:
            return False, "Code facture invalide"

        valide, msg = self.valider_codes_obligatoires(facture)
        if not valide:
            return False, msg

        # mode_payement et téléphone optionnels à la modification
        if facture.mode_payement:
            valide, msg = self.valider_mode_payement(facture.mode_payement)
            if not valide:
                return False, msg

        if facture.telephone:
            valide, msg = self.valider_telephone(facture.telephone)
            if not valide:
                return False, msg

        self._nettoyer_facture(facture)

        if self.dao.modifier(facture):
            self.logger.info(f"Facture {facture.code_facture_four} modifiee")
            return True, "Facture modifiee avec succes"

        return False, "Erreur lors de la modification de la facture"

    def supprimer_facture(self, code_facture_four: str) -> Tuple[bool, str]:
        """Supprime une facture et toutes ses lignes panier en cascade."""
        if not code_facture_four:
            return False, "Code facture invalide"

        if self.dao.supprimer(code_facture_four):
            self.logger.info(f"Facture {code_facture_four} supprimee avec ses lignes panier")
            return True, "Facture supprimee avec succes"

        return False, "Erreur lors de la suppression de la facture"

    # =========================================================================
    # RÉCUPÉRATION
    # =========================================================================

    def obtenir_par_code(self, code_facture_four: str) -> Optional[FactureFournisseur]:
        """Retourne une facture fournisseur par son code."""
        return self.dao.obtenir_par_code(code_facture_four)

    def lister_factures(self, code_session: str) -> List[FactureFournisseur]:
        """Retourne toutes les factures fournisseurs d'une session."""
        return self.dao.lister_par_session(code_session)

    def lister_par_fournisseur(self, code_fournisseur: str, code_session: str) -> List[FactureFournisseur]:
        """Retourne toutes les factures d'un fournisseur pour une session."""
        return self.dao.lister_par_fournisseur(code_fournisseur, code_session)

    def obtenir_facture_complete(self, code_facture_four: str) -> Optional[Dict]:
        """Retourne la facture avec entête et lignes panier."""
        return self.dao.facture_complete(code_facture_four)

    def rechercher_facture(self, critere: str, code_session: str) -> List[FactureFournisseur]:
        """Recherche des factures par code ou nom fournisseur."""
        return self.dao.rechercher_par_critere(critere, code_session)

    # =========================================================================
    # STATISTIQUES CARDS
    # =========================================================================

    def obtenir_factures_aujourd_hui(self, code_session: str) -> int:
        """Card Factures du Jour."""
        return self.dao.nombre_factures_aujourd_hui(code_session)

    def obtenir_total_factures_session(self, code_session: str) -> int:
        """Card Total Factures."""
        return self.dao.nombre_total_par_session(code_session)

    def obtenir_montant_total_session(self, code_session: str) -> float:
        """Card Dépenses Totales."""
        return self.dao.montant_total_par_session(code_session)

    def obtenir_montant_aujourd_hui(self, code_session: str) -> float:
        """Card Dépenses du Jour."""
        return self.dao.montant_total_aujourd_hui(code_session)

    # =========================================================================
    # STATISTIQUES GRAPHES
    # =========================================================================

    def obtenir_factures_par_mois(self, code_session: str) -> Dict[str, int]:
        """Nombre de factures fournisseurs par mois pour le graphe mensuel."""
        return self.dao.nombre_par_mois(code_session)

    def obtenir_dernieres_factures(self, code_session: str, limite: int = 10) -> List[Dict]:
        """Retourne les N dernières factures de la session pour l'onglet Historique."""
        if not code_session:
            self.logger.warning("obtenir_dernieres_factures: code_session manquant")
            return []
        try:
            resultats = self.dao.lister_dernieres_factures(code_session, limite)
            self.logger.info(
                f"Historique factures: {len(resultats)} résultat(s) "
                f"pour session={code_session} (limite={limite})"
            )
            return resultats
        except Exception as e:
            self.logger.error(f"Erreur obtenir_dernieres_factures: {e}", exc_info=True)
            return []

    # =========================================================================
    # INFORMATIONS CABINET
    # =========================================================================

    def get_cabinet_info(self) -> Dict[str, Optional[str]]:
        """Récupère les informations du cabinet médical."""
        try:
            info = self.cabinetdao.get_info_cabinet() or {}
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
