import sys
import os
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.modele_panier_fourni import PanierFactureFourni
from service_metier.panier_fourni_service import PanierFourniService


class PanierFactureFourniControleur:
    """
    Controleur MVC pour la gestion du panier d approvisionnement.
    Fait le lien entre la vue et le service.
    Orchestre les appels sans contenir de logique metier.
    """

    def __init__(self):
        self.service = PanierFourniService()
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # DELEGATION AU SERVICE (pas de logique metier ici)
    # =========================================================================

    # =========================================================================
    # METHODES CRUD
    # =========================================================================

    def ajouter_ligne(self, panier: PanierFactureFourni) -> Tuple[bool, str]:
        """Delegue l ajout au service."""
        return self.service.ajouter_ligne(panier)

    def modifier_ligne(self, panier: PanierFactureFourni) -> Tuple[bool, str]:
        """Delegue la modification au service."""
        return self.service.modifier_ligne(panier)

    def supprimer_ligne(self, code_panier_four: str) -> Tuple[bool, str]:
        """Delegue la suppression au service."""
        return self.service.supprimer_ligne(code_panier_four)

    # =========================================================================
    # METHODES DE RECUPERATION
    # =========================================================================

    def obtenir_par_code(self, code_panier_four: str) -> Optional[PanierFactureFourni]:
        """Retourne une ligne panier par son code."""
        return self.service.obtenir_par_code(code_panier_four)

    def lister_par_facture(self, code_facture_four: str) -> List[PanierFactureFourni]:
        """Retourne toutes les lignes du panier pour une facture donnee."""
        return self.service.lister_par_facture(code_facture_four)

    def lister_par_session(self, code_session: str) -> List[PanierFactureFourni]:
        """Retourne toutes les lignes d approvisionnement d une session."""
        return self.service.lister_par_session(code_session)

    def lister_lots_par_produit(self, code_produit: str, code_session: str) -> List[Dict]:
        """Retourne tous les lots d un produit avec stock restant et statut."""
        return self.service.lister_lots_par_produit(code_produit, code_session)

    def rechercher(self, critere: str, code_session: str) -> List[PanierFactureFourni]:
        """Recherche des lignes panier par designation ou code produit."""
        return self.service.rechercher(critere, code_session)
    
    def obtenir_designation_produit(self, code_produit: str) -> str:
        """Retourne le libelle du produit."""
        return self.service.obtenir_designation_produit(code_produit)
    
    def obtenir_prix_achat_produit(self, code_produit: str) -> float:
        """Retourne le prix d'achat unitaire du produit."""
        return self.service.obtenir_prix_achat_produit(code_produit)
    
    def actualiser_prix_achat_produit(self, code_produit: str, nouveau_prix: float) -> Tuple[bool, str]:
        """Met a jour le prix d'achat d'un produit."""
        return self.service.actualiser_prix_achat_produit(code_produit, nouveau_prix)
    
    def obtenir_valeur_lots_a_expirer(self, code_session: str, jours: int = 30) -> float:
        """Card Perte Potentielle : valeur financiere des lots bientot expires."""
        return self.service.obtenir_valeur_lots_a_expirer(code_session, jours)

    def obtenir_top_produits_consommes(self, code_session: str, limite: int = 10) -> List[Dict]:
        """Retourne les produits les plus prescrits pour anticiper les reapprovisionnements."""
        return self.service.obtenir_top_produits_consommes(code_session, limite)

    # =========================================================================
    # METHODES STOCK & EXPIRATION
    # =========================================================================

    def obtenir_stock(self, code_produit: str, code_session: str) -> Optional[Dict]:
        """Retourne la ligne de stock global d un produit."""
        return self.service.obtenir_stock(code_produit, code_session)

    def obtenir_ruptures_stock(self, code_session: str) -> List[Dict]:
        """Retourne les produits en rupture de stock."""
        return self.service.obtenir_ruptures_stock(code_session)

    def obtenir_stock_faible(self, code_session: str, seuil: int = 10) -> List[Dict]:
        """Retourne les produits avec stock sous le seuil."""
        return self.service.obtenir_stock_faible(code_session, seuil)

    def obtenir_lots_a_expirer(self, code_session: str, jours: int = 30) -> List[Dict]:
        """Retourne les lots dont l expiration est dans moins de jours."""
        return self.service.obtenir_lots_a_expirer(code_session, jours)

    def obtenir_lots_expires(self, code_session: str) -> List[Dict]:
        """Retourne les lots dont la date d expiration est depassee."""
        return self.service.obtenir_lots_expires(code_session)

    # =========================================================================
    # METHODES STATISTIQUES CARDS
    # =========================================================================

    def obtenir_nombre_ruptures(self, code_session: str) -> int:
        """Card Rupture de Stock : nombre de produits a 0."""
        return self.service.obtenir_nombre_ruptures(code_session)

    def obtenir_nombre_lots_a_expirer(self, code_session: str, jours: int = None) -> int:
        """Card A Expirer : nombre de lots proches de l expiration."""
        return self.service.obtenir_nombre_lots_a_expirer(code_session, jours)

    def obtenir_nombre_lots_expires(self, code_session: str) -> int:
        """Card Expires : nombre de lots dont la date est depassee."""
        return self.service.obtenir_nombre_lots_expires(code_session)

    def obtenir_valeur_stock(self, code_session: str) -> float:
        """Card Valeur Stock : valeur totale du stock en prix achat."""
        return self.service.obtenir_valeur_stock(code_session)

    # =========================================================================
    # METHODES STATISTIQUES PAR PRODUIT
    # =========================================================================

    def obtenir_lots_valides_par_produit(self, code_produit: str, code_session: str) -> int:
        """Nombre de lots valides (expiration loin) pour un produit specifique."""
        return self.service.obtenir_lots_valides_par_produit(code_produit, code_session)

    def obtenir_lots_a_expirer_par_produit(self, code_produit: str, code_session: str, jours: int = 30) -> int:
        """Nombre de lots bientot en expiration pour un produit specifique."""
        return self.service.obtenir_lots_a_expirer_par_produit(code_produit, code_session, jours)

    def obtenir_lots_expires_par_produit(self, code_produit: str, code_session: str) -> int:
        """Nombre de lots expires pour un produit specifique."""
        return self.service.obtenir_lots_expires_par_produit(code_produit, code_session)

    # =========================================================================
    # METHODE FEFO
    # =========================================================================

    def obtenir_date_fefo(self, code_produit: str, code_session: str, quantite: int) -> Optional[datetime]:
        """Retourne la date d expiration du lot prioritaire (FEFO)."""
        return self.service.obtenir_date_fefo(code_produit, code_session, quantite)
    
    
    def verifier_stock_avant_prescription(self, code_produit: str, code_session: str, quantite: int) -> Tuple[bool, str]:
        """Verifie si le stock est suffisant avant une prescription."""
        return self.service.verifier_stock_avant_prescription(code_produit, code_session, quantite)

    def obtenir_historique_fournisseur(self, code_fournisseur: str, code_session: str) -> List[Dict]:
        """Retourne l historique complet des approvisionnements d un fournisseur."""
        return self.service.obtenir_historique_fournisseur(code_fournisseur, code_session)

    def obtenir_comparaison_entrees_sorties(self, code_session: str) -> Dict[str, Dict[str, int]]:
        """Compare les quantites entrees et sorties par mois."""
        return self.service.obtenir_comparaison_entrees_sorties(code_session)
    
    def obtenir_quantites_par_statut_expiration(self, code_session: str) -> Dict[str, int]:
        """Retourne les quantités par statut d'expiration pour les statistiques."""
        return self.service.obtenir_quantites_par_statut_expiration(code_session)
    
    def obtenir_quantites_par_type_produit(self, code_session: str) -> Dict[str, int]:
        """Retourne les quantités par type de produit pour les statistiques."""
        return self.service.obtenir_quantites_par_type_produit(code_session)
    
    def obtenir_stock_detaille(self, code_session: str, limite: int = 20) -> List[Dict]:
        """Retourne le stock détaillé par produit pour les statistiques."""
        return self.service.obtenir_stock_detaille(code_session, limite)

    # =========================================================================
    # METHODES DE VALIDATION
    # =========================================================================

    def valider_quantite(self, quantite) -> Tuple[bool, str]:
        """Valide que la quantite est un entier strictement positif."""
        try:
            qte = int(quantite)
            if qte <= 0:
                return False, "La quantite doit etre superieure a 0"
            return True, ""
        except Exception:
            return False, "La quantite doit etre un nombre entier valide"

    def valider_prix(self, prix, champ_nom: str = "prix") -> Tuple[bool, str]:
        """Valide que le prix est un nombre strictement positif."""
        try:
            prix_float = float(prix)
            if prix_float <= 0:
                return False, f"Le {champ_nom} doit etre superieur a 0"
            return True, ""
        except Exception:
            return False, f"Le {champ_nom} doit etre un nombre valide"

    def valider_date_expiration(self, date_str: str) -> Tuple[bool, str]:
        """Valide le format de la date d'expiration."""
        if not date_str or date_str.strip() == "":
            return False, "La date d'expiration est obligatoire"
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True, ""
        except Exception:
            return False, "Format de date invalide (YYYY-MM-DD attendu)"

    # =========================================================================
    # INFORMATIONS CABINET
    # =========================================================================

    def get_cabinet_info(self) -> Dict[str, Optional[str]]:
        """Recupere les informations du cabinet medical."""
        return self.service.get_cabinet_info()