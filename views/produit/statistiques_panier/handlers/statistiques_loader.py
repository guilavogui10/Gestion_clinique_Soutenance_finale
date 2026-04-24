"""
Handler pour le chargement des statistiques du stock.
Responsabilité : Récupération et transformation des données statistiques.
Pattern : Service Layer + Data Transfer Object (DTO).

Architecture :
    - Séparation stricte entre logique métier et présentation
    - Gestion centralisée des erreurs
    - Logging pour traçabilité
    - Type hints pour maintenabilité
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class StatistiquesDTO:
    """
    Data Transfer Object pour les statistiques.
    Encapsule les données pour éviter le couplage direct avec le contrôleur.
    """
    
    def __init__(self):
        # Statistiques d'expiration
        self.nb_expires: int = 0
        self.nb_bientot_expires: int = 0
        self.nb_valides: int = 0
        self.valeur_stock_total: float = 0.0
        
        # Statistiques par type
        self.stock_liquide: int = 0
        self.stock_pommade: int = 0
        self.stock_comprime: int = 0
        
        # Pourcentages pour les donuts
        self.pct_liquide: int = 0
        self.pct_pommade: int = 0
        self.pct_comprime: int = 0
        
        # Stock détaillé par libellé
        self.stock_detaille: List[Dict] = []
    
    def calculer_pourcentages(self):
        """Calcule les pourcentages pour les graphes donut."""
        total = self.stock_liquide + self.stock_pommade + self.stock_comprime
        
        if total > 0:
            self.pct_liquide = int((self.stock_liquide / total) * 100)
            self.pct_pommade = int((self.stock_pommade / total) * 100)
            self.pct_comprime = int((self.stock_comprime / total) * 100)
        else:
            self.pct_liquide = self.pct_pommade = self.pct_comprime = 0


class StatistiquesDataLoader:
    """
    Handler pour le chargement des statistiques du stock.
    Responsabilité unique : Récupérer et transformer les données.
    """
    
    # Constantes métier
    JOURS_ALERTE_EXPIRATION = 30
    SEUIL_STOCK_FAIBLE = 10
    
    # Mapping des types de produits
    TYPE_LIQUIDE = "Liquide"
    TYPE_POMMADE = "Pommade"
    TYPE_COMPRIME = "Comprimé"
    
    # Couleurs par type — dynamiques via theme_manager
    @staticmethod
    def _couleurs_type():
        from views.shared.theme_manager import theme_manager
        c = theme_manager.colors()
        return {
            StatistiquesDataLoader.TYPE_LIQUIDE:  c['info'],
            StatistiquesDataLoader.TYPE_POMMADE:  c['accent'],
            StatistiquesDataLoader.TYPE_COMPRIME: c['warning'],
        }
    
    def __init__(self, panier_ctrl):
        """
        Initialise le loader avec le contrôleur.
        
        Args:
            panier_ctrl: Instance de PanierFactureFourniControleur
        """
        self.panier_ctrl = panier_ctrl
        self.logger = logging.getLogger(__name__)
        self.logger.info("[StatistiquesLoader] Initialisation")
    
    def charger_statistiques_completes(self, code_session: str) -> Tuple[bool, Optional[StatistiquesDTO], str]:
        """
        Charge toutes les statistiques en une seule opération.
        Pattern : Facade pour simplifier l'interface.
        
        Args:
            code_session: Code de la session active
        
        Returns:
            tuple: (succès, dto_statistiques, message_erreur)
        """
        self.logger.info(f"[StatistiquesLoader] Chargement statistiques pour session={code_session}")
        
        if not code_session:
            return False, None, "Code session invalide"
        
        if not self.panier_ctrl:
            return False, None, "Contrôleur panier non initialisé"
        
        try:
            dto = StatistiquesDTO()
            
            # 1. Charger les statistiques d'expiration
            ok, msg = self._charger_stats_expiration(dto, code_session)
            if not ok:
                return False, None, msg
            
            # 2. Charger les statistiques par type
            ok, msg = self._charger_stats_par_type(dto, code_session)
            if not ok:
                return False, None, msg
            
            # 3. Charger le stock détaillé
            ok, msg = self._charger_stock_detaille(dto, code_session)
            if not ok:
                return False, None, msg
            
            # 4. Calculer les pourcentages
            dto.calculer_pourcentages()
            
            self.logger.info("[StatistiquesLoader] Statistiques chargées avec succès")
            return True, dto, ""
            
        except Exception as e:
            error_msg = f"Erreur lors du chargement des statistiques: {str(e)}"
            self.logger.error(f"[StatistiquesLoader] {error_msg}", exc_info=True)
            return False, None, error_msg
    
    def _charger_stats_expiration(self, dto: StatistiquesDTO, code_session: str) -> Tuple[bool, str]:
        """
        Charge les statistiques d'expiration (expirés, bientôt expirés, valides).
        
        Args:
            dto: Objet DTO à remplir
            code_session: Code de la session
        
        Returns:
            tuple: (succès, message_erreur)
        """
        try:
            # ✅ RESPECT DU MVC : Appel du contrôleur qui appelle le DAO
            quantites = self.panier_ctrl.obtenir_quantites_par_statut_expiration(code_session)
            
            dto.nb_expires = quantites.get('qte_expire', 0)
            dto.nb_bientot_expires = quantites.get('qte_bientot', 0)
            dto.nb_valides = quantites.get('qte_valide', 0)
            
            # Valeur totale du stock
            dto.valeur_stock_total = self.panier_ctrl.obtenir_valeur_stock(code_session) or 0.0
            
            self.logger.debug(
                f"[StatistiquesLoader] Expiration: "
                f"expirés={dto.nb_expires}, "
                f"bientôt={dto.nb_bientot_expires}, "
                f"valides={dto.nb_valides}"
            )
            
            return True, ""
            
        except Exception as e:
            return False, f"Erreur chargement stats expiration: {str(e)}"
    
    def _charger_stats_par_type(self, dto: StatistiquesDTO, code_session: str) -> Tuple[bool, str]:
        """
        Charge les statistiques par type de produit (Liquide, Pommade, Comprimé).
        
        Args:
            dto: Objet DTO à remplir
            code_session: Code de la session
        
        Returns:
            tuple: (succès, message_erreur)
        """
        try:
            # ✅ RESPECT DU MVC : Appel du contrôleur qui appelle le DAO
            stock_par_type = self.panier_ctrl.obtenir_quantites_par_type_produit(code_session)
            
            dto.stock_liquide = stock_par_type.get('Liquide', 0)
            dto.stock_pommade = stock_par_type.get('Pommade', 0)
            dto.stock_comprime = stock_par_type.get('Comprimé', 0)
            
            self.logger.debug(
                f"[StatistiquesLoader] Par type: "
                f"liquide={dto.stock_liquide}, "
                f"pommade={dto.stock_pommade}, "
                f"comprimé={dto.stock_comprime}"
            )
            
            return True, ""
            
        except Exception as e:
            return False, f"Erreur chargement stats par type: {str(e)}"
    
    def _charger_stock_detaille(self, dto: StatistiquesDTO, code_session: str) -> Tuple[bool, str]:
        """
        Charge le stock détaillé par libellé de produit.
        
        Args:
            dto: Objet DTO à remplir
            code_session: Code de la session
        
        Returns:
            tuple: (succès, message_erreur)
        """
        try:
            # ✅ RESPECT DU MVC : Appel du contrôleur qui appelle le DAO
            dto.stock_detaille = self.panier_ctrl.obtenir_stock_detaille(code_session, limite=20)
            
            self.logger.debug(
                f"[StatistiquesLoader] Stock détaillé: {len(dto.stock_detaille)} produits"
            )
            
            return True, ""
            
        except Exception as e:
            return False, f"Erreur chargement stock détaillé: {str(e)}"
    
    # =========================================================================
    # MÉTHODES UTILITAIRES PRIVÉES
    # =========================================================================
    
    def _compter_tous_les_lots(self, code_session: str) -> int:
        """
        Compte le nombre total de lots dans le stock.
        
        Args:
            code_session: Code de la session
        
        Returns:
            int: Nombre total de lots
        """
        try:
            lignes = self.panier_ctrl.lister_par_session(code_session)
            return len(lignes)
        except Exception:
            return 0
    
    def _obtenir_type_produit(self, ligne) -> str:
        """
        Extrait le type de produit d'une ligne panier.
        Gère les différents formats possibles (objet, dict).
        
        Args:
            ligne: Ligne de panier (objet ou dict)
        
        Returns:
            str: Type de produit (Liquide, Pommade, Comprimé)
        """
        try:
            # Si c'est un objet PanierFactureFourni
            if hasattr(ligne, 'type'):
                return getattr(ligne, 'type', self.TYPE_COMPRIME)
            
            # Si c'est un dictionnaire (depuis le DAO avec jointure)
            if isinstance(ligne, dict) and 'type' in ligne:
                return ligne['type'] or self.TYPE_COMPRIME
            
            # Par défaut
            return self.TYPE_COMPRIME
            
        except Exception:
            return self.TYPE_COMPRIME
    
    def _obtenir_designation(self, ligne) -> str:
        """
        Extrait la désignation d'une ligne panier.
        
        Args:
            ligne: Ligne de panier
        
        Returns:
            str: Désignation du produit
        """
        try:
            # Si c'est un objet PanierFactureFourni
            if hasattr(ligne, 'designation'):
                return getattr(ligne, 'designation', "Produit inconnu")
            
            # Si c'est un dictionnaire
            if isinstance(ligne, dict):
                # Essayer designation d'abord
                if 'designation' in ligne and ligne['designation']:
                    return ligne['designation']
                # Sinon essayer libelle (depuis la jointure)
                if 'libelle' in ligne and ligne['libelle']:
                    return ligne['libelle']
            
            return "Produit inconnu"
            
        except Exception:
            return "Produit inconnu"
    
    def _obtenir_quantite_stock(self, ligne) -> int:
        """
        Extrait la quantité en stock d'une ligne panier.
        
        Args:
            ligne: Ligne de panier
        
        Returns:
            int: Quantité en stock
        """
        try:
            # Si c'est un objet PanierFactureFourni
            if hasattr(ligne, 'quantite_four'):
                return getattr(ligne, 'quantite_four', 0)
            
            # Si c'est un dictionnaire
            if isinstance(ligne, dict):
                # Essayer quantite_four
                if 'quantite_four' in ligne:
                    return ligne['quantite_four'] or 0
                # Essayer stock_restant (si calculé)
                if 'stock_restant' in ligne:
                    return ligne['stock_restant'] or 0
            
            return 0
            
        except Exception:
            return 0
    
    def obtenir_couleur_par_type(self, type_produit: str) -> str:
        """
        Retourne la couleur associée à un type de produit.
        
        Args:
            type_produit: Type de produit
        
        Returns:
            str: Code couleur hexadécimal
        """
        from views.shared.theme_manager import theme_manager
        return self._couleurs_type().get(type_produit, theme_manager.colors()['text_muted'])
