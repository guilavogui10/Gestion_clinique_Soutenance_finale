"""
prescription_controleur.py
---------------------------
Contrôleur MVC — Gestion des prescriptions (service pharmacie).
Orchestre les appels entre la vue et le service.
"""

import sys
import os
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.modele_panier_prescription_produit import PanierPrescriptionProduit
from service_metier.prescription_service import PrescriptionService


class PrescriptionControleur:
    """
    Contrôleur MVC pour la gestion des prescriptions produits.
    Fait le lien entre la vue et le service.
    Orchestre les appels sans contenir de logique metier.
    """

    def __init__(self):
        self.service = PrescriptionService()
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # DELEGATION AU SERVICE (pas de logique metier ici)
    # =========================================================================

    def ajouter_ligne(self, prescription: PanierPrescriptionProduit) -> Tuple[bool, str]:
        """Delegue l ajout au service."""
        return self.service.ajouter_ligne(prescription)

    def modifier_ligne(self, prescription: PanierPrescriptionProduit) -> Tuple[bool, str]:
        """Delegue la modification au service."""
        return self.service.modifier_ligne(prescription)

    def supprimer_ligne(self, code_prescription: str) -> Tuple[bool, str]:
        """Delegue la suppression au service."""
        return self.service.supprimer_ligne(code_prescription)

    def valider_prescription_visite(self, code_acte: str) -> Tuple[bool, str]:
        """Delègue la validation au service."""
        return self.service.valider_prescription_visite(code_acte)

    def obtenir_par_code(self, code_prescription: str) -> Optional[PanierPrescriptionProduit]:
        """Retourne un objet PanierPrescriptionProduit ou None."""
        return self.service.obtenir_par_code(code_prescription)

    def lister_par_acte(self, code_acte: str) -> List[PanierPrescriptionProduit]:
        """Retourne les lignes du panier prescription d un acte médical."""
        return self.service.lister_par_acte(code_acte)

    def lister_par_session(self, code_session: str) -> List[PanierPrescriptionProduit]:
        """Toutes les prescriptions de la session (tableau principal)."""
        return self.service.lister_par_session(code_session)

    def lister_groupes_par_acte(self, code_session: str) -> List[Dict]:
        """Liste regroupée : 1 ligne par acte médical."""
        return self.service.lister_groupes_par_acte(code_session)

    def lister_par_visite(self, code_visite: str) -> List[PanierPrescriptionProduit]:
        """Toutes les prescriptions liées à une visite."""
        return self.service.lister_par_visite(code_visite)

    def rechercher(self, critere: str, code_session: str) -> List[PanierPrescriptionProduit]:
        """Recherche sur code, désignation, nom/prénom patient."""
        return self.service.rechercher(critere, code_session)

    def obtenir_prescription_complete(self, code_prescription: str) -> Optional[Dict]:
        """Retourne un dict complet avec infos patient + produit."""
        return self.service.obtenir_prescription_complete(code_prescription)

    def obtenir_patients_en_attente(self, code_session: str) -> List[Dict]:
        """Retourne les patients avec statut 'Attente pharmacie'."""
        return self.service.obtenir_patients_en_attente(code_session)

    def obtenir_historique_patient(self, code_patient: str) -> List[Dict]:
        """Historique complet des prescriptions d un patient."""
        return self.service.obtenir_historique_patient(code_patient)

    def lister_produits(self) -> List[Dict]:
        """Retourne tous les produits actifs pour peupler combo_produit."""
        return self.service.lister_produits()

    def obtenir_infos_produit(self, code_produit: str) -> Tuple[str, float]:
        """Retourne (designation, prix_vente_unitaire) d un produit."""
        return self.service.obtenir_infos_produit(code_produit)

    def obtenir_montant_total_acte(self, code_acte: str) -> float:
        """Total du panier prescription en cours."""
        return self.service.obtenir_montant_total_acte(code_acte)

    def obtenir_nombre_lignes_acte(self, code_acte: str) -> int:
        """Nombre de produits dans le panier en cours."""
        return self.service.obtenir_nombre_lignes_acte(code_acte)

    def get_montant_pharmacie_par_visite(self, code_visite: str) -> float:
        """Agrège TOUTES les lignes d une visite en UN seul montant pharmacie."""
        return self.service.get_montant_pharmacie_par_visite(code_visite)

    def get_detail_lignes_par_visite(self, code_visite: str) -> List[Dict]:
        """Retourne le détail des lignes pour affichage dans la facture patient."""
        return self.service.get_detail_lignes_par_visite(code_visite)

    def obtenir_nombre_prescriptions_aujourd_hui(self, code_session: str) -> int:
        """Card 'Prescriptions du Jour'."""
        return self.service.obtenir_nombre_prescriptions_aujourd_hui(code_session)

    def obtenir_nombre_total_session(self, code_session: str) -> int:
        """Card 'Total Session'."""
        return self.service.obtenir_nombre_total_session(code_session)

    def obtenir_nombre_en_attente(self, code_session: str) -> int:
        """Card 'En Attente'."""
        return self.service.obtenir_nombre_en_attente(code_session)

    def obtenir_montant_total_session(self, code_session: str) -> float:
        """Card 'Chiffre d Affaire Session'."""
        return self.service.obtenir_montant_total_session(code_session)

    def obtenir_quantites_par_statut_expiration(self, code_session: str) -> Dict[str, int]:
        """Cards expiration : Expiré / Bientôt / Valide."""
        return self.service.obtenir_quantites_par_statut_expiration(code_session)

    def obtenir_quantites_par_type_produit(self, code_session: str) -> Dict[str, int]:
        """DonutCards : Stock Liquide / Pommade / Comprimé."""
        return self.service.obtenir_quantites_par_type_produit(code_session)

    def obtenir_stock_detaille(self, code_session: str, limite: int = 20) -> List[Dict]:
        """Card libellé (liste scrollable) : stock par produit."""
        return self.service.obtenir_stock_detaille(code_session, limite)

    def obtenir_prescriptions_par_mois(self, code_session: str) -> Dict[str, int]:
        """Graphique barres : nombre de prescriptions par mois."""
        return self.service.obtenir_prescriptions_par_mois(code_session)

    def obtenir_revenu_total(self, code_session: str, date_debut: str = None, date_fin: str = None) -> float:
        """Chiffre d affaire pharmacie avec filtre date optionnel."""
        return self.service.obtenir_revenu_total(code_session, date_debut, date_fin)

    def obtenir_top_designations(self, code_session: str, limite: int = 10) -> List[Dict]:
        """Top N désignations les plus fréquentes."""
        return self.service.obtenir_top_designations(code_session, limite)

    def obtenir_prescriptions_par_produit(self, code_session: str) -> List[Dict]:
        """Agrégation par produit : nb, quantité totale, montant."""
        return self.service.obtenir_prescriptions_par_produit(code_session)

    def obtenir_top_produits_prescrits(self, code_session: str, limite: int = None) -> List[Dict]:
        """Top N produits par quantité prescrite."""
        return self.service.obtenir_top_produits_prescrits(code_session, limite)

    def obtenir_comparaison_entrees_sorties(self, code_session: str) -> Dict[str, Dict[str, int]]:
        """Compare entrées / sorties par mois."""
        return self.service.obtenir_comparaison_entrees_sorties(code_session)

    def obtenir_top_produits_consommes(self, code_session: str, limite: int = None) -> List[Dict]:
        """Top produits consommés avec stock restant."""
        return self.service.obtenir_top_produits_consommes(code_session, limite)

    def verifier_stock_avant_prescription(self, code_produit: str, code_session: str, quantite: int) -> Tuple[bool, str]:
        """Vérifie le stock GLOBAL avant ajouter_ligne()."""
        return self.service.verifier_stock_avant_prescription(code_produit, code_session, quantite)

    def obtenir_date_fefo(self, code_produit: str, code_session: str, quantite: int) -> Optional[datetime]:
        """Retourne la date FEFO pour affichage informatif dans la vue."""
        return self.service.obtenir_date_fefo(code_produit, code_session, quantite)

    def get_cabinet_info(self) -> Dict[str, Optional[str]]:
        """Informations du cabinet pour l en-tête des ordonnances."""
        return self.service.get_cabinet_info()

    # --------- RAPPORTS PDF ---------

    def generer_pdf_rapport_prescriptions_par_date(self, code_session):
        """Récupère tous les groupes de la session et génère un PDF groupé par date de consultation."""
        from services.pdf_rapports.rapport_prescription import RapportPrescriptionPDF
        groupes = self.lister_groupes_par_acte(code_session) or []
        info_cabinet = self.get_cabinet_info()
        return RapportPrescriptionPDF.generer_pdf_prescriptions_par_date(groupes, info_cabinet)

    def generer_pdf_rapport_date_precise_prescriptions(self, code_session, date_cible):
        """Génère un PDF des prescriptions pour une date de consultation précise."""
        from services.pdf_rapports.rapport_prescription import RapportPrescriptionPDF
        groupes = self.lister_groupes_par_acte(code_session) or []
        info_cabinet = self.get_cabinet_info()
        return RapportPrescriptionPDF.generer_pdf_prescriptions_date_precise(groupes, date_cible, info_cabinet)

    # --------- WORKFLOW PATIENT ---------
    def demarrer_prescription(self, code_visite: str) -> tuple:
        from service_metier.visite_service import VisiteService
        return VisiteService().demarrer_prescription(code_visite)

    def terminer_prescription(self, code_visite: str) -> tuple:
        from service_metier.visite_service import VisiteService
        return VisiteService().terminer_prescription(code_visite)
