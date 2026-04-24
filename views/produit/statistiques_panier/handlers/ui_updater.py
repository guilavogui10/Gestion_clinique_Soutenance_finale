"""
Handler UIUpdater - Mise à jour de l'interface utilisateur.
Responsabilité : Mettre à jour les composants UI avec les données du DTO.
Pattern : Service Layer, Separation of Concerns.
"""

import logging
from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from .statistiques_loader import StatistiquesDTO

from ..utils.formatters import Formatters


class UIUpdater:
    """
    Handler pour la mise à jour de l'interface utilisateur.
    
    Responsabilités :
    - Mettre à jour les cards d'expiration
    - Mettre à jour les cards par type (StatCard)
    - Mettre à jour la liste de stock détaillé
    
    Pattern : Service Layer pour séparer la logique de mise à jour de l'UI.
    """
    
    def __init__(self):
        """Initialise le handler UI."""
        self.logger = logging.getLogger(__name__)
    
    def mettre_a_jour_cards_expiration(self, dto: 'StatistiquesDTO', cards: Dict[str, Any]) -> None:
        """
        Met à jour les 4 cards d'expiration.
        
        Args:
            dto: StatistiquesDTO contenant les données
            cards: Dictionnaire avec les clés 'expires', 'bientot', 'valides', 'valeur'
        """
        self.logger.debug("[UIUpdater] Mise à jour cards expiration")
        
        try:
            # Card Produits Expirés
            cards['expires'].update_value(str(dto.nb_expires))
            
            # Card Bientôt Expirés
            cards['bientot'].update_value(str(dto.nb_bientot_expires))
            
            # Card Produits Valides
            cards['valides'].update_value(str(dto.nb_valides))
            
            # Card Valeur Stock Global
            valeur_formatee = Formatters.formater_montant(dto.valeur_stock_total)
            cards['valeur'].update_value(valeur_formatee)
            
            self.logger.debug("[UIUpdater] Cards expiration mises à jour")
            
        except Exception as e:
            self.logger.error(f"[UIUpdater] Erreur mise à jour cards expiration: {e}")
            raise
    
    def mettre_a_jour_cards_type(self, dto: 'StatistiquesDTO', cards: Dict[str, Any]) -> None:
        """
        Met à jour les 3 cards par type de produit (StatCard).
        
        Args:
            dto: StatistiquesDTO contenant les données
            cards: Dictionnaire avec les clés 'liquide', 'pommade', 'comprime'
        """
        self.logger.debug("[UIUpdater] Mise à jour cards type")
        
        try:
            # Card Liquide - Afficher seulement la quantité
            cards['liquide'].update_value(str(dto.stock_liquide))
            
            # Card Pommade - Afficher seulement la quantité
            cards['pommade'].update_value(str(dto.stock_pommade))
            
            # Card Comprimé - Afficher seulement la quantité
            cards['comprime'].update_value(str(dto.stock_comprime))
            
            self.logger.debug("[UIUpdater] Cards type mises à jour")
            
        except Exception as e:
            self.logger.error(f"[UIUpdater] Erreur mise à jour cards type: {e}")
            raise
    
    def mettre_a_jour_stock_detaille(self, dto: 'StatistiquesDTO', card_detail: Any) -> None:
        """
        Met à jour la card de stock détaillé.
        
        Args:
            dto: StatistiquesDTO contenant les données
            card_detail: Instance de StockDetailCard
        """
        self.logger.debug("[UIUpdater] Mise à jour stock détaillé")
        
        try:
            # Charger les produits dans la card
            card_detail.charger_produits(dto.stock_detaille)
            
            self.logger.debug(
                f"[UIUpdater] Stock détaillé mis à jour: {len(dto.stock_detaille)} produits"
            )
            
        except Exception as e:
            self.logger.error(f"[UIUpdater] Erreur mise à jour stock détaillé: {e}")
            raise
    
    def afficher_donnees_vides(self, cards_expiration: Dict[str, Any], cards_type: Dict[str, Any], card_detail: Any) -> None:
        """
        Affiche des valeurs vides/zéro dans tous les composants.
        Utilisé lors de la réinitialisation ou en cas d'erreur.
        
        Args:
            cards_expiration: Dictionnaire des cards d'expiration
            cards_type: Dictionnaire des cards par type
            card_detail: Card de stock détaillé
        """
        self.logger.debug("[UIUpdater] Affichage données vides")
        
        try:
            # Cards expiration
            cards_expiration['expires'].update_value("0")
            cards_expiration['bientot'].update_value("0")
            cards_expiration['valides'].update_value("0")
            cards_expiration['valeur'].update_value("0 GNF")
            
            # Cards type - Afficher seulement les quantités
            cards_type['liquide'].update_value("0")
            cards_type['pommade'].update_value("0")
            cards_type['comprime'].update_value("0")
            
            # Stock détaillé
            if card_detail:
                card_detail.vider()
            
            self.logger.debug("[UIUpdater] Données vides affichées")
            
        except Exception as e:
            self.logger.error(f"[UIUpdater] Erreur affichage données vides: {e}")
            raise
