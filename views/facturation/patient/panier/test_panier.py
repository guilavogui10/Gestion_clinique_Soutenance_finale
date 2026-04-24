"""
Tests unitaires pour les composants du panier refactorisé.
Démontre la testabilité de l'architecture modulaire.
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Tests basiques sans framework (pour démonstration)
def test_panier_styles():
    """Test des styles CSS centralisés."""
    from .styles.panier_styles import PanierStyles
    
    print("✓ Test PanierStyles...")
    assert PanierStyles.VERT_PRINCIPAL == "#003f20"
    assert PanierStyles.ROUGE == "#e74c3c"
    assert "border-radius" in PanierStyles.input_normal()
    assert "border-radius" in PanierStyles.input_valide()
    print("  ✅ PanierStyles OK")


def test_data_loader():
    """Test du DataLoader."""
    from .handlers.data_loader import DataLoader
    
    print("✓ Test DataLoader...")
    loader = DataLoader("#003f20")
    assert loader.vert_principal == "#003f20"
    print("  ✅ DataLoader OK")


def test_validation_handler():
    """Test du ValidationHandler."""
    from .handlers.validation_handler import ValidationHandler
    
    print("✓ Test ValidationHandler...")
    
    # Mock du contrôleur
    class MockPanierCtrl:
        def valider_quantite(self, texte):
            try:
                int(texte)
                return True, "OK"
            except:
                return False, "Invalide"
        
        def valider_prix(self, texte, label):
            try:
                float(texte.replace(" ", ""))
                return True, "OK"
            except:
                return False, "Invalide"
        
        def valider_date_expiration(self, texte):
            return len(texte) == 10, "OK" if len(texte) == 10 else "Invalide"
    
    handler = ValidationHandler(MockPanierCtrl())
    assert handler.panier_ctrl is not None
    print("  ✅ ValidationHandler OK")


def test_panier_operations():
    """Test du PanierOperations."""
    from .handlers.panier_operations import PanierOperations
    
    print("✓ Test PanierOperations...")
    
    # Mock des contrôleurs
    class MockPanierCtrl:
        pass
    
    class MockFactureCtrl:
        pass
    
    operations = PanierOperations(MockPanierCtrl(), MockFactureCtrl())
    assert operations.panier_ctrl is not None
    assert operations.facture_ctrl is not None
    print("  ✅ PanierOperations OK")


def test_architecture_complete():
    """Test de l'architecture complète."""
    print("✓ Test architecture complète...")
    
    # Vérifier que tous les modules sont importables
    from . import PanierProduitWidget
    from .components.animated_frame import AnimatedFrame
    from .components.panier_header import PanierHeader
    from .components.panier_form import PanierForm
    from .components.panier_footer import PanierFooter
    from .components.panier_ligne_item import PanierLigneItem
    from .handlers.data_loader import DataLoader
    from .handlers.validation_handler import ValidationHandler
    from .handlers.panier_operations import PanierOperations
    from .styles.panier_styles import PanierStyles
    
    print("  ✅ Tous les modules sont importables")
    print("  ✅ Architecture complète OK")


def test_retrocompatibilite():
    """Test de la rétrocompatibilité."""
    print("✓ Test rétrocompatibilité...")
    
    # L'ancien import doit toujours fonctionner
    from .panier_widget import PanierProduitWidget
    from .components.animated_frame import AnimatedFrame
    
    print("  ✅ Imports rétrocompatibles OK")


def run_all_tests():
    """Exécute tous les tests."""
    print("\n" + "="*60)
    print("TESTS UNITAIRES - Architecture Panier Refactorisee")
    print("="*60 + "\n")
    
    try:
        test_panier_styles()
        test_data_loader()
        test_validation_handler()
        test_panier_operations()
        test_architecture_complete()
        test_retrocompatibilite()
        
        print("\n" + "="*60)
        print("TOUS LES TESTS SONT PASSES AVEC SUCCES !")
        print("="*60 + "\n")
        
        print("Resumé :")
        print("  - 6 tests executes")
        print("  - 6 tests reussis")
        print("  - 0 test echoue")
        print("\nL'architecture refactorisee est fonctionnelle !\n")
        
        return True
        
    except Exception as e:
        print(f"\nERREUR : {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
