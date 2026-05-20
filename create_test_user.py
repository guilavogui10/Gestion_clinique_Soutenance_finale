"""
create_test_user.py
-------------------
Script pour créer un compte de test non-responsable pour tester les permissions.

Usage:
    python create_test_user.py
"""

import sys
from pathlib import Path

# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

from data.dao_personnel import PersonnelDAO
from data.dao_user import UserDAO
from models.modele_personnel import ModelePersonnel
from models.modele_user import ModeleUser


def creer_personnel_test():
    """Crée un personnel de test non-responsable"""
    personnel_dao = PersonnelDAO()
    
    # Générer un nouveau code
    code_personnel = personnel_dao.generer_nouveau_code()
    
    # Créer le personnel (Chirurgien NON responsable)
    personnel = ModelePersonnel(
        code=code_personnel,
        nom="Test",
        prenom="Chirurgien",
        adresse="Conakry, Guinée",
        date_naissance="1990-01-01",
        contact="+224 600 00 00 01",
        mail="chirurgien.test@clinique.com",
        fonction="Chirurgien",
        photo_path=None,
        est_responsable=0  # NON RESPONSABLE
    )
    
    if personnel_dao.enregistrer_personnel(personnel):
        print(f"✅ Personnel créé avec succès : {code_personnel}")
        print(f"   Nom: {personnel.get_prenom()} {personnel.get_nom()}")
        print(f"   Fonction: {personnel.get_fonction()}")
        print(f"   Est responsable: NON")
        return code_personnel
    else:
        print("❌ Erreur lors de la création du personnel")
        return None


def creer_utilisateur_test(code_personnel):
    """Crée un compte utilisateur pour le personnel de test"""
    user_dao = UserDAO()
    
    # Générer un nouveau code utilisateur
    code_user = user_dao.generer_nouveau_code()
    
    # Créer l'utilisateur
    user = ModeleUser(
        code=code_user,
        mdp="test123",  # Mot de passe simple pour les tests
        role="Chirurgien",
        id_personnel=code_personnel
    )
    
    if user_dao.enregistrer_utilisateur(user):
        print(f"✅ Utilisateur créé avec succès : {code_user}")
        print(f"   Login: {code_user}")
        print(f"   Mot de passe: test123")
        print(f"   Rôle: Chirurgien")
        return True
    else:
        print("❌ Erreur lors de la création de l'utilisateur")
        return False


def main():
    print("=" * 60)
    print("  Création d'un compte de test NON-RESPONSABLE")
    print("=" * 60)
    print()
    
    # Étape 1 : Créer le personnel
    print("[1/2] Création du personnel...")
    code_personnel = creer_personnel_test()
    
    if not code_personnel:
        print("\n❌ Échec de la création du personnel")
        return
    
    print()
    
    # Étape 2 : Créer l'utilisateur
    print("[2/2] Création du compte utilisateur...")
    if creer_utilisateur_test(code_personnel):
        print()
        print("=" * 60)
        print("  ✅ COMPTE DE TEST CRÉÉ AVEC SUCCÈS !")
        print("=" * 60)
        print()
        print("📋 Informations de connexion :")
        print("   Login: (voir le code utilisateur ci-dessus)")
        print("   Mot de passe: test123")
        print()
        print("🔒 Permissions :")
        print("   - Rôle: Chirurgien")
        print("   - Est responsable: NON")
        print("   - Peut créer: NON (nécessite autorisation)")
        print("   - Peut modifier: NON (nécessite autorisation)")
        print("   - Peut voir résultats: NON (nécessite autorisation)")
        print()
        print("🧪 Pour tester :")
        print("   1. Connectez-vous avec ce compte")
        print("   2. Allez dans Chirurgies")
        print("   3. Essayez de créer/modifier/voir résultats")
        print("   4. Le système demandera l'autorisation au responsable")
        print()
    else:
        print("\n❌ Échec de la création de l'utilisateur")


if __name__ == "__main__":
    main()
