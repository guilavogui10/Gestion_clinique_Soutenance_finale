"""
Point d'entrée pour le widget statistiques (rétrocompatibilité).
Importe depuis la nouvelle architecture modulaire refactorisée.

REFACTORISATION COMPLÈTE TERMINÉE ✅
====================================

L'ancien fichier monolithique (620+ lignes) a été refactorisé en une
architecture modulaire professionnelle avec 10+ fichiers spécialisés.

NOUVELLE ARCHITECTURE :
views/common/statistiques_panier/
├── statistiques_widget.py      # Widget principal (orchestrateur)
├── components/                  # Composants UI réutilisables
│   ├── animated_frame.py       # ✅ Cadre avec animation
│   ├── stat_card.py            # ✅ Card statistique simple
│   ├── donut_card.py           # ✅ Card avec graphe donut
│   ├── ligne_stock_card.py     # ✅ Ligne de stock
│   └── stock_detail_card.py    # ✅ Card scrollable
├── handlers/                    # Logique métier
│   ├── statistiques_loader.py  # ✅ Chargement données
│   └── ui_updater.py           # ✅ Mise à jour UI
├── styles/                      # Styles CSS centralisés
│   └── statistiques_styles.py  # ✅ Tous les styles CSS
└── utils/                       # Utilitaires
    └── formatters.py           # ✅ Formatage montants, etc.

PRINCIPES APPLIQUÉS :
✅ SOLID Principles
✅ Design Patterns (MVC, Facade, Factory, Composition, Service Layer)
✅ Separation of Concerns (UI / Logique / Styles / Utils)
✅ Clean Code (Noms explicites, fonctions courtes, docstrings)

AVANTAGES :
✅ Maintenabilité : Code organisé et structuré
✅ Testabilité : Composants testables unitairement
✅ Réutilisabilité : Composants réutilisables
✅ Évolutivité : Facile à étendre

BACKUP :
L'ancien fichier est sauvegardé dans vue_statistiquePanier_OLD.py
"""

# Import depuis la nouvelle architecture modulaire
from .statistiques_panier import StatistiquesStockWidget

# Exports pour rétrocompatibilité
__all__ = ['StatistiquesStockWidget']


# ============================================================================
# NOTES POUR LES DÉVELOPPEURS
# ============================================================================
#
# Ce fichier sert de point d'entrée pour maintenir la rétrocompatibilité.
# Tous les imports existants continuent de fonctionner :
#
#   from views.common.vue_statistiquePanier import StatistiquesStockWidget
#
# Le widget fonctionne exactement comme avant, mais avec une architecture
# modulaire professionnelle en arrière-plan.
#
# Pour utiliser directement la nouvelle architecture :
#
#   from views.common.statistiques_panier import StatistiquesStockWidget
#   from views.common.statistiques_panier.components import StatCard, DonutCard
#   from views.common.statistiques_panier.handlers import StatistiquesDataLoader
#   from views.common.statistiques_panier.styles import StatistiquesStyles
#
# ============================================================================
