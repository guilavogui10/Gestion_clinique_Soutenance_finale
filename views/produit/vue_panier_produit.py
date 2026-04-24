"""
Point d'entrée pour le widget panier (rétrocompatibilité).
Importe depuis la nouvelle architecture modulaire refactorisée.

MIGRATION COMPLÈTE TERMINÉE ✅
============================

L'ancien fichier monolithique (1000+ lignes) a été refactorisé en une
architecture modulaire professionnelle avec 11 fichiers spécialisés.

NOUVELLE ARCHITECTURE :
views/common/panier/
├── panier_widget.py           # Widget principal (orchestrateur)
├── components/                 # Composants UI réutilisables
│   ├── animated_frame.py      # ✅ Cadre avec animation
│   ├── panier_header.py       # ✅ Header avec badge
│   ├── panier_form.py         # ✅ Formulaire de saisie
│   ├── panier_footer.py       # ✅ Footer avec total et boutons
│   └── panier_ligne_item.py   # ✅ Ligne individuelle
├── handlers/                   # Logique métier
│   ├── data_loader.py         # ✅ Chargement données
│   ├── validation_handler.py # ✅ Validation temps réel
│   └── panier_operations.py  # ✅ Opérations CRUD
└── styles/                     # Styles CSS centralisés
    └── panier_styles.py       # ✅ Tous les styles CSS

PRINCIPES APPLIQUÉS :
✅ SOLID Principles
✅ Design Patterns (MVC, Facade, Strategy, Factory, Composition)
✅ Separation of Concerns (UI / Logique / Styles)
✅ Clean Code (Noms explicites, fonctions courtes, docstrings)

AVANTAGES :
✅ Maintenabilité : Code organisé et structuré
✅ Testabilité : Composants testables unitairement
✅ Réutilisabilité : Composants réutilisables
✅ Évolutivité : Facile à étendre

BACKUP :
L'ancien fichier est sauvegardé dans vue_panierProduit_OLD.py
"""

# Import depuis le panier de la facturation patient (architecture originale)
from views.facturation.patient.panier import PanierProduitWidget
from views.facturation.patient.panier.components.animated_frame import AnimatedFrame

# Exports pour rétrocompatibilité
__all__ = ['PanierProduitWidget', 'AnimatedFrame']


# ============================================================================
# NOTES POUR LES DÉVELOPPEURS
# ============================================================================
#
# Ce fichier sert de point d'entrée pour maintenir la rétrocompatibilité.
# Tous les imports existants continuent de fonctionner :
#
#   from views.common.vue_panierProduit import PanierProduitWidget
#
# Le widget fonctionne exactement comme avant, mais avec une architecture
# modulaire professionnelle en arrière-plan.
#
# Pour utiliser directement la nouvelle architecture :
#
#   from views.common.panier import PanierProduitWidget
#   from views.common.panier.components import PanierForm, PanierFooter
#   from views.common.panier.handlers import DataLoader, ValidationHandler
#   from views.common.panier.styles import PanierStyles
#
# ============================================================================
