"""
test_permissions_ameliorees.py
-------------------------------
Script de test pour les nouvelles fonctionnalités du système de permissions.
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service_metier.permission_service import PermissionService
from data.dao_audit_permission import AuditPermissionDAO
from data.dao_otp_tentatives import OTPTentativesDAO


def afficher_titre(titre):
    """Affiche un titre formaté."""
    print("\n" + "=" * 70)
    print(f"  {titre}")
    print("=" * 70)


def test_limitation_tentatives():
    """Test de la limitation des tentatives OTP."""
    afficher_titre("TEST 1 : Limitation des tentatives OTP")
    
    tentatives_dao = OTPTentativesDAO()
    identifiant_otp = "TEST_U0001_modification_test"
    
    print("\n📋 Configuration :")
    print(f"   - Tentatives max : {tentatives_dao.MAX_TENTATIVES}")
    print(f"   - Durée blocage : {tentatives_dao.DUREE_BLOCAGE_MINUTES} minutes")
    
    # Créer une tentative
    print("\n1️⃣ Création d'une tentative...")
    tentative = tentatives_dao.creer_ou_obtenir_tentative("U0001", identifiant_otp)
    if tentative:
        print(f"   ✅ Tentative créée : ID={tentative['id']}")
    else:
        print("   ❌ Échec de création")
        return False
    
    # Simuler des échecs
    print("\n2️⃣ Simulation d'échecs...")
    for i in range(1, tentatives_dao.MAX_TENTATIVES + 2):
        tentatives_dao.incrementer_tentative(identifiant_otp, est_echec=True)
        info = tentatives_dao.obtenir_info_tentative(identifiant_otp)
        
        if info:
            print(f"   Tentative {i} : {info['nb_echecs']} échec(s)")
            
            if info['est_bloque']:
                print(f"   🔒 BLOQUÉ ! Temps restant : {info['minutes_restantes_blocage']} min")
                break
    
    # Vérifier le blocage
    print("\n3️⃣ Vérification du blocage...")
    est_bloque = tentatives_dao.est_bloque(identifiant_otp)
    if est_bloque:
        print("   ✅ Utilisateur correctement bloqué")
    else:
        print("   ❌ Utilisateur non bloqué (erreur)")
        return False
    
    # Débloquer
    print("\n4️⃣ Déblocage manuel...")
    if tentatives_dao.debloquer(identifiant_otp):
        print("   ✅ Déblocage réussi")
        est_bloque = tentatives_dao.est_bloque(identifiant_otp)
        if not est_bloque:
            print("   ✅ Utilisateur débloqué")
        else:
            print("   ❌ Utilisateur toujours bloqué")
            return False
    else:
        print("   ❌ Échec du déblocage")
        return False
    
    # Nettoyer
    tentatives_dao.supprimer_tentative(identifiant_otp)
    print("\n🧹 Nettoyage effectué")
    
    return True


def test_audit():
    """Test du système d'audit."""
    afficher_titre("TEST 2 : Système d'audit")
    
    audit_dao = AuditPermissionDAO()
    
    # Créer une demande
    print("\n1️⃣ Création d'une demande d'audit...")
    demande_id = audit_dao.creer_demande(
        code_demandeur="U0001",
        role_demandeur="chirurgien",
        est_responsable=False,
        action="modification",
        contexte="Test chirurgie #TEST001",
        code_autorisateur="U0002",
        email_destinataire="test@example.com",
        code_otp_envoye="123456"
    )
    
    if demande_id:
        print(f"   ✅ Demande créée : ID={demande_id}")
    else:
        print("   ❌ Échec de création")
        return False
    
    # Mettre à jour le statut
    print("\n2️⃣ Mise à jour du statut...")
    identifiant_otp = "U0001_modification_Test chirurgie #TEST001"
    if audit_dao.mettre_a_jour_statut(identifiant_otp, "autorise", "U0002"):
        print("   ✅ Statut mis à jour : autorise")
    else:
        print("   ❌ Échec de mise à jour")
        return False
    
    # Obtenir les demandes en attente
    print("\n3️⃣ Récupération des demandes en attente...")
    demandes = audit_dao.obtenir_demandes_en_attente("U0002")
    print(f"   📊 {len(demandes)} demande(s) en attente pour U0002")
    
    # Obtenir l'historique
    print("\n4️⃣ Récupération de l'historique...")
    historique = audit_dao.obtenir_historique_utilisateur("U0001", limite=10)
    print(f"   📊 {len(historique)} demande(s) dans l'historique de U0001")
    
    if historique:
        derniere = historique[0]
        print(f"\n   Dernière demande :")
        print(f"   - Action : {derniere['action']}")
        print(f"   - Contexte : {derniere['contexte']}")
        print(f"   - Statut : {derniere['statut']}")
        print(f"   - Date : {derniere['date_demande']}")
    
    # Obtenir les statistiques
    print("\n5️⃣ Statistiques globales...")
    stats = audit_dao.obtenir_statistiques()
    if stats:
        print(f"   📊 Total demandes : {stats.get('total_demandes', 0)}")
        print(f"   ✅ Autorisées : {stats.get('autorisees', 0)}")
        print(f"   ❌ Refusées : {stats.get('refusees', 0)}")
        print(f"   ⏱️  En attente : {stats.get('en_attente', 0)}")
        temps_moyen = stats.get('temps_moyen_reponse_sec')
        if temps_moyen:
            print(f"   ⏱️  Temps moyen réponse : {temps_moyen:.1f}s")
    
    return True


