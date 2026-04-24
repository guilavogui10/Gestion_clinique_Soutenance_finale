"""
Point d'entrée pour le widget prescription (rétrocompatibilité).
Importe depuis la nouvelle architecture modulaire refactorisée.

MIGRATION COMPLÈTE TERMINÉE ✅
============================

L'ancien fichier monolithique a été refactorisé en une
architecture modulaire professionnelle avec 11 fichiers spécialisés.

NOUVELLE ARCHITECTURE :
views/common/prescription/
├── prescription_widget.py           # Widget principal (orchestrateur)
├── components/                       # Composants UI réutilisables
│   ├── animated_frame.py            # ✅ Cadre avec animation
│   ├── prescription_header.py       # ✅ Header avec badge
│   ├── prescription_form.py         # ✅ Formulaire de saisie + carte patient
│   ├── prescription_footer.py       # ✅ Footer avec total et boutons
│   ├── prescription_ligne_item.py   # ✅ Ligne individuelle
│   ├── modern_quantity_spinner.py   # ✅ Spinner quantité moderne
│   ├── modern_price_input.py        # ✅ Champ prix formaté (readonly)
│   └── modern_message_box.py        # ✅ Boîtes de dialogue modernes
├── handlers/                         # Logique métier
│   ├── data_loader.py               # ✅ Chargement patients/produits/panier
│   ├── validation_handler.py        # ✅ Validation quantité temps réel
│   └── prescription_operations.py   # ✅ Opérations CRUD prescription
└── styles/                           # Styles CSS centralisés
    └── prescription_styles.py        # ✅ Tous les styles CSS (palette médicale)

PRINCIPES APPLIQUÉS :
✅ SOLID Principles
✅ Design Patterns (MVC, Facade, Strategy, Factory, Composition)
✅ Separation of Concerns (UI / Logique / Styles)
✅ Clean Code (Noms explicites, fonctions courtes, docstrings)

RÈGLES MÉTIER CLÉS :
✅ date_expiration JAMAIS saisie manuellement → FEFO automatique (DAO)
✅ designation et prix_applique auto-complétés depuis produits
✅ Vérification stock AVANT chaque prescription
✅ statut_patient → 'Attente payement' après validation de la prescription
✅ Pas de statut_facture ligne par ligne → appartient à facture_patient

AVANTAGES :
✅ Maintenabilité : Code organisé et structuré
✅ Testabilité : Composants testables unitairement
✅ Réutilisabilité : Composants réutilisables
✅ Évolutivité : Facile à étendre
"""

# Import depuis la nouvelle architecture modulaire
from .panier_prescription.prescription_widget import PrescriptionWidget
from .panier_prescription.components.animated_frame import AnimatedFrame

# Exports pour rétrocompatibilité
__all__ = ['PrescriptionWidget', 'AnimatedFrame']


# ============================================================================
# NOTES POUR LES DÉVELOPPEURS
# ============================================================================
#
# Ce fichier sert de point d'entrée pour maintenir la rétrocompatibilité.
# Tous les imports existants continuent de fonctionner :
#
#   from views.common.vue_prescriptionProduit import PrescriptionWidget
#
# Le widget fonctionne exactement comme avant, mais avec une architecture
# modulaire professionnelle en arrière-plan.
#
# Pour utiliser directement la nouvelle architecture :
#
#   from views.common.prescription import PrescriptionWidget
#   from views.common.prescription.components import PrescriptionForm
#   from views.common.prescription.handlers import PrescriptionOperations
#   from views.common.prescription.styles import PrescriptionStyles
#
# Injection du contrôleur depuis la vue parente :
#
#   from controllers.prescription_controleur import PrescriptionControleur
#   from views.common.vue_prescriptionProduit import PrescriptionWidget
#
#   widget = PrescriptionWidget(prescription_ctrl=PrescriptionControleur())
#   widget.charger_donnees(code_session)
#
#   # Quand un patient est sélectionné depuis la liste d'attente :
#   widget.charger_patient({
#       'nom': 'Diallo', 'prenom': 'Mamadou',
#       'code_visite': 'VIS001',
#       'code_consultation': 'CON001',
#       'code_session': code_session
#   })
#
# ============================================================================
