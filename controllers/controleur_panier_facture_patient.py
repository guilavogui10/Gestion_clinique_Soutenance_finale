import sys
import os
import logging
import re
from typing import Dict, Optional, List, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.dao_panier_facture_patient import PanierFactureDAO
from models.modele_panier_facture import PanierFacture
from parametre.dao_param import CabinetDAO


class PanierFacturePatientControleur:
    """
    Controleur MVC pour la gestion des lignes panier de la facture patient.
    Fait le lien entre la vue et le DAO.
    Contient toute la logique metier et la validation des donnees.
    """

    def __init__(self):
        self.dao        = PanierFactureDAO()
        self.cabinetdao = CabinetDAO()
        self.logger     = logging.getLogger(__name__)

    # =========================================================================
    # METHODES DE VALIDATION (LOGIQUE METIER)
    # =========================================================================

    def valider_designation(self, designation: str) -> Tuple[bool, str]:
        """Valide que la designation est non vide et sans caracteres interdits."""
        if not designation or designation.strip() == "":
            return False, "La designation est obligatoire"
        if len(designation.strip()) < 2:
            return False, "La designation doit contenir au moins 2 caracteres"
        if re.search(r'[<>{}[\]\\|`~@#$%^*+=]', designation):
            return False, "La designation contient des caracteres speciaux interdits"
        return True, ""

    def valider_quantite(self, quantite) -> Tuple[bool, str]:
        """Valide que la quantite est un entier strictement positif."""
        try:
            qte = int(quantite)
            if qte <= 0:
                return False, "La quantite doit etre superieure a 0"
            return True, ""
        except Exception:
            return False, "La quantite doit etre un nombre entier valide"

    def valider_prix(self, prix) -> Tuple[bool, str]:
        """Valide que le prix est un nombre strictement positif."""
        try:
            prix_float = float(prix)
            if prix_float <= 0:
                return False, "Le prix applique doit etre superieur a 0"
            return True, ""
        except Exception:
            return False, "Le prix applique doit etre un nombre valide"

    def valider_codes_obligatoires(self, ligne: PanierFacture) -> Tuple[bool, str]:
        """Valide que les codes obligatoires (facture, reference) sont renseignes."""
        if not ligne.get_code_facture():
            return False, "Le code facture est obligatoire"
        if not ligne.get_numero_reference():
            return False, "Le numero de reference est obligatoire"
        return True, ""

    def valider_ligne(self, ligne: PanierFacture) -> Tuple[bool, str]:
        """
        Regroupe toutes les validations communes a l ajout et a la modification.
        Evite la duplication de code entre ajouter et modifier.
        """
        valide, msg = self.valider_designation(ligne.get_designation())
        if not valide:
            return False, msg

        valide, msg = self.valider_quantite(ligne.get_quantite_facture())
        if not valide:
            return False, msg

        valide, msg = self.valider_prix(ligne.get_prix_applique())
        if not valide:
            return False, msg

        return True, ""

    def _nettoyer_ligne(self, ligne: PanierFacture) -> None:
        """Nettoie les champs texte et normalise les valeurs numeriques."""
        ligne.set_designation(ligne.get_designation().strip())
        ligne.set_quantite_facture(int(ligne.get_quantite_facture()))
        ligne.set_prix_applique(float(ligne.get_prix_applique()))

    # =========================================================================
    # METHODES CRUD
    # =========================================================================

    def ajouter_ligne(self, ligne: PanierFacture) -> Tuple[bool, str]:
        """
        Valide et ajoute une ligne dans le panier de la facture patient.

        Args:
            ligne (PanierFacture): Objet ligne a inserer.

        Returns:
            Tuple(bool, str): (succes, message)
        """
        valide, msg = self.valider_ligne(ligne)
        if not valide:
            return False, msg

        valide, msg = self.valider_codes_obligatoires(ligne)
        if not valide:
            return False, msg

        self._nettoyer_ligne(ligne)

        if self.dao.ajouter(ligne):
            self.logger.info(f"Ligne panier {ligne.get_code_paniere()} ajoutee - facture {ligne.get_code_facture()}")
            return True, "Ligne ajoutee au panier avec succes"

        return False, "Erreur lors de l ajout de la ligne dans le panier"

    def modifier_ligne(self, ligne: PanierFacture) -> Tuple[bool, str]:
        """
        Valide et modifie une ligne existante du panier.

        Args:
            ligne (PanierFacture): Objet ligne avec les nouvelles donnees.

        Returns:
            Tuple(bool, str): (succes, message)
        """
        if not ligne.get_code_paniere():
            return False, "Code ligne panier invalide"

        valide, msg = self.valider_ligne(ligne)
        if not valide:
            return False, msg

        self._nettoyer_ligne(ligne)

        if self.dao.modifier(ligne):
            self.logger.info(f"Ligne panier {ligne.get_code_paniere()} modifiee")
            return True, "Ligne panier modifiee avec succes"

        return False, "Erreur lors de la modification de la ligne panier"

    def supprimer_ligne(self, code_paniere: str) -> Tuple[bool, str]:
        """
        Supprime une ligne du panier par son code.

        Args:
            code_paniere (str): Code de la ligne a supprimer.

        Returns:
            Tuple(bool, str): (succes, message)
        """
        if not code_paniere:
            return False, "Code ligne panier invalide"

        if self.dao.supprimer(code_paniere):
            self.logger.info(f"Ligne panier {code_paniere} supprimee")
            return True, "Ligne supprimee du panier avec succes"

        return False, "Erreur lors de la suppression de la ligne panier"

    def supprimer_lignes_facture(self, code_facture: str) -> Tuple[bool, str]:
        """
        Supprime toutes les lignes du panier d'une facture.
        Utilise lors de l'annulation ou de la regeneration d'une facture.

        Args:
            code_facture (str): Code de la facture concernee.

        Returns:
            Tuple(bool, str): (succes, message)
        """
        if not code_facture:
            return False, "Code facture invalide"

        if self.dao.supprimer_par_facture(code_facture):
            self.logger.info(f"Toutes les lignes panier de la facture {code_facture} supprimees")
            return True, "Lignes panier supprimees avec succes"

        return False, "Erreur lors de la suppression des lignes panier"

    # =========================================================================
    # METHODES DE RECUPERATION
    # =========================================================================

    def obtenir_par_code(self, code_paniere: str) -> Optional[PanierFacture]:
        """Retourne une ligne panier par son code."""
        return self.dao.obtenir_par_code(code_paniere)

    def lister_par_facture(self, code_facture: str) -> List[PanierFacture]:
        """Retourne toutes les lignes du panier pour une facture donnee."""
        return self.dao.lister_par_facture(code_facture)

    # =========================================================================
    # METHODES STATISTIQUES
    # =========================================================================

    def obtenir_total_facture(self, code_facture: str) -> float:
        """
        Calcule et retourne le montant total d'une facture
        en sommant ses lignes panier.
        """
        try:
            return self.dao.calculer_total_facture(code_facture) or 0.0
        except Exception as e:
            self.logger.error(f"Erreur calculer_total_facture: {e}")
            return 0.0

    def obtenir_repartition_par_service(self, code_session: str) -> List[Dict]:
        """
        Repartition des montants par type de service pour les factures payees.
        Utilise pour le graphique revenus par service du dashboard.
        Retourne : [{'designation', 'nombre', 'total'}, ...]
        """
        try:
            return self.dao.repartition_par_service(code_session)
        except Exception as e:
            self.logger.error(f"Erreur repartition_par_service: {e}")
            return []

    def obtenir_resume_economie_session(self, code_session: str) -> Dict:
        """
        KPI globaux de la vue economie du cabinet
        bases sur les lignes panier payees.
        """
        try:
            return self.dao.resume_economie_session(code_session)
        except Exception as e:
            self.logger.error(f"Erreur resume_economie_session: {e}")
            return {
                "chiffre_affaires_total": 0.0,
                "nombre_services_factures": 0,
                "nombre_factures_payees": 0,
                "panier_moyen_facture": 0.0,
                "service_plus_rentable": "",
                "montant_service_plus_rentable": 0.0,
            }

    def obtenir_top_services_par_revenus(self, code_session: str, limite: int = 5) -> List[Dict]:
        """Retourne le classement des services par revenus."""
        try:
            return self.dao.top_services_par_revenus(code_session, limite)
        except Exception as e:
            self.logger.error(f"Erreur top_services_par_revenus: {e}")
            return []

    def obtenir_volume_vs_revenus_par_service(self, code_session: str) -> List[Dict]:
        """Retourne le volume et les revenus pour chaque service."""
        try:
            return self.dao.volume_vs_revenus_par_service(code_session)
        except Exception as e:
            self.logger.error(f"Erreur volume_vs_revenus_par_service: {e}")
            return []

    def obtenir_top_services_par_volume(self, code_session: str, limite: int = 10) -> List[Dict]:
        """Retourne le classement des services par volume."""
        try:
            return self.dao.top_services_par_volume(code_session, limite)
        except Exception as e:
            self.logger.error(f"Erreur top_services_par_volume: {e}")
            return []

    def obtenir_evolution_chiffre_affaires_par_mois(self, code_session: str) -> Dict:
        """Retourne l'evolution mensuelle du chiffre d'affaires."""
        try:
            return self.dao.evolution_chiffre_affaires_par_mois(code_session)
        except Exception as e:
            self.logger.error(f"Erreur evolution_chiffre_affaires_par_mois: {e}")
            return {}

    def obtenir_apercu_facture_detail(self, code_facture: str) -> Dict:
        """Retourne l'apercu detaille des lignes panier d'une facture."""
        try:
            return self.dao.apercu_facture_detail(code_facture)
        except Exception as e:
            self.logger.error(f"Erreur apercu_facture_detail: {e}")
            return {"code_facture": code_facture, "lignes": [], "total_facture": 0.0}

    def obtenir_derniere_facture_payee_apercu(self, code_session: str) -> Dict:
        """Retourne l'apercu de la derniere facture payee de la session."""
        try:
            return self.dao.derniere_facture_payee_apercu(code_session)
        except Exception as e:
            self.logger.error(f"Erreur derniere_facture_payee_apercu: {e}")
            return {"code_facture": "", "lignes": [], "total_facture": 0.0}

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
                "logo_url":        final_logo,
            }

        except Exception as e:
            self.logger.error(f"Erreur get_cabinet_info: {e}")
            return {
                "nom_cabinet":     "Cabinet ophtalmologique",
                "adresse_cabinet": "",
                "logo_url":        None,
            }
