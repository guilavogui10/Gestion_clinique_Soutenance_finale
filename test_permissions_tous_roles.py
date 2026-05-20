"""
Script de test des permissions pour tous les rôles
"""
from service_metier.permission_service import PermissionService

def test_permissions_tous_roles():
    """Teste les permissions pour tous les rôles de la base de données."""
    
    service = PermissionService()
    
    # Rôles à tester
    roles = [
        ("medecin", "Médecin"),
        ("infimiere", "Infirmière"),
        ("caissier", "Caissier"),
        ("Ingenieur", "Ingénieur"),
        ("Ingenieur informaticien", "Ingénieur informaticien"),
        ("Directeur Général", "Directeur Général"),
    ]
    
    # Actions à tester
    actions = [
        (service.ACTION_LECTURE, "Lecture"),
        (service.ACTION_IMPRESSION, "Impression"),
        (service.ACTION_CONSULTATION, "Consultation"),
        (service.ACTION_MODIFICATION, "Modification"),
        (service.ACTION_SUPPRESSION, "Suppression"),
    ]
    
    print("=" * 80)
    print("TEST DES PERMISSIONS POUR TOUS LES RÔLES")
    print("=" * 80)
    print()
    
    for role_code, role_nom in roles:
        print(f"\n{'=' * 80}")
        print(f"RÔLE : {role_nom} ({role_code})")
        print(f"{'=' * 80}")
        
        # Test en tant que responsable
        print(f"\n  En tant que RESPONSABLE :")
        print(f"  {'-' * 76}")
        for action_code, action_nom in actions:
            autorise, message = service.verifier_permission(
                code_utilisateur="TEST",
                role=role_code,
                est_responsable=True,
                action=action_code
            )
            
            statut = "✅ AUTORISÉ" if autorise else "❌ REFUSÉ"
            print(f"    {action_nom:20} : {statut}")
            if message:
                print(f"                           → {message}")
        
        # Test en tant que non-responsable
        print(f"\n  En tant que NON-RESPONSABLE :")
        print(f"  {'-' * 76}")
        for action_code, action_nom in actions:
            autorise, message = service.verifier_permission(
                code_utilisateur="TEST",
                role=role_code,
                est_responsable=False,
                action=action_code
            )
            
            statut = "✅ AUTORISÉ" if autorise else "❌ REFUSÉ"
            print(f"    {action_nom:20} : {statut}")
            if message:
                print(f"                           → {message}")
    
    print(f"\n{'=' * 80}")
    print("TEST TERMINÉ")
    print(f"{'=' * 80}\n")
    
    # Résumé
    print("\n📊 RÉSUMÉ DES RÈGLES DE PERMISSIONS :")
    print("-" * 80)
    print("1. Directeur Général & Administrateur → TOUS LES DROITS")
    print("2. Responsable → Lecture, Impression, Consultation, Modification")
    print("                 (Suppression nécessite OTP du DG)")
    print("3. Non-responsable → Lecture, Impression")
    print("                     (Consultation/Modification nécessitent OTP du responsable)")
    print("                     (Suppression nécessite OTP du DG)")
    print("-" * 80)
    print("\n✅ Ces règles s'appliquent à TOUS les rôles de manière uniforme !")
    print()

if __name__ == "__main__":
    test_permissions_tous_roles()
