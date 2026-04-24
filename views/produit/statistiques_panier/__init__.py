"""
Package statistiques_panier - Statistiques du stock pharmaceutique.

Architecture : MVC + Service Layer + DTO
Niveau : SENIOR / EXPERT
Statut : PRODUCTION READY

Composants :
- components/ : Composants UI réutilisables
- handlers/ : Logique métier (StatistiquesDataLoader, UIUpdater)
- styles/ : Styles CSS centralisés
- utils/ : Utilitaires de formatage

Point d'entrée principal : StatistiquesStockWidget
"""

from .statistiques_widget import StatistiquesStockWidget
from .handlers.statistiques_loader import StatistiquesDataLoader, StatistiquesDTO

__all__ = ['StatistiquesStockWidget', 'StatistiquesDataLoader', 'StatistiquesDTO']
