"""
verifier_installation.py
------------------------
Script pour vérifier que toutes les améliorations sont correctement installées.
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def afficher_titre(titre):
    """Affiche un titre formaté."""
    print("\n" + "=" * 70)
    print(f"  {titre}")
    print("=" * 70)


def verifier_fichiers():
    """Vérifie que tous les nouveaux fichiers existent."""
    afficher_titre("VÉRIFICATION DES FICHIERS")
    
    fichiers_requis = [
        # Scripts
        ("scripts/create_audit_table.sql", "Script SQL"),
        ("scripts/init_audit_tables.py", "Script d'initialisation"),
        ("scripts/test_permissions_ameliorees.py", "Script de test"),
        ("scripts/verifier_installation.py", "Script de vérification"),
        
        # DAO
        ("data/dao_audit_permission.py", "DAO Audit"),
        ("data/dao_otp_tentatives.py", "DAO Tentatives OTP"),
        
        # Documentation
        ("GUIDE_MISE_A_JOUR_PERMISSIONS.md", "Guide de mise à jour"),
        ("README_PERMISSIONS_AMELIOREES.md", "README améliorations"),
        ("CHANGELOG_PERMISSIONS.md", "Changelog"),
    ]
    
    tous_presents = True
    
    for fichier, description in fichiers_requis:
        chemin = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            fichier
        )
        
        if os.path.exists(chemin):
            print(f"   ✅ {description:30} : {fichier}")
        else:
            print(f"   ❌ {description:30} : {fichier} (MANQUANT)")
            tous_presents = False
    
    return tous_presents


def verifier_imports():
    """Vérifie que tous les modules peuvent être importés."""
    afficher_titre("VÉRIFICATION DES IMPORTS")
    
    imports_requis = [
        ("data.dao_audit_permission", "AuditPermissionDAO"),
        ("data.dao_otp_tentatives", "OTPTentativesDAO"),
        ("service_metier.permission_service", "PermissionService"),
        ("controllers.controleur_permission", "PermissionControleur"),
        ("core.vault_service", "VaultService"),
    ]
    
    tous_importables = True
    
    for module, classe in imports_requis:
        try:
            mod = __import__(module, fromlist=[classe])
            cls = getattr(mod, classe)
            print(f"   ✅ {module:40} : {classe}")
        except ImportError as e:
            print(f"   ❌ {module:40} : Erreur d'import - {e}")
            tous_importables = False
        except AttributeError as e:
            print(f"   ❌ {module:40} : Classe {classe} introuvable - {e}")
            tous_importables = False
        except Exception as e:
            print(f"   ❌ {module:40} : Erreur - {e}")
            tous_importables = False
    
    return tous_importables


def verifier_tables():
    """Vérifie que les tables de base de données existent."""
    afficher_titre("VÉRIFICATION DES TABLES")
    
    try:
        from connexion.db_connection import DBConnection
        
        db = DBConnection()
        conn = db.connect()
        
        if not conn:
            print("   ❌ Impossible de se connecter à la base de données")
            return False
        
        cursor = conn.cursor()
        
        tables_requises = [
            ("audit_permissions", "Table d'audit des permissions"),
            ("otp_tentatives", "Table des tentatives OTP"),
        ]
        
        toutes_presentes = True
        
        for table, description in tables_requises:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            if cursor.fetchone():
                print(f"   ✅ {description:40} : {table}")
            else:
                print(f"   ❌ {description:40} : {table} (MANQUANTE)")
                toutes_presentes = False
        
        conn.close()
        return toutes_presentes
        
    except Exception as e:
        print(f"   ❌ Erreur lors de la vérification : {e}")
        return False


def verifier_methodes():
    """Vérifie que les nouvelles méthodes existent."""
    afficher_titre("VÉRIFICATION DES MÉTHODES")
    
    try:
        from service_metier.permission_service import PermissionService
        from controllers.controleur_permission import PermissionControleur
        
        permission_service = PermissionService()
        permission_controleur = PermissionControleur()
        
        methodes_service = [
            ("refuser_autorisation", "Refuser une autorisation"),
            ("obtenir_demandes_en_attente", "Obtenir demandes en attente"),
            ("obtenir_historique_utilisateur", "Obtenir historique utilisateur"),
        ]
        
        methodes_controleur = [
            ("refuser_autorisation", "Refuser une autorisation"),
            ("obtenir_demandes_en_attente", "Obtenir demandes en attente"),
            ("obtenir_historique_utilisateur", "Obtenir historique utilisateur"),
        ]
        
        toutes_presentes = True
        
        print("\n   📦 PermissionService :")
        for methode, description in methodes_service:
            if hasattr(permission_service, methode):
                print(f"      ✅ {description:40} : {methode}()")
            else:
                print(f"      ❌ {description:40} : {methode}() (MANQUANTE)")
                toutes_presentes = False
        
        print("\n   📦 PermissionControleur :")
        for methode, description in methodes_controleur:
            if hasattr(permission_controleur, methode):
                print(f"      ✅ {description:40} : {methode}()")
            else:
                print(f"      ❌ {description:40} : {methode}() (MANQUANTE)")
                toutes_presentes = False
        
        return toutes_presentes
        
    except Exception as e:
        print(f"   ❌ Erreur lors de la vérification : {e}")
        return False


def verifier_configuration():
    """Vérifie la configuration."""
    afficher_titre("VÉRIFICATION DE LA CONFIGURATION")
    
    try:
        from data.dao_otp_tentatives import OTPTentativesDAO
        
        tentatives_dao = OTPTentativesDAO()
        
        print(f"   📊 Configuration OTP :")
        print(f"      - Tentatives max : {tentatives_dao.MAX_TENTATIVES}")
        print(f"      - Durée blocage : {tentatives_dao.DUREE_BLOCAGE_MINUTES} minutes")
        
        if tentatives_dao.MAX_TENTATIVES > 0 and tentatives_dao.DUREE_BLOCAGE_MINUTES > 0:
            print(f"   ✅ Configuration valide")
            return True
        else:
            print(f"   ❌ Configuration invalide")
            return False
        
    except Exception as e:
        print(f"   ❌ Erreur lors de la vérification : {e}")
        return False


def afficher_recommandations():
    """Affiche les recommandations post-installation."""
    afficher_titre("RECOMMANDATIONS")
    
    print("""
   📋 Prochaines étapes :
   
   1. ✅ Exécuter les tests :
      python scripts\\test_permissions_ameliorees.py
   
   2. ✅ Configurer le nettoyage automatique :
      - Créer une tâche planifiée quotidienne
      - Exécuter dao_audit_permission.nettoyer_anciennes_demandes(90)
      - Exécuter dao_otp_tentatives.nettoyer_anciennes_tentatives(24)
   
   3. ✅ Former l'équipe :
      - Lire README_PERMISSIONS_AMELIOREES.md
      - Lire GUIDE_MISE_A_JOUR_PERMISSIONS.md
      - Tester avec des comptes de test
   
   4. ✅ Surveiller :
      - Consulter les statistiques régulièrement
      - Vérifier les demandes en attente
      - Analyser l'historique des utilisateurs
   
   5. ✅ Documenter :
      - Mettre à jour la documentation interne
      - Former les nouveaux utilisateurs
      - Créer des procédures opérationnelles
    """)


def main():
    """Point d'entrée principal."""
    
    print("\n" + "=" * 70)
    print("  🔍 VÉRIFICATION DE L'INSTALLATION")
    print("  Système de permissions amélioré v2.0")
    print("=" * 70)
    
    resultats = []
    
    # Vérifications
    tests = [
        ("Fichiers", verifier_fichiers),
        ("Imports", verifier_imports),
        ("Tables", verifier_tables),
        ("Méthodes", verifier_methodes),
        ("Configuration", verifier_configuration),
    ]
    
    for nom, test_func in tests:
        try:
            resultat = test_func()
            resultats.append((nom, resultat))
        except Exception as e:
            print(f"\n❌ Erreur lors de la vérification '{nom}' : {e}")
            resultats.append((nom, False))
    
    # Résumé
    afficher_titre("RÉSUMÉ")
    
    print()
    for nom, resultat in resultats:
        statut = "✅ OK" if resultat else "❌ ERREUR"
        print(f"   {statut:12} : {nom}")
    
    nb_reussis = sum(1 for _, r in resultats if r)
    nb_total = len(resultats)
    
    print(f"\n   📊 Score : {nb_reussis}/{nb_total} vérifications réussies")
    
    if nb_reussis == nb_total:
        print("\n   🎉 Installation complète et fonctionnelle !")
        afficher_recommandations()
        return 0
    else:
        print("\n   ⚠️  Installation incomplète ou problèmes détectés.")
        print("\n   📝 Actions à effectuer :")
        
        for nom, resultat in resultats:
            if not resultat:
                if nom == "Tables":
                    print(f"      - Exécuter : python scripts\\init_audit_tables.py")
                elif nom == "Fichiers":
                    print(f"      - Vérifier que tous les fichiers ont été créés")
                elif nom == "Imports":
                    print(f"      - Vérifier les dépendances Python")
                elif nom == "Méthodes":
                    print(f"      - Vérifier que les fichiers ont été correctement modifiés")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
