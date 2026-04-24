"""
prescription_service.py
------------------------
Service métier — Gestion des prescriptions (service pharmacie).

Responsabilités :
  - Validation et nettoyage des données saisies
  - Orchestration entre PrescriptionProduitDAO et PanierFactureFourniDAO
  - Vérification stock AVANT chaque prescription (via stock_dao)
  - date_expiration JAMAIS validée ni saisie → auto-remplie par FEFO dans le DAO
  - Mise à disposition des données (cards, tableau, panier)
  - Pont vers facture_patient via get_montant_pharmacie_par_visite()

Pattern :
  self.dao       = PrescriptionProduitDAO   (prescriptions)
  self.stock_dao = PanierFactureFourniDAO   (stock, cards expiration, types)

Note : statut_facture retiré — le paiement est atomique sur facture_patient,
       pas ligne par ligne.
"""

import os
import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from data.dao_panier_prescription_produit import PrescriptionProduitDAO
from data.dao_panier_facture_fourni import PanierFactureFourniDAO
from models.modele_panier_prescription_produit import PanierPrescriptionProduit
from parametre.dao_param import CabinetDAO


class PrescriptionService:
    """
    Service métier pour la gestion des prescriptions produits.

    Règles métier clés :
      1. Vérifier le stock AVANT d'ajouter (verifier_stock_avant_prescription)
      2. Ne JAMAIS valider ni demander date_expiration → FEFO automatique
      3. designation et prix_applique sont auto-complétés par le DAO si absents
      4. À la validation finale → statut_patient passe à 'Attente payement'
      5. Pas de gestion de statut_facture — appartient à facture_patient
    """

    # =========================================================================
    # CONSTANTES MÉTIER
    # =========================================================================

    JOURS_ALERTE_EXPIRATION = 30
    SEUIL_STOCK_FAIBLE = 10
    LIMITE_TOP_PRODUITS = 10

    def __init__(self, dao=None, stock_dao=None, cabinet_dao=None):
        self.dao = dao or PrescriptionProduitDAO()
        self.stock_dao = stock_dao or PanierFactureFourniDAO()
        self.cabinetdao = cabinet_dao or CabinetDAO()
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def valider_texte(self, texte: str, nom_champ: str,
                      min_longueur: int = 2) -> Tuple[bool, str]:
        """Valide un champ texte : non vide, longueur min, sans caractères interdits."""
        if not texte or texte.strip() == "":
            return False, f"Le champ '{nom_champ}' est obligatoire."
        if len(texte.strip()) < min_longueur:
            return False, f"'{nom_champ}' doit contenir au moins {min_longueur} caractères."
        if re.search(r'[<>{}[\]\\|`~@#$%^*+=]', texte):
            return False, f"'{nom_champ}' contient des caractères spéciaux interdits."
        return True, ""

    def valider_quantite(self, quantite) -> Tuple[bool, str]:
        """Valide que la quantité est un entier strictement positif."""
        try:
            if int(quantite) <= 0:
                return False, "La quantité doit être supérieure à 0."
            return True, ""
        except (ValueError, TypeError):
            return False, "La quantité doit être un nombre entier valide."

    def valider_prix(self, prix, nom_champ: str = "prix") -> Tuple[bool, str]:
        """Valide qu'un prix est un nombre strictement positif."""
        try:
            if float(prix) <= 0:
                return False, f"Le {nom_champ} doit être supérieur à 0."
            return True, ""
        except (ValueError, TypeError):
            return False, f"Le {nom_champ} doit être un nombre valide."

    def valider_codes_obligatoires(self, prescription: PanierPrescriptionProduit) -> Tuple[bool, str]:
        """Valide que tous les codes FK sont renseignés."""
        if not prescription.code_produit:
            return False, "Le produit est obligatoire."
        if not prescription.code_visite:
            return False, "La visite est obligatoire."
        if not prescription.code_consultation:
            return False, "La consultation est obligatoire."
        if not prescription.code_session:
            return False, "La session est obligatoire."
        return True, ""

    def valider_prescription(self, prescription: PanierPrescriptionProduit) -> Tuple[bool, str]:
        """
        Validation complète avant ajout ou modification.
        Ne valide PAS date_expiration (FEFO auto).
        Ne valide PAS designation/prix (auto-complétés par le DAO).
        """
        valide, msg = self.valider_codes_obligatoires(prescription)
        if not valide:
            return False, msg

        valide, msg = self.valider_quantite(prescription.quantite_prescript)
        if not valide:
            return False, msg

        # Prix validé seulement si fourni manuellement
        if prescription.prix_applique and prescription.prix_applique != 0:
            valide, msg = self.valider_prix(prescription.prix_applique, "prix appliqué")
            if not valide:
                return False, msg

        return True, ""

    def _nettoyer_prescription(self, prescription: PanierPrescriptionProduit) -> None:
        """Normalise les valeurs numériques et nettoie les champs texte."""
        if prescription.designation:
            prescription.designation = prescription.designation.strip()
        prescription.quantite_prescript = int(prescription.quantite_prescript)
        if prescription.prix_applique:
            prescription.prix_applique = float(prescription.prix_applique)

    # =========================================================================
    # CRUD
    # =========================================================================

    def ajouter_ligne(self, prescription: PanierPrescriptionProduit) -> Tuple[bool, str]:
        """
        Valide, vérifie le stock, puis ajoute une ligne de prescription.

        Flux en 4 étapes :
          1. Validation des données
          2. Vérification stock suffisant (table stocks)
          3. Nettoyage
          4. DAO → FEFO auto + insertion
        """
        # 1. Validation
        valide, msg = self.valider_prescription(prescription)
        if not valide:
            return False, msg

        # 2. Vérification stock AVANT le DAO
        stock_ok, info_stock = self.stock_dao.verifier_stock_suffisant(
            prescription.code_produit,
            prescription.code_session,
            prescription.quantite_prescript
        )
        if not stock_ok:
            return False, info_stock

        # 3. Nettoyage
        self._nettoyer_prescription(prescription)

        # 4. Ajout via DAO
        if self.dao.ajouter(prescription):
            self.logger.info(
                f"Prescription ajoutée — produit: {prescription.code_produit} "
                f"| consultation: {prescription.code_consultation} "
                f"| qté: {prescription.quantite_prescript}"
            )
            return True, "Produit prescrit avec succès."

        return False, "Erreur lors de l'enregistrement de la prescription."

    def modifier_ligne(self, prescription: PanierPrescriptionProduit) -> Tuple[bool, str]:
        """Valide et modifie une ligne de prescription existante."""
        if not prescription.code_prescription:
            return False, "Code prescription invalide."

        valide, msg = self.valider_prescription(prescription)
        if not valide:
            return False, msg

        self._nettoyer_prescription(prescription)

        if self.dao.modifier(prescription):
            self.logger.info(f"Prescription {prescription.code_prescription} modifiée.")
            return True, "Prescription modifiée avec succès."

        return False, "Erreur lors de la modification de la prescription."

    def supprimer_ligne(self, code_prescription: str) -> Tuple[bool, str]:
        """Supprime une ligne de prescription."""
        if not code_prescription or code_prescription.strip() == "":
            return False, "Code prescription invalide."

        if self.dao.supprimer(code_prescription):
            self.logger.info(f"Prescription {code_prescription} supprimée.")
            return True, "Prescription supprimée avec succès."

        return False, "Erreur lors de la suppression de la prescription."

    def valider_prescription_visite(self, code_visite: str, code_consultation: str) -> Tuple[bool, str]:
        """
        Valide la prescription d'une visite.
        Met le statut_patient à 'Attente payement'.
        """
        if not code_visite:
            return False, "Code visite invalide."
        if not code_consultation:
            return False, "Code consultation invalide."

        # Sécurité : vérifier qu'il existe au moins une ligne
        try:
            nb_lignes = self.dao.nombre_lignes_consultation(code_consultation)
        except Exception:
            nb_lignes = 0

        if nb_lignes <= 0:
            return False, "La prescription est vide."

        if self.dao.valider_prescription_visite(code_visite, code_consultation):
            self.logger.info(f"Prescription validée — visite {code_visite} vers paiement.")
            return True, "Prescription validée — patient orienté vers le paiement."

        return False, "Erreur lors de la validation de la prescription."

    # =========================================================================
    # RÉCUPÉRATION
    # =========================================================================

    def obtenir_par_code(self, code_prescription: str) -> Optional[PanierPrescriptionProduit]:
        """Retourne un objet PanierPrescriptionProduit ou None."""
        return self.dao.obtenir_par_code(code_prescription)

    def lister_par_consultation(self, code_consultation: str) -> List[PanierPrescriptionProduit]:
        """Retourne les lignes du panier prescription d'une consultation."""
        return self.dao.obtenir_par_consultation(code_consultation)

    def lister_par_session(self, code_session: str) -> List[PanierPrescriptionProduit]:
        """Toutes les prescriptions de la session (tableau principal)."""
        return self.dao.lister_par_session(code_session)

    def lister_groupes_par_consultation(self, code_session: str) -> List[Dict]:
        """Liste regroupée : 1 ligne par consultation."""
        return self.dao.lister_groupes_par_consultation(code_session)

    def lister_par_visite(self, code_visite: str) -> List[PanierPrescriptionProduit]:
        """Toutes les prescriptions liées à une visite."""
        return self.dao.lister_par_visite(code_visite)

    def rechercher(self, critere: str, code_session: str) -> List[PanierPrescriptionProduit]:
        """Recherche sur code, désignation, nom/prénom patient."""
        if not critere or len(critere.strip()) < 2:
            return []
        return self.dao.rechercher_par_critere(critere.strip(), code_session)

    def obtenir_prescription_complete(self, code_prescription: str) -> Optional[Dict]:
        """Retourne un dict complet avec infos patient + produit."""
        return self.dao.prescription_complete(code_prescription)

    # =========================================================================
    # PATIENTS
    # =========================================================================

    def obtenir_patients_en_attente(self, code_session: str) -> List[Dict]:
        """Retourne les patients avec statut 'Attente pharmacie' sans prescription."""
        return self.dao.patients_en_attente_prescription(code_session)

    def obtenir_historique_patient(self, code_patient: str) -> List[Dict]:
        """Historique complet des prescriptions d'un patient."""
        return self.dao.historique_patient(code_patient)

    # =========================================================================
    # PRODUITS (pour peupler les combos de la vue)
    # =========================================================================

    def lister_produits(self) -> List[Dict]:
        """Retourne tous les produits actifs pour peupler combo_produit."""
        return self.dao.lister_produits()

    def obtenir_infos_produit(self, code_produit: str) -> Tuple[str, float]:
        """
        Retourne (designation, prix_vente_unitaire) d'un produit.
        Lazy Import via ProduitService pour éviter les imports circulaires.
        """
        try:
            from service_metier.produit_service import ProduitService
            ctrl = ProduitService()
            designation = ctrl.obtenir_libelle_par_code(code_produit) or ""
            prix = ctrl.obtenir_prix_vente_par_code(code_produit) or 0.0
            return designation, float(prix)
        except Exception as e:
            self.logger.error(f"Erreur obtenir_infos_produit ({code_produit}): {e}")
            return "", 0.0

    # =========================================================================
    # CALCULS PAR CONSULTATION
    # =========================================================================

    def obtenir_montant_total_consultation(self, code_consultation: str) -> float:
        """Total du panier prescription en cours."""
        try:
            return self.dao.montant_total_consultation(code_consultation) or 0.0
        except Exception as e:
            self.logger.error(f"Erreur montant_total_consultation: {e}")
            return 0.0

    def obtenir_nombre_lignes_consultation(self, code_consultation: str) -> int:
        """Nombre de produits dans le panier en cours."""
        try:
            return self.dao.nombre_lignes_consultation(code_consultation) or 0
        except Exception as e:
            self.logger.error(f"Erreur nombre_lignes_consultation: {e}")
            return 0

    # =========================================================================
    # PONT VERS FACTURE PATIENT
    # =========================================================================

    def get_montant_pharmacie_par_visite(self, code_visite: str) -> float:
        """
        Agrège TOUTES les lignes d'une visite en UN seul montant pharmacie.
        Injecté comme ligne 'Pharmacie' dans facture_patient.
        """
        if not code_visite:
            return 0.0
        try:
            return self.dao.get_montant_pharmacie_par_visite(code_visite) or 0.0
        except Exception as e:
            self.logger.error(f"Erreur get_montant_pharmacie_par_visite: {e}")
            return 0.0

    def get_detail_lignes_par_visite(self, code_visite: str) -> List[Dict]:
        """Retourne le détail des lignes pour affichage dans la facture patient."""
        if not code_visite:
            return []
        try:
            return self.dao.get_detail_lignes_par_visite(code_visite)
        except Exception as e:
            self.logger.error(f"Erreur get_detail_lignes_par_visite: {e}")
            return []

    # =========================================================================
    # CARDS STATISTIQUES
    # =========================================================================

    def obtenir_nombre_prescriptions_aujourd_hui(self, code_session: str) -> int:
        """Card 'Prescriptions du Jour'."""
        try:
            return self.dao.nombre_prescriptions_aujourd_hui(code_session) or 0
        except Exception as e:
            self.logger.error(f"Erreur nb_prescriptions_aujourd_hui: {e}")
            return 0

    def obtenir_nombre_total_session(self, code_session: str) -> int:
        """Card 'Total Session'."""
        try:
            return self.dao.nombre_total_par_session(code_session) or 0
        except Exception as e:
            self.logger.error(f"Erreur nb_total_session: {e}")
            return 0

    def obtenir_nombre_en_attente(self, code_session: str) -> int:
        """Card 'En Attente'."""
        try:
            return self.dao.nombre_prescriptions_en_attente(code_session) or 0
        except Exception as e:
            self.logger.error(f"Erreur nb_en_attente: {e}")
            return 0

    def obtenir_montant_total_session(self, code_session: str) -> float:
        """Card 'Chiffre d'Affaire Session'."""
        try:
            return self.dao.montant_total_session(code_session) or 0.0
        except Exception as e:
            self.logger.error(f"Erreur montant_total_session: {e}")
            return 0.0

    # =========================================================================
    # CARDS STOCK (depuis PanierFactureFourniDAO)
    # =========================================================================

    def obtenir_quantites_par_statut_expiration(self, code_session: str) -> Dict[str, int]:
        """Cards expiration : Expiré / Bientôt / Valide."""
        try:
            return self.stock_dao.obtenir_quantites_par_statut(code_session)
        except Exception as e:
            self.logger.error(f"Erreur quantites_par_statut: {e}")
            return {'qte_expire': 0, 'qte_bientot': 0, 'qte_valide': 0}

    def obtenir_quantites_par_type_produit(self, code_session: str) -> Dict[str, int]:
        """DonutCards : Stock Liquide / Pommade / Comprimé."""
        try:
            return self.stock_dao.obtenir_quantites_par_type(code_session)
        except Exception as e:
            self.logger.error(f"Erreur quantites_par_type: {e}")
            return {'Liquide': 0, 'Pommade': 0, 'Comprimé': 0}

    def obtenir_stock_detaille(self, code_session: str, limite: int = 20) -> List[Dict]:
        """Card libellé (liste scrollable) : stock par produit."""
        try:
            return self.stock_dao.obtenir_stock_detaille_par_produit(code_session, limite)
        except Exception as e:
            self.logger.error(f"Erreur stock_detaille: {e}")
            return []

    # =========================================================================
    # GRAPHES & STATISTIQUES AVANCÉES
    # =========================================================================

    def obtenir_prescriptions_par_mois(self, code_session: str) -> Dict[str, int]:
        """Graphique barres : nombre de prescriptions par mois."""
        return self.dao.nombre_par_mois(code_session)

    def obtenir_revenu_total(self, code_session: str,
                              date_debut: str = None,
                              date_fin: str = None) -> float:
        """Chiffre d'affaire pharmacie avec filtre date optionnel."""
        return self.dao.revenu_total(code_session, date_debut, date_fin)

    def obtenir_top_designations(self, code_session: str, limite: int = 10) -> List[Dict]:
        """Top N désignations les plus fréquentes (graphique camembert)."""
        return self.dao.top_designations(code_session, limite)

    def obtenir_prescriptions_par_produit(self, code_session: str) -> List[Dict]:
        """Agrégation par produit : nb, quantité totale, montant."""
        return self.dao.prescriptions_par_produit(code_session)

    def obtenir_top_produits_prescrits(self, code_session: str, limite: int = None) -> List[Dict]:
        """Top N produits par quantité prescrite."""
        if limite is None:
            limite = self.LIMITE_TOP_PRODUITS
        return self.dao.top_produits_prescrits(code_session, limite)

    def obtenir_comparaison_entrees_sorties(self, code_session: str) -> Dict[str, Dict[str, int]]:
        """Compare entrées / sorties par mois."""
        return self.stock_dao.comparaison_entrees_sorties_par_mois(code_session)

    def obtenir_top_produits_consommes(self, code_session: str, limite: int = None) -> List[Dict]:
        """Top produits consommés avec stock restant."""
        if limite is None:
            limite = self.LIMITE_TOP_PRODUITS
        return self.stock_dao.top_produits_consommes(code_session, limite)

    # =========================================================================
    # VÉRIFICATION STOCK
    # =========================================================================

    def verifier_stock_avant_prescription(self, code_produit: str,
                                           code_session: str,
                                           quantite: int) -> Tuple[bool, str]:
        """Vérifie le stock GLOBAL avant ajouter_ligne()."""
        valide, msg = self.valider_quantite(quantite)
        if not valide:
            return False, msg
        return self.stock_dao.verifier_stock_suffisant(
            code_produit, code_session, quantite
        )

    def obtenir_date_fefo(self, code_produit: str,
                           code_session: str,
                           quantite: int) -> Optional[datetime]:
        """Retourne la date FEFO pour affichage informatif dans la vue."""
        return self.dao.get_date_expiration_fefo(
            code_produit, code_session, quantite
        )

    # =========================================================================
    # INFORMATIONS CABINET
    # =========================================================================

    def get_cabinet_info(self) -> Dict[str, Optional[str]]:
        """Informations du cabinet pour l'en-tête des ordonnances."""
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
