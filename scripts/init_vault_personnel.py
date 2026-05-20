"""
init_vault_personnel.py
------------------------
Script utilitaire pour initialiser les clés TOTP Vault pour tous les personnels existants.

Usage:
    python init_vault_personnel.py

Ce script :
1. Récupère tous les personnels de la base de données
2. Crée une clé TOTP Vault pour chaque personnel
3. Affiche un rapport des créations réussies/échouées
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers.controleur_personnel import ControllerPersonnel
from core.vault_service import VaultService


def main():
    print("=" * 60)
    print("INITIALISATION DES CLÉS VAULT POUR LES PERSONNELS")
    print("=" * 60)
    print()
    
    # Vérifier la connexion Vault
    vault = VaultService()
    if not vault.est_connecte():
        print("❌ ERREUR : Service Vault non connecté !")
        print("Veuillez vérifier :")
        print("  1. Que Vault est démarré (start_vault.ps1)")
        print("  2. Que les variables d'environnement sont configurées (.env)")
        print("     - VAULT_URL")
        print("     - VAULT_TOKEN")
        return 1
    
    print("✅ Service Vault connecté")
    print()
    
    # Initialiser le contrôleur
    ctrl = ControllerPersonnel()
    
    # Récupérer tous les personnels
    print("📋 Récupération des personnels...")
    personnels = ctrl.lister_tout()
    
    if not personnels:
        print("⚠️  Aucun personnel trouvé dans la base de données")
        return 0
    
    print(f"✅ {len(personnels)} personnel(s) trouvé(s)")
    print()
    
    # Créer les clés Vault
    print("🔑 Création des clés TOTP Vault...")
    print("-" * 60)
    
    resultat = ctrl.creer_cles_vault_pour_tous()
    
    print()
    print("=" * 60)
    print("RAPPORT DE CRÉATION")
    print("=" * 60)
    print(f"Total de personnels    : {resultat['total']}")
    print(f"Clés créées avec succès: {resultat['succes']} ✅")
    print(f"Échecs                 : {resultat['echecs']} ❌")
    print("=" * 60)
    
    if resultat['echecs'] > 0:
        print()
        print("⚠️  Certaines clés n'ont pas pu être créées.")
        print("Vérifiez les logs ci-dessus pour plus de détails.")
        return 1
    
    print()
    print("✅ Toutes les clés TOTP Vault ont été créées avec succès !")
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print()
        print("⚠️  Opération annulée par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ ERREUR FATALE : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
