"""
panier_fourni_service.py
-------------------------
Service métier — Gestion du panier d'approvisionnement fournisseur.

Responsabilités :
  - Validation (texte, quantité, prix, date d'expiration, codes obligatoires)
  - CRUD : ajouter, modifier, supprimer ligne
  - Récupération : par code, par facture, par session, lots par produit, recherche
  - Lookup produit : désignation et prix d'achat (via ProduitService)
  - Mise à jour prix d'achat produit
  - Stock & Expiration : ruptures, stock faible, lots à expirer, lots expirés
  - Statistiques cards : ruptures, lots expiration, valeur stock
  - Statistiques par produit : lots valides, à expirer, expirés
  - FEFO, vérification stock, historique fournisseur, comparaison entrées/sorties
  - Informations cabinet
"""

import os
import logging
import re
from typing import Dict, Optional, List, Tuple, Union
from datetime import datetime

from data.dao_panier_facture_fourni import PanierFactureFourniDAO
from models.modele_panier_fourni import PanierFactureFourni
from parametre.dao_param import CabinetDAO


class PanierFourniService:
    """
    Service métier pour la gestion du panier d'approvisionnement.
    Contient la validation, le CRUD, le stock, l'expiration, les statistiques.
    """

    # =========================================================================
    # CONSTANTES MÉTIER
    # =========================================================================

    JOURS_ALERTE_EXPIRATION = 30
    SEUIL_STOCK_FAIBLE = 10
    LIMITE_TOP_PRODUITS = 10

    def __init__(self, dao=None, cabinet_dao=None):
        self.dao = dao or PanierFactureFourniDAO()
        self.cabinetdao = cabinet_dao or CabinetDAO()
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def valider_texte(self, texte: str, nom_champ: str, min_longueur: int = 3) -> Tuple[bool, str]:
        """Valide un champ texte : non vide, longueur min, sans caractères interdits."""
        if not texte or texte.strip() == "":
            return False, f"Le champ {nom_champ} est obligatoire"
        if len(texte.strip()) < min_longueur:
            return False, f"Le {nom_champ} doit contenir au moins {min_longueur} caracteres"
        if re.search(r'[<>{}[\]\\|`~@#$%^*+=]', texte):
            return False, f"Le {nom_champ} contient des caracteres speciaux interdits"
        return True, ""

    def valider_quantite(self, quantite: int) -> Tuple[bool, str]:
        """Valide que la quantité est un entier strictement positif."""
        try:
            qte = int(quantite)
            if qte <= 0:
                return False, "La quantite doit etre superieure a 0"
            return True, ""
        except Exception:
            return False, "La quantite doit etre un nombre entier valide"

    def valider_prix(self, prix: float, nom_champ: str) -> Tuple[bool, str]:
        """Valide qu'un prix est un nombre strictement positif."""
        try:
            prix_float = float(prix)
            if prix_float <= 0:
                return False, f"Le {nom_champ} doit etre superieur a 0"
            return True, ""
        except Exception:
            return False, f"Le {nom_champ} doit etre un nombre valide"

    def valider_date_expiration(self, date_expiration: Union[str, datetime, None]) -> Tuple[bool, str]:
        """Valide que la date d'expiration est dans le futur."""
        if not date_expiration:
            return False, "La date d expiration est obligatoire"
        try:
            date_obj = None

            if isinstance(date_expiration, str):
                # Essayer le format DD/MM/YYYY (format UI)
                try:
                    date_obj = datetime.strptime(date_expiration, "%d/%m/%Y").date()
                except ValueError:
                    # Essayer le format YYYY-MM-DD (format MySQL)
                    try:
                        date_obj = datetime.strptime(date_expiration, "%Y-%m-%d").date()
                    except ValueError:
                        return False, "Format de date invalide (attendu: JJ/MM/AAAA ou AAAA-MM-JJ)"
            else:
                date_obj = date_expiration.date() if hasattr(date_expiration, "date") else date_expiration

            if date_obj <= datetime.now().date():
                return False, "La date d expiration doit etre dans le futur"

            return True, ""
        except Exception as e:
            return False, f"Format de date invalide: {str(e)}"

    def valider_codes_obligatoires(self, panier: PanierFactureFourni) -> Tuple[bool, str]:
        """Valide que les codes produit, facture et session sont renseignés."""
        if not panier.code_produit:
            return False, "Le produit est obligatoire"
        if not panier.code_facture_four:
            return False, "La facture fournisseur est obligatoire"
        if not panier.code_session:
            return False, "La session est obligatoire"
        return True, ""

    def valider_panier(self, panier: PanierFactureFourni) -> Tuple[bool, str]:
        """Regroupe toutes les validations communes à l'ajout et à la modification."""
        valide, msg = self.valider_texte(panier.designation, "designation")
        if not valide:
            return False, msg

        valide, msg = self.valider_quantite(panier.quantite_four)
        if not valide:
            return False, msg

        valide, msg = self.valider_prix(panier.prix_unitaire, "prix unitaire")
        if not valide:
            return False, msg

        valide, msg = self.valider_date_expiration(panier.date_expiration)
        if not valide:
            return False, msg

        return True, ""

    def _nettoyer_panier(self, panier: PanierFactureFourni) -> None:
        """Nettoie les champs texte et normalise les valeurs numériques."""
        panier.designation = panier.designation.strip()
        panier.quantite_four = int(panier.quantite_four)
        panier.prix_unitaire = float(panier.prix_unitaire)

        # Conversion de la date au format MySQL (YYYY-MM-DD)
        if isinstance(panier.date_expiration, str):
            try:
                # Format UI : DD/MM/YYYY → Format MySQL : YYYY-MM-DD
                date_obj = datetime.strptime(panier.date_expiration, "%d/%m/%Y")
                panier.date_expiration = date_obj.strftime("%Y-%m-%d")
            except ValueError:
                if not isinstance(panier.date_expiration, datetime):
                    try:
                        datetime.strptime(panier.date_expiration, "%Y-%m-%d")
                    except ValueError:
                        pass
        elif isinstance(panier.date_expiration, datetime):
            panier.date_expiration = panier.date_expiration.strftime("%Y-%m-%d")

    # =========================================================================
    # CRUD
    # =========================================================================

    def ajouter_ligne(self, panier: PanierFactureFourni) -> Tuple[bool, str]:
        """
        Valide et ajoute une ligne produit dans le panier.
        Le DAO recalcule automatiquement le montant_total et met à jour le stock.
        """
        valide, msg = self.valider_panier(panier)
        if not valide:
            return False, msg

        valide, msg = self.valider_codes_obligatoires(panier)
        if not valide:
            return False, msg

        self._nettoyer_panier(panier)

        if self.dao.ajouter(panier):
            self.logger.info(f"Ligne panier {panier.code_panier_four} ajoutee - produit {panier.code_produit}")
            return True, "Produit ajoute au panier avec succes"

        return False, "Erreur lors de l ajout du produit dans le panier"

    def modifier_ligne(self, panier: PanierFactureFourni) -> Tuple[bool, str]:
        """
        Valide et modifie une ligne du panier.
        Le DAO ajuste le stock (différence) et recalcule le montant_total.
        """
        if not panier.code_panier_four:
            return False, "Code ligne panier invalide"

        valide, msg = self.valider_panier(panier)
        if not valide:
            return False, msg

        self._nettoyer_panier(panier)

        if self.dao.modifier(panier):
            self.logger.info(f"Ligne panier {panier.code_panier_four} modifiee")
            return True, "Ligne panier modifiee avec succes"

        return False, "Erreur lors de la modification de la ligne panier"

    def supprimer_ligne(self, code_panier_four: str) -> Tuple[bool, str]:
        """Supprime une ligne du panier (DAO recalcule et décrémente le stock)."""
        if not code_panier_four:
            return False, "Code ligne panier invalide"

        if self.dao.supprimer(code_panier_four):
            self.logger.info(f"Ligne panier {code_panier_four} supprimee")
            return True, "Ligne supprimee du panier avec succes"

        return False, "Erreur lors de la suppression de la ligne panier"

    # =========================================================================
    # RÉCUPÉRATION
    # =========================================================================

    def obtenir_par_code(self, code_panier_four: str) -> Optional[PanierFactureFourni]:
        """Retourne une ligne panier par son code."""
        return self.dao.obtenir_par_code(code_panier_four)

    def lister_par_facture(self, code_facture_four: str) -> List[PanierFactureFourni]:
        """Retourne toutes les lignes du panier pour une facture donnée."""
        return self.dao.lister_par_facture(code_facture_four)

    def lister_par_session(self, code_session: str) -> List[PanierFactureFourni]:
        """Retourne toutes les lignes d'approvisionnement d'une session."""
        return self.dao.lister_par_session(code_session)

    def lister_lots_par_produit(self, code_produit: str, code_session: str) -> List[Dict]:
        """Retourne tous les lots d'un produit avec stock restant et statut."""
        return self.dao.lister_lots_par_produit(code_produit, code_session)

    def rechercher(self, critere: str, code_session: str) -> List[PanierFactureFourni]:
        """Recherche des lignes panier par désignation ou code produit."""
        return self.dao.rechercher_par_critere(critere, code_session)

    # =========================================================================
    # LOOKUP PRODUIT (via ProduitService — évite imports circulaires)
    # =========================================================================

    def obtenir_designation_produit(self, code_produit: str) -> str:
        """
        Retourne le libellé du produit pour auto-remplir le champ désignation.
        Pattern : Lazy Import via ProduitService pour éviter les imports circulaires.
        """
        try:
            from service_metier.produit_service import ProduitService
            return ProduitService().obtenir_libelle_par_code(code_produit) or ""
        except Exception as e:
            self.logger.error(f"Erreur obtention designation: {e}")
            return ""

    def obtenir_prix_achat_produit(self, code_produit: str) -> float:
        """
        Retourne le prix d'achat unitaire du produit pour auto-remplir le champ prix.
        Pattern : Lazy Import via ProduitService pour éviter les imports circulaires.
        """
        try:
            from service_metier.produit_service import ProduitService
            return ProduitService().obtenir_prix_achat_par_code(code_produit)
        except Exception as e:
            self.logger.error(f"Erreur obtention prix achat: {e}")
            return 0.0

    def actualiser_prix_achat_produit(self, code_produit: str, nouveau_prix: float) -> Tuple[bool, str]:
        """
        Met à jour le prix d'achat d'un produit après validation du panier.
        Pattern : Lazy Import via ProduitService pour éviter les imports circulaires.
        """
        try:
            from service_metier.produit_service import ProduitService
            return ProduitService().actualiser_prix_achat(code_produit, nouveau_prix)
        except Exception as e:
            self.logger.error(f"Erreur actualisation prix achat: {e}")
            return False, f"Erreur: {e}"

    def obtenir_valeur_lots_a_expirer(self, code_session: str, jours: int = 30) -> float:
        """Card Perte Potentielle : valeur financière des lots bientôt expirés."""
        return self.dao.valeur_lots_a_expirer(code_session, jours)

    def obtenir_top_produits_consommes(self, code_session: str, limite: int = 10) -> List[Dict]:
        """Retourne les produits les plus prescrits pour anticiper les réapprovisionnements."""
        return self.dao.top_produits_consommes(code_session, limite)

    # =========================================================================
    # STOCK & EXPIRATION
    # =========================================================================

    def obtenir_stock(self, code_produit: str, code_session: str) -> Optional[Dict]:
        """Retourne la ligne de stock global d'un produit."""
        return self.dao.get_stock(code_produit, code_session)

    def obtenir_ruptures_stock(self, code_session: str) -> List[Dict]:
        """Retourne les produits en rupture de stock."""
        return self.dao.produits_en_rupture_stock(code_session)

    def obtenir_stock_faible(self, code_session: str, seuil: int = 10) -> List[Dict]:
        """Retourne les produits avec stock sous le seuil."""
        return self.dao.produits_stock_faible(code_session, seuil)

    def obtenir_lots_a_expirer(self, code_session: str, jours: int = 30) -> List[Dict]:
        """Retourne les lots dont l'expiration est dans moins de N jours."""
        return self.dao.lots_a_expirer(code_session, jours)

    def obtenir_lots_expires(self, code_session: str) -> List[Dict]:
        """Retourne les lots dont la date d'expiration est dépassée."""
        return self.dao.lots_expires(code_session)

    # =========================================================================
    # STATISTIQUES CARDS
    # =========================================================================

    def obtenir_nombre_ruptures(self, code_session: str) -> int:
        """Card Rupture de Stock : nombre de produits à 0."""
        try:
            return self.dao.nombre_ruptures(code_session) or 0
        except Exception as e:
            self.logger.error(f"Erreur obtention nombre ruptures: {e}")
            return 0

    def obtenir_nombre_lots_a_expirer(self, code_session: str, jours: int = None) -> int:
        """Card À Expirer : nombre de lots proches de l'expiration."""
        if jours is None:
            jours = self.JOURS_ALERTE_EXPIRATION
        try:
            return self.dao.nombre_lots_a_expirer(code_session, jours) or 0
        except Exception as e:
            self.logger.error(f"Erreur obtention nombre lots a expirer: {e}")
            return 0

    def obtenir_nombre_lots_expires(self, code_session: str) -> int:
        """Card Expirés : nombre de lots dont la date est dépassée."""
        try:
            return self.dao.nombre_lots_expires(code_session) or 0
        except Exception as e:
            self.logger.error(f"Erreur obtention nombre lots expires: {e}")
            return 0

    def obtenir_valeur_stock(self, code_session: str) -> float:
        """Card Valeur Stock : valeur totale du stock en prix achat."""
        try:
            return self.dao.valeur_stock_total(code_session) or 0.0
        except Exception as e:
            self.logger.error(f"Erreur obtention valeur stock: {e}")
            return 0.0

    # =========================================================================
    # STATISTIQUES PAR PRODUIT
    # =========================================================================

    def obtenir_lots_valides_par_produit(self, code_produit: str, code_session: str) -> int:
        """Nombre de lots valides pour un produit spécifique."""
        return self.dao.nombre_lots_valides_par_produit(code_produit, code_session)

    def obtenir_lots_a_expirer_par_produit(self, code_produit: str, code_session: str, jours: int = 30) -> int:
        """Nombre de lots bientôt en expiration pour un produit spécifique."""
        return self.dao.nombre_lots_a_expirer_par_produit(code_produit, code_session, jours)

    def obtenir_lots_expires_par_produit(self, code_produit: str, code_session: str) -> int:
        """Nombre de lots expirés pour un produit spécifique."""
        return self.dao.nombre_lots_expires_par_produit(code_produit, code_session)

    # =========================================================================
    # FEFO
    # =========================================================================

    def obtenir_date_fefo(self, code_produit: str, code_session: str, quantite: int) -> Optional[datetime]:
        """Retourne la date d'expiration du lot prioritaire (FEFO)."""
        return self.dao.get_date_expiration_fefo(code_produit, code_session, quantite)

    def verifier_stock_avant_prescription(self, code_produit: str, code_session: str, quantite: int) -> Tuple[bool, str]:
        """Vérifie si le stock est suffisant avant une prescription."""
        return self.dao.verifier_stock_suffisant(code_produit, code_session, quantite)

    def obtenir_historique_fournisseur(self, code_fournisseur: str, code_session: str) -> List[Dict]:
        """Retourne l'historique complet des approvisionnements d'un fournisseur."""
        return self.dao.historique_approvisionnements_par_fournisseur(code_fournisseur, code_session)

    def obtenir_comparaison_entrees_sorties(self, code_session: str) -> Dict[str, Dict[str, int]]:
        """Compare les quantités entrées et sorties par mois."""
        return self.dao.comparaison_entrees_sorties_par_mois(code_session)

    def obtenir_quantites_par_statut_expiration(self, code_session: str) -> Dict[str, int]:
        """Retourne les quantités par statut d'expiration pour les statistiques."""
        return self.dao.obtenir_quantites_par_statut(code_session)

    def obtenir_quantites_par_type_produit(self, code_session: str) -> Dict[str, int]:
        """Retourne les quantités par type de produit pour les statistiques."""
        return self.dao.obtenir_quantites_par_type(code_session)

    def obtenir_stock_detaille(self, code_session: str, limite: int = 20) -> List[Dict]:
        """Retourne le stock détaillé par produit pour les statistiques."""
        return self.dao.obtenir_stock_detaille_par_produit(code_session, limite)

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
