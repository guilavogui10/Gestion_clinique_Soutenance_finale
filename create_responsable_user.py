"""
create_responsable_user.py
---------------------------
Script pour créer un compte de test RESPONSABLE pour tester les permissions.

Usage:
    python create_responsable_user.py
"""

import sys
from pathlib import Path

# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

from data.dao_personnel import PersonnelDAO
from data.dao_user import UserDAO
from models.modele_personnel import ModelePersonnel
from models.modele_user import ModeleUser


def creer_personnel_responsable():
    """Crée un personnel de test RESPONSABLE"""
    personnel_dao = PersonnelDAO()
    
    # Générer un nouveau code
    code_personnel = personnel_dao.generer_nouveau_code()
    
    # Créer le personnel (Chirurgien RESPONSABLE)
    personnel = ModelePersonnel(
        code=code_personnel,
        nom="Responsable",
        prenom="Chirurgien",
        adresse="Conakry, Guinée",
        date_naissance="1985-01-01",
        contact="+224 600 00 00 02",
        mail="chirurgien.responsable@clinique.com",
        fonction="Chirurgien",
        photo_path=None,
        est_responsable=1  # RESPONSABLE
    )
    
    if personnel_dao.enregistrer_personnel(personnel):
        print(f"✅ Personnel créé avec succès : {code_personnel}")
        print(f"   Nom: {personnel.get_prenom()} {personnel.get_nom()}")
        print(f"   Fonction: {personnel.get_fonction()}")
        print(f"   Est responsable: OUI")
        return code_personnel
    else:
        print("❌ Erreur lors de la création du personnel")
        return None


def creer_utilisateur_responsable(code_personnel):
    """Crée un compte utilisateur pour le personnel responsable"""
    user_dao = UserDAO()
    
    # Générer un nouveau code utilisateur
    code_user = user_dao.generer_nouveau_code()
    
    # Créer l'utilisateur
    user = ModeleUser(
        code=code_user,
        mdp="resp123",  # Mot de passe simple pour les tests
        role="Chirurgien",
        id_personnel=code_personnel
    )
    
    if user_dao.enregistrer_utilisateur(user):
        print(f"✅ Utilisateur créé avec succès : {code_user}")
        print(f"   Login: {code_user}")
        print(f"   Mot de passe: resp123")
        print(f"   Rôle: Chirurgien")
        return True
    else:
        print("❌ Erreur lors de la création de l'utilisateur")
        return False


def main():
    print("=" * 60)
    print("  Création d'un compte de test RESPONSABLE")
    print("=" * 60)
    print()
    
    # Étape 1 : Créer le personnel
    print("[1/2] Création du personnel...")
    code_personnel = creer_personnel_responsable()
    
    if not code_personnel:
        print("\n❌ Échec de la création du personnel")
        return
    
    print()
    
    # Étape 2 : Créer l'utilisateur
    print("[2/2] Création du compte utilisateur...")
    if creer_utilisateur_responsable(code_personnel):
        print()
        print("=" * 60)
        print("  ✅ COMPTE RESPONSABLE CRÉÉ AVEC SUCCÈS !")
        print("=" * 60)
        print()
        print("📋 Informations de connexion :")
        print("   Login: (voir le code utilisateur ci-dessus)")
        print("   Mot de passe: resp123")
        print()
        print("🔒 Permissions :")
        print("   - Rôle: Chirurgien")
        print("   - Est responsable: OUI")
        print("   - Peut créer: OUI")
        print("   - Peut modifier: OUI")
        print("   - Peut voir résultats: OUI (avec OTP de confirmation)")
        print()
        print("📧 Email pour OTP :")
        print("   chirurgien.responsable@clinique.com")
        print()
        print("🧪 Pour tester :")
        print("   1. Connectez-vous avec ce compte")
        print("   2. Allez dans Chirurgies")
        print("   3. Créer/Modifier → Accès direct")
        print("   4. Voir résultats → OTP envoyé à votre email")
        print()
    else:
        print("\n❌ Échec de la création de l'utilisateur")


if __name__ == "__main__":
    main()