def test_permission_service():
    """Test du service de permissions amélioré."""
    afficher_titre("TEST 3 : Service de permissions")
    
    permission_service = PermissionService()
    
    # Test 1 : Vérification des permissions
    print("\n1️⃣ Vérification des permissions...")
    
    # Non-responsable veut modifier
    autorise, message = permission_service.verifier_permission(
        code_utilisateur="U0001",
        role="chirurgien",
        est_responsable=False,
        action="modification"
    )
    print(f"   Non-responsable + modification : {'✅ Autorisé' if autorise else '❌ Refusé'}")
    if message:
        print(f"   Message : {message}")
    
    # Responsable veut modifier
    autorise, message = permission_service.verifier_permission(
        code_utilisateur="U0002",
        role="chirurgien",
        est_responsable=True,
        action="modification"
    )
    print(f"   Responsable + modification : {'✅ Autorisé' if autorise else '❌ Refusé'}")
    
    # DG veut supprimer
    autorise, message = permission_service.verifier_permission(
        code_utilisateur="U0003",
        role="Directeur Général",
        est_responsable=True,
        action="suppression"
    )
    print(f"   DG + suppression : {'✅ Autorisé' if autorise else '❌ Refusé'}")
    if message:
        print(f"   Message : {message}")
    
    # Test 2 : Obtenir l'historique
    print("\n2️⃣ Historique utilisateur...")
    historique = permission_service.obtenir_historique_utilisateur("U0001", limite=5)
    print(f"   📊 {len(historique)} demande(s) trouvée(s)")
    
    # Test 3 : Demandes en attente
    print("\n3️⃣ Demandes en attente...")
    demandes = permission_service.obtenir_demandes_en_attente("U0002")
    print(f"   📊 {len(demandes)} demande(s) en attente")
    
    return True


def test_nettoyage():
    """Test des fonctions de nettoyage."""
    afficher_titre("TEST 4 : Nettoyage automatique")
    
    audit_dao = AuditPermissionDAO()
    tentatives_dao = OTPTentativesDAO()
    
    print("\n1️⃣ Nettoyage des anciennes demandes d'audit...")
    nb_supprime = audit_dao.nettoyer_anciennes_demandes(jours=90)
    print(f"   🧹 {nb_supprime} demande(s) supprimée(s)")
    
    print("\n2️⃣ Nettoyage des anciennes tentatives OTP...")
    nb_supprime = tentatives_dao.nettoyer_anciennes_tentatives(heures=24)
    print(f"   🧹 {nb_supprime} tentative(s) supprimée(s)")
    
    return True


def main():
    """Point d'entrée principal."""
    
    print("\n" + "=" * 70)
    print("  🧪 TESTS DES PERMISSIONS AMÉLIORÉES")
    print("=" * 70)
    
    tests = [
        ("Limitation des tentatives OTP", test_limitation_tentatives),
        ("Système d'audit", test_audit),
        ("Service de permissions", test_permission_service),
        ("Nettoyage automatique", test_nettoyage),
    ]
    
    resultats = []
    
    for nom, test_func in tests:
        try:
            resultat = test_func()
            resultats.append((nom, resultat))
        except Exception as e:
            print(f"\n❌ Erreur lors du test '{nom}' : {e}")
            resultats.append((nom, False))
    
    # Résumé
    afficher_titre("RÉSUMÉ DES TESTS")
    
    print()
    for nom, resultat in resultats:
        statut = "✅ RÉUSSI" if resultat else "❌ ÉCHOUÉ"
        print(f"   {statut} : {nom}")
    
    nb_reussis = sum(1 for _, r in resultats if r)
    nb_total = len(resultats)
    
    print(f"\n   📊 Score : {nb_reussis}/{nb_total} tests réussis")
    
    if nb_reussis == nb_total:
        print("\n   🎉 Tous les tests sont passés avec succès !")
        return 0
    else:
        print("\n   ⚠️  Certains tests ont échoué.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
