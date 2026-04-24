import sys
import os
import logging
import re
from typing import Dict, Optional, List, Tuple
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.dao_factureFournisseur import FactureFournisseurDAO
from models.modele_factureFournisseur import FactureFournisseur
from parametre.dao_param import CabinetDAO


class FactureFournisseurControleur:
    """
    Controleur MVC pour la gestion des factures fournisseurs.
    Fait le lien entre la vue et le DAO.
    Contient toute la logique metier et la validation des donnees.

    Logique :
        creer()     → appelee une seule fois quand le fournisseur est selectionne
        finaliser() → appelee quand l utilisateur valide la livraison
        supprimer() → supprime la facture ET toutes ses lignes panier en cascade
    """

    MODES_PAYEMENT_VALIDES = ['especes', 'cheque', 'virement', 'mobile money', 'orange money', 'mtn mobile money']

    def __init__(self):
        self.dao        = FactureFournisseurDAO()
        self.cabinetdao = CabinetDAO()
        self.logger     = logging.getLogger(__name__)

    # =========================================================================
    # METHODES DE VALIDATION (LOGIQUE METIER)
    # =========================================================================

    def valider_telephone(self, telephone: str) -> Tuple[bool, str]:
        """Valide que le telephone contient uniquement des chiffres et a une longueur correcte."""
        if not telephone or telephone.strip() == "":
            return False, "Le telephone est obligatoire"
        tel = telephone.strip().replace(" ", "").replace("-", "")
        if not tel.isdigit():
            return False, "Le telephone doit contenir uniquement des chiffres"
        if not (8 <= len(tel) <= 15):
            return False, "Le telephone doit contenir entre 8 et 15 chiffres"
        return True, ""

    def valider_mode_payement(self, mode_payement: str) -> Tuple[bool, str]:
        """Valide que le mode de payement est parmi les valeurs autorisees."""
        if not mode_payement or mode_payement.strip() == "":
            return False, "Le mode de payement est obligatoire"
        if mode_payement.lower().strip() not in self.MODES_PAYEMENT_VALIDES:
            return False, f"Le mode de payement doit etre : {', '.join(self.MODES_PAYEMENT_VALIDES)}"
        return True, ""

    def valider_codes_obligatoires(self, facture: FactureFournisseur) -> Tuple[bool, str]:
        """Valide que les codes fournisseur et session sont renseignes."""
        if not facture.code_fournisseur:
            return False, "Le fournisseur est obligatoire"
        if not facture.code_session:
            return False, "La session est obligatoire"
        return True, ""

    def valider_finalisation(self, facture: FactureFournisseur) -> Tuple[bool, str]:
        """
        Regroupe les validations pour la finalisation de la facture.
        mode_payement et telephone obligatoires uniquement a la validation.
        """
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
    # METHODES CRUD
    # =========================================================================

    def creer_facture(self, facture: FactureFournisseur) -> Tuple[bool, str]:
        """
        Valide et cree une nouvelle entete de facture fournisseur.
        Appelee une seule fois quand l utilisateur selectionne le fournisseur.
        Le montant_total demarre a 0 — il sera recalcule par PanierFactureFourniDAO.
        """
        valide, msg = self.valider_codes_obligatoires(facture)
        if not valide:
            return False, msg

        if self.dao.creer(facture):
            self.logger.info(f"Facture {facture.code_facture_four} creee pour fournisseur {facture.code_fournisseur}")
            return True, facture.code_facture_four
        
        return False, "Erreur lors de la creation de la facture fournisseur"

    def finaliser_facture(self, facture: FactureFournisseur) -> Tuple[bool, str]:
        """
        Valide et finalise la facture avec mode de payement et telephone.
        Appelee quand l utilisateur valide la livraison.
        """
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
        Valide et modifie les informations d une facture existante.
        Ne touche pas au montant_total gere par PanierFactureFourniDAO.
        """
        if not facture.code_facture_four:
            return False, "Code facture invalide"

        valide, msg = self.valider_codes_obligatoires(facture)
        if not valide:
            return False, msg

        # mode_payement et telephone optionnels a la modification
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
        """
        Supprime une facture et toutes ses lignes panier en cascade.
        Le DAO decremente automatiquement le stock pour chaque ligne supprimee.
        """
        if not code_facture_four:
            return False, "Code facture invalide"

        if self.dao.supprimer(code_facture_four):
            self.logger.info(f"Facture {code_facture_four} supprimee avec ses lignes panier")
            return True, "Facture supprimee avec succes"

        return False, "Erreur lors de la suppression de la facture"

    # =========================================================================
    # METHODES DE RECUPERATION
    # =========================================================================

    def obtenir_par_code(self, code_facture_four: str) -> Optional[FactureFournisseur]:
        """Retourne une facture fournisseur par son code."""
        return self.dao.obtenir_par_code(code_facture_four)

    def lister_factures(self, code_session: str) -> List[FactureFournisseur]:
        """Retourne toutes les factures fournisseurs d une session."""
        return self.dao.lister_par_session(code_session)

    def lister_par_fournisseur(self, code_fournisseur: str, code_session: str) -> List[FactureFournisseur]:
        """Retourne toutes les factures d un fournisseur pour une session."""
        return self.dao.lister_par_fournisseur(code_fournisseur, code_session)

    def obtenir_facture_complete(self, code_facture_four: str) -> Optional[Dict]:
        """
        Retourne la facture avec entete et lignes panier.
        Utilisee pour l impression de la facture.
        Retourne : {'entete': ..., 'lignes': [...]}
        """
        return self.dao.facture_complete(code_facture_four)

    def rechercher_facture(self, critere: str, code_session: str) -> List[FactureFournisseur]:
        """Recherche des factures par code ou nom fournisseur."""
        return self.dao.rechercher_par_critere(critere, code_session)

    # =========================================================================
    # METHODES STATISTIQUES CARDS
    # =========================================================================

    def obtenir_factures_aujourd_hui(self, code_session: str) -> int:
        """Card Factures du Jour : nombre de factures creees aujourd hui."""
        return self.dao.nombre_factures_aujourd_hui(code_session)

    def obtenir_total_factures_session(self, code_session: str) -> int:
        """Card Total Factures : nombre total de factures de la session."""
        return self.dao.nombre_total_par_session(code_session)

    def obtenir_montant_total_session(self, code_session: str) -> float:
        """Card Depenses Totales : somme de tous les montants de la session."""
        return self.dao.montant_total_par_session(code_session)

    def obtenir_montant_aujourd_hui(self, code_session: str) -> float:
        """Card Depenses du Jour : somme des montants des factures d aujourd hui."""
        return self.dao.montant_total_aujourd_hui(code_session)

    # =========================================================================
    # METHODES STATISTIQUES GRAPHES
    # =========================================================================

    def obtenir_factures_par_mois(self, code_session: str) -> Dict[str, int]:
        """
        Retourne le nombre de factures fournisseurs par mois pour le graphe mensuel.
        Format : {Jan: 2, Fev: 5, Mar: 0, ...}
        """
        return self.dao.nombre_par_mois(code_session)
    
    
    def obtenir_dernieres_factures(self, code_session: str, limite: int = 10) -> List[Dict]:
        """
        Retourne les N dernières factures de la session pour l'onglet Historique.
        
        Args:
            code_session: Code de la session en cours
            limite: Nombre maximum de factures à retourner (défaut: 10)
        
        Returns:
            Liste de dictionnaires avec infos facture + fournisseur,
            triée par date décroissante.
        """
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
        """Recupere les informations du cabinet medical."""
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